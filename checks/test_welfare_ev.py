"""Check EV1 (0.4.3, 21 Nov 2026): the equivalent variation (EV) by household
group, infinity_gem/welfare.py, an OPT-IN measure computed after the solve (design note a design note (not included)).

Models: '0.3 recommended' on Infinity GEM's own SAM v1.0 (rice=True: LES demand, the static model behind every current setting) and the same
model with Cobb-Douglas demand (les=None). Shock sizes: the MEASURED 2026 oil shock (preshock/oil_shock_size.py, central window
"conflict period": crude and imported fuel products at their measured changes, as in scenarios/oil_2026_measured.py), and TEST
VALUES, labelled as such, where a test needs a transfer, a small or a scaled shock (they are not forecasts).

Tests (each prints [PASS] or [FAIL]; exit 0 only if all pass):
  T1 reference: the EV of the reference run against itself is 0 (< 1e-9 ₱ bn) and against a zero-shock re-solve < 1e-6, in every
     group, for LES and Cobb-Douglas; the demand guard's gaps are round-off (< 1e-10) on both runs; the guard refuses a
     solution whose quantities are not the model's demands (QH of one group raised by 1%). (Bar set at 1e-10 after the first
     run, 21 Nov 2026, 00:31 AM, gave 3.7e-12 against a first bar of 1e-12: SAM v1.0's Cobb-Douglas budget shares sum to 1
     within 5.6e-13, the SAM's column balance, and Cobb-Douglas utility scales with spending to that power, so the utility gap
     is 5.6e-13 x ln E, about 3.7e-12; LES gaps are 3e-15.)
  T2 closed form = brute force: in every group, e(p_R, u_S), the spending that buys the scenario's utility at reference prices,
     found (a) by a search over spending with the engine's own demand equation and the direct utility of the scenario's
     quantities (Brent's method) and (b) by minimising p_R.q over bundles with that utility (SLSQP: no closed form used),
     equals the closed form within 1e-7 of reference spending (LES and Cobb-Douglas; measured oil shock, short run).
  T3 sign and size: (a) revealed preference, exact for any shock size: EV_h <= p_R.(q_S - q_R) (the real consumption change at
     reference prices) and CV_h >= dE_h - q_R.dp, in every group, short and long run (measured oil shock); total EV < 0 in
     both (a rise in import prices makes the country poorer); (b) a ₱10 bn transfer to rural Q1 (TEST VALUE; savings
     closure): its EV is positive, within 5% of its change in consumption spending and below ₱10 bn; every other group's
     |EV| is below 5% of the transfer.
  T4 second order: for a 10% and a 5% rise in the world price of imported fuel products (TEST VALUES), the gap between the EV
     and its first-order term dE - q_R.dp (Shephard's lemma) shrinks by a factor of 3.5 to 4.5, in every group.
  T5 aggregation: the total row equals the sum of the ten groups in every peso column (1e-9 ₱ bn); its ev_pct = total EV /
     total reference spending x 100; spending_change + price_effect = ev in every row (1e-9).
  T6 Hosoe cross-check: on Hosoe, Gasawa and Hashimoto's standard model (validation/hosoe/, check V5; tariffs abolished), the
     Cobb-Douglas branch gives the EV of pycge's own solution (Hosoe's List 8.2 formula on pycge's quantities; pycge is a
     human-written port of stdcge.gms) within 1e-9.
  T7 dynamic, per year: on the '0.3 recommended' dynamic model (hybrid, rice=True), ev_path of a zero-shock scenario is 0 in
     every year and group (< 1e-6 ₱ bn); a 10% construction-investment cut in 2026 (TEST VALUE) gives a row for every year
     and group, a total EV below 0 in 2026, and total = sum of groups in every year (1e-9).
  T8 opt-in: in a fresh process, importing the engine, the dynamic model, the settings and the microsimulation does not import
     infinity_gem.welfare, and no infinity_gem module other than welfare.py names it.

Run:  py -I -X utf8 checks/test_welfare_ev.py
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import os
import subprocess
import sys
import warnings
from pathlib import Path

os.environ["INFINITY_GEM_FIES_BASE"] = "fies2023"   # as the suite pins it (this test uses no poverty figure; the pin keeps runs alike)

import numpy as np                                                   # noqa: E402
from scipy.optimize import brentq, minimize                         # noqa: E402

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "preshock"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from infinity_gem import welfare as W                                    # noqa: E402
from infinity_gem.cge import CGE                                         # noqa: E402
from infinity_gem.oil import cge_oil_shock                               # noqa: E402
from infinity_gem.settings import cge_kwargs, dynamic_kwargs, short_run_closure   # noqa: E402
from oil_shock_size import shock_sizes                               # noqa: E402

CENTRAL = "conflict period (Mar 2026 to latest)"
RESULTS = []


def report(name, ok, detail):
    RESULTS.append(bool(ok))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")


def model(les=True, **closure):
    kw = cge_kwargs("0.3 recommended", rice=True)
    path = kw.pop("path")
    if not les:
        kw["les"] = None
    return CGE.from_sam(path, **kw, **closure)


def oil_spec(m):
    z = shock_sizes().loc[CENTRAL]
    spec = cge_oil_shock(m, float(z["crude (Dubai)"]) / 100)
    spec["pwm_scale"]["cpetr"] = 1 + float(z["fuel products, weighted"]) / 100
    return spec


def les_demand(m, p, E):
    """The engine's household demand (cge.py household block): q = gamma + b (E - p.gamma) / p (Cobb-Douglas: gamma = 0)."""
    gamma, b, _ = W.demand_params(m)
    return gamma + b * (E - p @ gamma)[None, :] / p[:, None]


def first_order(b, s):
    """dE - q_R.dp by group (Shephard's lemma), and the real consumption change at reference prices p_R.(q_S - q_R)."""
    dE = np.asarray(s["EH"]) - np.asarray(b["EH"])
    return dE - (np.asarray(s["PQ"]) - np.asarray(b["PQ"])) @ np.asarray(b["QH"]), np.asarray(b["PQ"]) @ (np.asarray(s["QH"]) - np.asarray(b["QH"]))


SR = short_run_closure("0.3 recommended")
M_LES_SR, M_CD_SR, M_LES_LR = model(True, **SR), model(False, **SR), model(True)
SOLS = {}
for key, m in (("les_sr", M_LES_SR), ("cd_sr", M_CD_SR), ("les_lr", M_LES_LR)):
    b = m.solve({})
    s = m.solve(oil_spec(m))
    assert b.ok and s.ok, f"{key}: solve failed"
    SOLS[key] = (m, b, s)


def t1():
    worst_self, worst_zero, worst_gap = 0.0, 0.0, 0.0
    for key in ("les_sr", "cd_sr"):
        m, b, _ = SOLS[key]
        z = m.solve({})
        worst_self = max(worst_self, float(W.equivalent_variation(m, b, b)["ev"].abs().max()))
        worst_zero = max(worst_zero, float(W.equivalent_variation(m, b, z)["ev"].abs().max()))
        worst_gap = max(worst_gap, *W.demand_check(m, b).values(), *W.demand_check(m, z).values())
    m, b, s = SOLS["les_sr"]
    bad = dict(s.v)
    bad["QH"] = np.asarray(s["QH"], float).copy()
    bad["QH"][:, 0] *= 1.01
    try:
        W.equivalent_variation(m, b, type(s)(s.x, bad, s.ok, s.message, s.residual_max))
        refused = False
    except ValueError:
        refused = True
    ok = worst_self < 1e-9 and worst_zero < 1e-6 and worst_gap < 1e-10 and refused
    report("T1 reference", ok, f"EV vs itself {worst_self:.1e}, vs a zero-shock re-solve {worst_zero:.1e} ₱ bn; demand guard gaps "
                               f"{worst_gap:.1e}; perturbed quantities refused: {refused}")


def t2():
    worst_a, worst_b, n = 0.0, 0.0, 0
    for key in ("les_sr", "cd_sr"):
        m, b, s = SOLS[key]
        gamma, bb, _ = W.demand_params(m)
        pR = np.asarray(b["PQ"], float)
        ER = np.asarray(b["EH"], float)
        uS = W.direct_utility(m, np.asarray(s["QH"], float))            # from the scenario's own quantities
        ev = W.equivalent_variation(m, b, s)["ev"].to_numpy()[:-1]
        for h in range(len(m.H)):
            def gap(E, h=h):
                Ev = np.full(len(m.H), ER[h])
                Ev[h] = E
                return np.log(W.direct_utility(m, les_demand(m, pR, Ev))[h]) - np.log(uS[h])
            lo = float(pR @ gamma[:, h]) + 1e-9 * ER[h]
            E_a = brentq(gap, lo, 5 * ER[h], xtol=1e-12 * ER[h], rtol=1e-15, maxiter=500)
            worst_a = max(worst_a, abs((E_a - ER[h]) - ev[h]) / ER[h])
            pos = bb[:, h] > 0                                             # goods with b = 0 stay at their subsistence level
            g_, b_, p_ = gamma[pos, h], bb[pos, h], pR[pos]
            y0 = np.log(np.asarray(s["QH"], float)[pos, h] - g_)
            scale = ER[h]
            res = minimize(lambda y: float(p_ @ np.exp(y)) / scale, y0, jac=lambda y: p_ * np.exp(y) / scale, method="SLSQP",
                           constraints=[{"type": "eq", "fun": lambda y: float(b_ @ y) - np.log(uS[h]),
                                         "jac": lambda y: b_}], options={"ftol": 1e-15, "maxiter": 1000})
            E_b = float(p_ @ g_) + float(pR[~pos] @ gamma[~pos, h]) + float(p_ @ np.exp(res.x))
            worst_b = max(worst_b, abs((E_b - ER[h]) - ev[h]) / ER[h])
            n += 1
    ok = worst_a < 1e-7 and worst_b < 1e-7
    report("T2 closed form = brute force", ok, f"{n} group cases (LES and Cobb-Douglas, measured oil shock, short run): search over "
                                               f"spending {worst_a:.1e}, SLSQP minimisation {worst_b:.1e} of reference spending")


def t3():
    worst_ev, worst_cv, totals = -np.inf, -np.inf, []
    for key in ("les_sr", "les_lr"):
        m, b, s = SOLS[key]
        t = W.equivalent_variation(m, b, s)
        ev = t["ev"].to_numpy()[:-1]
        lin, drc = first_order(b, s)
        pR, pS = np.asarray(b["PQ"], float), np.asarray(s["PQ"], float)
        cv = np.asarray(s["EH"]) - W.expenditure(m, pS, W.indirect_utility(m, pR, np.asarray(b["EH"])))
        scale = np.asarray(b["EH"], float)
        worst_ev = max(worst_ev, float(np.max((ev - drc) / scale)))          # must be <= 0
        worst_cv = max(worst_cv, float(np.max((lin - cv) / scale)))          # must be <= 0
        totals.append(float(t.loc[W.TOTAL, "ev"]))
    m = model(True, closure="savings")
    b = m.solve({})
    s = m.solve({"trg_h_add": {"hhd-r1": 10.0}})                             # TEST VALUE: ₱10 bn to rural Q1
    t = W.equivalent_variation(m, b, s)
    r1 = t.loc["hhd-r1"]
    others = float(t.drop(index=["hhd-r1", W.TOTAL])["ev"].abs().max())
    ratio = float(r1["ev"] / r1["spending_change"])
    ok = (worst_ev <= 1e-12 and worst_cv <= 1e-12 and max(totals) < 0 and b.ok and s.ok and 0 < r1["ev"] < 10.0
          and abs(ratio - 1) < 0.05 and others < 0.5)
    report("T3 sign and size", ok, f"measured oil shock: max (EV - real consumption change) {worst_ev:.1e}, max (first order - CV) "
                                   f"{worst_cv:.1e} of spending (both must be <= 0); total EV short run ₱{totals[0]:,.1f} bn, long run "
                                   f"₱{totals[1]:,.1f} bn; ₱10 bn to rural Q1 (test value): EV ₱{r1['ev']:.3f} bn = {ratio:.4f} x its "
                                   f"spending change; largest other group |EV| ₱{others:.3f} bn")


def t4():
    m, b, _ = SOLS["les_sr"]
    gaps = {}
    for x in (0.10, 0.05):                                                  # TEST VALUES: world price of imported fuel products
        s = m.solve({"pwm_scale": {"cpetr": 1 + x}})
        assert s.ok
        lin, _ = first_order(b, s)
        gaps[x] = W.equivalent_variation(m, b, s)["ev"].to_numpy()[:-1] - lin
    r = gaps[0.10] / gaps[0.05]
    ok = bool(np.all((r > 3.5) & (r < 4.5)))
    report("T4 second order", ok, f"gap EV - (dE - q_R.dp) at +10% / at +5% (test values): {r.min():.3f} to {r.max():.3f} over the "
                                  f"ten groups (4 = exactly second order); gap at +10%: {np.abs(gaps[0.10]).max():.3f} ₱ bn at most")


def t5():
    worst_sum, worst_pct, worst_split = 0.0, 0.0, 0.0
    for key in SOLS:
        m, b, s = SOLS[key]
        t = W.equivalent_variation(m, b, s)
        g, tot = t.drop(index=W.TOTAL), t.loc[W.TOTAL]
        for c in ("consumption_ref", "consumption_sim", "spending_change", "price_effect", "ev"):
            worst_sum = max(worst_sum, abs(float(g[c].sum() - tot[c])))
        worst_pct = max(worst_pct, abs(float(tot["ev_pct"] - g["ev"].sum() / g["consumption_ref"].sum() * 100)))
        worst_split = max(worst_split, float((t["spending_change"] + t["price_effect"] - t["ev"]).abs().max()))
    ok = worst_sum < 1e-9 and worst_pct < 1e-12 and worst_split < 1e-9
    report("T5 aggregation", ok, f"total - sum of groups {worst_sum:.1e} ₱ bn; total ev_pct {worst_pct:.1e} pp; spending change + "
                                 f"price effect - EV {worst_split:.1e} ₱ bn (3 cases)")


def t6():
    spec = importlib.util.spec_from_file_location("compare_hosoe", str(ROOT / "validation" / "hosoe" / "compare_hosoe.py"))
    mod = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):
        spec.loader.exec_module(mod)
    m, b, s, _ = mod.rows["CD exact"]
    t = W.equivalent_variation(m, b, s)
    gap = abs(float(t.loc[W.TOTAL, "ev"]) - float(mod.ev_p))
    ok = gap < 1e-9 and t.attrs["form"] == "Cobb-Douglas"
    report("T6 Hosoe cross-check", ok, f"tariffs abolished: Infinity GEM welfare.py EV {float(t.loc[W.TOTAL, 'ev']):.9f}, pycge (Hosoe "
                                       f"List 8.2 on pycge's quantities) {float(mod.ev_p):.9f}; gap {gap:.1e}")


def t7():
    from infinity_gem.dynamic import DynamicCGE
    d = DynamicCGE(**dynamic_kwargs("0.3 recommended", rice=True))
    base = d.baseline()
    ez = W.ev_path(d, d.scenario({2026: {}}))
    zero = float(ez["ev"].abs().max())
    e = W.ev_path(d, d.scenario({2026: {"qinv_scale": {"ccons": 0.9}}}))     # TEST VALUE: a 10% construction-investment cut
    years = sorted(base.solutions)
    full = sorted(set(e.index.get_level_values("year"))) == years and len(e) == len(years) * (len(d.m.H) + 1)
    worst = 0.0
    for t in years:
        f = e.loc[t]
        worst = max(worst, abs(float(f.drop(index=W.TOTAL)["ev"].sum() - f.loc[W.TOTAL, "ev"])))
    ev26 = float(e.loc[(2026, W.TOTAL), "ev"])
    pct26 = float(e.loc[(2026, W.TOTAL), "ev_pct"])
    ok = zero < 1e-6 and full and ev26 < 0 and worst < 1e-9
    report("T7 dynamic, per year", ok, f"zero shock max |EV| {zero:.1e} ₱ bn over {len(years)} years x {len(d.m.H)} groups; 10% "
                                       f"construction cut in 2026 (test value): total EV 2026 ₱{ev26:,.1f} bn ({pct26:+.3f}% of "
                                       f"consumption); total - sum of groups {worst:.1e}")


def t8():
    code = ("import sys; sys.path.insert(0, sys.argv[1]); import infinity_gem.cge, infinity_gem.dynamic, infinity_gem.settings, "
            "infinity_gem.microsim, infinity_gem.microlink; print('infinity_gem.welfare' in sys.modules)")
    p = subprocess.run([sys.executable, "-I", "-c", code, str(ROOT)], capture_output=True, text=True, timeout=600)
    loaded = p.stdout.strip()
    named = [f.name for f in (ROOT / "infinity_gem").glob("*.py")
             if f.name != "welfare.py" and any(k in f.read_text(encoding="utf-8", errors="replace")
                                               for k in ("from .welfare", "import welfare", "infinity_gem.welfare"))]
    ok = loaded == "False" and not named
    report("T8 opt-in", ok, f"welfare imported by the engine, dynamic model, settings or microsimulation: {loaded or p.stderr[-120:]}; "
                            f"other modules naming it: {named or 'none'}")


if __name__ == "__main__":
    for fn in (t1, t2, t3, t4, t5, t6, t7, t8):
        try:
            fn()
        except Exception as exc:                       # a crash is a failure
            report(fn.__name__.upper(), False, f"ERROR: {exc!r}")
    print(f"{sum(RESULTS)} of {len(RESULTS)} pass")
    sys.exit(0 if all(RESULTS) and len(RESULTS) == 8 else 1)
