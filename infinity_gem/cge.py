"""Infinity GEM static CGE model, calibrated to an IFPRI Nexus-style SAM.

The structure follows the IFPRI Standard CGE model (Lofgren, Harris and Robinson, 2002,
"A Standard Computable General Equilibrium (CGE) Model in GAMS", IFPRI Microcomputers in Policy
Research 5), simplified where the Philippine SAM allows:

Production   Each activity combines value added (CES over labour types, land and capital) and
             intermediate inputs (fixed coefficients, Leontief) in fixed proportions.
Outputs      Activities produce commodities in fixed shares (the SAM's make matrix).
Exports      Domestic output is split between exports and domestic sales by a CET function;
             world prices are given (small open economy).
Imports      Domestic demand is for a composite of imports and domestic goods (Armington CES).
Margins      Each unit of composite supply needs trade and transport services (fixed per unit).
Taxes        Import tariffs, sales taxes, a factor tax on capital (2023 SAM) or an activity tax on
             output (2018 SAM, 'atax'; added in 0.3), direct taxes on enterprises and households:
             all at fixed rates.
Households   Ten groups (rural and urban quintiles) receive factor income, enterprise and
             government transfers and remittances; pay taxes; save a fixed share; spend the rest
             in fixed budget shares (Cobb-Douglas), or (0.3, option les=) a Linear Expenditure System with
             Philippine income elasticities (infinity_gem/demand.py).
Government   Fixed real consumption and real transfers; its savings adjust.
Rest of world Foreign savings fixed in foreign currency; the real exchange rate adjusts.
Investment   Closure choice: 'investment' (real investment fixed; household saving rates adjust)
             or 'savings' (saving rates fixed; investment adjusts).
Numeraire    Consumer price index = 1.

Home consumption in the SAM is treated as marketed consumption (see SAM.move_home_consumption_to_market).

Solving
-------
The model is written as a square system F(x) = 0 in activity levels, domestic and composite
prices, factor prices, the exchange rate, a closure variable and a Walras slack. At the benchmark
every residual is zero by construction; after a shock the solver (scipy) finds the new x.
The Walras slack must be zero in every solution: if it is not, the model's accounts do not close.

Usage
-----
>>> from infinity_gem.cge import CGE
>>> m = CGE.from_sam()                 # calibrate to the 2023 SAM
>>> base = m.solve()                   # benchmark (reproduces the SAM)
>>> sim = m.solve({"qinv_scale": {"ccons": 0.9}})   # 10% less construction investment
>>> m.compare(base, sim)
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy.optimize import root

from .sam import SAM

FACTORS = ("flab-n", "flab-p", "flab-s", "flnd", "fcap")
DEFAULT_ELASTICITIES = {"sigma_va": 0.8, "sigma_q": 2.0, "omega_t": 2.0}
# 0.3.13 (pricing='markup'): the activities whose prices clear their markets by default, agriculture, forestry and fishing:
# the SAM activity codes of PSA's industry "Agriculture, forestry, and fishing" (the SAMs' labels: crops, livestock, forestry,
# fisheries; the same list as dynamic.PSA_INDUSTRIES, which check MK1 compares). Every other activity sets a markup price.
MARKET_PRICE_ACTS = ("amaiz", "arice", "apuls", "aoils", "aroot", "avege", "asugr", "atoba", "acott", "afrui", "acoff", "aocrp",
                     "acatt", "apoul", "aoliv", "afore", "afish")


def _by_code(value, codes, default):
    """One elasticity for all codes (a number) or one per code (a dict; missing codes take the default)."""
    if isinstance(value, dict):
        return np.array([float(value.get(c, default)) for c in codes])
    return np.full(len(codes), float(value))


def _pos(x):
    return np.maximum(x, 1e-12)


@dataclass
class Solution:
    x: np.ndarray
    v: dict            # every model variable, as numpy arrays or floats
    ok: bool
    message: str
    residual_max: float
    shocks: dict = field(default_factory=dict)

    def __getitem__(self, k):
        return self.v[k]

    def __contains__(self, k):          # 0.3.11: "QFH" in sol (hoarded labour)
        return k in self.v


class CGE:
    # ================================================================== calibration
    def __init__(self, sam: SAM, elasticities=None, closure="investment", unemployed=(), capital="mobile", les=None,
                 margins="composite", home="market", gov="real", inv="fixed", wage="real", land="mobile",
                 fx="fixed", pricing="flex", sticky_acts=None, hoarding=0.0, energy_nest=None, interest=None, vintage=None,
                 markup_acts=None, labour_cap=False):
        """closure: 'investment' (real investment fixed, saving rates adjust), 'savings' (saving rates
        fixed, investment adjusts) or 'keynesian' (short-run, demand-driven: investment AND saving rates
        fixed; the exchange rate is fixed and serves as numeraire; foreign savings (the current account)
        adjust; unemployed labour types have a fixed real wage, so output and employment are set by
        demand. Without any `unemployed` labour type the closure still solves, but output is then
        supply-determined and the current account absorbs demand shocks).
        closure='interest' (0.3.11, 20 Oct 2026, opt-in; MANAGE-WB's bond market, World Bank PRWP
        11258): a real interest rate r (pp; 0 at the benchmark) clears savings and investment. Real investment demand
        moves by exp(-theta r / 100) and household saving rates by (1 + eps r / 100), with interest={'theta': % of real
        investment per pp, 'eps': % of saving rates per pp}. eps = 0 is the 'savings' closure exactly and theta = 0 the
        'investment' closure (r only re-labels the adjustment; check IR1). theta: the DSGE-CGE link (research/dsge/
        investment_response.py; the CGE link's matched values 1.9-3.3, central about 2).
        unemployed: labour types with a fixed real wage and variable employment, e.g. ('flab-n', 'flab-p').
        capital: 'mobile' (one economy-wide rental rate) or 'fixed' (each activity keeps its capital;
        rental rates differ by activity) - the usual short-run assumption. 'vintage' (0.3.12, 20 Oct 2026, opt-in; MANAGE-WB's capital vintages, Beyene et al. 2025, PRWP 11258): each activity starts the year with its
        OLD capital (shock key 'kscale', as for 'fixed'); a pool of NEW capital (shock key 'knew', a share of the benchmark
        stock) is mobile and earns one rate RN. An activity uses old capital K_old x min(1, (W_a / RN) ** e), with
        vintage={'e': e} (MANAGE-WB's invElas, default 0.7): a contracting activity releases old capital into the pool as
        its rental falls below RN; an expanding one pays RN and hires from the pool (NK_a >= 0, W_a <= RN, complementary).
        The pool, new plus released, is fully employed. e = 0 keeps every activity's old capital in place (only the new pool
        moves; with no new pool this is 'fixed' capital exactly); e -> infinity is 'mobile' (check VN1).
        les: None (Cobb-Douglas household demand, as before) or LES parameters (0.3), e.g.
        infinity_gem.demand.les_briones2023(): {'eta': {commodity: income elasticity}, 'own_price': {...},
        'fit': 'all'|'food'} or with an explicit 'frisch' (a number or {household: value}). See infinity_gem/demand.py.
        margins: 'composite' (default, as before: trade and transport margins are charged per unit of the composite
        good, after the import/domestic choice) or 'split' (0.3, verification Phase 3: IFPRI's treatment, Lofgren
        et al. 2002 eq. 1, 3 and 27: the margin is added to the import price and to the domestic demand price
        BEFORE buyers choose between them; the SAM's margin on each good is shared between domestic sales and
        imports in proportion to their values, as in validation/ifpri/build_ifpri_inputs.py; no export margins,
        because the SAM records none).
        home: 'market' (default, as before: the SAM's home consumption, households' own produce, is treated as if bought
        on the market; SAM.move_home_consumption_to_market) or 'separate' (0.3.1, verification Phase 3: IFPRI's
        treatment, Lofgren et al. 2002 eq. 18 and 34: own produce is valued at the producer price PX and consumed
        directly, with no trade margin, sales tax or import competition; marketed output = gross output - home use;
        a fixed share of each household's budget, as for market goods; CPI weights cover market purchases only, as
        in IFPRI's code). Not yet combined with les=.
        gov: 'real' (default: fixed real government consumption; government saving adjusts) or 'cd' (0.3.1, Hosoe
        et al. 2010 stdcge: the government saves a fixed share of its revenue and spends the rest in fixed value shares).
        inv: 'fixed' (default: fixed real proportions) or 'value_shares' (Hosoe et al.: fixed value shares of total
        savings). Both options exist for the Hosoe cross-check (validation/hosoe/, check V5).
        wage: how the wage of the `unemployed` labour types is fixed (0.3.4). 'real' (default,
        as before): indexed one-for-one to the CPI within the period, W = wbar x CPI. 'nominal': fixed in pesos for the
        period, W = wbar (sticky pay: Philippine wages are set in nominal pesos by the regional wage boards and adjusted
        about once a year). The two differ only in the Keynesian closure; elsewhere the CPI is the numeraire.
        land: 'mobile' (default, as before: one economy-wide land rent, land moves between crops) or 'fixed' (0.3.7: each activity keeps its land within the period and land rents differ by activity, as capital
        does under capital='fixed'; a season's land is planted before the weather is known). With 'fixed', the shock
        key 'lscale' {activity: factor} sets the EFFECTIVE land each activity has (e.g. a drought: rice 0.9 = a tenth
        of the rice land's effective use lost to lack of water).
        fx: the exchange rate in the Keynesian closure (0.3.8, 17 Oct 2026 D1). 'fixed' (default, as
        before): the exchange rate is fixed (the numeraire) and foreign savings, the current account, absorb any change in the
        import bill. 'flexible': foreign savings stay at the level of the shock key 'fsav_scale' and the exchange rate adjusts
        (a balance-of-payments constraint); needs wage='nominal' and at least one `unemployed` labour type, whose peso wage is
        then the nominal anchor.
        Incomplete pass-through of the peso to import prices (0.3.13, 23 Oct 2026, P2(b) of docs/design/MARKUP_DEMAND_SIDE_
        PROPOSAL_22Oct2026.md, opt-in; the Keynesian closure with the fixed peso only): the shock keys 'erpt' (phi: one share, or
        {commodity: share}, commodities not listed 1) and 'exr_ref' (the peso at which foreign suppliers anchor their peso prices;
        default 1, the benchmark's) set the import price PM = pwm x exr_ref x (EXR / exr_ref) ** phi x (1 + tm): the foreign
        supplier absorbs the share 1 - phi of a move of the peso within the period (pricing to market), so its US$ price, pwm x
        (EXR / exr_ref) ** (phi - 1), is what the current account pays. Re-exports keep the world price (they are not sold here).
        The key left out (or phi = 1) is the model as before. BSP DP 2025-16 (Parmanand, Platitas, Castanares and Dacio, Dec 2025,
        Table 5): pass-through of a depreciation to inflation 0.10 in the short run, 0.75 in the long run. Check ER1.
        A within-year share of the world price reaching domestic import prices (0.3.13, 23 Oct 2026, opt-in; next step 1 in a review note (not included); the Keynesian closure only): the shock keys 'oil_pass'
        (omega: one share, or {commodity: share}, commodities not listed 1) and 'oil_ref' (R: the reference world price in pesos,
        pwm x EXR at the reference; one number or {commodity: value}; default 1, the benchmark's) set the domestic peso price of those
        imports, before the tariff, to R x (pwm x EXR / R) ** omega, and PM = that x (1 + tm) (plus the margin with 'split'): within the
        period only the share omega of a move of the world price in pesos (a world price or a peso change) reaches buyers at home.
        The country still pays the world price (the current account pays pwm), so the government absorbs the rest at the border:
        MTAX = tm x (domestic price) x QM - (pwm x EXR - domestic price) x QM, a subsidy when the world price is above R and a levy
        when it is below (reported: 'OILSUB' by commodity, 'PM_dom'). It stands for what keeps retail fuel prices from rising in
        proportion to world fuel prices within the year, mainly the excise, a fixed peso amount per litre (the model's sales tax is
        ad valorem, so the revenue it books rises with the price where the excise's does not), and lags in retail prices; it is
        calibrated to PSA's retail fuel CPI against world fuel prices in pesos in 2022 and 2026 (scenarios/row83_oil_passthrough.py).
        A share of 1, or the keys left out, is the model as before; a commodity may not carry both 'erpt' and 'oil_pass'. Check OP1.
        pricing: how activity prices are set in the Keynesian closure (0.3.8, review D2). 'flex' (default, as before): zero
        profit, so prices follow full unit cost, including the rents of fixed capital, which fall when demand falls. 'sticky':
        prices of the activities in `sticky_acts` (a list of activity codes; required) are rigid downward: a rise in unit cost
        is passed on in full, but of a fall below the anchor only the share (1 - stickiness) is passed on ("prices rise faster
        than they fall": Peltzman 2000, Journal of Political Economy 108(3); 16 Oct 2026). With c = unit cost (zero-profit cost, as in 'flex') and A the
        anchor (shock key 'pa_anchor' {activity: unit revenue PA (1 - ta)}; default the benchmark's), unit revenue is
            PA (1 - ta) = c + stickiness x A x f((A - c) / A),   f(z) = max(0, z), smoothed for 0 < z < 1e-4 (f(0) = 0),
        with 'stickiness' a shock key (0 = flexible, the default value; 1 = no fall at all). The gap between price and cost is
        profit, paid to capital (operating surplus), so the accounts still close; quantities stay on the production function.
        pricing='markup' (0.3.13, 22 Oct 2026, opt-in; docs/design/SR_PRICE_FORMATION_markup_passthrough_
        DESIGN_21Oct2026.md, option (c) of the design, 22 Oct 2026: stickiness and markup together form the
        short-run price setting): the structuralist short run, flex-price farms and fix-price industry and services (Taylor 1983,
        Structuralist Macroeconomics; Dervis, de Melo and Robinson 1982, ch. 6; in the Philippines C. Bautista's 1987 UPSE model,
        reviewed in Cororaton 1994, PIDS DP 94-03, pp. 70-76). The activities in `markup_acts` (default: every activity except
        agriculture, forestry and fishing, MARKET_PRICE_ACTS, and except pure exporters) set the price of their home sales as a
        markup over unit variable cost,
            PDS (1 - ta) = (1 + mu) x AVC,   AVC = sum over labour types of W x (labour per unit of output) + sum over inputs of PQ x ica,
        mu being the shock key 'markup' ({activity: mu}; default the benchmark's capital income / variable cost). For an activity
        that does not export PDS is its output price, PA (1 - ta) = (1 + mu) x AVC (the design note's equation). Exports are sold
        at world prices: they follow the CET's own relative-price rule, QE = r(PE / PDS) x reference home sales (shock key
        'mk_qd'; default the SAM's), so world demand, not home demand, sets them (the structuralist export function, elasticity
        omega); home sales are the rest of output (the CET inverted). (Setting the markup on PA instead forced the home price of an
        exporter to move by 1 / (its home share) times the cost change, and has no solution for a pure exporter: tried and
        dropped, 22 Oct 2026.) A pure exporter (no home sales: on the 2023 SAMs machinery and electronics, amach) keeps its
        zero-profit price. Their installed
        technology is Leontief in utilisation: labour per unit of output is fixed at the reference technology (shock key 'mk_coef',
        factor use per unit of output at TFP 1, factors x activities; default the SAM's), divided by TFP; output follows demand;
        capital stays installed (capital='fixed' is required) and its rent RK (per unit of installed capital) is the residual,
        revenue less variable cost, so neither demand nor the rent feeds back into these prices; the capital market clears by
        utilisation (reported as UTIL = capital services needed at the reference technology / installed capital; no ceiling).
        A cost change passes into these prices as (1 + mu) times its change per unit (the structuralist markup on prime cost), so
        their pass-through is that of the input-output price model written on shares of VARIABLE cost. The shock key 'mk_pass'
        (lam; default 1) charges the markup on only the share lam of a cost change: home unit revenue = AVC + mu x (lam x AVC +
        (1 - lam) x A / (1 + mu)), A the anchor; lam = 0 keeps the margin per unit fixed in pesos, so the cost push is the plain
        input-output price model's (check I1's formula on the SAM), as regulated prices pass fuel on (ERC's generation charge,
        LTFRB fares); both are homogeneous, the margin being tied to the anchor. A pass-through that depends on the output gap
        (0.3.13, 23 Oct 2026, P6 of a design note (not included); shock keys 'mk_gap' = s and 'mk_gdp'
        = Y_ref): the margin per unit is mu x (A / (1 + mu) + lam_e x (AVC - A / (1 + mu))) with lam_e = lam + s x g, g = 100 x
        (Y / Y_ref - 1) the output gap in percent, Y real GDP at benchmark prices (as gdp()) and Y_ref its reference (default the
        benchmark's). With s > 0 margins absorb more of a cost rise in a slump and pass more of it on in a boom (state-dependent
        pass-through); with costs at the reference the margin is the reference margin whatever the gap. s = 0 (default) is the
        rule above exactly. Check MG1. The other activities keep
        zero-profit prices ('flex'). Downward stickiness stays available on top (shock keys 'stickiness' and 'pa_anchor', as for
        'sticky'): for the activities in `sticky_acts` (default: the markup activities) only the share (1 - stickiness) of a fall
        of the markup price (1 + mu) x AVC below the anchor is passed on; stickiness 0 (default) = pure markup. Markup activities
        may not use land; not combined with energy_nest or home='separate' yet. CGE.markup_at() centres the markups, the installed
        technology, the reference home sales and the stickiness anchor on another solution (the dynamic model's baseline year).
        Check MK1.
        hoarding: paid labour hoarding in the Keynesian closure (0.3.11; Rotemberg and Summers 1990, Quarterly
        Journal of Economics 105(4); Biddle 2014, Journal of Economic Perspectives 28(2)). 0 (default) = none, results unchanged.
        With h > 0 and the shock key 'hoard_ref' (labour by factor and activity of the reference year, e.g. the baseline's),
        when an activity's labour demand QF falls below its reference the share h of the shortfall stays employed and paid
        but does not produce: QFH = h x ref x f((ref - QF) / ref), f(z) = max(0, z) smoothed for 0 < z < 1e-4, for the
        `unemployed` (fixed-wage) labour types only, and scaled down so that a type's hoarded total never exceeds its slack
        (supply - productive employment; 19 Oct 2026: no idle workers at full employment). Employment
        (EMP, the labour markets and the wage curve's slack) and labour income include QFH; its wage bill is paid out of capital
        income (lower profits), so value added, GDP and every account are unchanged in total. Evidence (PSA, 2026): real GVA in
        construction −9.5% y/y in H1 while LFS construction jobs fell 0.8% and mean hours 0.17%.
        labour_cap: the employment cap as one smooth complementarity condition (0.3.13, 23 Oct 2026, opt-in; step 2 of a design note (not included), section 3; the Keynesian closure with the fixed peso only). False (default)
        = as before: employment of the `unemployed` (fixed-wage) labour types follows demand without a ceiling (the dynamic model's
        employment cap, if any, switches a type to market clearing between solves). True: each fixed-wage type k gets a wage premium
        LP_k (unknown, slice 'LCAP') with W_k = wbar_k x (CPI if wage='real' else 1) x (1 + LP_k), and the complementarity
            E_k <= S_k,  LP_k >= 0,  (S_k - E_k) x LP_k = 0,
        E_k its PRODUCTIVE employment (labour demand QF summed over activities), S_k = QFS0_k x qfs_scale_k its cap (the labour
        supply), written as the Fischer-Burmeister residual a + b - sqrt(a^2 + b^2 + 2e-20) with a = (S_k - E_k) / QFS0_k and
        b = LP_k (smoothed as capital='vintage', check VN1). Paid hoarding (hoarding > 0) is bounded by the slack S_k - E_k, so
        employment with hoarded labour (EMP) stays at most S_k and a type at its cap hoards nothing, as the switching rule had it (a
        capped type there clears its market and does not hoard; a cap on EMP itself would leave hoarding free to fill any gap at
        the cap, a continuum of solutions). Below the cap LP_k = 0 to about 1e-18 (the model as before); at the cap the wage rises
        above its anchor and employment equals S_k, the market-clearing regime, with no switching between models. Reported:
        'LPREM' (by factor; 0 for the others). Check EC1."""
        if not 0.0 <= hoarding < 1.0:
            raise ValueError("hoarding must be in [0, 1)")
        if hoarding > 0 and closure != "keynesian":
            raise ValueError("hoarding is an option of the Keynesian (short-run) closure")
        self.hoarding = float(hoarding)
        if fx not in ("fixed", "flexible"):
            raise ValueError("fx must be 'fixed' or 'flexible'")
        if pricing not in ("flex", "sticky", "markup"):
            raise ValueError("pricing must be 'flex', 'sticky' or 'markup'")
        if (fx == "flexible" or pricing == "sticky") and closure != "keynesian":
            raise ValueError("fx='flexible' and pricing='sticky' are options of the Keynesian (short-run) closure")
        if pricing == "markup" and (closure != "keynesian" or capital != "fixed"):    # 0.3.13
            raise ValueError("pricing='markup' is an option of the Keynesian (short-run) closure with capital='fixed'")
        if pricing == "markup" and energy_nest is not None:
            raise NotImplementedError("pricing='markup' is not combined with energy_nest yet")
        if markup_acts is not None and pricing != "markup":
            raise ValueError("markup_acts needs pricing='markup'")
        if fx == "flexible" and (wage != "nominal" or not unemployed):
            raise ValueError("fx='flexible' needs wage='nominal' and an unemployed labour type (the peso wage anchors prices)")
        if pricing == "sticky" and not sticky_acts:
            raise ValueError("pricing='sticky' needs sticky_acts (the activities whose prices are rigid downward)")
        self.fx, self.pricing = fx, pricing
        if land not in ("mobile", "fixed"):
            raise ValueError("land must be 'mobile' or 'fixed'")
        self.land = land
        if wage not in ("real", "nominal"):
            raise ValueError("wage must be 'real' or 'nominal'")
        self.wage = wage
        if margins not in ("composite", "split"):
            raise ValueError("margins must be 'composite' or 'split'")
        if home not in ("market", "separate"):
            raise ValueError("home must be 'market' or 'separate'")
        if home == "separate" and les is not None:
            raise NotImplementedError("home='separate' with les= is not built yet")
        self.margins = margins
        self.home = home
        if gov not in ("real", "cd") or inv not in ("fixed", "value_shares"):
            raise ValueError("gov must be 'real' or 'cd'; inv must be 'fixed' or 'value_shares'")
        self.gov, self.inv = gov, inv
        el = dict(DEFAULT_ELASTICITIES)
        el.update(elasticities or {})
        # 0.3: each elasticity may be one number (all sectors, as before) or a dict {code: value} by activity
        # (sigma_va) or commodity (sigma_q, omega_t); codes missing from a dict take the default value.
        # sigma_va exactly 1 selects the Cobb-Douglas limit (closed form); values within 1e-6 of 1 but not 1 are refused.
        for k in ("sigma_va", "sigma_q"):
            vals = el[k].values() if isinstance(el[k], dict) else [el[k]]
            if any(abs(v - 1.0) < 1e-6 and not (k == "sigma_va" and v == 1.0) for v in vals):
                raise ValueError(f"{k} = 1 (Cobb-Douglas) divides by zero in the CES formulas; use 0.99 or 1.01")
        self.el = el
        self.closure = closure
        if closure == "interest":                    # 0.3.11
            iv = dict(interest or {})
            if set(iv) - {"theta", "eps"} or min(iv.get("theta", 0.0), iv.get("eps", 0.0)) < 0 or                     not (iv.get("theta", 0.0) > 0 or iv.get("eps", 0.0) > 0):
                raise ValueError("closure='interest' needs interest={'theta': >= 0, 'eps': >= 0}, not both 0")
        self.interest = {"theta": float((interest or {}).get("theta", 0.0)), "eps": float((interest or {}).get("eps", 0.0))}
        self.unemployed = list(unemployed)
        if labour_cap and (closure != "keynesian" or not unemployed):     # 0.3.13 (check EC1)
            raise ValueError("labour_cap is an option of the Keynesian (short-run) closure with fixed-wage ('unemployed') labour types")
        if labour_cap and fx == "flexible":
            raise ValueError("labour_cap needs fx='fixed': with every fixed-wage type at its cap no peso wage would anchor prices")
        self.labour_cap = bool(labour_cap)
        if capital not in ("mobile", "fixed", "vintage"):
            raise ValueError("capital must be 'mobile', 'fixed' or 'vintage'")
        self.capital = capital
        self.vint_e = None
        if capital == "vintage":                     # 0.3.12
            self.vint_e = float((vintage or {}).get("e", 0.7))
            if self.vint_e < 0:
                raise ValueError("vintage={'e': ...} needs e >= 0 (MANAGE-WB's invElas, default 0.7; 0 = old capital stays put)")
        self.sam0 = sam
        s = sam.move_home_consumption_to_market()
        self.sam = s
        t = s.table
        self.has_ftax, self.has_atax = "ftax" in t.index, "atax" in t.index
        self.A = s.accounts("a")
        self.C = s.accounts("c")
        self.H = s.accounts("hhd")
        self.F = [f for f in FACTORS if f in t.index]
        A, C, H, F = self.A, self.C, self.H, self.F
        nA, nC = len(A), len(C)

        # ---- production
        self.QA0 = t.loc[A].sum(axis=1).values                      # activity output (row = col totals)
        # activity tax on the value of output (2018 SAM); zero when the SAM has no 'atax' account (2023)
        self.ta = t.loc["atax", A].values / self.QA0 if self.has_atax else np.zeros(nA)
        self.ica = (t.loc[C, A].values / self.QA0)                  # C x A
        self.QF0 = t.loc[F, A].values                               # F x A (value units, WF0 = 1)
        self.QVA0 = self.QF0.sum(axis=0)
        self.iva = self.QVA0 / self.QA0
        self.delta = self.QF0 / np.where(self.QVA0 == 0, 1, self.QVA0)   # CES share parameters (sum to 1)
        self.use = self.QF0 > 0
        self.sigva = _by_code(el["sigma_va"], A, DEFAULT_ELASTICITIES["sigma_va"])
        self.tfp = np.ones(nA)
        self.QFS0 = self.QF0.sum(axis=1)                            # factor supplies
        # 0.3.11 (19 Oct 2026; MANAGE-WB's top node, Beyene et al. 2025, Figure 2.1): value added and energy
        # in one CES bundle per activity (elasticity sigma_ve), the energy commodities substitutable in a lower CES (sigma_e);
        # other intermediates stay Leontief. energy_nest = {"energy": [commodity codes], "sigma_ve": s1, "sigma_e": s2}.
        # None = as before (R0 unchanged). Benchmark prices are 1, so the shares calibrate from the SAM's cost shares.
        self.en = None
        if energy_nest is not None:
            E = [C.index(c) for c in energy_nest["energy"] if c in C]
            s1, s2 = float(energy_nest["sigma_ve"]), float(energy_nest["sigma_e"])
            if not E:
                raise ValueError("energy_nest: none of its energy commodities is in the SAM")
            if min(s1, s2) <= 0 or min(abs(s1 - 1), abs(s2 - 1)) < 1e-6:
                raise ValueError("energy_nest: elasticities must be positive and not 1 (use 0.99 or 1.01)")
            e0 = self.ica[E].sum(axis=0)                            # energy per unit of output, by activity
            ive = self.iva + e0
            safe = lambda x: np.where(x > 0, x, 1.0)
            ica_ne = self.ica.copy()
            ica_ne[E] = 0.0
            self.en = dict(E=np.array(E), s1=s1, s2=s2, ica_ne=ica_ne, ive=ive, has=e0 > 0,
                           dva=np.where(ive > 0, self.iva / safe(ive), 1.0), den=np.where(ive > 0, e0 / safe(ive), 0.0),
                           de=np.where(e0 > 0, self.ica[E] / safe(e0), 0.0))

        # ---- make matrix, output and trade
        make = t.loc[A, C].values                                   # A x C: activity a's sales of commodity c
        self.theta = make / self.QA0[:, None]
        # 0.3.1 (home='separate'): home consumption by commodity and household at benchmark prices (PX0 = 1), read
        # from the SAM's activity -> household cells before they were moved to the market; zero by default
        self.HC = np.zeros((nC, len(H)))
        if home == "separate":
            t0 = sam.table
            for a in A:
                for j, h in enumerate(H):
                    if h in t0.columns and t0.loc[a, h]:
                        self.HC[C.index("c" + a[1:]), j] = t0.loc[a, h]
        hcs = self.HC.sum(axis=1)
        self.QX0 = make.sum(axis=0) - hcs                           # marketed output (= all output by default)
        self.QE0 = t.loc[C, "row"].values
        self.QD0 = self.QX0 - self.QE0
        self.QM0 = t.loc["row", C].values
        mtax = t.loc["mtax", C].values
        stax = t.loc["stax", C].values
        trc = t.loc["trc", C].values
        # Re-exports: where recorded exports exceed domestic output (e.g. electronics, 'cmach'), the
        # excess is treated as imported goods exported again at world prices, with no tariff, margin or
        # domestic value added. They enter both sides of the current account in fixed quantities.
        self.rex = np.maximum(self.QE0 - self.QX0, 0.0)
        self.QE0 = self.QE0 - self.rex
        self.QM0 = self.QM0 - self.rex
        if (self.QM0 < -1e-9).any():
            raise ValueError("Re-exports exceed imports")
        self.QD0 = np.maximum(self.QX0 - self.QE0, 0.0)
        uses = ["trc"] + H + ["gov", "s-i", "dstk"]
        self.QQ0 = t.loc[C, A].sum(axis=1).values + t.loc[C, uses].sum(axis=1).values - hcs
        with np.errstate(divide="ignore", invalid="ignore"):
            self.tm = np.where(self.QM0 > 0, mtax / np.where(self.QM0 > 0, self.QM0, 1), 0.0)
            base = self.QD0 + self.QM0 + mtax + trc
            self.tq = np.where(base > 0, stax / np.where(base > 0, base, 1), 0.0)
            self.icq = np.where(self.QQ0 > 0, trc / np.where(self.QQ0 > 0, self.QQ0, 1), 0.0)
        if ((mtax > 1e-9) & (self.QM0 <= 0)).any():
            raise ValueError("Import tax without imports")
        gap = self.QQ0 - (self.QD0 + self.QM0 + mtax + trc + stax)
        if np.abs(gap).max() > 1e-6:
            raise ValueError(f"Commodity accounts do not close (max gap {np.abs(gap).max():.3g})")
        msrv = t.loc[C, "trc"].values
        self.sm = msrv / msrv.sum() if msrv.sum() > 0 else np.zeros(nC)   # margin services mix (none in a SAM without margins)
        self.pwm = np.ones(nC)
        self.pwe = np.ones(nC)

        # masks
        self.hasX = self.QX0 > 1e-12
        self.hasE = self.QE0 > 1e-12
        self.hasD = self.QD0 > 1e-12
        self.hasM = self.QM0 > 1e-12
        self.hasQ = self.QQ0 > 1e-12

        # CET (exports vs domestic sales), only where both exist
        om = el["omega_t"]
        self.omega = _by_code(om, C, DEFAULT_ELASTICITIES["omega_t"])
        self.rt = (self.omega + 1) / self.omega
        both = self.hasE & self.hasD
        self.gam = np.full(nC, 0.5)
        self.gamc = np.full(nC, 0.5)          # 1 - gam, computed directly (0.3: stable for low CET elasticities)
        self.kgam = np.ones(nC)               # (1 - gam) / gam
        self.at = np.ones(nC)
        r0 = np.where(both, self.QE0 / np.where(self.hasD, self.QD0, 1), 1.0)
        self.kgam[both] = r0[both] ** (1.0 / self.omega[both])
        self.gam[both] = 1.0 / (1.0 + self.kgam[both])
        self.gamc[both] = self.kgam[both] / (1.0 + self.kgam[both])
        g, rt = self.gam, self.rt
        self.at[both] = self.QX0[both] / (g[both] * self.QE0[both] ** rt[both]
                                          + self.gamc[both] * self.QD0[both] ** rt[both]) ** (1 / rt[both])

        # Armington (imports vs domestic), only where both exist
        sq = el["sigma_q"]
        self.sigq = _by_code(sq, C, DEFAULT_ELASTICITIES["sigma_q"])
        mix = self.hasM & self.hasD
        # 0.3 (margins='split'): margin per unit of domestic sales and of imports (IFPRI icd = icm here); zero by default
        with np.errstate(divide="ignore", invalid="ignore"):
            dm = self.QD0 + self.QM0
            self.icx = np.where(dm > 0, trc / np.where(dm > 0, dm, 1), 0.0) if margins == "split" else np.zeros(nC)
        PM0 = 1 + self.tm + self.icx                     # margin-inclusive import price (= 1 + tm by default)
        PDD0 = 1 + self.icx                              # margin-inclusive domestic demand price (= 1 by default)
        self.dq = np.zeros(nC)
        self.aq = np.ones(nC)
        ratio = np.where(mix, self.QM0 / np.where(self.hasD, self.QD0, 1) * (PM0 / PDD0) ** self.sigq, 0.0)
        self.dq[mix] = ratio[mix] / (1 + ratio[mix])
        V0 = PM0 * self.QM0 + PDD0 * self.QD0
        PARM0 = np.where(self.hasQ, V0 / np.where(self.hasQ, self.QQ0, 1), 1.0)
        s_ = self.sigq
        self.aq[mix] = (self.dq[mix] * PM0[mix] ** (1 - s_[mix]) + (1 - self.dq[mix]) * PDD0[mix] ** (1 - s_[mix])) \
            ** (1 / (1 - s_[mix])) / PARM0[mix]
        # import-only and domestic-only composites: X = QQ with a fixed price wedge
        self.k_m = np.where(self.hasM & ~self.hasD, PARM0 / np.where(PM0 > 0, PM0, 1), 1.0)
        self.k_d = np.where(self.hasD & ~self.hasM, PARM0 / PDD0, 1.0)

        # ---- institutions
        v = lambda r, c: s.v(r, c) if (r in t.index and c in t.columns) else 0.0   # missing account = 0
        self.frow_in = np.array([v(f, "row") for f in F])          # factor income from abroad (FCU)
        self.frow_out = np.array([v("row", f) for f in F])
        YF0 = self.QFS0 + self.frow_in
        self.tf = np.array([v("ftax", f) for f in F]) / YF0
        dist0 = (1 - self.tf) * YF0 - self.frow_out
        self.inst = H + ["ent"]
        self.shif = np.array([[v(i, f) / dist0[k] for k, f in enumerate(F)] for i in self.inst])   # I x F
        # enterprises
        self.trg_ent = v("ent", "gov")
        self.erow_in = v("ent", "row")
        YE0 = sum(v("ent", f) for f in F) + self.trg_ent + self.erow_in
        self.te = v("dtax", "ent") / YE0
        self.she = np.array([v(h, "ent") for h in H]) / YE0
        self.sheg = v("gov", "ent") / YE0
        self.erow_out = v("row", "ent")
        # households
        self.trg_h = np.array([v(h, "gov") for h in H])
        self.hrow_in = np.array([v(h, "row") for h in H])
        YH0 = t.loc[H].sum(axis=1).values
        self.tins = np.array([v("dtax", h) for h in H]) / YH0
        self.tgh = np.array([v("gov", h) for h in H]) / YH0
        self.hrow_out = np.array([v("row", h) for h in H])
        DY0 = YH0 * (1 - self.tins - self.tgh) - self.hrow_out
        self.mps = np.array([v("s-i", h) for h in H]) / DY0
        EH0 = DY0 * (1 - self.mps)
        self.beta = (t.loc[C, H].values - self.HC) / EH0            # C x H budget shares (market purchases)
        self.beta_h = self.HC / EH0                                 # C x H budget shares of own produce (0 by default)
        self.les = None
        if les is not None:                                         # 0.3: Linear Expenditure System
            from .demand import fit_frisch
            eta0 = np.array([float(les["eta"].get(c, 1.0)) for c in C])
            q0 = t.loc[C, H].values                                 # benchmark quantities (benchmark prices = 1)
            mb, gam, frisch, aggs = np.zeros_like(q0), np.zeros_like(q0), [], []
            for h in range(len(H)):
                w = self.beta[:, h]
                agg = float(w @ eta0)
                e = eta0 / agg                                      # Engel aggregation: w @ e = 1
                if "frisch" in les:
                    fr = les["frisch"]
                    phi = float(fr[H[h]] if isinstance(fr, dict) else fr)
                else:
                    eps = np.array([float(les["own_price"].get(c, -1.0)) for c in C])
                    mask = None
                    if les.get("fit", "all") == "food":
                        from .demand import FOOD
                        mask = np.array([c in FOOD for c in C])
                    phi = fit_frisch(w, e, eps, mask)
                mb[:, h] = e * w                                    # marginal budget shares (sum to 1)
                gam[:, h] = q0[:, h] - mb[:, h] * (-EH0[h] / phi)   # subsistence quantities
                frisch.append(phi); aggs.append(agg)
            if (q0 - gam < -1e-9).any():
                raise ValueError("LES calibration gives negative supernumerary quantities")
            self.les = dict(mb=mb, gamma=gam, frisch=np.array(frisch), engel_sum=np.array(aggs))
        # government
        self.qg = t.loc[C, "gov"].values
        self.grow_in = v("gov", "row")
        self.grow_out = v("row", "gov")
        if gov == "cd":                     # Hosoe: Sg = ssg * revenue; consumption = fixed value shares of the rest
            YG0 = float(t.loc["gov"].sum())                           # total government receipts (row total)
            self.ssg = v("s-i", "gov") / YG0
            self.gsh = self.qg / self.qg.sum()
        # investment, stocks, foreign savings
        self.qinv = t.loc[C, "s-i"].values
        self.qdst = t.loc[C, "dstk"].values
        self.fsav = v("s-i", "row")
        # CPI weights (household consumption)
        hc = t.loc[C, H].sum(axis=1).values - hcs                   # market purchases (all purchases by default)
        self.cwts = hc / hc.sum()
        self.YH0, self.YE0, self.EH0 = YH0, YE0, EH0
        # 0.3.8 (pricing='sticky', review D2): activities whose prices are rigid downward
        self.isST = np.array([a in (sticky_acts or ()) for a in A]) if pricing == "sticky" else np.zeros(nA, bool)
        # 0.3.13 (pricing='markup'): the markup activities, their benchmark markups (capital income / variable cost, variable
        # cost = labour and intermediate inputs at benchmark prices) and their installed technology (factor use per unit of output)
        self.isMK, self.mu0, self.mk_coef0 = np.zeros(nA, bool), np.zeros(nA), None
        if pricing == "markup":
            if home != "market":
                raise NotImplementedError("pricing='markup' is not combined with home='separate' yet")
            acts = [a for a in A if a not in MARKET_PRICE_ACTS] if markup_acts is None else list(markup_acts)
            bad = [a for a in acts if a not in A]
            if bad:
                raise ValueError(f"markup_acts: not activities of this SAM: {bad}")
            # A markup activity sets the price of its sales AT HOME: it must make one commodity (the SAMs' make matrices are
            # diagonal) that has domestic sales. A pure exporter (on the 2023 SAMs machinery and electronics, amach: all its output
            # is exported) sells at world prices and keeps its zero-profit price; the default leaves it out, a list naming it is refused.
            com = np.argmax(self.theta, axis=1)
            one = ((self.theta > 1e-12).sum(axis=1) == 1) & np.isclose(self.theta[np.arange(nA), com], 1.0, rtol=0, atol=1e-12)
            exp_only = [a for i, a in enumerate(A) if a in acts and one[i] and not self.hasD[com[i]]]
            if markup_acts is None:
                acts = [a for a in acts if a not in exp_only]
            elif exp_only:
                raise ValueError(f"markup_acts: {exp_only} sell only abroad (no domestic sales): their price is the world price")
            multi = [a for i, a in enumerate(A) if a in acts and not one[i]]
            if multi:
                raise ValueError(f"markup_acts: {multi} make more than one commodity (not built: the 2023 SAMs' make matrices are diagonal)")
            self.isMK = np.array([a in acts for a in A])
            self.mk_com = com                                                   # the commodity each activity makes
            self.mkC = np.zeros(nC, bool)
            self.mkC[com[self.isMK]] = True                                     # commodities priced by a markup at home
            if "flnd" in F and (self.QF0[F.index("flnd")][self.isMK] > 0).any():
                raise ValueError("pricing='markup': markup activities may not use land: "
                                 f"{[a for i, a in enumerate(A) if self.isMK[i] and self.QF0[F.index('flnd'), i] > 0]}")
            self.isST = np.array([a in (acts if sticky_acts is None else sticky_acts) for a in A])
            kc_ = F.index("fcap")
            self.mk_lab = [k for k, f in enumerate(F) if f.startswith("flab")]    # the variable factors: labour
            self.mk_coef0 = self.QF0 / self.QA0[None, :]
            vc = self.QF0[self.mk_lab].sum(axis=0) + self.ica.sum(axis=0) * self.QA0
            self.mu0 = np.where(self.isMK & (vc > 0), self.QF0[kc_] / np.where(vc > 0, vc, 1.0), 0.0)
            self.hasK = self.QF0[kc_] > 0
            # 0.3.13 (P6): real GDP at the benchmark (as gdp(): household, government, investment and stocks, exports less
            # imports, at benchmark prices 1), the default reference of 'mk_gdp'
            self.real_gdp0 = float(t.loc[C, H].values.sum() + self.qg.sum() + self.qinv.sum() + self.qdst.sum() + self.QE0.sum()
                                   - self.QM0.sum())
            self.iMK = np.where(self.isMK)[0]
            self.iMKK = np.where(self.isMK & self.hasK)[0]                     # markup activities with installed capital

        # ---- unknown vector layout
        self.iD = np.where(self.hasD)[0]
        self.iQ = np.where(self.hasQ)[0]
        self.nF_active = [k for k in range(len(F)) if self.QFS0[k] > 0]
        self.kcap = F.index("fcap")
        self.klnd = F.index("flnd") if "flnd" in F else None      # SAMs without land (e.g. Hosoe's test SAM): no land
        if self.land == "fixed" and self.klnd is None:
            raise ValueError("land='fixed' needs a SAM with a land factor ('flnd')")
        self.iFM = [k for k in self.nF_active if F[k] not in self.unemployed
                    and not (k == self.kcap and self.capital in ("fixed", "vintage"))
                    and not (k == self.klnd and self.land == "fixed")]
        self.iU = [k for k in self.nF_active if F[k] in self.unemployed]
        self.iK = np.where(self.QF0[self.kcap] > 0)[0] if self.capital in ("fixed", "vintage") else np.array([], dtype=int)
        self.iL = np.where(self.QF0[self.klnd] > 0)[0] if self.land == "fixed" else np.array([], dtype=int)
        self._layout()

    def _layout(self):
        nA = len(self.A)
        sizes = [("QA", nA), ("PDS", len(self.iD)), ("PQ", len(self.iQ)), ("WF", len(self.iFM)),
                 ("RK", len(self.iK)), ("RL", len(self.iL)),
                 ("NK", len(self.iK) if self.capital == "vintage" else 0), ("RN", 1 if self.capital == "vintage" else 0),   # 0.3.12
                 ("EXR", 1), ("CLOS", 0 if self.closure == "keynesian" else 1),
                 ("GADJ", 1 if self.gov == "cd" else 0), ("WALRAS", 1),
                 ("LCAP", len(self.iU) if getattr(self, "labour_cap", False) else 0)]   # 0.3.13: wage premia at the cap
        self.slices, pos = {}, 0
        for k, n in sizes:
            self.slices[k] = slice(pos, pos + n)
            pos += n
        self.n = pos

    @classmethod
    def from_sam(cls, path=None, **kw):
        """Calibrate to a SAM file (default: 2023). A SAM published in rounded figures (2018) is balanced first
        (SAM.load_for_model); the 2023 SAM is used exactly as before."""
        return cls(SAM.load_for_model(path), **kw)

    # ================================================================== model equations
    def x0(self):
        x = np.zeros(self.n)
        x[self.slices["QA"]] = 1.0          # activity levels relative to benchmark
        x[self.slices["PDS"]] = 1.0
        x[self.slices["PQ"]] = 1.0
        x[self.slices["WF"]] = 1.0
        x[self.slices["RK"]] = 1.0
        x[self.slices["RL"]] = 1.0
        x[self.slices["RN"]] = 1.0            # vintage: the new-capital rate (NK starts at 0)
        x[self.slices["EXR"]] = 1.0
        x[self.slices["GADJ"]] = 1.0
        if self.closure == "investment":
            x[self.slices["CLOS"]] = 0.0
        elif self.closure == "savings":
            x[self.slices["CLOS"]] = 1.0
        return x

    def evaluate(self, x, sh):
        """Compute every variable from the unknowns x under shocks sh; return (residuals, vars)."""
        nC, nA = len(self.C), len(self.A)
        g = lambda k: x[self.slices[k]]
        QA = g("QA") * self.QA0
        PDS = np.ones(nC); PDS[self.iD] = g("PDS")
        PQ = np.ones(nC); PQ[self.iQ] = g("PQ")
        WF = np.ones(len(self.F)); WF[self.iFM] = g("WF")
        if self.closure == "keynesian" and self.fx == "fixed":   # fixed exchange rate (numeraire); foreign savings adjust
            EXR, FSAVS = sh["exr"], g("EXR")[0]
        else:
            EXR, FSAVS = g("EXR")[0], sh["fsav_scale"]
        WALRAS = g("WALRAS")[0]
        if self.closure == "investment":
            MPSADJ, IADJ = g("CLOS")[0], sh["iadj"]
        elif self.closure == "savings":
            MPSADJ, IADJ = sh["mpsadj"], g("CLOS")[0]
        elif self.closure == "interest":             # 0.3.11: r (pp) clears S = I
            r_ = g("CLOS")[0]
            MPSADJ = (1 + sh["mpsadj"]) * (1 + self.interest["eps"] / 100 * r_) - 1
            IADJ = sh["iadj"] * np.exp(-self.interest["theta"] / 100 * r_)
        else:
            MPSADJ, IADJ = sh["mpsadj"], sh["iadj"]

        pwm = self.pwm * sh["pwm_scale"]
        pwe = self.pwe * sh["pwe_scale"]
        tm = self.tm * sh["tm_scale"]
        tq = self.tq * sh["tq_scale"]
        pwm_x = pwm                             # 0.3.13 (P2(b)): the world price, paid for re-exports in any case
        if sh["erpt"] is not None:              # incomplete pass-through: the suppliers' US$ price of imports sold here (check ER1)
            pwm = self._ptm(pwm, EXR, sh)
        PM = pwm * EXR * (1 + tm)
        oil_on = sh["oil_pass"] is not None     # 0.3.13 (check OP1): only the share omega of a move of the world price in
        if oil_on:                              # pesos reaches the domestic price of the listed imports within the period; the government
            WOIL = pwm * EXR                    # absorbs the rest at the border (MTAX below)
            lst = sh["oil_pass"] != 1.0
            PMd = np.where(lst, self._oil_dom(WOIL, sh), WOIL)
            PM = np.where(lst, PMd * (1 + tm), PM)
        PE = pwe * EXR
        # 0.3: input-intensity TWIST. A commodity's coefficient is scaled for every user and all other
        # intermediate inputs are scaled the other way, so total intermediate input per unit of output (at benchmark
        # prices) is unchanged; likewise for the mix of margin services. 1 = benchmark (no effect, no computation).
        ica, sm = self.ica, self.sm
        s_ica, s_sm = sh["ica_scale"], sh["sm_scale"]
        if np.any(s_ica != 1.0):
            tw = s_ica != 1.0
            ica = self.ica.copy()
            ica[tw] = self.ica[tw] * s_ica[tw][:, None]
            rest0 = self.ica[~tw].sum(axis=0)
            need = self.ica.sum(axis=0) - ica[tw].sum(axis=0)
            ica[~tw] = self.ica[~tw] * np.where(rest0 > 0, need / np.where(rest0 > 0, rest0, 1), 1.0)[None, :]
        if np.any(s_sm != 1.0):
            tw = s_sm != 1.0
            sm = self.sm.copy()
            sm[tw] = self.sm[tw] * s_sm[tw]
            rest0 = self.sm[~tw].sum()
            sm[~tw] = self.sm[~tw] * (1.0 - sm[tw].sum()) / rest0
        PTRC = float(sm @ PQ)
        if self.margins == "split":             # 0.3: IFPRI eq. 1 (import price includes its margin)
            PM = PM + self.icx * PTRC
        CPI = float(self.cwts @ PQ)
        for k in self.iU:                       # fixed wage: indexed to the CPI ('real') or fixed in pesos ('nominal')
            WF[k] = sh["wbar"][k] * (CPI if self.wage == "real" else 1.0)
        if self.labour_cap:                     # 0.3.13 (labour_cap): at its cap a fixed-wage type is paid its anchor x (1 + LP)
            LP = g("LCAP")
            WF[self.iU] = WF[self.iU] * (1.0 + LP)

        # ---- supply side: CET split of domestic output
        QX = self.theta.T @ QA
        QE = np.zeros(nC); QDs = np.zeros(nC)
        both = self.hasE & self.hasD
        r = np.zeros(nC)
        r[both] = ((PE[both] / _pos(PDS[both])) * self.kgam[both]) ** self.omega[both]
        rt = self.rt
        denom = np.ones(nC)
        denom[both] = self.at[both] * (self.gam[both] * r[both] ** rt[both] + self.gamc[both]) ** (1 / rt[both])
        QDs[both] = QX[both] / denom[both]
        QE[both] = r[both] * QDs[both]
        onlyD = self.hasD & ~self.hasE
        onlyE = self.hasE & ~self.hasD
        QDs[onlyD] = QX[onlyD]
        QE[onlyE] = QX[onlyE]
        if self.pricing == "markup":            # 0.3.13: a markup activity's exports follow the CET's relative-price rule at its
            mc = self.mkC & both                # REFERENCE home sales (world demand, not home demand, sets them); its home sales are
            qd_ = self.QD0 if sh["mk_qd"] is None else sh["mk_qd"]          # the rest of its output (the CET inverted)
            QE[mc] = r[mc] * qd_[mc]
            QDs[mc] = _pos(((QX[mc] / self.at[mc]) ** rt[mc] - self.gam[mc] * QE[mc] ** rt[mc]) / self.gamc[mc]) ** (1 / rt[mc])
        PX = np.ones(nC)
        m = self.hasX
        PX[m] = (PE[m] * QE[m] + PDS[m] * QDs[m]) / _pos(QX[m])
        PA = self.theta @ PX

        # ---- value added (CES) and zero profit
        W = WF[:, None] * np.ones((1, nA))
        if self.capital in ("fixed", "vintage"):
            W[self.kcap, self.iK] = g("RK")       # activity-specific rental rates
        if self.land == "fixed":
            W[self.klnd, self.iL] = g("RL")       # activity-specific land rents (0.3.7)
        sig = self.sigva
        cd = sig == 1.0                                       # Cobb-Douglas limit: PVA = prod(W ** delta)
        sig_ = np.where(cd, 0.5, sig)                         # placeholder exponent for the CD columns (overwritten)
        with np.errstate(divide="ignore", invalid="ignore"):
            terms = np.where(self.use, self.delta * _pos(W) ** (1 - sig_), 0.0)
            PVA = terms.sum(axis=0) ** (1 / (1 - sig_))
            PVA_cd = np.exp(np.where(self.use, self.delta * np.log(_pos(W)), 0.0).sum(axis=0))
        PVA = np.where(cd, PVA_cd, PVA) / (self.tfp * sh["tfp_scale"])
        ta = self.ta * sh["ta_scale"]
        QEd = None
        if self.en is None:
            UCOST = ica.T @ PQ + self.iva * PVA
            QVA = self.iva * QA
        else:                                   # 0.3.11: value added-energy bundle
            if np.any(s_ica != 1.0):
                raise NotImplementedError("ica_scale shocks are not combined with energy_nest yet")
            PEN, PVAE, QVA, QEd = self._energy_nest(PQ, PVA, QA, sh["en_shares"])
            UCOST = self.en["ica_ne"].T @ PQ + self.en["ive"] * PVAE
        ZP = PA * (1 - ta) - UCOST
        # factor demand: QF = (QVA / TFP) * delta * (TFP * PVA / W)^sigma   (= QVA * delta at the benchmark)
        tfp = self.tfp * sh["tfp_scale"]
        QF = np.where(self.use, QVA / tfp * self.delta * (PVA * tfp / _pos(W)) ** sig, 0.0)
        UNITREV = PA * (1 - ta)
        if self.pricing == "markup":            # 0.3.13: markup activities are Leontief in utilisation (see __init__)
            kk, im, ik, lab = self.kcap, self.iMK, self.iMKK, self.mk_lab
            coef = self.mk_coef0 if sh["mk_coef"] is None else sh["mk_coef"]    # factor use per unit of output at TFP 1
            QF[np.ix_(lab, im)] = coef[np.ix_(lab, im)] * (QA / tfp)[im][None, :]   # labour: fixed per unit of output
            Kmk = self.QF0[kk, ik] * sh["kscale"][ik] * sh["qfs_scale"][kk]           # installed capital
            UTIL = np.ones(nA)
            UTIL[ik] = coef[kk, ik] * QA[ik] / tfp[ik] / Kmk     # capital services needed / installed capital (reporting)
            QF[kk, ik] = Kmk                                     # paid the residual rent RK per unit installed
            AVC = (W[lab] * coef[lab]).sum(axis=0) / tfp + ica.T @ PQ    # unit variable cost: labour and intermediate inputs
            PROFIT = (UNITREV - AVC) * QA                        # revenue less variable cost (capital's income, markup acts)
        QFH = np.zeros_like(QF)                 # 0.3.11: hoarded labour, employed and paid but not producing
        if self.hoarding > 0 and sh["hoard_ref"] is not None:
            # 19 Oct 2026, about 8:40 AM: hoarding only where there is slack. (1) Only the fixed-wage labour types (iU) hoard: a
            # type whose market clears (none unemployed, e.g. capped at its supply) is bid for, and no firm keeps idle workers
            # then. (2) A type's hoarded total is at most its slack, supply - productive employment: firms keep workers who would
            # otherwise be unemployed, they do not take them from production. Without (2), at full employment the hoarded
            # workers crowded out producing ones (2027 in the QPM link: wages +3.5%, GDP -0.46%) and the employment cap could
            # cycle at its edge. Where the desired hoarding is below the slack (the 2026 scenarios' 2026 case) nothing changes.
            eps = 1e-4                                          # C1 smoothing of max(0, z) near 0, as for sticky prices
            pos = lambda z_: np.where(z_ <= 0, 0.0, np.where(z_ < eps, z_ * z_ / (2 * eps), z_ - eps / 2))
            lab = [k_ for k_ in self.iU if self.F[k_].startswith("flab")]
            if lab:
                ref = sh["hoard_ref"][lab]
                z = np.where(ref > 0, (ref - QF[lab]) / np.where(ref > 0, ref, 1.0), 0.0)
                want = self.hoarding * ref * pos(z)                       # desired hoarding by labour type x activity
                sup = self.QFS0[lab] * sh["qfs_scale"][lab]
                slack = sup * pos((sup - QF[lab].sum(axis=1)) / sup)      # max(0, supply - productive employment), smoothed
                Wd = want.sum(axis=1)
                got = Wd - sup * pos((Wd - slack) / sup)                  # min(desired, slack), smoothed
                QFH[lab] = want * np.where(Wd > 0, got / np.where(Wd > 0, Wd, 1.0), 0.0)[:, None]

        # ---- incomes
        YFva = (W * QF).sum(axis=1)
        if self.hoarding > 0:                   # hoarded workers' wages, paid out of capital income (profits)
            HB = W * QFH
            YFva = YFva + HB.sum(axis=1)
            YFva[self.kcap] -= HB.sum()
        if self.pricing == "sticky":            # 0.3.8 (review D2): prices rigid downward; profit = price - cost, to capital
            st, A_ = self.isST, sh["pa_anchor"]
            UC = UCOST                                          # unit cost (the zero-profit price of 'flex')
            z = (A_ - UC) / A_
            eps = 1e-4                                          # C1 smoothing of max(0, z) near 0 (bias at most eps / 2)
            fz = np.where(z <= 0, 0.0, np.where(z < eps, z * z / (2 * eps), z - eps / 2))
            ZP = np.where(st, UNITREV - (UC + sh["stickiness"] * A_ * fz), ZP)
            YFva = YFva.copy()
            YFva[self.kcap] += float((((UNITREV - UC) * QA) * st).sum())
        elif self.pricing == "markup":          # 0.3.13: home price (1 - ta) PDS = (1 + mu) x unit variable cost, stickiness for falls
            mk, st, A_ = self.isMK, self.isST, sh["pa_anchor"]
            URD = np.where(mk, PDS[self.mk_com] * (1 - ta), UNITREV)   # unit revenue at home (markup acts), or of all output (others)
            mu_, lam = sh["markup"], sh["mk_pass"]              # the price the rule sets: markup price, or zero-profit cost (others)
            MG = mu_ * (lam * AVC + (1 - lam) * A_ / (1 + mu_))  # the margin per unit (0.3.13, P6: kept for the gap rule below)
            CM = np.where(mk, AVC + MG, UCOST)                  # mk_pass 1: (1 + mu) x AVC
            z = (A_ - CM) / A_
            eps = 1e-4                                          # C1 smoothing of max(0, z) near 0, as for 'sticky'
            fz = np.where(z <= 0, 0.0, np.where(z < eps, z * z / (2 * eps), z - eps / 2))
            ZP = URD - (CM + np.where(st, sh["stickiness"] * A_ * fz, 0.0))
            YFva = YFva.copy()                                  # capital income: RK x installed capital (in W x QF) for markup
            YFva[self.kcap] += float((((UNITREV - UCOST) * QA) * (st & ~mk)).sum())   # activities; sticky zero-profit ones as 'sticky'
            YFva[self.kcap] += float((PROFIT * (mk & ~self.hasK)).sum())              # markup activities without installed capital
        frow_in = self.frow_in * sh["frow_in_scale"]
        YF = YFva + frow_in * EXR
        dist = (1 - self.tf) * YF - self.frow_out * EXR
        YIF = self.shif * dist[None, :]
        nH = len(self.H)
        trg_ent = self.trg_ent * sh["trg_scale"]
        YE = YIF[nH].sum() + trg_ent * CPI + self.erow_in * EXR
        ESAV = YE * (1 - self.te - self.she.sum() - self.sheg) - self.erow_out * EXR + sh["sav_add"] * CPI   # 0.3.6
        trg_h = self.trg_h * sh["trg_scale"] * sh["trg_h_scale"]
        hrow_in = self.hrow_in * sh["remit_scale"]
        trg_add = sh["trg_h_add"]                # additional real transfers, ₱ bn at benchmark prices (e.g. an Ayuda change)
        YH = YIF[:nH].sum(axis=1) + self.she * YE + (trg_h + trg_add) * CPI + hrow_in * EXR
        tins = self.tins * sh["tins_scale"]
        DY = YH * (1 - tins - self.tgh) - self.hrow_out * EXR
        mps = np.clip(self.mps * (1 + MPSADJ), -1, 1)
        HSAV = mps * DY
        EH = DY - HSAV
        if self.les is None:
            QH = self.beta * EH[None, :] / _pos(PQ)[:, None]
        else:                                    # LES: subsistence + marginal share of supernumerary spending
            g_, mb_ = self.les["gamma"], self.les["mb"]
            QH = g_ + mb_ * (EH - PQ @ g_)[None, :] / _pos(PQ)[:, None]
        if self.home == "separate":
            # 0.3.1, book eq. 34: own produce valued at the producer price, PX * QHA = beta_h * EH; book eq. 18:
            # marketed output = gross output - home use, split by the CET at the prices found above (PX does not
            # depend on the quantity: constant returns)
            QHA = self.beta_h * EH[None, :] / _pos(PX)[:, None]
            QXm = QX - QHA.sum(axis=1)
            QDs[both] = QXm[both] / denom[both]
            QE[both] = r[both] * QDs[both]
            QDs[onlyD] = QXm[onlyD]
            QE[onlyE] = QXm[onlyE]
            QX = QXm
        else:
            QHA = np.zeros_like(self.HC)

        # ---- demand for composite goods
        if self.gov == "cd":                     # fixed value shares; GADJ = nominal spending index (solved)
            QG = self.qg * g("GADJ")[0] / _pos(PQ)
        else:
            QG = self.qg * sh["qg_scale_vec"] * sh["qg_scale"]
        if self.inv == "value_shares":           # fixed value shares; IADJ = nominal investment index
            QINV = self.qinv * IADJ * sh["qinv_scale_vec"] / _pos(PQ)
        else:
            QINV = self.qinv * IADJ * sh["qinv_scale_vec"]
        QINT = ica @ QA
        if self.en is not None:                 # 0.3.11: energy inputs come from the nest
            QINT = self.en["ica_ne"] @ QA
            QINT[self.en["E"]] += QEd.sum(axis=1)
        D = QINT + QH.sum(axis=1) + QG + QINV + self.qdst
        if self.margins == "composite":
            icq = self.icq
            T = float(icq @ D) / (1 - float(icq @ sm))
            QQ = D + sm * T

            # ---- Armington split and composite price
            PDD = PDS
            QDd = np.zeros(nC); QM = np.zeros(nC); PARM = np.ones(nC)
            mix = self.hasM & self.hasD
            s_ = self.sigq
            PARM[mix] = (self.dq[mix] * PM[mix] ** (1 - s_[mix]) + (1 - self.dq[mix]) * PDD[mix] ** (1 - s_[mix])) \
                ** (1 / (1 - s_[mix])) / self.aq[mix]
            # CES demands: QM = (QQ / aq) * dq * (aq * PARM / PM)^sigma,  QD = (QQ / aq) * (1 - dq) * (aq * PARM / PDD)^sigma
            QM[mix] = QQ[mix] / self.aq[mix] * self.dq[mix] * (self.aq[mix] * PARM[mix] / PM[mix]) ** s_[mix]
            QDd[mix] = QQ[mix] / self.aq[mix] * (1 - self.dq[mix]) * (self.aq[mix] * PARM[mix] / _pos(PDD[mix])) ** s_[mix]
            onlyM = self.hasM & ~self.hasD
            onlyDd = self.hasD & ~self.hasM
            PARM[onlyM] = PM[onlyM] * self.k_m[onlyM]
            QM[onlyM] = QQ[onlyM] * self.k_m[onlyM]
            PARM[onlyDd] = PDD[onlyDd] * self.k_d[onlyDd]
            QDd[onlyDd] = QQ[onlyDd] * self.k_d[onlyDd]
        else:
            # 0.3, margins='split' (IFPRI eq. 3, 24-27): margins enter the demand prices of imports (PM, above) and of
            # domestic goods (PDD) before the Armington choice. Import and domestic demand per unit of composite good
            # depend on prices only (um, ud), so the margin requirement per unit of composite good is
            # kappa = icx * (um + ud), and margin demand T solves T = kappa . (D + sm * T).
            icq = np.zeros(nC)
            PDD = PDS + self.icx * PTRC
            um = np.zeros(nC); ud = np.zeros(nC); PARM = np.ones(nC)
            mix = self.hasM & self.hasD
            s_ = self.sigq
            PARM[mix] = (self.dq[mix] * PM[mix] ** (1 - s_[mix]) + (1 - self.dq[mix]) * PDD[mix] ** (1 - s_[mix])) \
                ** (1 / (1 - s_[mix])) / self.aq[mix]
            um[mix] = self.dq[mix] / self.aq[mix] * (self.aq[mix] * PARM[mix] / PM[mix]) ** s_[mix]
            ud[mix] = (1 - self.dq[mix]) / self.aq[mix] * (self.aq[mix] * PARM[mix] / _pos(PDD[mix])) ** s_[mix]
            onlyM = self.hasM & ~self.hasD
            onlyDd = self.hasD & ~self.hasM
            PARM[onlyM] = PM[onlyM] * self.k_m[onlyM]
            um[onlyM] = self.k_m[onlyM]
            PARM[onlyDd] = PDD[onlyDd] * self.k_d[onlyDd]
            ud[onlyDd] = self.k_d[onlyDd]
            kappa = self.icx * (um + ud)
            T = float(kappa @ D) / (1 - float(kappa @ sm))
            QQ = D + sm * T
            QM = um * QQ
            QDd = ud * QQ
        PQcalc = (1 + tq) * (PARM + icq * PTRC)
        if self.pricing == "markup" and sh["mk_gap"] != 0.0:   # 0.3.13 (P6, check MG1): the pass-through lam + s x output gap (%)
            YR = float(QH.sum() + QHA.sum() + QG.sum() + (QINV + self.qdst).sum() + QE.sum() - QM.sum())   # real GDP, as gdp()
            lam_e = lam + sh["mk_gap"] * self._output_gap(YR, sh)
            MG = mu_ * (lam_e * AVC + (1 - lam_e) * A_ / (1 + mu_))
            CM = np.where(mk, AVC + MG, UCOST)
            z = (A_ - CM) / A_
            fz = np.where(z <= 0, 0.0, np.where(z < 1e-4, z * z / (2 * 1e-4), z - 1e-4 / 2))   # as above (eps 1e-4)
            ZP = URD - (CM + np.where(st, sh["stickiness"] * A_ * fz, 0.0))

        # ---- government
        ATAX = ta * PA * QA
        MTAX = tm * pwm * EXR * QM
        if oil_on:                              # 0.3.13 (check OP1): the tariff on the domestic price less what the government absorbs,
            OILSUB = np.where(lst, (WOIL - PMd) * QM, 0.0)     # (pwm x EXR - domestic price) x QM: a subsidy above the reference
            MTAX = np.where(lst, tm * PMd * QM - OILSUB, MTAX)
        STAX = tq * (PARM + icq * PTRC) * QQ
        YG = (self.te * YE + (tins * YH).sum() + (self.tf * YF).sum() + MTAX.sum() + STAX.sum() + ATAX.sum()
              + self.sheg * YE + (self.tgh * YH).sum() + self.grow_in * EXR)
        GEXP = float(PQ @ QG) + ((trg_h + trg_add) * CPI).sum() + trg_ent * CPI + self.grow_out * EXR
        GEXP += sh["sav_add"] * CPI + sh["grow_out_add"] * EXR      # 0.3.6: diverted public money, saved or sent abroad
        GSAV = YG - GEXP

        # ---- residuals
        res = []
        res.append(ZP)                                                    # zero profit
        res.append((QDs[self.iD] - QDd[self.iD]) / self.QD0[self.iD])     # domestic sales market
        res.append(PQ[self.iQ] - PQcalc[self.iQ])                          # composite price
        k = self.iFM
        res.append(((QF + QFH).sum(axis=1)[k] - self.QFS0[k] * sh["qfs_scale"][k]) / self.QFS0[k])  # factor markets
        NK_v, RN_v = None, 1.0
        if self.capital == "fixed":
            kk, ia = self.kcap, self.iK
            rk = (QF[kk, ia] - self.QF0[kk, ia] * sh["kscale"][ia] * sh["qfs_scale"][kk]) / self.QF0[kk, ia]
            if self.pricing == "markup":         # 0.3.13: a markup activity's installed capital earns the residual (RK x K = profit)
                rk = np.where(self.isMK[ia], (W[kk, ia] * QF[kk, ia] - PROFIT[ia]) / self.QF0[kk, ia], rk)
            res.append(rk)
        elif self.capital == "vintage":          # 0.3.12: old capital by activity, a mobile pool of new
            kk, ia = self.kcap, self.iK
            Kold = self.QF0[kk, ia] * sh["kscale"][ia] * sh["qfs_scale"][kk]
            RN_v, NK_v = float(g("RN")[0]), g("NK")
            z = 1.0 - (_pos(W[kk, ia]) / _pos(RN_v)) ** self.vint_e
            eps = 1e-4                                          # C1 smoothing of max(0, z) near 0, exact at the benchmark
            pos = lambda z_: np.where(z_ <= 0, 0.0, np.where(z_ < eps, z_ * z_ / (2 * eps), z_ - eps / 2))
            u = 1.0 - pos(z)                                    # old capital in use: min(1, (W_a / RN) ** e)
            res.append((QF[kk, ia] - (Kold * u + NK_v)) / self.QF0[kk, ia])                   # capital used = old in use + new
            a_, b_ = NK_v / self.QF0[kk, ia], RN_v - W[kk, ia]                               # NK >= 0, W <= RN, NK (RN - W) = 0
            res.append(a_ + b_ - np.sqrt(a_ * a_ + b_ * b_ + 2e-20))                          # Fischer-Burmeister (smoothed 1e-10)
            pool = sh["knew"] * self.QFS0[kk] + float((Kold * (1.0 - u)).sum())                # new capital plus released old
            res.append(np.array([(float(NK_v.sum()) - pool) / self.QFS0[kk]                        # the pool is fully employed
                                 + 1e-3 * (RN_v - float(np.max(W[kk, ia])))]))
            # (the 1e-3 term pins RN to the highest rental when nothing is on offer and nothing is released, where RN would
            # otherwise be free; whenever an activity hires, RN equals its rental, the highest, and the term is zero)
        if self.land == "fixed":
            kl, il = self.klnd, self.iL
            res.append((QF[kl, il] - self.QF0[kl, il] * sh["lscale"][il] * sh["qfs_scale"][kl]) / self.QF0[kl, il])
        imp_fcu = (pwm * (QM + self.rex)).sum() if sh["erpt"] is None else (pwm * QM + pwm_x * self.rex).sum()   # 0.3.13 (P2(b))
        fcu_out = imp_fcu + self.frow_out.sum() + self.erow_out + self.hrow_out.sum() + self.grow_out \
            + sh["grow_out_add"]
        fcu_in = (pwe * (QE + self.rex)).sum() + frow_in.sum() + self.erow_in + hrow_in.sum() + self.grow_in + self.fsav * FSAVS
        res.append(np.array([(fcu_out - fcu_in) / self.QM0.sum()]))        # current account
        INVV = float(PQ @ (QINV + self.qdst))
        SAV = HSAV.sum() + ESAV + GSAV + self.fsav * FSAVS * EXR
        res.append(np.array([(SAV - INVV - WALRAS) / self.qinv.sum()]))    # savings = investment
        if self.closure != "keynesian":
            res.append(np.array([CPI - sh["cpi"]]))                        # numeraire (the fixed exchange rate is the numeraire otherwise)
        if self.gov == "cd":
            res.append(np.array([(GEXP - (1 - self.ssg) * YG) / self.qg.sum()]))   # government spends revenue net of saving
        if self.labour_cap:                     # 0.3.13 (labour_cap, check EC1): E <= S, LP >= 0, (S - E) LP = 0, Fischer-Burmeister
            ku = self.iU                        # (smoothed 1e-10, as capital='vintage'); E = productive employment: hoarding is bounded
            a_ = (self.QFS0[ku] * sh["qfs_scale"][ku] - QF.sum(axis=1)[ku]) / self.QFS0[ku]   # by the slack, so none at the cap
            res.append(a_ + LP - np.sqrt(a_ * a_ + LP * LP + 2e-20))
        R = np.concatenate(res)

        V = dict(W=W, EMP=(QF + QFH).sum(axis=1), QFH=QFH, pwm=pwm, pwe=pwe, QA=QA, QX=QX, QE=QE, QD=QDd, QM=QM, QQ=QQ, QF=QF, QVA=QVA, QINT=QINT, QH=QH, QHA=QHA, QG=QG,
                 QINV=QINV, PA=PA, PX=PX, PDS=PDS, PE=PE, PM=PM, PQ=PQ, PVA=PVA, WF=WF, EXR=EXR,
                 CPI=CPI, PTRC=PTRC, YF=YF, YIF=YIF, YE=YE, YH=YH, DY=DY, EH=EH, HSAV=HSAV, ESAV=ESAV,
                 YG=YG, GEXP=GEXP, GSAV=GSAV, MTAX=MTAX, STAX=STAX, ATAX=ATAX, T=T, MPSADJ=MPSADJ, IADJ=IADJ,
                 RINT=(float(g("CLOS")[0]) if self.closure == "interest" else 0.0),
                 WALRAS=WALRAS, fcu_out=fcu_out, fcu_in=fcu_in, FSAV=self.fsav * FSAVS, UNITREV=UNITREV)
        if self.capital == "vintage":
            V["NK"], V["RN"] = NK_v, RN_v
        if self.labour_cap:                      # 0.3.13: the wage premium over the anchor, by factor (0 below the cap)
            V["LPREM"] = np.zeros(len(self.F))
            V["LPREM"][self.iU] = LP
        if sh["erpt"] is not None:               # 0.3.13 (P2(b)): 'pwm' = the US$ unit value of imports sold here and re-exports,
            qr = QM + self.rex                   # so gdp() and rebuild_sam() value both at what the current account pays; 'pwm_home':
            V["pwm"] = np.where(qr > 0, (pwm * QM + pwm_x * self.rex) / np.where(qr > 0, qr, 1.0), pwm)   # the suppliers' price
            V["pwm_home"] = pwm                  # of imports sold here
        if oil_on:                               # 0.3.13 (check OP1): the government's absorption by commodity (pesos) and the domestic
            V["OILSUB"], V["PM_dom"] = OILSUB, PMd   # peso price of imports before the tariff (the world price where omega is 1)
        if self.pricing == "markup":             # 0.3.13: unit variable cost, utilisation, markups; PVA of markup activities =
            V["AVC"], V["UTIL"], V["MU"] = AVC, UTIL, np.asarray(sh["markup"], float)   # factor payments per unit of value added
            V["PVA"] = np.where(self.isMK, (W * QF).sum(axis=0) / _pos(QVA), PVA)
        return R, V

    # ================================================================== shocks and solving
    def default_shocks(self):
        nC, nA, nF = len(self.C), len(self.A), len(self.F)
        return dict(iadj=1.0, mpsadj=0.0, pwm_scale=np.ones(nC), pwe_scale=np.ones(nC), tm_scale=np.ones(nC),
                    tq_scale=np.ones(nC), tfp_scale=np.ones(nA), frow_in_scale=np.ones(nF), trg_scale=1.0,
                    trg_h_scale=np.ones(len(self.H)), remit_scale=np.ones(len(self.H)), tins_scale=np.ones(len(self.H)),
                    qg_scale=1.0, qg_scale_vec=np.ones(nC), qinv_scale_vec=np.ones(nC), qfs_scale=np.ones(nF),
                    fsav_scale=1.0, cpi=1.0, exr=1.0, wbar=np.ones(nF), kscale=np.ones(nA), lscale=np.ones(nA),
                    trg_h_add=np.zeros(len(self.H)), ta_scale=np.ones(nA), ica_scale=np.ones(nC), sm_scale=np.ones(nC),
                    sav_add=0.0, grow_out_add=0.0, pa_anchor=1 - self.ta, stickiness=0.0, hoard_ref=None, en_shares=None,
                    knew=0.0,                                   # 0.3.12: new capital, share of the stock
                    markup=self.mu0.copy(), mk_coef=None, mk_qd=None,   # 0.3.13 (pricing='markup'); None = the SAM's
                    mk_pass=1.0,
                    erpt=None, exr_ref=1.0,                     # 0.3.13 (P2(b)): None = full pass-through of the peso (as before)
                    mk_gap=0.0, mk_gdp=None,                    # 0.3.13 (P6): 0 = mk_pass as given (as before); None = benchmark GDP
                    oil_pass=None, oil_ref=np.ones(nC))         # 0.3.13: None = the world price in full (as before)

    def make_shocks(self, spec=None):
        """Translate a readable shock spec into arrays. Keys:
        'qinv_scale': {commodity: factor}   real investment demand (e.g. {'ccons': 0.9})
        'qg_scale': factor or {commodity: factor}   real government consumption
        'pwm_scale' / 'pwe_scale': {commodity: factor}   world import / export prices
        'tm_scale', 'tq_scale': {commodity: factor}   tariff and sales-tax rates
        'tfp_scale': {activity: factor}   productivity
        'qfs_scale': {factor: factor}   factor supplies (e.g. {'fcap': 1.05})
        'lscale': {activity: factor}   effective land of that activity (only with land='fixed'; 0.3.7, e.g. drought)
        'remit_scale': factor or {household: factor}   remittances (foreign currency)
        'trg_scale': factor   all government transfers (real);  'trg_h_scale': {household: factor}
        'trg_h_add': {household: ₱ bn}   additional real government transfers (negative = a cut), e.g. an Ayuda change;
                     needed because the SAM records only ₱103.7 bn of transfers to households
        'tins_scale': factor or {household: factor}   household direct-tax rates
        'ta_scale': factor or {activity: factor}   activity-tax rates (2018 SAM only; 0.3)
        'ica_scale': {commodity: factor}   input-intensity twist: that commodity per unit of output, for every activity,
                     with all other intermediate inputs scaled down so total input per unit is unchanged (0.3)
        'sm_scale': {commodity: factor}   the same twist within the mix of margin services (0.3)
        'fsav_scale': factor   foreign savings;  'iadj' / 'mpsadj': closure levels;  'cpi': numeraire level
        'pa_anchor': {activity: unit revenue}, 'stickiness': share   downward price rigidity (pricing='sticky' only; 0.3.8);
                     'stickiness' may also be {activity: share} (0.3.11, sectoral; infinity_gem/stickiness.py)
        'sav_add': ₱ bn   government money paid out and SAVED by its recipients, not spent (real, benchmark prices;
                   enters private (enterprise) saving): e.g. diverted public funds that are hoarded or banked (0.3.6)
        'grow_out_add': ₱ bn   government money sent ABROAD (foreign-currency units, base exchange rate 1): e.g.
                   diverted public funds moved out of the country (0.3.6). Both default 0: results unchanged.
        'en_shares': {'dva', 'den', 'de'}   share parameters of the value added-energy bundle centred on another point
                   (energy_shares_at; energy_nest only; 0.3.11). Default None: the SAM's.
        'markup': {activity: mu} or one number   markups of the home price over unit variable cost (pricing='markup' only;
                   0.3.13); default the benchmark's (capital income / variable cost). 'mk_coef': factors x activities array, factor
                   use per unit of output at TFP 1 (the installed technology; labour rows used, the capital row for UTIL). 'mk_qd':
                   array by commodity, the reference home sales at which a markup activity's exports follow the CET's relative-price
                   rule. None = the SAM's. markup_at() gives all three and the matching 'pa_anchor', centred on another solution.
                   'mk_pass': one share or {activity: share}, the share lam of a change in unit variable cost on which the markup
                   is charged: home unit revenue = AVC + mu x (lam x AVC + (1 - lam) x A / (1 + mu)), A = 'pa_anchor'. 1 (default)
                   = the proportional markup on prime cost (Taylor 1983; the design note's equation); 0 = the margin per unit
                   fixed in pesos at the reference (A - A / (1 + mu)), whose cost push is the plain input-output price model's.
        'mk_gap': s, 'mk_gdp': Y_ref (pricing='markup' only; 0.3.13, P6): the pass-through is mk_pass + s x the output gap in
                   percent, 100 x (real GDP / Y_ref - 1); Y_ref default the benchmark's real GDP. s = 0 (default) = as before.
        'erpt': one share or {commodity: share} in [0, 1] (commodities not listed: 1), 'exr_ref': the reference peso (default 1)
                   (0.3.13, P2(b); Keynesian closure with the fixed peso only): import prices PM = pwm x exr_ref x (EXR /
                   exr_ref) ** erpt x (1 + tm), the foreign supplier absorbing the rest (see __init__). Check ER1.
        'oil_pass': one share or {commodity: share} in [0, 1] (not listed: 1), 'oil_ref': the reference world price in pesos, one
                   positive number or {commodity: value} (default 1) (0.3.13; Keynesian closure only): the domestic
                   peso price of those imports is oil_ref x (pwm x EXR / oil_ref) ** oil_pass before the tariff, the government
                   absorbing the rest at the border (see __init__). A commodity may not carry both 'erpt' and 'oil_pass'. Check OP1.
        """
        sh = self.default_shocks()
        idx = {"c": {c: i for i, c in enumerate(self.C)}, "a": {a: i for i, a in enumerate(self.A)},
               "f": {f: i for i, f in enumerate(self.F)}, "h": {h: i for i, h in enumerate(self.H)}}
        vec_keys = {"qinv_scale": ("qinv_scale_vec", "c"), "pwm_scale": ("pwm_scale", "c"), "pwe_scale": ("pwe_scale", "c"),
                    "tm_scale": ("tm_scale", "c"), "tq_scale": ("tq_scale", "c"), "tfp_scale": ("tfp_scale", "a"),
                    "qfs_scale": ("qfs_scale", "f"), "remit_scale": ("remit_scale", "h"), "trg_h_scale": ("trg_h_scale", "h"),
                    "tins_scale": ("tins_scale", "h"), "frow_in_scale": ("frow_in_scale", "f"),
                    "wbar": ("wbar", "f"), "kscale": ("kscale", "a"), "lscale": ("lscale", "a"), "trg_h_add": ("trg_h_add", "h"),
                    "ta_scale": ("ta_scale", "a"), "ica_scale": ("ica_scale", "c"), "sm_scale": ("sm_scale", "c"),
                    "pa_anchor": ("pa_anchor", "a"), "markup": ("markup", "a")}
        if "lscale" in (spec or {}) and self.land != "fixed":
            raise ValueError("'lscale' needs land='fixed' (with mobile land it would be ignored)")
        if self.pricing != "markup" and any(k in (spec or {}) for k in ("markup", "mk_coef", "mk_qd", "mk_pass", "mk_gap", "mk_gdp")):
            raise ValueError("'markup', 'mk_coef', 'mk_qd', 'mk_pass', 'mk_gap' and 'mk_gdp' need pricing='markup' (otherwise they "
                             "would be ignored)")                    # 0.3.13
        if any(k in (spec or {}) for k in ("erpt", "exr_ref")) and not (self.closure == "keynesian" and self.fx == "fixed"):
            raise ValueError("'erpt' and 'exr_ref' (incomplete pass-through of the peso to import prices; 0.3.13) need the "
                             "Keynesian closure with the fixed peso (fx='fixed'): elsewhere the peso is determined by the model")
        if any(k in (spec or {}) for k in ("oil_pass", "oil_ref")) and self.closure != "keynesian":
            raise ValueError("'oil_pass' and 'oil_ref' (a within-year share of the world price reaching domestic prices; 0.3.13) "
                             "need the Keynesian (short-run) closure: in the long run world prices pass through in full")
        for k, val in (spec or {}).items():
            if k == "qg_scale":
                if isinstance(val, dict):
                    for c, f in val.items(): sh["qg_scale_vec"][idx["c"][c]] = f
                else:
                    sh["qg_scale"] = float(val)
            elif k in vec_keys:
                tgt, kind = vec_keys[k]
                if isinstance(val, dict):
                    for name, f in val.items(): sh[tgt][idx[kind][name]] = f
                else:
                    sh[tgt][:] = float(val)
            elif k in ("trg_scale", "fsav_scale", "iadj", "mpsadj", "cpi", "exr", "sav_add", "grow_out_add"):
                sh[k] = float(val)
            elif k == "knew":                           # 0.3.12
                if self.capital != "vintage":
                    raise ValueError("'knew' (new capital) needs capital='vintage'")
                sh[k] = float(val)
            elif k == "stickiness":                     # 0.3.8: one share; 0.3.11 (19 Oct 2026): or {activity: share}
                if isinstance(val, dict):               # (sectoral, infinity_gem/stickiness.py); activities not listed: 0
                    sh[k] = np.zeros(len(self.A))
                    for a, f in val.items(): sh[k][idx["a"][a]] = f
                else:
                    sh[k] = float(val)
            elif k == "mk_pass":                        # 0.3.13 (pricing='markup'): one share or {activity: share}; not listed: 1
                if isinstance(val, dict):
                    sh[k] = np.ones(len(self.A))
                    for a, f in val.items(): sh[k][idx["a"][a]] = f
                else:
                    sh[k] = float(val)
            elif k == "mk_gap":                         # 0.3.13 (P6): one number, the change of mk_pass per percent of output gap
                if isinstance(val, (bool, np.bool_)) or not np.isfinite(float(val)):
                    raise ValueError(f"'mk_gap' must be a finite number, not {val!r}")
                sh[k] = float(val)
            elif k == "mk_gdp":                         # 0.3.13 (P6): the reference real GDP (benchmark prices); None = benchmark
                if val is not None and (isinstance(val, (bool, np.bool_)) or not np.isfinite(float(val)) or float(val) <= 0):
                    raise ValueError(f"'mk_gdp' must be None or a positive number, not {val!r}")
                sh[k] = None if val is None else float(val)
            elif k == "erpt":                           # 0.3.13 (P2(b)): one share or {commodity: share}; not listed: 1
                vals = dict(val) if isinstance(val, dict) else {c: val for c in self.C}
                bad = [c for c in vals if c not in idx["c"]]
                if bad:
                    raise ValueError(f"'erpt': not commodities of this SAM: {bad}")
                e_ = np.ones(len(self.C))
                for c, f in vals.items():
                    if isinstance(f, (bool, np.bool_)) or not np.isfinite(float(f)) or not 0.0 <= float(f) <= 1.0:
                        raise ValueError(f"'erpt' ({c}): the share of a move of the peso passed into import prices must be a "
                                         f"number in [0, 1], not {f!r}")
                    e_[idx["c"][c]] = float(f)
                sh[k] = e_
            elif k == "exr_ref":                        # 0.3.13 (P2(b)): the peso the suppliers' peso prices are anchored to
                if isinstance(val, (bool, np.bool_)) or not np.isfinite(float(val)) or float(val) <= 0:
                    raise ValueError(f"'exr_ref' must be a positive number, not {val!r}")
                sh[k] = float(val)
            elif k in ("oil_pass", "oil_ref"):          # 0.3.13: one value or {commodity: value}; not listed: 1
                vals = dict(val) if isinstance(val, dict) else {c: val for c in self.C}
                bad = [c for c in vals if c not in idx["c"]]
                if bad:
                    raise ValueError(f"'{k}': not commodities of this SAM: {bad}")
                o_ = np.ones(len(self.C))
                for c, f in vals.items():
                    if isinstance(f, (bool, np.bool_)) or not np.isfinite(float(f)):
                        raise ValueError(f"'{k}' ({c}) must be a finite number, not {f!r}")
                    if k == "oil_pass" and not 0.0 <= float(f) <= 1.0:
                        raise ValueError(f"'oil_pass' ({c}): the share of a move of the world price in pesos reaching domestic prices "
                                         f"within the period must be in [0, 1], not {f!r}")
                    if k == "oil_ref" and float(f) <= 0:
                        raise ValueError(f"'oil_ref' ({c}): the reference world price in pesos must be positive, not {f!r}")
                    o_[idx["c"][c]] = float(f)
                sh[k] = o_
            elif k == "hoard_ref":                      # 0.3.11: labour by factor x activity of the reference year
                sh[k] = None if val is None else np.asarray(val, float)
            elif k in ("mk_coef", "mk_qd"):             # 0.3.13 (pricing='markup'): installed technology; reference home sales
                sh[k] = None if val is None else np.asarray(val, float)
                need = self.QF0.shape if k == "mk_coef" else self.QD0.shape
                if sh[k] is not None and sh[k].shape != need:
                    raise ValueError(f"'{k}' must have shape {need}, not {sh[k].shape}")
            elif k == "en_shares":                      # 0.3.11: bundle shares centred on a reference point
                if val is not None and self.en is None:
                    raise ValueError("'en_shares' needs energy_nest")
                sh[k] = None if val is None else {n: np.asarray(val[n], float) for n in ("dva", "den", "de")}
            else:
                raise KeyError(f"Unknown shock '{k}'")
        if sh["oil_pass"] is not None and sh["erpt"] is not None and np.any((sh["oil_pass"] != 1.0) & (sh["erpt"] != 1.0)):
            both = [c for i, c in enumerate(self.C) if sh["oil_pass"][i] != 1.0 and sh["erpt"][i] != 1.0]
            raise ValueError(f"{both}: a commodity may not carry both 'erpt' (the peso's pass-through, the supplier absorbing the rest) "
                             "and 'oil_pass' (the world price's, the government absorbing the rest)")
        return sh

    def solve(self, spec=None, x_start=None, tol=1e-10, verbose=False) -> Solution:
        sh = self.make_shocks(spec)
        x0 = self.x0() if x_start is None else x_start.copy()
        if self.capital == "vintage" and sh["knew"] > 0:      # 0.3.12: warm start for the new-capital unknowns
            # With no new capital in the start vector, every activity sits at the kink of its complementarity condition
            # (NK = 0 and W = RN at once) and the solver stalls (the first dynamic year after the benchmark). Spread the
            # pool over activities in proportion to their excess demand at the start vector (or to their old capital).
            V0 = self.evaluate(x0, sh)[1]
            kk, ia = self.kcap, self.iK
            Kold = self.QF0[kk, ia] * sh["kscale"][ia] * sh["qfs_scale"][kk]
            excess = np.maximum(np.asarray(V0["QF"], float)[kk, ia] - Kold, 0.0)
            w = excess if excess.sum() > 0 else Kold
            x0[self.slices["NK"]] = sh["knew"] * self.QFS0[kk] * w / w.sum()
        f = lambda x: self.evaluate(x, sh)[0]
        r0 = f(x0)
        if np.abs(r0).max() < tol:
            R, V = self.evaluate(x0, sh)
            return Solution(x0, V, True, "starting point already solves the model", float(np.abs(R).max()), spec or {})
        out = root(f, x0, method="hybr", options={"xtol": 1e-12, "maxfev": 200 * (self.n + 1)})
        if not out.success or np.abs(out.fun).max() > 1e-7:
            out2 = root(f, out.x if np.isfinite(out.x).all() else x0, method="lm", options={"xtol": 1e-13, "maxiter": 20000})
            if np.abs(out2.fun).max() < np.abs(out.fun).max():
                out = out2
        R, V = self.evaluate(out.x, sh)
        ok = bool(np.abs(R).max() < 1e-7)
        if verbose:
            print(f"solve: {'OK' if ok else 'FAILED'}  max residual {np.abs(R).max():.2e}  Walras {V['WALRAS']:.2e}  ({out.message})")
        return Solution(out.x, V, ok, str(out.message), float(np.abs(R).max()), spec or {})

    # ================================================================== reporting
    def gdp(self, sol: Solution) -> dict:
        """Nominal GDP by expenditure and by income, and real GDP at benchmark prices."""
        v = sol.v
        C_ = float(v["PQ"] @ v["QH"].sum(axis=1)) + float(v["PX"] @ v["QHA"].sum(axis=1))   # + own produce (0.3.1)
        G_ = float(v["PQ"] @ v["QG"])
        I_ = float(v["PQ"] @ (v["QINV"] + self.qdst))
        X_ = float(v["PE"] @ v["QE"]) + float(v["EXR"] * (v["pwe"] @ self.rex))
        M_ = float(v["EXR"] * (v["pwm"] @ (v["QM"] + self.rex)))
        gdp_exp = C_ + G_ + I_ + X_ - M_
        va = float((v["W"] * v["QF"]).sum())
        gdp_inc = va + float(v["MTAX"].sum() + v["STAX"].sum() + v["ATAX"].sum())
        real = float(v["QH"].sum() + v["QHA"].sum() + v["QG"].sum() + (v["QINV"] + self.qdst).sum() + v["QE"].sum() - v["QM"].sum())
        return dict(nominal_expenditure=gdp_exp, nominal_income=gdp_inc, real=real,
                    C=C_, G=G_, I=I_, X=X_, M=M_)

    def compare(self, base: Solution, sim: Solution) -> pd.DataFrame:
        gb, gs = self.gdp(base), self.gdp(sim)
        rows = [("Real GDP (benchmark prices)", gb["real"], gs["real"]),
                ("Real household consumption", base["QH"].sum() + base["QHA"].sum(), sim["QH"].sum() + sim["QHA"].sum()),
                ("Real investment", base["QINV"].sum(), sim["QINV"].sum()),
                ("Real exports", base["QE"].sum(), sim["QE"].sum()),
                ("Real imports", base["QM"].sum(), sim["QM"].sum()),
                ("Exchange rate (index)", base["EXR"], sim["EXR"]),
                ("Consumer price index", base["CPI"], sim["CPI"]),
                ("Government savings", base["GSAV"], sim["GSAV"])]
        for k, f in enumerate(self.F):
            rows.append((f"Factor price {f}", base["WF"][k], sim["WF"][k]))
            rows.append((f"Employment {f}", base["EMP"][k], sim["EMP"][k]))
        rows.append(("Capital rental (average)", float((base["W"][self.kcap] * base["QF"][self.kcap]).sum() / base["QF"][self.kcap].sum()),
                     float((sim["W"][self.kcap] * sim["QF"][self.kcap]).sum() / sim["QF"][self.kcap].sum())))
        for i, h in enumerate(self.H):
            rows.append((f"Real consumption {h}", base["EH"][i] / base["CPI"], sim["EH"][i] / sim["CPI"]))
        df = pd.DataFrame(rows, columns=["variable", "base", "sim"])
        df["pct_change"] = (df["sim"] / df["base"] - 1) * 100
        return df

    def _energy_nest(self, PQ, PVA, QA, shares=None):
        """0.3.11: (PEN, PVAE, QVA, QEd) of the value added-energy bundle. PEN: price of the energy bundle (CES
        over the energy commodities, sigma_e); PVAE: price of the VA-energy bundle (CES of PVA and PEN, sigma_ve); QVA: value
        added demanded; QEd: energy commodity x activity demand. All equal the Leontief values at benchmark prices (1).
        shares: {'dva', 'den', 'de'} centred on another point (energy_shares_at); None = the SAM's."""
        en = self.en
        d = shares or en
        E, s1, s2 = en["E"], en["s1"], en["s2"]
        PE_ = _pos(PQ[E])[:, None]
        PEN = np.where(en["has"], (d["de"] * PE_ ** (1 - s2)).sum(axis=0) ** (1 / (1 - s2)), 1.0)
        PVAE = (d["dva"] * _pos(PVA) ** (1 - s1) + d["den"] * PEN ** (1 - s1)) ** (1 / (1 - s1))
        QVAE = en["ive"] * QA
        QVA = QVAE * d["dva"] * (PVAE / _pos(PVA)) ** s1
        QEN = QVAE * d["den"] * (PVAE / PEN) ** s1
        QEd = d["de"] * QEN[None, :] * (PEN[None, :] / PE_) ** s2
        return PEN, PVAE, QVA, QEd

    def energy_shares_at(self, PQ, PVA, QA, ref):
        """0.3.11: share parameters of this model's bundle (its own elasticities) that reproduce, at prices PQ
        and PVA and output QA, the input choices of the model `ref` (with or without the bundle). The short-run model's
        installed technology is then centred on the baseline year's point, not on the SAM's: with the hybrid closure's lower
        short-run elasticities the short-run model still reproduces the baseline year when nothing is shocked (putty-clay;
        MANAGE-WB's old vintage). Returns the shock key 'en_shares'."""
        en = self.en
        E, s1, s2 = en["E"], en["s1"], en["s2"]
        if ref.en is not None and not np.array_equal(ref.en["E"], E):
            raise ValueError("energy_shares_at: the reference model bundles other energy commodities")
        PE_ = _pos(PQ[E])[:, None]
        if ref.en is not None:
            PEN, PVAE, QVA, QEd = ref._energy_nest(PQ, PVA, QA)
            QEN = (PE_ * QEd).sum(axis=0) / PEN
        else:                                   # Leontief reference: fixed value added and energy per unit of output
            QVA, QEd = ref.iva * QA, ref.ica[E] * QA[None, :]
            QEN = QEd.sum(axis=0)
            PEN = np.where(QEN > 0, (PE_ * QEd).sum(axis=0) / np.where(QEN > 0, QEN, 1.0), 1.0)
            PVAE = np.where(QVA + QEN > 0, (_pos(PVA) * QVA + PEN * QEN) / np.where(QVA + QEN > 0, QVA + QEN, 1.0), 1.0)
        QVAE = en["ive"] * QA
        safe = lambda x: np.where(x > 0, x, 1.0)
        on = QVAE > 0
        return dict(dva=np.where(on, QVA / safe(QVAE) * (_pos(PVA) / PVAE) ** s1, en["dva"]),
                    den=np.where(on, QEN / safe(QVAE) * (PEN / PVAE) ** s1, en["den"]),
                    de=np.where(en["has"] & (QEN > 0), QEd / safe(QEN)[None, :] * (PE_ / PEN[None, :]) ** s2, en["de"]))

    def _output_gap(self, Y, sh):
        """0.3.13 (P6, check MG1): the output gap the markup pass-through responds to, in percent: 100 x (Y / Y_ref - 1), Y real
        GDP at benchmark prices, Y_ref the shock key 'mk_gdp' (the dynamic model's baseline year) or the benchmark's."""
        ref = self.real_gdp0 if sh["mk_gdp"] is None else sh["mk_gdp"]
        return 100.0 * (Y / ref - 1.0)

    def _ptm(self, pwm, EXR, sh):
        """0.3.13 (P2(b), check ER1): the US$ price foreign suppliers charge for imports sold here when they absorb the share
        1 - erpt of a move of the peso against its reference exr_ref (pricing to market): pwm x (EXR / exr_ref) ** (erpt - 1), so
        that the peso price is pwm x exr_ref x (EXR / exr_ref) ** erpt. erpt 1 = the world price (full pass-through)."""
        return pwm * (EXR / sh["exr_ref"]) ** (sh["erpt"] - 1.0)

    def _oil_dom(self, W, sh):
        """0.3.13 (check OP1): the domestic peso price, before the tariff, of imports whose world price in pesos W =
        pwm x EXR reaches buyers at home only by the share oil_pass within the period: oil_ref x (W / oil_ref) ** oil_pass, oil_ref the
        reference world price in pesos (in the dynamic model the baseline year's). oil_pass 1 = W, the world price in full."""
        return sh["oil_ref"] * (W / sh["oil_ref"]) ** sh["oil_pass"]

    def markup_at(self, ref: Solution, tfp=1.0) -> dict:
        """0.3.13 (pricing='markup'): the shock keys that centre this model on a zero-profit solution `ref` of a model of the
        same SAM (the dynamic model's baseline year, solved in the long-run closure), so that this model reproduces it when nothing
        is shocked, as the sticky option's anchor does. 'markup': the home price over unit variable cost, less 1, with variable
        cost = revenue less capital and land income (labour and intermediate inputs, whatever input mix `ref` used); for an
        activity that does not export this is capital income / variable cost. 'mk_coef': factor use per unit of output at TFP 1,
        tfp being the productivity `ref` was solved with (one number, or one per activity). 'mk_qd': ref's home sales. 'pa_anchor':
        the price the stickiness rule compares with, (1 - ta) x home price for markup activities, unit revenue for the others."""
        W, QF, QA = (np.asarray(ref[k], float) for k in ("W", "QF", "QA"))
        UR = np.asarray(ref["UNITREV"], float)
        cap = W[self.kcap] * QF[self.kcap]
        land = W[self.klnd] * QF[self.klnd] if self.klnd is not None else 0.0
        avc = (UR * QA - cap - land) / QA
        urd = np.where(self.isMK, np.asarray(ref["PDS"], float)[self.mk_com] * UR / np.asarray(ref["PA"], float), UR)
        mu = np.where(self.isMK & (avc > 0), urd / np.where(avc > 0, avc, 1.0) - 1.0, 0.0)
        tf = np.broadcast_to(np.asarray(tfp, float), QA.shape)
        return {"markup": {a: float(mu[i]) for i, a in enumerate(self.A)}, "mk_coef": QF * (tf / QA)[None, :],
                "mk_qd": np.asarray(ref["QD"], float).copy(), "pa_anchor": {a: float(urd[i]) for i, a in enumerate(self.A)}}

    def rebuild_sam(self, sol: Solution) -> pd.DataFrame:
        """Rebuild the SAM implied by a solution (used by the replication check)."""
        v = sol.v
        idx = self.sam.codes
        S = pd.DataFrame(0.0, index=idx, columns=idx)
        A, C, H, F = self.A, self.C, self.H, self.F
        EXR, CPI = v["EXR"], v["CPI"]
        S.loc[A, C] = self.theta * v["QA"][:, None] * v["PX"][None, :]
        if self.home == "separate":                  # 0.3.1: own produce goes back to the activity -> household cells
            for a in A:
                k = C.index("c" + a[1:])
                val = v["PX"][k] * v["QHA"][k]
                S.loc[a, "c" + a[1:]] -= val.sum()
                S.loc[a, H] = val
        if self.en is None:
            S.loc[C, A] = self.ica * v["QA"][None, :] * v["PQ"][:, None]
        else:                                   # 0.3.11: energy cells from the nest
            ici = self.en["ica_ne"] * v["QA"][None, :]
            ici[self.en["E"]] = self._energy_nest(v["PQ"], v["PVA"], v["QA"], self.make_shocks(sol.shocks)["en_shares"])[3]
            S.loc[C, A] = ici * v["PQ"][:, None]
        FP = v["W"] * v["QF"]
        if "QFH" in v and np.any(v["QFH"]):          # 0.3.11: hoarded wages to labour, out of each activity's capital
            HB = v["W"] * v["QFH"]
            FP = FP + HB
            FP[self.kcap] = FP[self.kcap] - HB.sum(axis=0)
        S.loc[F, A] = FP
        S.loc[C, "trc"] = v["PQ"] * self.sm * v["T"]
        if self.margins == "split":
            S.loc["trc", C] = self.icx * (v["QM"] + v["QD"]) * v["PTRC"]
        else:
            S.loc["trc", C] = self.icq * v["QQ"] * v["PTRC"]
        S.loc[C, H] = v["QH"] * v["PQ"][:, None]
        S.loc[C, "gov"] = v["QG"] * v["PQ"]
        S.loc[C, "s-i"] = v["QINV"] * v["PQ"]
        S.loc[C, "dstk"] = self.qdst * v["PQ"]
        S.loc[C, "row"] = v["QE"] * v["PE"] + v["pwe"] * EXR * self.rex
        S.loc["row", C] = v["pwm"] * EXR * (v["QM"] + self.rex)
        S.loc["mtax", C] = v["MTAX"]
        S.loc["stax", C] = v["STAX"]
        for k, f in enumerate(F):
            S.loc[f, "row"] = self.frow_in[k] * EXR
            S.loc["row", f] = self.frow_out[k] * EXR
            if self.has_ftax:
                S.loc["ftax", f] = self.tf[k] * v["YF"][k]
            for i, inst in enumerate(self.inst):
                S.loc[inst, f] = v["YIF"][i, k]
        S.loc["ent", "gov"] = self.trg_ent * CPI
        S.loc["ent", "row"] = self.erow_in * EXR
        S.loc["dtax", "ent"] = self.te * v["YE"]
        S.loc[H, "ent"] = self.she * v["YE"]
        S.loc["gov", "ent"] = self.sheg * v["YE"]
        S.loc["row", "ent"] = self.erow_out * EXR
        S.loc["s-i", "ent"] = v["ESAV"]
        S.loc[H, "gov"] = self.trg_h * CPI
        S.loc[H, "row"] = self.hrow_in * EXR
        S.loc["dtax", H] = self.tins * v["YH"]
        S.loc["gov", H] = self.tgh * v["YH"]
        S.loc["row", H] = self.hrow_out * EXR
        S.loc["s-i", H] = v["HSAV"]
        S.loc["gov", "dtax"] = self.te * v["YE"] + (self.tins * v["YH"]).sum()
        if self.has_ftax:
            S.loc["gov", "ftax"] = (self.tf * v["YF"]).sum()
        if self.has_atax:
            S.loc["atax", A] = v["ATAX"]
            S.loc["gov", "atax"] = float(v["ATAX"].sum())
        S.loc["gov", "mtax"] = v["MTAX"].sum()
        S.loc["gov", "stax"] = v["STAX"].sum()
        S.loc["gov", "row"] = self.grow_in * EXR
        S.loc["row", "gov"] = self.grow_out * EXR
        S.loc["s-i", "gov"] = v["GSAV"]
        S.loc["s-i", "row"] = self.fsav * EXR
        S.loc["dstk", "s-i"] = float(v["PQ"] @ self.qdst)
        return S
