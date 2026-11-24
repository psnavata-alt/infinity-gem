"""Equivalent variation (EV) by household group: a money-metric welfare measure, computed AFTER the solve.

0.4.3, 21 Nov 2026. OPT-IN: nothing in the engine, the dynamic model or the
settings calls this module, so no existing result changes (R0 and the setting checks are untouched); it reads two solutions
and returns a table. Check EV1 (checks/test_welfare_ev.py). Design note: a design note (not included).

Use
    from infinity_gem.settings import cge_model
    from infinity_gem.welfare import equivalent_variation, ev_path
    m = cge_model("0.3 recommended", rice=True); b = m.solve(); s = m.solve(spec)
    equivalent_variation(m, b, s)       # one row per SAM household group, plus "All households"
    d = DynamicCGE(**dynamic_kwargs(...)); d.baseline(); sim = d.scenario(shocks)
    ev_path(d, sim)                     # the same, year by year, against the baseline (or reference=another path)

What it measures. EV_h is the change in household group h's consumption spending that, at the REFERENCE run's prices, would
change the group's utility exactly as the scenario does:
    EV_h = e_h(p_R, u_h,S) - e_h(p_R, u_h,R) = e_h(p_R, v_h(p_S, E_h,S)) - E_h,R
e = the expenditure function, v = the indirect utility function, p = PQ (the price buyers pay for each commodity, with sales
taxes and trade margins), E = EH (the group's consumption spending). EV > 0: the group is better off. Units: the SAM's
(billions of pesos) at the reference run's prices. This is the definition DR-GEM uses (Resources for the Future, DR-GEM v1.0,
Model/DR-GEM_welfare.gms lines 190-212: the wealth at reference-case prices that gives the policy case's utility, less the
reference wealth, line 205; ideas only, the code is CC BY-NC-ND 4.0 and is not copied), simplified for Infinity GEM: one period
at a time (DR-GEM's is a present value under perfect foresight), no leisure in utility (Infinity GEM's households do not choose
hours), saving outside utility (saving follows the closure's rule). Hosoe, Gasawa and Hashimoto (2010), Textbook of Computable
General Equilibrium Modelling, ch. 8 (Fig. 8.1, p. 135; List 8.2, p. 136) compute the same EV for a Cobb-Douglas household;
check EV1 reproduces the EV of their standard model as solved by pycge, a human-written port (validation/hosoe/).

Closed forms (no extra solve). Infinity GEM's LES (cge.py, les=) comes from a Stone-Geary utility U_h = prod_c (q_c - gamma_c)^b_c
with marginal budget shares b summing to 1 (Lofgren, Harris and Robinson 2002, A Standard CGE Model in GAMS, IFPRI MPR 5,
eqs. 33-34, p. 33; Cicowiez and Lofgren 2017, GEM-Core, World Bank PRWP 8272, eq. INS8, p. 44). Its demand
q_c = gamma_c + b_c (E - p.gamma) / p_c (cge.py, household block) gives
    v(p, E) = (E - p.gamma) prod_c (b_c / p_c)^b_c          e(p, u) = p.gamma + u prod_c (p_c / b_c)^b_c
    EV      = p_R.gamma + (E_S - p_S.gamma) prod_c (p_R,c / p_S,c)^b_c - E_R
Cobb-Douglas (the engine without les=) is the case gamma = 0, b = the budget shares beta; with home='separate' own produce,
priced at PX, is one more good per commodity with share beta_h. Split: EV = (E_S - E_R) + [e(p_R, u_S) - e(p_S, u_S)], the
spending change plus the price effect (what the scenario's price change costs, or saves, at the scenario's living standard).

Guard. Before it reports, equivalent_variation checks on both solutions that the model's own quantities QH are this utility's
demands: spending on goods = EH, and the utility of QH = the indirect utility at (PQ, EH), to 1e-6 relative (demand_check). A
model whose household demand is not this LES or Cobb-Douglas (for instance a future demand system) is refused, not mis-measured.

Limits. A representative group, not each FIES family (the spread within a group is not measured: the poverty count does that
through the microsimulation); consumption only (not saving, leisure, public services or job security); one period at a time
(a present value over years needs a sourced discount rate, not chosen here); the EV inherits the calibrated LES's assumptions.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

UNITS = "billions of pesos (the SAM's units) at the reference run's prices"
TOTAL = "All households"
TOL = 1e-6                                   # demand_check tolerance (relative); round-off gives about 1e-14
COLUMNS = ["consumption_ref", "consumption_sim", "spending_change", "price_effect", "ev", "ev_pct"]


def utility_form(model) -> str:
    """'LES (Stone-Geary)' when the model was built with les=, else 'Cobb-Douglas'."""
    return "LES (Stone-Geary)" if getattr(model, "les", None) is not None else "Cobb-Douglas"


def demand_params(model):
    """(gamma, b, separate): subsistence quantities and marginal budget shares (goods x household groups) of the utility behind
    the model's household demand; separate = own produce (home='separate') stacked under the market goods (Cobb-Douglas only:
    the engine refuses les= with home='separate')."""
    les = getattr(model, "les", None)
    sep = getattr(model, "home", "market") == "separate"
    if les is not None:
        if sep:
            raise NotImplementedError("LES with home='separate' is not built in the engine either")
        return np.asarray(les["gamma"], float), np.asarray(les["mb"], float), False
    b = np.asarray(model.beta, float)
    if sep:
        b = np.vstack([b, np.asarray(model.beta_h, float)])
    return np.zeros_like(b), b, sep


def _prices(sol, sep: bool) -> np.ndarray:
    p = np.asarray(sol["PQ"], float)
    if sep:
        p = np.concatenate([p, np.asarray(sol["PX"], float)])
    if not (p > 0).all():
        raise ValueError("a consumer price is zero or negative: the expenditure function is not defined there")
    return p


def _quantities(sol, sep: bool) -> np.ndarray:
    q = np.asarray(sol["QH"], float)
    if sep:
        q = np.vstack([q, np.asarray(sol["QHA"], float)])
    return q


def _log_b(b: np.ndarray) -> np.ndarray:
    return np.where(b > 0, np.log(np.where(b > 0, b, 1.0)), 0.0)


def indirect_utility(model, p, E) -> np.ndarray:
    """v_h(p, E_h) for every group: (E - p.gamma) prod_c (b_c / p_c)^b_c (goods with b_c = 0 drop out of the product)."""
    gamma, b, _ = demand_params(model)
    p, E = np.asarray(p, float), np.asarray(E, float)
    S = E - p @ gamma
    if (S <= 0).any():
        raise ValueError("spending at or below the subsistence cost p.gamma: utility is not defined")
    return np.exp(np.log(S) + (b * (_log_b(b) - np.log(p)[:, None])).sum(axis=0))


def expenditure(model, p, u) -> np.ndarray:
    """e_h(p, u_h) for every group: p.gamma + u prod_c (p_c / b_c)^b_c."""
    gamma, b, _ = demand_params(model)
    p = np.asarray(p, float)
    return p @ gamma + np.asarray(u, float) * np.exp((b * (np.log(p)[:, None] - _log_b(b))).sum(axis=0))


def direct_utility(model, q) -> np.ndarray:
    """U_h(q_h) for every group: prod_c (q_c - gamma_c)^b_c over goods with b_c > 0."""
    gamma, b, _ = demand_params(model)
    z = np.asarray(q, float) - gamma
    pos = b > 0
    if (z[pos] <= 0).any():
        raise ValueError("a quantity at or below its subsistence level: utility is not defined")
    return np.exp(np.where(pos, b * np.log(np.where(pos, z, 1.0)), 0.0).sum(axis=0))


def demand_check(model, sol) -> dict:
    """Largest relative gaps over the groups between (i) spending on goods p.q and EH ('budget') and (ii) the utility of the
    solution's own quantities and the indirect utility at its prices and spending ('utility'). Both are round-off (about
    1e-14) when the model's household demand is the LES or Cobb-Douglas this module assumes."""
    _, _, sep = demand_params(model)
    p, q, E = _prices(sol, sep), _quantities(sol, sep), np.asarray(sol["EH"], float)
    budget = float(np.max(np.abs(p @ q - E) / np.abs(E)))
    utility = float(np.max(np.abs(direct_utility(model, q) / indirect_utility(model, p, E) - 1)))
    return {"budget": budget, "utility": utility}


def equivalent_variation(model, reference, scenario, check: bool = True) -> pd.DataFrame:
    """EV of `scenario` against `reference` (two solutions of `model`), by SAM household group, plus a total row.

    Columns (billions of pesos at the reference run's prices, except ev_pct):
      consumption_ref, consumption_sim   EH in the two runs (current pesos of each run)
      spending_change                    consumption_sim - consumption_ref
      price_effect                       e(p_R, u_S) - e(p_S, u_S): the scenario's price change valued at its living standard
      ev                                 spending_change + price_effect = e(p_R, u_S) - E_R (> 0: better off)
      ev_pct                             ev as % of the reference run's consumption spending
    The total row sums the peso columns; its ev_pct is the total EV over total reference spending. df.attrs holds the utility
    form and the units. check=True refuses solutions whose quantities are not this utility's demands (demand_check)."""
    gamma, b, sep = demand_params(model)
    if check:
        for name, s in (("reference", reference), ("scenario", scenario)):
            g = demand_check(model, s)
            if max(g.values()) > TOL:
                raise ValueError(f"the {name} solution's household quantities are not the demands of the model's "
                                 f"{utility_form(model)} utility (gaps {g}); EV not computed")
    pR, pS = _prices(reference, sep), _prices(scenario, sep)
    ER, ES = np.asarray(reference["EH"], float), np.asarray(scenario["EH"], float)
    SS = ES - pS @ gamma
    if (SS <= 0).any():
        raise ValueError("scenario spending at or below the subsistence cost: utility is not defined")
    e_RS = pR @ gamma + SS * np.exp((b * (np.log(pR) - np.log(pS))[:, None]).sum(axis=0))   # e(p_R, u_S)
    out = pd.DataFrame({"consumption_ref": ER, "consumption_sim": ES, "spending_change": ES - ER,
                        "price_effect": e_RS - ES, "ev": e_RS - ER}, index=list(model.H))
    out["ev_pct"] = out["ev"] / out["consumption_ref"] * 100
    tot = out[COLUMNS[:-1]].sum()
    tot["ev_pct"] = tot["ev"] / tot["consumption_ref"] * 100
    out.loc[TOTAL] = tot
    out.index.name = "group"
    out.attrs.update(form=utility_form(model), units=UNITS)
    return out[COLUMNS]


def ev_path(dyn, scenario, reference=None, check: bool = True) -> pd.DataFrame:
    """Year-by-year EV of a DynamicCGE path against its baseline (or `reference`, another path of the same model), indexed by
    (year, group). Each year is measured at that year's reference prices, with the household demand of dyn.m: every DynamicCGE
    year model (long run, short run, savings-driven) is built from the same SAM and les= argument, and check=True confirms it
    on every year's two solutions (demand_check). No present value is taken (see the module notes)."""
    ref = dyn.base if reference is None else reference
    frames = []
    for t in scenario.solutions:
        if t in ref.solutions:
            f = equivalent_variation(dyn.m, ref.solutions[t], scenario.solutions[t], check=check)
            frames.append(f.assign(year=t).set_index("year", append=True).reorder_levels(["year", "group"]))
    if not frames:
        raise ValueError("the scenario and the reference share no year")
    out = pd.concat(frames)
    out.attrs.update(form=utility_form(dyn.m), units=UNITS + " of each year")
    return out
