"""Check MC1 (Infinity GEM 0.4.1, 13 Nov 2026): a ceiling on the gap rule's markup pass-through removes its boom branch.

The 0.4 miss (review notes of 12-13 Nov 2026, not included): in the static
short-run model under markup pricing (mk_pass 0, world oil +30%) with the P6 gap rule at a slope s near the fitted 0.48, a solve from
another start finds a second, boom solution (output gap about +6%) beside the slump one. The mechanism: in a boom the rule's
pass-through lam_e = mk_pass + s x gap rises far above 1 (at +6%, 3: margins rise three times as fast as cost), the margin income feeds
the 46% of household income distributed from profits, and demand validates the boom. The option: cge.py shock key 'mk_ceiling' = c
(DynamicCGE sr_markup_ceiling): lam_e kept at or below c by the floor's smoothed max. c = 1 is the definition's upper bound, the
proportional markup (Taylor 1983; mk_pass 1): margins may rise at most in proportion to cost. It binds only above the proportional markup,
so it cannot move a slump (lam_e < 0 there).
Static case (as MF1): Infinity GEM's own SAM (v1.0, rice-split), "0.3 recommended" short-run closure, land fixed, markup pricing, mk_pass 0,
world oil +30%, floor -1, s = 0.5 and s = the 0.4 setting's 0.4818.
  T1  the flag reproduced without a ceiling: the plain solve gives a slump, the homogeneity solve (every nominal anchor x 1.1) a boom
      (real GDP more than 3% apart);
  T2  with the ceiling 1, the homogeneity solve gives the slump: homogeneity of degree 1 holds (quantities 1e-8, prices / 1.1 1e-8);
  T3  the ceiling does not move the slump: identical arrays (0.0) with and without it (it does not bind: lam_e < 0 < 1);
  T4  from starts around the boom (the boom solution itself; every price x 0.9, 1.1, 1.3), the ceiling model returns to the slump
      (real GDP within 1e-6) or fails to solve; it never finds a second solution;
  T5  guards: 'mk_ceiling' NaN, True, without 'mk_gap', at or below 'mk_floor', with flexible pricing; DynamicCGE sr_markup_ceiling
      'x', without sr_markup_gap, at or below sr_markup_floor: all refused;
  T6  dynamic (MF1's small case, 2026 short run, s 0.1): sr_markup_ceiling 1 = none (every array, every year, to 1e-8: the solver's
      tolerance, the second path warm-starting from the first), and the year's spec carries the key.
Run: py -I -X utf8 checks/test_markup_ceiling.py   (prints one line per test; exit code 1 on failure; the suite runs it as MC1)
"""
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np                                                              # noqa: E402

from infinity_gem import stickiness as STK                                         # noqa: E402
from infinity_gem.cge import CGE                                                    # noqa: E402
from infinity_gem.dynamic import DynamicCGE                                         # noqa: E402
from infinity_gem.oil import cge_oil_shock                                          # noqa: E402
from infinity_gem.settings import OPTION_C_04, cge_kwargs, dynamic_kwargs, short_run_closure     # noqa: E402

KEYS = ("QA", "QH", "QE", "QM", "PQ", "PDS", "EH", "WF", "CPI", "EXR")
RES = []


def rd(a_, b_):
    a_, b_ = np.asarray(a_, float), np.asarray(b_, float)
    return float(np.max(np.abs(a_ - b_) / np.maximum(np.abs(b_), 1e-9)))


def same(x, y, keys=KEYS):
    return max(rd(x[k], y[k]) for k in keys)


def record(name, ok, msg):
    RES.append(bool(ok))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {msg}", flush=True)


def gap(m, s):
    return 100 * (m.gdp(s)["real"] / m.real_gdp0 - 1)


def scaled(m, spec):
    """The homogeneity test's spec: every nominal anchor x 1.1 (MF1 T5's)."""
    return {**spec, "exr": 1.1, "wbar": {x: 1.1 for x in m.unemployed}, "pa_anchor": {a: 1.1 * (1 - m.ta[i]) for i, a in enumerate(m.A)}}


def static():
    kw = cge_kwargs("0.3 recommended", rice=True)
    path = kw.pop("path")
    base = dict(**short_run_closure("0.3 recommended"), land="fixed", **kw)
    m = CGE.from_sam(path, **base, pricing="markup")
    m.solve()
    out = {}
    for s in (0.5, float(OPTION_C_04["sr_markup_gap"])):
        oil = {**cge_oil_shock(m, 0.30), "mk_pass": 0.0, "mk_gap": s, "mk_floor": -1.0}
        a = m.solve(oil)
        b = m.solve(scaled(m, oil))
        ac = m.solve({**oil, "mk_ceiling": 1.0})
        bc = m.solve(scaled(m, {**oil, "mk_ceiling": 1.0}))
        out[s] = (oil, a, b, ac, bc)
    s5 = 0.5
    oil, a, b, ac, bc = out[s5]
    flag = a.ok and b.ok and abs(gap(m, b) - gap(m, a)) > 3.0
    record("T1 the boom branch without a ceiling (s 0.5)", flag,
           f"plain solve: gap {gap(m, a):+.2f}%; homogeneity solve: gap {gap(m, b):+.2f}% (ok {a.ok}, {b.ok})"
           + "; s 0.4818: " + ", ".join(f"{gap(m, x):+.2f}%" if x.ok else "no solution" for x in out[float(OPTION_C_04['sr_markup_gap'])][1:3]))
    hq, hp, msg = [], [], []
    for s, (oil_, a_, b_, ac_, bc_) in out.items():
        if not (ac_.ok and bc_.ok):
            hq.append(np.inf)
            msg.append(f"s {s:g}: not solved ({ac_.ok}, {bc_.ok})")
            continue
        hq.append(max(rd(bc_[k], ac_[k]) for k in ("QA", "QE", "QM", "QH")))
        hp.append(max(rd(np.asarray(bc_[k], float)[i_] / 1.1, np.asarray(ac_[k], float)[i_]) for k, i_ in (("PQ", m.iQ), ("PDS", m.iD))))
        msg.append(f"s {s:g}: gaps {gap(m, ac_):+.3f}% / {gap(m, bc_):+.3f}%, q {hq[-1]:.1e}")
    record("T2 with the ceiling 1, one solution (homogeneity holds)", max(hq) < 1e-8 and (max(hp) if hp else 1) < 1e-8, "; ".join(msg))
    d3 = max(same(out[s][3], out[s][1]) for s in out)
    record("T3 the ceiling does not move the slump", d3 == 0.0, f"largest difference with and without the ceiling {d3:.1e}")
    starts = {"the boom solution": b.x}
    x0 = m.x0()
    for f in (0.9, 1.1, 1.3):
        starts[f"start x {f:g}"] = x0 * f
    bad, notes = 0, []
    for lab, xs in starts.items():
        try:
            r = m.solve({**oil, "mk_ceiling": 1.0}, x_start=xs)
        except Exception as e:                                          # a start that cannot be solved is not a second solution
            notes.append(f"{lab}: error {type(e).__name__}")
            continue
        if not r.ok:
            notes.append(f"{lab}: not solved")
            continue
        dev = abs(gap(m, r) - gap(m, ac))
        bad += dev > 1e-6
        notes.append(f"{lab}: gap {gap(m, r):+.4f}%")
    record("T4 no second solution with the ceiling", bad == 0, "; ".join(notes))
    refused = 0
    for spec in ({**oil, "mk_ceiling": float("nan")}, {**oil, "mk_ceiling": True}, {**cge_oil_shock(m, 0.30), "mk_ceiling": 1.0},
                 {**oil, "mk_ceiling": -1.0}, {**oil, "mk_ceiling": -2.0}):
        try:
            m.solve(spec)
        except ValueError:
            refused += 1
    try:
        CGE.from_sam(path, **base).solve({"mk_ceiling": 1.0})
    except ValueError:
        refused += 1
    return refused


def dynamic(refused):
    kwd = dynamic_kwargs("0.3 recommended", rice=True, land="fixed")
    kwd.update(wage_curve=10.5, hoarding=0.85, short_run_years=(2026,), sr_pricing="markup", sr_markup_pass=0.0)
    for bad in ({"sr_markup_ceiling": "x", "sr_markup_gap": 0.1}, {"sr_markup_ceiling": 1.0},
                {"sr_markup_ceiling": -1.0, "sr_markup_floor": -1.0, "sr_markup_gap": 0.1}):
        try:
            DynamicCGE(**{**kwd, **bad})
        except (ValueError, TypeError):
            refused += 1
    record("T5 guards", refused == 9, f"{refused} of 9 bad settings refused")
    d = DynamicCGE(**kwd)
    d.a["sr_stickiness"] = STK.sectoral([a for i, a in enumerate(d.ms.A) if d.ms.isMK[i]])
    d.baseline()
    t = 2026
    shock = {t: {**cge_oil_shock(d.m, 0.30), "qinv_scale": {"ccons": 0.85}}}
    keys = ("QA", "QH", "QE", "QM", "QINV", "EMP", "PQ", "WF", "EH", "DY", "YH")
    d.a["sr_markup_gap"] = 0.1
    p0 = d.scenario(shock)
    d.a["sr_markup_ceiling"] = 1.0
    p1 = d.scenario(shock)
    diff = max(rd(p0.solutions[y][k], p1.solutions[y][k]) for y in d.years for k in keys)
    spec = (p1.solutions[t].shocks or {}).get("mk_ceiling")
    # 1e-8, not 0.0: the second path starts its solves from the first one's solutions (the engine's warm starts), so the two agree to
    # the solver's tolerance; the ceiling's own term is exactly 0.0 below c (T3 shows the static arrays are identical)
    record("T6 dynamic: the ceiling 1 does not move a slump; the year carries it", diff < 1e-8 and spec == 1.0,
           f"largest difference {diff:.1e}; the short-run spec carries mk_ceiling {spec}")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    t0 = time.time()
    dynamic(static())
    print(f"MC1: {'ALL PASS' if all(RES) else 'FAIL'} ({sum(RES)} of {len(RES)}); {time.time() - t0:.0f} s")
    sys.exit(0 if all(RES) and len(RES) == 6 else 1)
