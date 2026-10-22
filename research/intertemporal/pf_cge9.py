"""The forward-looking CGE (Stage 2), step 3b-3c (17 Oct 2026): a 9-sector forward-looking (perfect-foresight) CGE on the condensed 2023 SAM.

Data: validation/ifpri/out/sam2023_condensed_9sectors.csv (built by validation/ifpri/build_condensed_sam.py from the IFPRI
2023 Philippine SAM: 9 activities and commodities, three labour types, land, capital, trade margins, import and sales
taxes, 10 household groups). Solver: pf_solver.py (Dynare's stacked Newton method, block-sparse Jacobian). Elasticities as
in the IFPRI validation (value added 0.8, Armington 2.0, CET 2.0).

Static block, every year: Infinity GEM's static CGE (infinity_gem/cge.py; Lofgren, Harris and Robinson 2002), condensed. The
block reproduces cge.py to 1e-9 percentage points under matched closures (check_static_vs_cge.py):
  - activity j: Leontief in intermediates and value added; value added CES (0.8) in three labour types, land, capital
    (and, with fixed_factors, a fixed factor of the activity); CET exports; one commodity per activity;
  - commodity i: Armington composite of domestic goods and imports (tariff ad valorem); trade margins (paid in the trade
    commodity) and sales tax on the composite; exports at world prices; exchange rate 1 (numeraire: foreign currency);
  - labour (three types) and land fully employed and mobile; capital (and fixed factors) fixed by activity within a year;
  - final demand: consumption, government consumption (fixed quantities), investment goods (fixed recipe), stock changes.
Forward-looking block: one Ramsey household (CRRA SIGMA, discount BETA) sets total consumption; Tobin's q with quadratic
adjustment costs by activity (Hayashi 1982); foreign assets b with a debt-elastic interest rate (Schmitt-Grohe and Uribe
2003). Variables are detrended by the trend growth rate g (balanced growth: labour, land and fixed factors grow in
effective units at g; Dynare's timing, K[t] = end-of-year capital, capital in use in year t = K[t-1] / (1 + g)).

Options (defaults reproduce the 17 Oct 8 PM version, step 3b, exactly):
  calib = "sam"   no growth (g = 0), delta 0.05, all SAM capital income is reproducible capital; r from the data
                  (about 8.4%), BETA = 1 / (1 + r).                                                         (step 3b)
          "pwt"   balanced growth calibrated to data, as Infinity GEM's documented baseline: depreciation 5.02% and
                  rent-earning capital 1.96 x GDP (Penn World Table 11.0; guide 08); g = investment / capital - delta
                  (6.2%); r = PWT 11.0 real internal rate of return, 2023 (17.88%); BETA = (1 + g)^SIGMA / (1 + r).
                  Capital income beyond (r + delta) K is a FIXED FACTOR of each activity (mixed income of the
                  self-employed and other non-reproducible income: Gollin 2002, JPE 110(2); Caselli and Feyrer 2007,
                  QJE 122(2)); in mining it is the natural-resource rent (World Bank WDI, see MINING_RESOURCE_SHARE).
  households = "one"     one Cobb-Douglas demand system (the SAM's total consumption shares)              (step 3b)
               "groups"  the ten household groups of the SAM, as in cge.py: factor income by ownership shares,
                  enterprise and government transfers, remittances, direct taxes, saving rates; each group spends in
                  its own budget shares. The Ramsey household sets TOTAL consumption; all groups' saving rates scale
                  by one factor (mpsadj) so that their spending adds up to it, which is cge.py's 'investment' closure.
  labour = "full"        full employment every year (as before)
           "wage_curve"  (Build 2, 18 Oct 2026) Infinity GEM's '0.3 recommended' short run in the years flagged by the
                  exogenous row 'sr' (1 = short-run year; path(..., sr=...)): all three labour types can be unemployed and
                  each type's peso wage follows a wage curve, ln w = beta_w x ln(employment / labour supply) (the wage
                  relative to its 2023 level; with the exchange rate fixed at 1 a peso wage is meaningful), as Infinity GEM's
                  dynamic.py (_wage_curve: wage = baseline wage x (employment / baseline employment)^beta); beta_w = 7.14,
                  Infinity GEM's central calibration to Okun's law (scenarios/calibrate_wage_curve.py, 17 Oct 2026).
                  Infinity GEM caps employment at labour supply instead of letting it rise above (dynamic.py employment_cap);
                  here the curve is symmetric, so a demand boost from full employment raises wages steeply. Other years:
                  full employment. The within-year block under fixed wages equals cge.py's Keynesian closure
                  (static_keynesian; check_static_vs_cge.py, to 2e-9 pp).
  bridge_baseline()  (Build 1, 18 Oct 2026, spec docs/design/ITEM74_SAM_rest_of_world_vs_BOP_evidence_
                  17Oct2026.md section 5) a base path that does not treat all of the SAM's foreign saving as a gift. Of the
                  SAM's ₱1,458 bn: (a) ₱778 bn is the national-accounts-vs-BOP trade bridge, not a cross-border flow, and (b)
                  ₱164 bn is the borrowing that keeps the NIIP ratio stable at trend growth; both stay permanent inflows
                  (constant shares of GDP). (c) The ₱516 bn excess of 2023's BOP deficit over (b) is BORROWED: it leaves the
                  permanent inflows, and households borrow it in 2023 through a temporary saving wedge (the discount factor x
                  omega[t], omega = 1 - kappa x lambda^t), repaying later. kappa is set so that 2023 borrowing equals the excess
                  (year 1 then has the SAM's trade balance); lambda = the decay of the IMF's projected excess of the deficit
                  over its norm, 2024-2028 (IMF CR 25/333, Table 5; EBA norm about -1% of GDP). Interest on the borrowing is
                  charged at the model rate with the debt-elastic premium; the SAM's investment-income flows carry the actual
                  yield on the existing position (the allocation-puzzle caveat: Gourinchas and Jeanne 2013).
  rot = share of household spending by rule-of-thumb (hand-to-mouth) households (18 Oct 2026, about 2:35 AM; Gali,
                  Lopez-Salido and Valles 2007, JEEA 5(1)): total spending = rot x current disposable income at the SAM's
                  saving rates + (1 - rot) x the Euler households' spending; needs households='groups'. Default 0 (as before).
                  The Euler households hold the capital and the foreign assets (the TANK structure).
  rit = share of investment by rule-of-thumb (cash-flow) investors (18 Oct 2026, about noon; Build 2c): each sector's
                  investment rate = (1 - rit) x the q-investors' rate, xbar + (q / pk - 1) / phi, + rit x xbar x
                  (rk / pk) / (r + delta), i.e. a share of investment follows the current real return on capital (the cash
                  flow of firms that cannot borrow against future profits; Fazzari, Hubbard and Petersen 1988; the investment
                  analogue of rot). Steady state unchanged (rk / pk = r + delta there). Default 0: the original q equation.
                  Why: without it, private investment RISES when public works are cut (Build 2b), against the data, where
                  private and public construction move together.
Stated simplifications (still): one Euler equation for the economy; direct taxes and transfers do not distort choices;
the government budget balances by a lump-sum item (Ricardian); non-trade inflows from abroad (incl. the SAM's foreign
saving) stay at their 2023 share of GDP (the SAM's foreign saving, 5.6% of GDP, is twice the 2023 current-account deficit
in the balance of payments, 2.8%, and eight times the borrowing that keeps BSP's end-2023 net external liabilities
stable at 6.2% growth: see notes in the step 3c output; reconciling the SAM's rest-of-world account is a data task).
NOT part of Infinity GEM; research code. Run:  py research/intertemporal/pf_cge9.py   (step 3b tests, default options)
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import root

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import pf_solver  # noqa: E402

ROOT = HERE.parents[1]
SAM_CSV = ROOT / "validation" / "ifpri" / "out" / "sam2023_condensed_9sectors.csv"
SECT = ["agri", "mine", "food", "oman", "chem", "util", "cons", "trad", "serv"]
LAB = ["flab-n", "flab-p", "flab-s"]
HH = [f"hhd-{a}{i}" for a in "ru" for i in range(1, 6)]
N = len(SECT)
TRAD = SECT.index("trad")
c_ = lambda z: np.asarray(z, float)[:, None]         # a sector vector as a column (broadcasts over years)

# ---- data for calib="pwt" (each with its source)
PWT = dict(depreciation=0.0502,       # PWT 11.0 capital detail, 2023: capital consumption / previous net stock (guide 08, Gold)
           capital_output=1.96,       # rent-earning capital / GDP: PWT 11.0 net stock 2.42 x GDP less public capital (IMF ICSD)
           irr=0.1788)                # PWT 11.0 'irr', Philippines 2023 (data/raw/macro/pwt110.xlsx); 0.168-0.230 in 2010-2023
# Mining's natural-resource rent as a share of its SAM capital income. World Bank WDI (downloaded 17 Oct 2026,
# data/raw/macro/WDI_natural_resource_rents_PHL_downloaded_2026-10-17/): mineral + natural gas + oil + coal rents, % of GDP.
# The lowest year of 2012-2021 (2016: 0.224 + 0.106 + 0.033 + 0.046 = 0.409% of GDP) is used, because the World Bank's rents
# use world-average extraction costs and overstate (Lange, Wodon and Carey 2018); the 2012-2021 average (0.87%) exceeds
# mining's whole SAM capital income, an upper bound.
MINING_RENT_PCT_GDP = 0.409
# Build 1 (the foreign-saving bridge): the SAM's foreign saving, ₱1,458 bn in 2023, split by the evidence note's section 5 (pesos, PSA GDP basis)
BRIDGE_SPLIT = dict(bridge=778 / 1458, sustainable=164 / 1458, temporary=516 / 1458)
IMF_CA = {2023: -2.8, 2024: -4.0, 2025: -3.8, 2026: -3.4, 2027: -3.1, 2028: -2.9}   # IMF CR 25/333, Table 5, % of GDP
IMF_NORM = -1.0                                   # IMF EBA current-account norm, about -0.9 to -1.2% of GDP (Annex II)


class CGE9:
    def __init__(self, sam_csv=SAM_CSV, sig_va=0.8, sig_a=2.0, omega=2.0, delta=0.05, sigma=2.0, phi=8.0, psi=0.02,
                 calib="sam", households="one", mining_rent_pct=MINING_RENT_PCT_GDP, public_capital=None,
                 labour="full", beta_w=7.14, rot=0.0, rit=0.0, rit_basis="return"):
        if calib not in ("sam", "pwt") or households not in ("one", "groups"):
            raise ValueError("calib must be 'sam' or 'pwt'; households 'one' or 'groups'")
        if labour not in ("full", "wage_curve"):
            raise ValueError("labour must be 'full' or 'wage_curve'")
        self.labour, self.beta_w = labour, float(beta_w)
        if not 0.0 <= rot < 1.0 or (rot and households != "groups"):
            raise ValueError("rot (share of rule-of-thumb spending) must be in [0, 1) and needs households='groups'")
        self.rot = float(rot)
        if not 0.0 <= rit < 1.0 or rit_basis not in ("return", "output"):
            raise ValueError("rit (share of rule-of-thumb investment) must be in [0, 1); rit_basis 'return' or 'output'")
        self.rit, self.rit_basis, self.X_ss = float(rit), rit_basis, None
        S = pd.read_csv(sam_csv, index_col=0)
        a = ["a" + s for s in SECT]
        c = ["c" + s for s in SECT]
        self.calib, self.households = calib, households
        # public capital, in deviations from the base path, as Infinity GEM's dynamic.py:
        # dKG[t] = (1 - delta_g) dKG[t-1] / (1 + g) + e dIG[t];  TFP of every activity x (1 + dKG_in / KG0)^phi
        self.pc = None if public_capital is None else dict(dict(delta_g=0.0352, e=0.77), **public_capital)
        self.sig_va, self.sig_a, self.omega, self.sigma, self.phi, self.psi = sig_va, sig_a, omega, sigma, phi, psi
        col = lambda r, k: S.loc[r, k].to_numpy(float)
        # ---- production and trade
        self.X0 = np.array([S.loc[a[j], c[j]] for j in range(N)])            # output at producer prices (px = 1)
        self.E0 = col(c, "row")                                               # exports (pe = pwe = 1)
        self.D0 = self.X0 - self.E0                                           # domestic sales (pd = 1)
        self.M0 = col("row", c)                                               # imports at world prices (pwm = 1)
        self.tm = np.divide(col("mtax", c), self.M0, out=np.zeros(N), where=self.M0 > 0)
        self.Q0 = self.D0 + (1 + self.tm) * self.M0                           # composite quantity (pa = 1 in 2023)
        trc = col("trc", c)
        self.mg = trc / self.Q0                                               # margin (units of trade) per unit of composite
        self.ts = col("stax", c) / (self.Q0 + trc)                            # sales tax on composite value plus margin
        self.pq0 = (1 + self.ts) * (1 + self.mg)                              # 2023 purchaser price
        assert abs(self.pq0[TRAD] - 1) < 1e-12, "the margin commodity must carry no margin or sales tax"
        inter = S.loc[c, a].to_numpy(float)
        self.aij = inter / self.pq0[:, None] / self.X0[None, :]               # composite units per unit of output
        Flab = S.loc[LAB, a].to_numpy(float)
        Fland = S.loc["flnd", a].to_numpy(float)
        Rcap = S.loc["fcap", a].to_numpy(float)                               # SAM capital income by activity
        self.VA0 = Flab.sum(0) + Fland + Rcap
        assert np.allclose(inter.sum(0) + self.VA0, self.X0), "activity accounts must balance (no activity taxes in this SAM)"
        self.iva = self.VA0 / self.X0
        self.L0 = Flab
        self.Land0 = Fland.sum()
        self.thE = self.E0 / self.X0
        self.alM = (1 + self.tm) * self.M0 / self.Q0
        self.I0 = S.loc[c, "s-i"].sum()                                       # fixed investment, ₱ bn
        self.GDP0 = float(self.VA0.sum() + col("mtax", c).sum() + col("stax", c).sum())
        # ---- capital, growth and the interest rate
        if calib == "sam":                                                    # step 3b (simplification: no growth)
            self.g, self.delta = 0.0, delta
            self.Rk = (self.g + delta) * Rcap.sum() / self.I0                 # rental per unit of capital = r + delta
            self.r_ss = self.Rk - delta
            self.beta = 1 / (1 + self.r_ss)
            ff = np.zeros(N)                                                  # no fixed factor
        else:                                                                 # balanced growth, data calibration
            self.delta = PWT["depreciation"]
            Ktot = PWT["capital_output"] * self.GDP0
            self.g = self.I0 / Ktot - self.delta                              # investment = (g + delta) x capital in use
            self.r_ss = PWT["irr"]
            self.Rk = self.r_ss + self.delta
            self.beta = (1 + self.g) ** sigma / (1 + self.r_ss)
            im = SECT.index("mine")
            ff = np.zeros(N)
            ff[im] = min(1.0, mining_rent_pct / 100 * self.GDP0 / Rcap[im])   # mining: resource rent share
            need = Ktot * self.Rk - (1 - ff[im]) * Rcap[im]                   # capital income of the other activities
            rest = np.arange(N) != im
            s_other = 1 - need / Rcap[rest].sum()
            if not 0 <= s_other < 1:
                raise ValueError(f"capital data imply a fixed-factor share of {s_other:.3f} outside [0, 1)")
            ff[rest] = s_other
        self.ff_share = ff
        self.FF0 = ff * Rcap                                                  # fixed-factor income (quantity, price 1)
        self.K0 = (1 - ff) * Rcap / self.Rk                                   # capital IN USE in the base year
        self.has_ff = self.FF0 > 1e-9
        self.iff = np.where(self.has_ff)[0]
        self.nff = len(self.iff)
        F6 = np.vstack([Flab, Fland[None, :], ((1 - ff) * Rcap)[None, :], self.FF0[None, :]])
        self.theta = F6 / self.VA0                                            # value shares (6 x 9): 3 labour, land, capital, fixed
        self.xbar = self.g + self.delta                                       # steady-state investment / capital in use
        self.kappa = S.loc[c, "s-i"].to_numpy(float) / self.pq0 / self.I0     # capital-good recipe (pk = 1 in 2023)
        # ---- final demand
        cons = S.loc[c, HH].sum(axis=1).to_numpy(float)
        self.C0 = cons.sum()
        self.shc = cons / self.C0                                             # aggregate budget shares (CPI weights)
        self.G0 = S.loc[c, "gov"].to_numpy(float) / self.pq0
        self.dstk = S.loc[c, "dstk"].to_numpy(float) / self.pq0
        # ---- the rest of the world: NF = non-trade inflows - outflows, including foreign saving (share of GDP with growth)
        other = [k for k in S.index if k not in c and k != "row"]
        self.NF0 = float(S.loc[other, "row"].sum() - S.loc["row", other].sum())
        self.FSAV0 = float(S.loc["s-i", "row"])
        self.HROW_IN = S.loc[HH, "row"].to_numpy(float)                       # remittances and other transfers to households
        if households == "groups":
            self._calibrate_groups(S, c)
        self.sam = S
        # ---- unknowns per year
        lay = [("pd", N), ("X", N), ("rk", N), ("w", 3), ("wl", 1), ("C", 1), ("wff", self.nff),
               ("mpsadj", 1 if households == "groups" else 0), ("I", N), ("q", N), ("K", N),
               ("dKG", 1 if public_capital is not None else 0), ("b", 1)]
        self.sl, pos = {}, 0
        for k, n in lay:
            self.sl[k] = slice(pos, pos + n)
            pos += n
        self.n_y = pos
        self.names = ([f"pd_{s}" for s in SECT] + [f"X_{s}" for s in SECT] + [f"rk_{s}" for s in SECT] + ["w_n", "w_p", "w_s", "wland", "C"]
                      + [f"wff_{SECT[j]}" for j in self.iff] + (["mpsadj"] if households == "groups" else [])
                      + [f"I_{s}" for s in SECT] + [f"q_{s}" for s in SECT] + [f"K_{s}" for s in SECT]
                      + (["dKG"] if public_capital is not None else []) + ["b"])
        self.n_x = 3 * N + 7
        self.x0 = np.concatenate([np.ones(N), np.ones(N), np.ones(N), [1.0, self.NF0, 1.0, 1.0, 0.0, 0.0, 1.0]])   # sr, omega
        if self.pc is not None:
            self.KG0 = self.pc["kg_gdp"] * self.GDP0                          # public capital in use, base year (PHP bn)

    def _calibrate_groups(self, S, c):
        """The SAM's institutions, as in infinity_gem/cge.py (same formulas): factor ownership shares, enterprises, households."""
        F = LAB + ["flnd", "fcap"]
        a = ["a" + s for s in SECT]
        YF0 = np.array([S.loc[f, a].sum() + S.loc[f, "row"] for f in F])
        self.frow_in = np.array([S.loc[f, "row"] for f in F])
        self.tf = np.array([S.loc["ftax", f] for f in F]) / YF0
        self.frow_out = np.array([S.loc["row", f] for f in F])
        dist0 = (1 - self.tf) * YF0 - self.frow_out
        inst = HH + ["ent"]
        self.shif = np.array([[S.loc[i, f] / dist0[k] for k, f in enumerate(F)] for i in inst])
        self.trg_ent, self.erow_in = S.loc["ent", "gov"], S.loc["ent", "row"]
        YE0 = sum(S.loc["ent", f] for f in F) + self.trg_ent + self.erow_in
        self.she = np.array([S.loc[h, "ent"] for h in HH]) / YE0
        self.trg_h = S.loc[HH, "gov"].to_numpy(float)
        YH0 = S.loc[HH].sum(axis=1).to_numpy(float)
        self.tins = S.loc["dtax", HH].to_numpy(float) / YH0
        self.tgh = S.loc["gov", HH].to_numpy(float) / YH0
        self.hrow_out = S.loc["row", HH].to_numpy(float)
        DY0 = YH0 * (1 - self.tins - self.tgh) - self.hrow_out
        self.mps = S.loc["s-i", HH].to_numpy(float) / DY0
        self.EH0 = DY0 * (1 - self.mps)
        self.bsh = S.loc[c, HH].to_numpy(float) / self.EH0                   # C x H budget shares
        assert np.allclose(self.bsh.sum(0), 1), "household accounts must balance"

    # ---------------------------------------------------------------- unpacking (arrays are (n, T))
    def split(self, y):
        d = {k: y[s] for k, s in self.sl.items()}
        d["wl"], d["C"], d["b"] = y[self.sl["wl"].start], y[self.sl["C"].start], y[self.sl["b"].start]
        d["mpsadj"] = y[self.sl["mpsadj"].start] if self.households == "groups" else None
        d["dKG"] = y[self.sl["dKG"].start] if self.pc is not None else None
        return d

    @staticmethod
    def split_x(x):
        return dict(A=x[0:9], pwm=x[9:18], pwe=x[18:27], g=x[27], NF=x[28], ls=x[29], remit=x[30], dIG=x[31], sr=x[32],
                    omega=x[33])

    def eff(self, xx, dKG_lag):
        """Exogenous values with public capital's effect on productivity (no change without public_capital)."""
        if self.pc is None:
            return xx
        xx = dict(xx)
        xx["A"] = xx["A"] * (1 + dKG_lag / (1 + self.g) / self.KG0) ** self.pc["phi"]
        return xx

    def kin(self, Klag):
        return Klag / (1 + self.g)                                           # capital in use this year (detrended)

    # ---------------------------------------------------------------- static block
    def static(self, v, Kin, xx):
        """Within-year quantities and prices, given prices, outputs, consumption, the capital in use and exogenous values."""
        pd_, X, rk, w, wl, C = v["pd"], v["X"], v["rk"], v["w"], v["wl"], v["C"]
        A, pwm, pwe = xx["A"], xx["pwm"], xx["pwe"]
        om, sa, sv = self.omega, self.sig_a, self.sig_va
        thE = c_(self.thE)
        px = ((1 - thE) * pd_ ** (1 + om) + thE * pwe ** (1 + om)) ** (1 / (1 + om))     # CET unit revenue
        D = c_(self.D0) * (X / c_(self.X0)) * (pd_ / px) ** om
        E = c_(self.E0) * (X / c_(self.X0)) * (pwe / px) ** om
        alM = c_(self.alM)
        pa = ((1 - alM) * pd_ ** (1 - sa) + alM * pwm ** (1 - sa)) ** (1 / (1 - sa))       # Armington unit cost
        Q = c_(self.Q0) * (D / c_(self.D0)) * (pd_ / pa) ** sa
        M = c_(self.M0) * (Q / c_(self.Q0)) * (pa / pwm) ** sa
        pq = c_(1 + self.ts) * (pa + c_(self.mg) * pa[TRAD])                               # trade carries no margin or tax
        wff = np.ones_like(pd_)
        if self.nff:
            wff = wff.copy(); wff[self.iff] = v["wff"]
        rel = [w[0], w[1], w[2], np.broadcast_to(wl, pd_.shape), rk / self.Rk, wff]        # factor prices / 2023 level
        cost = sum(c_(self.theta[f]) * rel[f] ** (1 - sv) for f in range(6))
        pva = cost ** (1 / (1 - sv)) / A
        VA = c_(self.iva) * X
        scale = (VA / c_(self.VA0)) * A ** (sv - 1) * pva ** sv
        Fd = [c_(self.L0[f]) * scale * rel[f] ** (-sv) for f in range(3)]
        land = (c_(self.theta[3] * self.VA0) * scale * rel[3] ** (-sv)).sum(0)
        Kd = c_(self.K0) * scale * rel[4] ** (-sv)
        FFd = c_(self.FF0) * scale * rel[5] ** (-sv)
        unit_cost = self.aij.T @ pq + c_(self.iva) * pva
        P = np.exp((c_(self.shc) * np.log(pq / c_(self.pq0))).sum(0))                     # consumer price index (1 in 2023)
        cpi_l = (c_(self.shc) * pq / c_(self.pq0)).sum(0)                                  # Laspeyres CPI (cge.py's numeraire)
        out = dict(px=px, D=D, E=E, pa=pa, Q=Q, M=M, pq=pq, pva=pva, VA=VA, Fd=Fd, land=land, Kd=Kd, FFd=FFd,
                   unit_cost=unit_cost, P=P, cpi_l=cpi_l, pk=(c_(self.kappa) * pq).sum(0), pwe=pwe, pwm=pwm, wff=wff)
        if self.households == "one":
            out["Cd"] = c_(self.shc) * P * C / pq
        else:
            out.update(self.groups(v, out, Kin, xx))
        return out

    def groups(self, v, s, Kin, xx):
        """cge.py's institution block: incomes of the ten groups and their spending (budget shares bsh)."""
        YF = np.vstack([v["w"][f] * s["Fd"][f].sum(0) for f in range(3)]
                       + [v["wl"] * s["land"], (v["rk"] * Kin).sum(0) + (s["wff"] * s["FFd"]).sum(0)])
        YF = YF + c_(self.frow_in)
        dist = c_(1 - self.tf) * YF - c_(self.frow_out)
        YIF = self.shif @ dist                                                          # (H + ent) x T
        YE = YIF[-1] + self.trg_ent * s["cpi_l"] + self.erow_in
        YH = YIF[:-1] + c_(self.she) * YE + c_(self.trg_h) * s["cpi_l"] + c_(self.HROW_IN) * xx["remit"]
        DY = YH * c_(1 - self.tins - self.tgh) - c_(self.hrow_out)
        EH = DY * (1 - c_(self.mps) * (1 + v["mpsadj"]))
        Cd = (self.bsh @ EH) / s["pq"]
        return dict(Cd=Cd, EH=EH, YH=YH, DY=DY)

    def rate(self, b):
        return self.r_ss - self.psi * (np.exp(b / self.GDP0) - 1)

    def trade_balance(self, s):
        return (s["pwe"] * s["E"]).sum(0) - (s["pwm"] * s["M"]).sum(0)

    def nf(self, xx):
        """Non-trade net inflows: NF plus the change in remittances (both in the group block and the current account)."""
        return xx["NF"] + (xx["remit"] - 1) * self.HROW_IN.sum()

    def market_residuals(self, v, s, xx, inv_total):
        """Commodity markets, zero profit, labour, land, fixed factors, household spending (scaled)."""
        demand = self.aij @ v["X"] + s["Cd"] + c_(self.G0) * xx["g"] + c_(self.kappa) * inv_total + c_(self.dstk)
        demand[TRAD] += (c_(self.mg) * s["Q"]).sum(0)
        out = [(s["Q"] - demand) / c_(self.Q0), s["px"] - s["unit_cost"]]
        out.append(np.vstack([(s["Fd"][f].sum(0) - self.L0[f].sum() * xx["ls"]) / self.L0[f].sum() for f in range(3)]))
        out.append(((s["land"] - self.Land0) / self.Land0)[None, :])
        if self.nff:
            out.append((s["FFd"][self.iff] - c_(self.FF0[self.iff])) / c_(self.FF0[self.iff]))
        if self.households == "groups":
            # total household spending: a share rot spends current disposable income at the SAM's saving rates (rule of
            # thumb, Gali, Lopez-Salido and Valles 2007), the rest follows the Euler equation (C); rot = 0: as before
            static = (s["DY"] * c_(1 - self.mps)).sum(0)
            target = self.rot * static + (1 - self.rot) * s["P"] * v["C"]
            out.append(((s["EH"].sum(0) - target) / self.C0)[None, :])
        return out

    # ---------------------------------------------------------------- dynamic residuals (vectorised over years)
    def resid(self, ylag, y, ylead, x, xlead):
        v, vl, vn = self.split(y), self.split(ylag), self.split(ylead)
        xx, xn = self.split_x(x), self.split_x(xlead)
        d, phi, g, xb = self.delta, self.phi, self.g, self.xbar
        Kin, Kin_n = self.kin(vl["K"]), self.kin(v["K"])
        if self.pc is not None:
            xx, xn = self.eff(xx, vl["dKG"]), self.eff(xn, v["dKG"])
        s = self.static(v, Kin, xx)
        sn = self.static(vn, Kin_n, xn)                        # next year produces with this year's end-of-year capital
        ik = v["I"] / Kin
        inv_total = (v["I"] + phi / 2 * (ik - xb) ** 2 * Kin).sum(0) + xx["dIG"]   # + extra public investment
        mk = self.market_residuals(v, s, xx, inv_total)
        if self.labour == "wage_curve":                                                # Build 2: short-run years
            emp = np.vstack([s["Fd"][f].sum(0) / (self.L0[f].sum() * xx["ls"]) for f in range(3)])
            mk[2] = np.where(xx["sr"][None, :] > 0.5, np.log(v["w"]) - self.beta_w * np.log(emp), mk[2])
        r_cap = (s["Kd"] - Kin) / c_(self.K0)                                          # capital demand = capital in use
        if self.rit:                     # Build 2c: a share rit of investment follows current cash flow or output
            ik_q = xb + (v["q"] / s["pk"] - 1) / phi
            if self.rit_basis == "output":           # accelerator: the sector's output relative to its steady state
                if self.X_ss is None:
                    raise RuntimeError("rit_basis='output' needs set_output_base() (the steady state's output) first")
                ik_cf = xb * v["X"] / c_(self.X_ss)
            else:
                ik_cf = xb * v["rk"] / (s["pk"] * self.Rk)
            r_q = s["pk"] * phi * ((1 - self.rit) * ik_q + self.rit * ik_cf - ik)
        else:
            r_q = v["q"] - s["pk"] * (1 + phi * (ik - xb))
        r_acc = (v["K"] - ((1 - d) * Kin + v["I"])) / c_(self.K0)
        r_ca = (v["b"] - ((1 + self.rate(vl["b"])) / (1 + g) * vl["b"] + self.trade_balance(s) + self.nf(xx))) / self.GDP0
        m = self.beta * xx["omega"] * (1 + g) ** (-self.sigma) * (vn["C"] / v["C"]) ** (-self.sigma) * s["P"] / sn["P"]
        r_bond = 1 - m * (1 + self.rate(v["b"]))
        ikn = vn["I"] / Kin_n
        r_euler = v["q"] - m * (vn["rk"] + vn["q"] * (1 - d) + sn["pk"] * phi / 2 * (ikn ** 2 - xb ** 2))
        extra = []
        if self.pc is not None:
            extra = [((v["dKG"] - ((1 - self.pc["delta_g"]) / (1 + g) * vl["dKG"] + self.pc["e"] * xx["dIG"])) / self.KG0)[None, :]]
        return np.vstack(mk[:2] + [r_cap] + mk[2:] + [r_q, r_acc] + extra + [r_ca[None, :], r_bond[None, :], r_euler])

    # ---------------------------------------------------------------- steady state (solved on its own)
    def _static_unknowns(self, z, K):
        v = dict(pd=z[0:9, None], X=z[9:18, None], w=z[18:21, None], wl=z[21:22], C=z[22:23])
        k = 23
        v["wff"] = z[k:k + self.nff, None]; k += self.nff
        v["mpsadj"] = z[k:k + 1] if self.households == "groups" else None
        k += 1 if self.households == "groups" else 0
        return v, k

    def set_output_base(self, y_ss=None):
        """Build 2c, rit_basis='output': store each sector's steady-state output (the accelerator's reference)."""
        y_ss = self.steady()[0] if y_ss is None else y_ss
        self.X_ss = np.asarray(self.split(y_ss[:, None])["X"][:, 0], float)
        return self.X_ss

    def steady(self, x=None, guess=None):
        """Balanced-growth steady state for constant exogenous values x: q = pk, I = (g + delta) Kin, rk = pk (r + delta),
        b = 0. Unknowns: pd, X, w, wland, C, [wff], [mpsadj], Kin (9)."""
        x = (self.x0 if x is None else np.asarray(x, float))[:, None]
        xx = self.split_x(x)
        dKG_ss = 0.0
        if self.pc is not None:                          # permanent extra public investment: dKG = e dIG (1 + g) / (g + delta_g)
            dKG_ss = float(self.pc["e"] * xx["dIG"][0] * (1 + self.g) / (self.g + self.pc["delta_g"]))
            xx = self.eff(xx, np.array([dKG_ss]))
        z0 = np.concatenate([np.ones(9), self.X0, np.ones(3), [1.0], [self.C0], np.ones(self.nff),
                             [0.0] * (self.households == "groups"), self.K0]) if guess is None else guess

        def build(z):
            v, k = self._static_unknowns(z, None)
            Kin = z[k:k + 9, None]
            pq = c_(self.pq0)
            for _ in range(3):                           # rk = pk Rk with pk from this year's prices: fixed-point passes
                v["rk"] = np.broadcast_to((c_(self.kappa) * pq).sum(0) * self.Rk, (9, 1))
                s = self.static(v, Kin, xx)
                pq = s["pq"]
            v["rk"] = np.broadcast_to(s["pk"] * self.Rk, (9, 1))
            s = self.static(v, Kin, xx)
            return v, s, Kin

        def f(z):
            v, s, Kin = build(z)
            mk = self.market_residuals(v, s, xx, self.xbar * Kin.sum(0) + xx["dIG"])
            r_cap = (s["Kd"] - Kin) / c_(self.K0)
            r_ca = (self.trade_balance(s) + self.nf(xx)) / self.GDP0
            return np.concatenate([r.ravel() for r in mk] + [r_cap.ravel(), r_ca.ravel()])
        sol = root(f, z0, method="hybr", options=dict(xtol=1e-14))
        res = float(np.abs(f(sol.x)).max())
        if res > 1e-9:
            raise RuntimeError(f"steady state not found (residual {res:.1e}): {sol.message}")
        v, s, Kin = build(sol.x)
        pk = float(s["pk"][0])
        y = np.zeros(self.n_y)
        y[self.sl["pd"]], y[self.sl["X"]], y[self.sl["rk"]] = v["pd"][:, 0], v["X"][:, 0], pk * self.Rk
        y[self.sl["w"]], y[self.sl["wl"]], y[self.sl["C"]] = v["w"][:, 0], v["wl"], v["C"]
        y[self.sl["wff"]] = v["wff"][:, 0]
        if self.households == "groups":
            y[self.sl["mpsadj"]] = v["mpsadj"]
        y[self.sl["I"]], y[self.sl["q"]] = self.xbar * Kin[:, 0], pk
        y[self.sl["K"]] = Kin[:, 0] * (1 + self.g)                            # end-of-year stock = next year's capital in use
        if self.pc is not None:
            y[self.sl["dKG"]] = dKG_ss
        return y, res

    # ---------------------------------------------------------------- one static year (the cross-check with cge.py)
    def static_equilibrium(self, x=None, K=None, inv_total=None):
        """One year on its own: capital in use fixed by activity (K, default 2023), real investment fixed (default 2023),
        foreign assets 0, so the current account balances and consumption is what is left: Infinity GEM's static closure
        'investment' with capital='fixed' (check_static_vs_cge.py). Unknowns: pd, X, rk, w, wland, C, [wff], [mpsadj]."""
        x = (self.x0 if x is None else np.asarray(x, float))[:, None]
        xx = self.split_x(x)
        K = (self.K0 if K is None else np.asarray(K, float))[:, None]
        inv_total = self.I0 if inv_total is None else inv_total
        z0 = np.concatenate([np.ones(9), self.X0, np.ones(3), [1.0], [self.C0], np.ones(self.nff),
                             [0.0] * (self.households == "groups"), np.full(9, self.Rk)])

        def unpack(z):
            v, k = self._static_unknowns(z, K)
            v["rk"] = z[k:k + 9, None]
            return v

        def f(z):
            v = unpack(z)
            s = self.static(v, K, xx)
            mk = self.market_residuals(v, s, xx, np.array([inv_total]))
            r_cap = (s["Kd"] - K) / c_(self.K0)
            r_ca = (self.trade_balance(s) + self.nf(xx)) / self.GDP0
            return np.concatenate([r.ravel() for r in mk] + [r_cap.ravel(), r_ca.ravel()])
        sol = root(f, z0, method="hybr", options=dict(xtol=1e-14))
        res = float(np.abs(f(sol.x)).max())
        if res > 1e-9:
            raise RuntimeError(f"static equilibrium not found (residual {res:.1e}): {sol.message}")
        v = unpack(sol.x)
        return v, self.static(v, K, xx), res

    def static_keynesian(self, x=None, K=None, inv_total=None):
        """One year in Infinity GEM's short-run (Keynesian) closure (Build 2, 18 Oct 2026): peso wages of all three labour
        types fixed at their 2023 level (employment set by demand), saving rates fixed (mpsadj 0), real investment fixed,
        capital fixed by activity, the exchange rate fixed at 1 and foreign saving free (the current account adjusts).
        = cge.py closure='keynesian', unemployed=all three, wage='nominal', capital='fixed', fx='fixed'
        (check_static_vs_cge.py). Needs households='groups'. Unknowns: pd, X, rk, wland, [wff]."""
        if self.households != "groups":
            raise ValueError("the Keynesian year needs households='groups' (consumption follows income and saving rates)")
        x = (self.x0 if x is None else np.asarray(x, float))[:, None]
        xx = self.split_x(x)
        K = (self.K0 if K is None else np.asarray(K, float))[:, None]
        inv_total = self.I0 if inv_total is None else inv_total
        z0 = np.concatenate([np.ones(9), self.X0, [1.0], np.ones(self.nff), np.full(9, self.Rk)])

        def unpack(z):
            v = dict(pd=z[0:9, None], X=z[9:18, None], w=np.ones((3, 1)), wl=z[18:19], C=np.array([self.C0]),
                     mpsadj=np.zeros(1))
            v["wff"] = z[19:19 + self.nff, None]
            v["rk"] = z[19 + self.nff:28 + self.nff, None]
            return v

        def f(z):
            v = unpack(z)
            s = self.static(v, K, xx)
            mk = self.market_residuals(v, s, xx, np.array([inv_total]))
            keep = mk[:2] + [mk[3]] + (mk[4:5] if self.nff else [])          # no labour clearing, no spending identity
            r_cap = (s["Kd"] - K) / c_(self.K0)
            return np.concatenate([r.ravel() for r in keep] + [r_cap.ravel()])
        sol = root(f, z0, method="hybr", options=dict(xtol=1e-14))
        res = float(np.abs(f(sol.x)).max())
        if res > 1e-9:
            raise RuntimeError(f"Keynesian year not found (residual {res:.1e}): {sol.message}")
        v = unpack(sol.x)
        s = self.static(v, K, xx)
        v["C"] = s["EH"].sum(0) / s["P"]                                      # real consumption the groups choose
        s["employment"] = np.array([s["Fd"][f].sum() / (self.L0[f].sum() * xx["ls"][0]) for f in range(3)])
        return v, s, res

    # ---------------------------------------------------------------- solve a path
    def path(self, T, **changes):
        """Exogenous values (33, T + 1), column 0 = year 1. changes: name -> function(rows) applied in place, e.g.
        pwm=lambda r: r.__setitem__((SECT.index('chem'), slice(0, 3)), 1.2); sr=lambda r: r.__setitem__((0, slice(0, 2)), 1)
        (years 1-2 short-run years, labour='wage_curve')."""
        X = np.repeat(self.x0[:, None], T + 1, axis=1)
        rows = dict(A=X[0:9], pwm=X[9:18], pwe=X[18:27], g=X[27:28], NF=X[28:29], ls=X[29:30], remit=X[30:31], dIG=X[31:32],
                    sr=X[32:33], omega=X[33:34])
        for k, fn in changes.items():
            fn(rows[k])
        return X

    def bridge_baseline(self, T=200, lam=None):
        """Build 1 (the foreign-saving bridge): the base path from the 2023 SAM when the SAM's temporary excess of foreign saving is borrowed
        and repaid (see the module notes). Returns (X, Y, y0, info) with info = dict(kappa, lam, temporary, ...)."""
        from scipy.optimize import brentq
        temp = BRIDGE_SPLIT["temporary"] * self.FSAV0
        if lam is None:                                   # IMF excess over the norm: 2024 -> 2028, four years
            lam = ((-IMF_CA[2028] + IMF_NORM) / (-IMF_CA[2024] + IMF_NORM)) ** (1 / 4)
        ss0 = self.steady()[0]                            # the SAM as a steady state, b = 0 (initial conditions)

        def make(kappa):
            return self.path(T, NF=lambda r: r.__setitem__(slice(None), self.NF0 - temp),
                             omega=lambda r: r.__setitem__((0, slice(None)), 1 - kappa * lam ** np.arange(r.shape[1])))

        def gap(kappa):
            Y, *_ = self.run(make(kappa), y_start=ss0)
            return float(self.split(Y)["b"][0]) + temp    # year-1 assets = -temp: 2023 borrows the excess
        kappa = brentq(gap, 0.0, 0.3, xtol=1e-10)
        X = make(kappa)
        Y, y0, yT, info = self.run(X, y_start=ss0)
        return X, Y, ss0, dict(kappa=kappa, lam=lam, temporary=temp, bridge=BRIDGE_SPLIT["bridge"] * self.FSAV0,
                               sustainable=BRIDGE_SPLIT["sustainable"] * self.FSAV0, newton=info["iterations"])

    def run(self, X, y_start=None, verbose=False):
        T = X.shape[1] - 1
        y0 = self.steady(X[:, 0])[0] if y_start is None else y_start
        yT = self.steady(X[:, -1])[0]
        guess = y0[:, None] + (yT - y0)[:, None] * np.linspace(0, 1, T)[None, :]
        Y, info = pf_solver.solve(self, y0, yT, X, guess, verbose=verbose, tol=1e-9)
        return Y, y0, yT, info

    def accounts(self, Y, y0, X):
        """GDP by expenditure and by income, per year (neither is an equation of the model)."""
        lag = np.column_stack([y0, Y[:, :-1]])
        v, vl, xx = self.split(Y), self.split(lag), self.split_x(X[:, :-1])
        Kin = self.kin(vl["K"])
        if self.pc is not None:
            xx = self.eff(xx, vl["dKG"])
        s = self.static(v, Kin, xx)
        adj = self.phi / 2 * (v["I"] / Kin - self.xbar) ** 2 * Kin
        inv_val = s["pk"] * ((v["I"] + adj).sum(0) + xx["dIG"])
        gov = (s["pq"] * c_(self.G0) * xx["g"]).sum(0)
        stk = (s["pq"] * c_(self.dstk)).sum(0)
        gdp_exp = s["P"] * v["C"] + gov + inv_val + stk + self.trade_balance(s)
        factor = (sum((v["w"][f] * s["Fd"][f].sum(0)) for f in range(3)) + v["wl"] * s["land"] + (v["rk"] * Kin).sum(0)
                  + (s["wff"] * s["FFd"]).sum(0))
        stax = (c_(self.ts) * (s["pa"] + c_(self.mg) * s["pa"][TRAD]) * s["Q"]).sum(0)
        mtax = (c_(self.tm) * s["pwm"] * s["M"]).sum(0)
        gdp_inc = factor + stax + mtax
        # real GDP at constant 2023 prices (quantities x 2023 prices); real income = nominal GDP / consumer prices
        cons_real = (c_(self.pq0) * s["Cd"]).sum(0)
        real_gdp = (cons_real + (c_(self.pq0) * c_(self.G0) * xx["g"]).sum(0) + (v["I"] + adj).sum(0) + xx["dIG"]
                    + (c_(self.pq0) * c_(self.dstk)).sum(0) + s["E"].sum(0) - s["M"].sum(0))
        emp = np.vstack([s["Fd"][f].sum(0) / (self.L0[f].sum() * xx["ls"]) for f in range(3)])   # employment / supply
        return dict(gdp_exp=gdp_exp, gdp_inc=gdp_inc, gap=float(np.abs(gdp_exp - gdp_inc).max() / self.GDP0),
                    real_gdp=real_gdp, real_income=gdp_exp / s["P"], s=s, v=v, employment=emp)

    def scale(self, y):
        """Size of each variable for relative gaps: |value|, at least 1; foreign assets relative to GDP."""
        sc = np.maximum(np.abs(y), 1.0)
        sc[self.sl["b"]] = self.GDP0
        return sc


def main(m=None, label="step 3b defaults: calib='sam', households='one'"):
    t0 = time.time()
    m = CGE9() if m is None else m
    print(f"[{label}] Calibration: GDP ₱{m.GDP0:,.0f} bn; trend growth g = {m.g * 100:.2f}%; steady-state interest rate "
          f"r = {m.r_ss * 100:.2f}% (delta {m.delta}); beta {m.beta:.4f}; capital in use ₱{m.K0.sum():,.0f} bn "
          f"({m.K0.sum() / m.GDP0:.2f} x GDP); fixed-factor share of capital income: mining {m.ff_share[1]:.3f}, others "
          f"{m.ff_share[0]:.3f}; net non-trade inflows ₱{m.NF0:,.0f} bn")
    res = {}
    y, r = m.steady()
    v = m.split(y[:, None])
    dev = max(np.abs(v["pd"] - 1).max(), np.abs(v["X"][:, 0] / m.X0 - 1).max(), np.abs(v["K"][:, 0] / (m.K0 * (1 + m.g)) - 1).max(),
              np.abs(v["w"] - 1).max(), abs(v["wl"][0] - 1), abs(v["C"][0] / m.C0 - 1),
              np.abs(v["wff"] - 1).max() if m.nff else 0.0, abs(v["mpsadj"][0]) if m.households == "groups" else 0.0)
    res["a"] = dev < 1e-8
    print(f"(a) the steady state at 2023 values reproduces the SAM (prices 1, outputs, capital, consumption): max gap {dev:.1e} "
          f"-> {'PASS' if res['a'] else 'FAIL'}  [{time.time() - t0:.1f} s]")
    ss = y
    T = 200                    # 200 years: the first 40 are identical to a 300-year horizon (test g)

    def gap(a, b):
        sc = m.scale(b if b.ndim == 1 else b[:, 0])
        gg = np.abs(a - (b if a.ndim == b.ndim else b[:, None])) / (sc if a.ndim == 1 else sc[:, None])
        return float(gg.max())

    X = m.path(T)
    Y, y0, yT, info = m.run(X, y_start=ss)
    dev = gap(Y, ss[:, None])
    res["b"] = dev < 1e-9
    print(f"(b) no shock from the 2023 steady state: max deviation {dev:.1e} ({info['iterations']} Newton steps; "
          f"{m.n_y * T:,} unknowns) -> {'PASS' if res['b'] else 'FAIL'}  [{time.time() - t0:.1f} s]")

    X = m.path(300, A=lambda r: r.__setitem__(slice(None), 1.05))
    Y, y0, yT, info = m.run(X, y_start=ss)
    s1 = m.steady(X[:, -1])[0]
    g20, g50, g100, g250 = (gap(Y[:, t], s1) for t in (19, 49, 99, 249))
    acc = m.accounts(Y, y0, X)
    res["c"] = g250 < 5e-3 and g250 < g100 < g50 < g20
    print(f"(c) permanent +5% productivity, all activities (300-year horizon): largest gap to the separately solved new steady "
          f"state after 20 / 50 / 100 / 250 years {g20 * 100:.2f}% / {g50 * 100:.2f}% / {g100 * 100:.2f}% / {g250 * 100:.3f}%; "
          f"real GDP year 1 {(acc['real_gdp'][0] / m.GDP0 - 1) * 100:+.2f}%, year 50 {(acc['real_gdp'][49] / m.GDP0 - 1) * 100:+.2f}%, "
          f"new steady state {(m.accounts(np.repeat(s1[:, None], 2, 1), s1, np.repeat(X[:, -1:], 3, 1))['real_gdp'][0] / m.GDP0 - 1) * 100:+.2f}%; "
          f"{info['iterations']} Newton steps, Jacobian nonzeros {info['nnz']:,} -> {'PASS' if res['c'] else 'FAIL'}  "
          f"[{time.time() - t0:.1f} s]")
    res["d"] = acc["gap"] < 1e-8
    print(f"(d) GDP by expenditure = GDP by income in every year (not imposed): max gap {acc['gap']:.1e} of GDP "
          f"-> {'PASS' if res['d'] else 'FAIL'}")
    Yc = Y[:, :T].copy()

    ic = SECT.index("chem")
    X = m.path(T, pwm=lambda r: r.__setitem__((ic, slice(0, 2)), 1.2))
    Y, y0, yT, info = m.run(X, y_start=ss)
    acc = m.accounts(Y, y0, X)
    v = m.split(Y)
    ca = np.diff(np.concatenate([[0.0], v["b"]]))
    res["e"] = bool(ca[0] < 0 and v["b"][1] < 0 and abs(v["b"][79]) < 0.2 * abs(v["b"].min()) and acc["gap"] < 1e-8)
    print(f"(e) world price of chemical and petroleum imports +20% in years 1-2: real GDP {(acc['real_gdp'][0] / m.GDP0 - 1) * 100:+.2f}% "
          f"/ {(acc['real_gdp'][1] / m.GDP0 - 1) * 100:+.2f}% / {(acc['real_gdp'][2] / m.GDP0 - 1) * 100:+.2f}% (years 1-3); "
          f"real income (GDP / consumer prices) {(acc['real_income'][0] / m.GDP0 - 1) * 100:+.2f}%; "
          f"consumption {(v['C'][0] / m.C0 - 1) * 100:+.2f}% / {(v['C'][1] / m.C0 - 1) * 100:+.2f}% / {(v['C'][2] / m.C0 - 1) * 100:+.2f}%; "
          f"consumer prices {(acc['s']['P'][0] - 1) * 100:+.2f}%; foreign borrowing years 1-2 ₱{-ca[0]:,.0f} bn, ₱{-ca[1]:,.0f} bn; "
          f"foreign assets year 80 ₱{v['b'][79]:,.1f} bn -> {'PASS' if res['e'] else 'FAIL'} (borrow during the episode, then repay)")

    X = m.path(T, g=lambda r: r.__setitem__((0, slice(3, None)), 1.1))
    Y, y0, yT, info = m.run(X, y_start=ss)
    v = m.split(Y)
    res["f"] = abs(v["C"][0] / m.C0 - 1) > 1e-3
    print(f"(f) government spending +10% from year 4, announced in year 1: consumption years 1-4 "
          f"{', '.join(f'{(c / m.C0 - 1) * 100:+.2f}%' for c in v['C'][:4])} (households cut spending before the tax-financed "
          f"rise: Ricardian) -> {'PASS' if res['f'] else 'FAIL'}")

    X2 = m.path(T, A=lambda r: r.__setitem__(slice(None), 1.05))
    Y2, *_ = m.run(X2, y_start=ss)
    dh = gap(Y2[:, :40], Yc[:, :40])
    res["g"] = dh < 1e-6
    print(f"(g) horizon {T} instead of 300 years (permanent +5% productivity): years 1-40 differ by at most {dh * 100:.6f}% "
          f"-> {'PASS' if res['g'] else 'FAIL'}  [{time.time() - t0:.1f} s]")
    print(f"\n{sum(res.values())} of {len(res)} tests pass")
    return m, res


if __name__ == "__main__":
    main()
