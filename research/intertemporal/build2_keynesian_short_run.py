"""The forward-looking CGE (Stage 2), Build 2 (18 Oct 2026, about 2 AM): a Keynesian short run in the forward-looking CGE, and measure C again.
NOT FOR CITATION (research code).

17 Oct 2026.

The option: pf_cge9.CGE9(labour="wage_curve", beta_w=7.14) with the short-run years flagged in the exogenous row 'sr'. In those
years each labour type's peso wage follows ln w = beta_w ln(employment / supply) (Infinity GEM's dynamic.py wage curve, beta =
its Okun calibration, 17 Oct 2026), so a fall in demand shows up as lost jobs, as in Infinity GEM's '0.3 recommended' short
run; other years are at full employment. The within-year block at fixed wages equals cge.py's Keynesian closure
(check_static_vs_cge.py, Keynesian rows, 2e-9 pp; a tamper test is caught).
Tests:
  (a) no shock, short-run years flagged: the path stays on the steady state;
  (b) a public-works cut in 2026 (year 1) lowers 2026 employment with the wage curve and not at full employment;
  (c) a very steep wage curve (beta_w = 1e4) gives the full-employment path back;
  (d) GDP identity in every case.
First use (measure C again, as step 4(c) but with a Keynesian short run in 2026-2027): the 2026 scenarios' economy has idle workers in
2026-2027, so measure C is run on top of a public-works shortfall sized so that 2026 employment is 0.75% below the no-shock path
(the central labour input 2026, outputs/engine_sensitivities_parts/variant_0.csv: -0.754%). Cumulative real GDP
gain 2026-2035 per peso of C, announced in 2026 against a surprise in 2027, low and high public capital, for two wage curves:
Infinity GEM's beta 7.14 and a rigid-wage benchmark, beta 0.5. Finding while building (18 Oct, about 1:55 AM): with beta 7.14 this
model makes few idle workers (a public-works cut of 1% of GDP lowers 2026 employment by only 0.08%): households are
Ricardian (they expect the lower taxes and consume more) and firms invest more as wages fall. Infinity GEM's beta was calibrated
in its recursive model, where consumption follows current income, so it does not carry over one for one; rule-of-thumb
(hand-to-mouth) consumers, the standard device (Gali, Lopez-Salido and Valles 2007, JEEA 5(1)), are the next step.
Run:  py research/intertemporal/build2_keynesian_short_run.py
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import numpy as np
from scipy.optimize import brentq

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT))
import pf_cge9 as P                                   # noqa: E402
from infinity_gem.settings import PUBLIC_CAPITAL          # noqa: E402

T = 200
GDP_2027, C_BN = 33180.0, 208.7                       # as step4_announced_infrastructure.py (the 2026 scenarios of 17 Oct 2026, measure C)
LABOUR_2026 = -0.754                                  # the central labour input 2026 (%), variant_0.csv
SR = lambda r: r.__setitem__((0, slice(0, 2)), 1.0)   # 2026 and 2027 are short-run years (the 2026 scenarios' 2025-2027, from 2026)


def run(m, ss, sr=True, **changes):
    X = m.path(T, **({"sr": SR} if sr else {}), **changes)
    Y, y0, yT, info = m.run(X, y_start=ss)
    return Y, m.accounts(Y, y0, X), X


def main():
    out = [f"# Build 2: a Keynesian short run in the forward-looking CGE ({datetime.now():%Y-%m-%d %H:%M})", "",
           "**NOT FOR CITATION** (research code; see the script's docstring).", ""]
    checks = {}
    m = P.CGE9(calib="pwt", households="groups", labour="wage_curve")
    mf = P.CGE9(calib="pwt", households="groups")                       # full employment, same calibration
    ss = m.steady()[0]
    Y, acc, X = run(m, ss)
    checks["(a) no shock, short-run years flagged: stays on the steady state"] = float(np.abs(Y - ss[:, None]).max() / np.abs(ss).max()) < 1e-10
    cut = -0.01 * m.GDP0                                                 # public-works cut of 1% of GDP in 2026
    Yw, aw, _ = run(m, ss, dIG=lambda r: r.__setitem__((0, 0), cut))
    Yf, af, _ = run(mf, ss, sr=False, dIG=lambda r: r.__setitem__((0, 0), cut))
    e_w, e_f = (aw["employment"][:, 0] - 1) * 100, (af["employment"][:, 0] - 1) * 100
    checks[f"(b) public-works cut 1% of GDP in 2026: employment 2026 {np.round(e_w, 3)}% with the wage curve, "
           f"{np.round(e_f, 4)}% at full employment"] = bool((e_w < -0.05).all() and (np.abs(e_f) < 1e-9).all())
    ms = P.CGE9(calib="pwt", households="groups", labour="wage_curve", beta_w=1e4)
    Ys, as_, _ = run(ms, ss, dIG=lambda r: r.__setitem__((0, 0), cut))
    gap = float((np.abs(Ys[:, :40] - Yf[:, :40]) / m.scale(ss)[:, None]).max())
    checks[f"(c) beta_w = 1e4 gives the full-employment path back (largest gap, years 1-40: {gap:.1e})"] = gap < 1e-3
    checks[f"(d) GDP identity (gaps {aw['gap']:.1e}, {as_['gap']:.1e})"] = max(aw["gap"], as_["gap"]) < 1e-8
    gdp0 = float(m.accounts(np.repeat(ss[:, None], 2, 1), ss, np.repeat(m.x0[:, None], 3, 1))["real_gdp"][0])
    out += ["## Tests", ""] + [f"- {k}: {'PASS' if v else 'FAIL'}" for k, v in checks.items()] + [""]
    out += [f"A public-works cut of 1% of GDP in 2026: real GDP 2026 {(aw['real_gdp'][0] / gdp0 - 1) * 100:+.3f}% with the "
            f"Keynesian short run, {(af['real_gdp'][0] / gdp0 - 1) * 100:+.3f}% at full employment.", ""]

    # ---- measure C on top of a 2026-2027 shortfall (idle workers, as in the 2026 scenarios)
    for name, beta in (("low", 7.14), ("high", 7.14), ("low", 0.5), ("high", 0.5)):
        pc = PUBLIC_CAPITAL[name]
        mk = P.CGE9(calib="pwt", households="groups", labour="wage_curve", public_capital=pc, beta_w=beta)
        mfp = P.CGE9(calib="pwt", households="groups", public_capital=pc)
        s0 = mk.steady()[0]
        g0 = float(mk.accounts(np.repeat(s0[:, None], 2, 1), s0, np.repeat(mk.x0[:, None], 3, 1))["real_gdp"][0])

        def emp26(size):
            _, a, _ = run(mk, s0, dIG=lambda r: r.__setitem__((0, 0), -size * mk.GDP0))
            return float(np.average(a["employment"][:, 0] - 1, weights=mk.L0.sum(1))) * 100 - LABOUR_2026
        size = brentq(emp26, 0.0, 0.25, xtol=1e-6)
        dig = C_BN / GDP_2027 * mk.GDP0
        short = lambda r: r.__setitem__((0, 0), -size * mk.GDP0)
        _, base, _ = run(mk, s0, dIG=short)
        rows = {}
        for lab, col in (("announced in 2026", None), ("surprise in 2027", None)):
            if lab.startswith("announced"):
                _, a, _ = run(mk, s0, dIG=lambda r: (short(r), r.__setitem__((0, 1), r[0, 1] + dig)))
            else:
                # surprise: 2026 as the shortfall path; from 2027 a new plan starting from the 2026 state
                Yb, _, _ = run(mk, s0, dIG=short)
                X2 = mk.path(T, sr=lambda r: r.__setitem__((0, slice(0, 1)), 1.0), dIG=lambda r: r.__setitem__((0, 0), dig))
                Y2, y02, _, _ = mk.run(X2, y_start=Yb[:, 0])
                a2 = mk.accounts(Y2, Yb[:, 0], X2)
                a = {"real_gdp": np.concatenate([[base["real_gdp"][0]], a2["real_gdp"][:-1]]),
                     "employment": np.column_stack([base["employment"][:, 0], a2["employment"][:, :-1]])}
            gain = float((a["real_gdp"][:10] - base["real_gdp"][:10]).sum())
            rows[lab] = (gain / dig, (a["real_gdp"][:4] / base["real_gdp"][:4] - 1) * 100,
                         (np.average(a["employment"][:, :2], axis=0, weights=mk.L0.sum(1)) / np.average(base["employment"][:, :2], axis=0, weights=mk.L0.sum(1)) - 1) * 100)
        # full employment, same programme and public capital, no shortfall (step 4(c) for comparison)
        sf = mfp.steady()[0]
        _, af0, _ = run(mfp, sf, sr=False)
        _, af1, _ = run(mfp, sf, sr=False, dIG=lambda r: r.__setitem__((0, 1), dig))
        fe = float((af1["real_gdp"][:10] - af0["real_gdp"][:10]).sum()) / dig
        out += [f"## Measure C, public capital '{name}' (phi {pc['phi']}, KG/GDP {pc['kg_gdp']}), wage curve beta {beta}; programme ₱{dig:,.1f} bn "
                f"(2023-SAM units) in 2027", "",
                f"Shortfall: a public-works cut of {size * 100:.3f}% of GDP in 2026 puts 2026 employment {LABOUR_2026}% below the "
                f"no-shock path (real GDP 2026 {(base['real_gdp'][0] / g0 - 1) * 100:+.3f}%).", "",
                "| Case | Output 2026-2035 per peso of C | Real GDP 2026, 2027, 2028, 2029 (% vs shortfall path) | Employment 2026, 2027 (%) |",
                "|---|---|---|---|"]
        for lab, (pp, g, e) in rows.items():
            out.append(f"| Keynesian short run, {lab} | ₱{pp:.2f} | {', '.join(f'{x:+.3f}' for x in g)} | {', '.join(f'{x:+.3f}' for x in e)} |")
        out += [f"| Full employment, announced (step 4(c) setting, no shortfall) | ₱{fe:.2f} | | |", ""]
        checks[f"{name}, beta {beta}: the Keynesian short run raises C's return above full employment"] = rows["announced in 2026"][0] > fe
    out += ["## All checks", ""] + [f"- {k}: {'PASS' if v else 'FAIL'}" for k, v in checks.items()] + [
            "", f"{sum(checks.values())} of {len(checks)} checks pass", "",
            "## Reading", "",
            "- With idle workers in 2026-2027, measure C employs them, so its 2027 effect is larger than at full employment "
            "(where it crowds out private uses). The ₱0.8 per peso of the 2026 scenarios (Infinity GEM's recursive model, Keynesian 2025-2027) is "
            "the comparable figure; this model adds foresight (announced vs surprise) and Ricardian households.",
            "- Lump-sum financing (Ricardian): households expect the taxes, which damps consumption. Infinity GEM's recursive model "
            "has no such response, one reason the two can differ."]
    txt = "\n".join(out) + "\n"
    p = ROOT / "outputs" / f"dscge_build2_keynesian_short_run_{datetime.now():%Y%m%d_%H%M}.md"
    p.write_text(txt, encoding="utf-8")
    print(txt); print(f"wrote {p}")
    return checks


if __name__ == "__main__":
    main()
