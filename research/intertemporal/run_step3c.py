"""The forward-looking CGE (Stage 2), step 3c (17 Oct 2026): all tests of the forward-looking 9-sector model, in one run.

1. Regression: pf_cge9.py with its default options reproduces the step 3b model (7 tests).
2. The new options (households='groups'; calib='pwt': growth, fixed factors, mining resource rent): the same 7 tests.
3. Cross-check of the within-year block against infinity_gem/cge.py (check_static_vs_cge.py), three configurations, and
   tamper tests showing the cross-check fails when an elasticity or a household parameter is changed by 1-2%.
4. Diagnostic: is the SAM's foreign saving consistent with a stable foreign-debt ratio on the growth path?
5. Illustration: the oil-type episode by household group (data calibration, ten groups).
Run:  py research/intertemporal/run_step3c.py
"""
from __future__ import annotations

import contextlib
import io
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import pf_cge9 as P                   # noqa: E402
import check_static_vs_cge as K       # noqa: E402


def section(t):
    print(f"\n## {t}\n")


def main():
    total = {}
    section("1. Regression: default options = the step 3b model")
    _, r = P.main(P.CGE9(), "defaults: calib='sam', households='one'")
    total["regression"] = all(r.values())
    section("2. New options")
    for kw, lab in ((dict(households="groups"), "households='groups'"), (dict(calib="pwt"), "calib='pwt'"),
                    (dict(calib="pwt", households="groups"), "calib='pwt', households='groups'")):
        print(f"### {lab}\n")
        _, r = P.main(P.CGE9(**kw), lab)
        total[lab] = all(r.values())
        print()
    section("3. Cross-check of the within-year block against Infinity GEM's cge.py")
    df, ok = K.main()
    total["cross-check"] = ok
    print("\nTamper tests (the cross-check must FAIL):")
    orig_init = P.CGE9.__init__
    caught = []
    for kw in (dict(sig_a=2.02), dict(omega=1.98), dict(sig_va=0.81)):
        def init(self, *a, _kw=kw, **k):
            orig_init(self, *a, **{**k, **_kw})
        P.CGE9.__init__ = init
        with contextlib.redirect_stdout(io.StringIO()):
            d2, ok2 = K.main(K.CONFIGS[:1])
        P.CGE9.__init__ = orig_init
        caught.append(not ok2)
        print(f"- {kw}: largest gap {d2['largest'].max():.2e} pp -> {'caught' if not ok2 else 'NOT CAUGHT'}")
    orig_cal = P.CGE9._calibrate_groups
    for name, fn in (("urban Q5's share of enterprise income +1%", lambda m: m.she.__setitem__(9, m.she[9] * 1.01)),
                     ("rural Q1's saving rate +2%", lambda m: m.mps.__setitem__(0, m.mps[0] * 1.02))):
        def cal(self, S, c, _fn=fn):
            orig_cal(self, S, c); _fn(self)
        P.CGE9._calibrate_groups = cal
        with contextlib.redirect_stdout(io.StringIO()):
            d2, ok2 = K.main(K.CONFIGS[1:2])
        P.CGE9._calibrate_groups = orig_cal
        caught.append(not ok2)
        print(f"- {name}: largest gap {d2['largest'].max():.2e} pp -> {'caught' if not ok2 else 'NOT CAUGHT'}")
    total["tampers caught"] = all(caught)

    section("4. Diagnostic: the SAM's foreign saving and a stable foreign-debt ratio")
    m = P.CGE9(calib="pwt")
    fsav = m.FSAV0 / m.GDP0
    niip = 0.116                             # NIIP end-2023, -11.6% of GDP: IMF Country Report 25/333, Annex II, p. 47 (data note)
    bgp = m.g / (1 + m.g) * niip
    print(f"- SAM foreign saving: ₱{m.FSAV0:,.0f} bn = {fsav * 100:.2f}% of the SAM's GDP")
    print("- Current-account deficit 2023: 2.8% of GDP (IMF Country Report 25/333, Annex II, p. 47; WDI 2.83%); IMF EBA norm: "
          "deficit 1.2% (2023), 0.9% (2024) (p. 48)")
    print(f"- Net international investment position end-2023: -{niip * 100:.1f}% of GDP (IMF CR 25/333, p. 47; BSP tables to confirm "
          f"when the BSP website is back)")
    print(f"- Borrowing that keeps that ratio stable at trend growth g = {m.g * 100:.2f}%: g/(1+g) x {niip * 100:.1f}% = "
          f"{bgp * 100:.2f}% of GDP")
    print(f"- Debt ratio that the SAM's foreign saving would sustain: {fsav * (1 + m.g) / m.g * 100:.0f}% of GDP")
    print("- Reading: the SAM's rest-of-world account carries about twice the balance-of-payments deficit (mainly a larger "
          "trade deficit: SAM 13% of GDP); no stable debt path fits it. The model keeps the SAM's non-trade inflows at "
          "their 2023 share of GDP; reconciling the SAM's rest-of-world account with the BOP is a data task (Infinity GEM's "
          "static model uses the same SAM).")

    section("5. Illustration: oil-type episode by household group (calib='pwt', households='groups'; NOT FOR CITATION)")
    m = P.CGE9(calib="pwt", households="groups")
    ss = m.steady()[0]
    ic = P.SECT.index("chem")
    X = m.path(200, pwm=lambda r: r.__setitem__((ic, slice(0, 2)), 1.2))
    Y, y0, yT, info = m.run(X, y_start=ss)
    acc = m.accounts(Y, y0, X)
    s = acc["s"]
    eh0 = m.EH0
    real = s["EH"] / eh0[:, None] / s["cpi_l"][None, :] - 1
    print("Real spending of each group (deflated by the CPI), % change from the steady state, years 1-3 and 5:")
    print("| group | year 1 | year 2 | year 3 | year 5 |\n|---|---|---|---|---|")
    for h, name in enumerate(P.HH):
        print(f"| {name} | {real[h, 0] * 100:+.2f} | {real[h, 1] * 100:+.2f} | {real[h, 2] * 100:+.2f} | {real[h, 4] * 100:+.2f} |")
    print(f"\nTotal consumption year 1 {(Y[m.sl['C'].start, 0] / m.C0 - 1) * 100:+.2f}%; saving-rate factor mpsadj year 1 "
          f"{Y[m.sl['mpsadj'].start, 0]:+.4f} (all groups' saving rates scaled by 1 + mpsadj). Same CPI for all groups here: "
          f"each group's own price index comes with the microsimulation link.")

    section("Summary")
    for k, v in total.items():
        print(f"- {k}: {'PASS' if v else 'FAIL'}")
    print(f"\n{sum(total.values())} of {len(total)} blocks pass")


if __name__ == "__main__":
    main()
