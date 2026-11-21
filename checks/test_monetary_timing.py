"""Check MT1 (Infinity GEM 0.4.1, 13 Nov 2026): the BSP rule's opt-in conventions (all absent = as before).

infinity_gem/dynamic.py monetary_scenario(observed=...) and rule keys phi_pi_lead, phi_pi_lag, quarter_weights; DynamicCGE.quarterly_rule;
infinity_gem/monetary.py rule(name, expected=...), bsp_observed_gap(), quarter_weights(). Research for the 0.4 miss "the rule's 2026 response
(+1.45 pp) is above the BSP's actual average (+0.49; +1.25 at year-end)"; scenarios/row83_04_misses_2026.py.
  T1  quarterly_rule with four equal targets equals annual_rule (1e-12), and a hand recursion with unequal targets (1e-12);
  T2  rule("pamph", expected="lead"/"lag") splits 1 + g2 into g2 on this year's gap and 1 on next/last year's; "dsge" refuses them;
  T3  bsp_observed_gap(2026) from the BIS daily file equals the gap computed by hand from the BSP's decisions in that file (4.50 from
      12 Dec 2025; 4.25 on 20 Feb 2026, the counterfactual from then; 4.50 24 Apr, 4.75 19 Jun, 5.00 28 Aug, 5.50 23 Oct; held after
      the last observation): average and end value (1e-9), quarter 1 = 0;
  T4  quarter_weights: mean 1 (1e-12), the quarter means of a known profile, and refusals (11 months; a mean of zero);
  T5  on a small dynamic case (MP1's: SAM v1.0 rice-split, "0.3 recommended", short run 2026, a 10% construction cut; theta 2):
      explicit phi_pi_lead = phi_pi_lag = 0 and quarter weights (1, 1, 1, 1) give the path of the rule without them (rate 1e-8,
      GDP 1e-8: the solver's tolerance, warm starts); an observed 2026 gap is applied exactly and 2027's rate is annual_rule from the observed end value at the converged
      gaps (1e-9); the "lead" fixed point satisfies its own rule at the converged gaps (within the iteration's tolerance).
Run: py -I -X utf8 checks/test_monetary_timing.py   (a few minutes; the suite runs it as check MT1)
"""
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import numpy as np                                               # noqa: E402
import pandas as pd                                              # noqa: E402

from infinity_gem import monetary as MO                              # noqa: E402
from infinity_gem.dynamic import DynamicCGE                          # noqa: E402


def report(res, name, ok, msg):
    res.append(bool(ok))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {msg}", flush=True)


def t1(res):
    r = {"rho": 0.7207904940378569, "phi_pi": 2.05, "phi_x": 0.1}
    a = DynamicCGE.annual_rule(r, 2.7, 0.4)
    q = DynamicCGE.quarterly_rule(r, [2.7] * 4, 0.4)
    tg, i, path = [0.3, 1.2, 4.0, -0.5], 0.4, []
    for x in tg:
        i = r["rho"] * i + (1 - r["rho"]) * x
        path.append(i)
    q2 = DynamicCGE.quarterly_rule(r, tg, 0.4)
    e = max(abs(a[0] - q[0]), abs(a[1] - q[1]), abs(q2[0] - np.mean(path)), abs(q2[1] - path[-1]))
    report(res, "T1 quarterly_rule = annual_rule; hand recursion", e < 1e-12, f"largest difference {e:.1e}")


def t2(res):
    c, ld, lg = MO.rule("pamph"), MO.rule("pamph", "lead"), MO.rule("pamph", "lag")
    ok = (abs(ld["phi_pi"] + ld["phi_pi_lead"] - c["phi_pi"]) < 1e-12 and abs(lg["phi_pi"] + lg["phi_pi_lag"] - c["phi_pi"]) < 1e-12
          and ld["phi_pi_lead"] == 1.0 and lg["phi_pi_lag"] == 1.0 and "phi_pi_lead" not in c and ld["rho"] == c["rho"])
    try:
        MO.rule("dsge", "lead")
        refused = False
    except (ValueError, FileNotFoundError) as e:
        refused = "expected" in str(e) or isinstance(e, FileNotFoundError)
    report(res, "T2 expected-inflation forms", ok and refused,
           f"current phi_pi {c['phi_pi']:.4f}; lead {ld['phi_pi']:.4f} + {ld['phi_pi_lead']:.0f} x next; lag {lg['phi_pi']:.4f} + "
           f"{lg['phi_pi_lag']:.0f} x last; dsge with lead refused {refused}")


def t3(res):
    o = MO.bsp_observed_gap(2026)
    s, last = MO.bsp_daily()
    moves = s[s.diff() != 0].loc["2025-12-01":"2026-12-31"]
    want = [("2025-12-12", 4.50), ("2026-02-20", 4.25), ("2026-04-24", 4.50), ("2026-06-19", 4.75), ("2026-08-28", 5.00),
            ("2026-10-23", 5.50)]
    got = [(f"{t:%Y-%m-%d}", float(v)) for t, v in moves.items()]
    # by hand: the gap is the actual rate less 4.25 from 20 Feb 2026, zero before; the rate after the last observation held
    steps = [("2026-01-01", 0.0), ("2026-02-20", 0.0), ("2026-04-24", 0.25), ("2026-06-19", 0.50), ("2026-08-28", 0.75),
             ("2026-10-23", 1.25), ("2027-01-01", None)]
    tot = 0.0
    for (d0, g), (d1, _) in zip(steps[:-1], steps[1:]):
        tot += g * (pd.Timestamp(d1) - pd.Timestamp(d0)).days
    avg = tot / 365
    ok = got == want and abs(o["i"] - avg) < 1e-9 and abs(o["i_end"] - 1.25) < 1e-9 and abs(o["quarters"][0]) < 1e-12
    report(res, "T3 the BSP's observed 2026 gap", ok, f"decisions {got == want}; average {o['i']:.6f} vs by hand {avg:.6f}; end "
           f"{o['i_end']:.2f}; quarters {[round(x, 3) for x in o['quarters']]}; last observation {o['last observation']}")


def t4(res):
    idx = pd.period_range("2026-01", "2026-12", freq="M")
    x = pd.Series([0, 0, 90, 60, 54, 20, 22, 35, 70, 72, 61, 53], index=idx, dtype=float)
    w = MO.quarter_weights(x, 2026)
    q = [x.iloc[3 * k:3 * k + 3].mean() / x.mean() for k in range(4)]
    e = max(abs(a - b) for a, b in zip(w, q))
    bad = 0
    for args in ((x.iloc[:11], 2026), (pd.Series(np.r_[np.ones(6), -np.ones(6)], index=idx), 2026)):
        try:
            MO.quarter_weights(*args)
        except ValueError:
            bad += 1
    ok = abs(np.mean(w) - 1) < 1e-12 and e < 1e-12 and bad == 2
    report(res, "T4 quarter weights", ok, f"weights {tuple(round(v, 3) for v in w)}; mean - 1 {np.mean(w) - 1:.1e}; refusals {bad}/2")


def t5(res):
    from infinity_gem.settings import dynamic_kwargs
    rule = {"rho": 0.7, "phi_pi": 1.5, "phi_x": 0.5, "phi_e": 0.0}        # MP1's coefficients (test only)
    kw = dynamic_kwargs("0.3 recommended", rice=True)
    kw["short_run_years"] = (2026,)
    d = DynamicCGE(**kw)
    d.baseline()
    cut = {2026: {"qinv_scale": {"ccons": 0.9}}}
    t0 = time.time()
    r0 = d.monetary_scenario(cut, rule=rule, theta=2.0)
    r1 = d.monetary_scenario(cut, rule=dict(rule, phi_pi_lead=0.0, phi_pi_lag=0.0, quarter_weights={2026: (1, 1, 1, 1)}), theta=2.0)
    e_rate = float((r0.monetary["policy_rate_gap_pp"] - r1.monetary["policy_rate_gap_pp"]).abs().max())
    e_gdp = float((r0.table.real_gdp / r1.table.real_gdp - 1).abs().max())
    # 1e-8: the second path warm-starts its solves from the first's solutions, so the two agree to the solver's tolerance
    report(res, "T5a zero lead/lag and equal weights = the rule without them", e_rate < 1e-8 and e_gdp < 1e-8,
           f"rate {e_rate:.1e}, GDP {e_gdp:.1e}; {time.time() - t0:.0f} s")
    ob = d.monetary_scenario(cut, rule=rule, theta=2.0, observed={2026: {"i": 0.5, "i_end": 1.0}})
    mo = ob.monetary
    tgt27 = rule["phi_pi"] * float(mo.loc[2027, "inflation_gap_pp"]) + rule["phi_x"] * float(mo.loc[2027, "output_gap_pct"])
    want27 = DynamicCGE.annual_rule(rule, tgt27, 1.0)[0]
    e_ob = max(abs(float(mo.loc[2026, "policy_rate_gap_pp"]) - 0.5), abs(float(mo.loc[2027, "policy_rate_gap_pp"]) - want27))
    report(res, "T5b observed 2026 gap; the rule from its end value", e_ob < 1e-9 and bool(mo.attrs["converged"]),
           f"2026 {float(mo.loc[2026, 'policy_rate_gap_pp']):.4f} (0.5); 2027 {float(mo.loc[2027, 'policy_rate_gap_pp']):.4f} vs "
           f"annual_rule {want27:.4f}; converged {mo.attrs['converged']} in {mo.attrs['iterations']}")
    lr = dict(rule, phi_pi=0.5, phi_pi_lead=1.0)
    ld = d.monetary_scenario(cut, rule=lr, theta=2.0)
    m2 = ld.monetary
    i_end, worst = 0.0, 0.0
    for t in m2.index:
        nxt = float(m2.loc[t + 1, "inflation_gap_pp"]) if t + 1 in m2.index else 0.0
        tg = lr["phi_pi"] * float(m2.loc[t, "inflation_gap_pp"]) + nxt + lr["phi_x"] * float(m2.loc[t, "output_gap_pct"])
        i_avg, i_end = DynamicCGE.annual_rule(lr, tg, i_end)
        worst = max(worst, abs(i_avg - float(m2.loc[t, "policy_rate_gap_pp"])))
    report(res, "T5c the lead rule's fixed point", worst < 0.01 and bool(m2.attrs["converged"]),
           f"largest gap between the rate and its rule at the converged gaps {worst:.4f} pp (tol 0.01); "
           f"rates {[round(float(v), 3) for v in m2['policy_rate_gap_pp']]}; converged {m2.attrs['converged']} in {m2.attrs['iterations']}")


def main():
    t0 = time.time()
    res = []
    for f in (t1, t2, t3, t4, t5):
        try:
            f(res)
        except Exception as e:                                   # a test that errors fails; it is never skipped
            report(res, f.__name__.upper(), False, f"error {e!r}"[:300])
    print(f"MT1: {sum(res)} of {len(res)} pass; {time.time() - t0:.0f} s", flush=True)
    return all(res) and len(res) == 7


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(0 if main() else 1)
