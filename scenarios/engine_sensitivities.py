"""Engine sensitivities D1-D2 of code review of dynamic.py (17 Oct 2026), on the combined 2026 run.

17 Oct 2026. Review: a review note (not included).

D1  Investment does not respond to income (every closure holds real investment on its baseline path). Variants:
    (a) savings-driven long-run years: in 2028-2030 household saving rates stay at the baseline's and investment follows
        savings (DynamicCGE(investment_closure="savings")), so a shock that lowers income lowers investment and capital;
    (b) fixed foreign borrowing in the short-run years 2025-2027: the current account cannot absorb the oil import bill and
        the peso adjusts instead (DynamicCGE(sr_fx="flexible"); the sticky peso wage is the nominal anchor);
    (c) both.
D2  Sticky peso wages with fully flexible prices. Variant: in the short-run years non-farm prices are rigid downward
    (DynamicCGE(sr_pricing="sticky"); cge.py pricing="sticky"): cost increases pass through in full, but only the share
    (1 - stickiness) of a cost fall ("prices rise faster than they fall": Peltzman 2000, JPE 108(3); 16 Oct 2026). Farm and mining prices stay flexible.
    Stickiness from the micro evidence on how long prices stay unchanged: Nakamura and Steinsson (2008), QJE 123(4),
    1415-1464: median duration of regular (non-sale) consumer prices 8-11 months in the US, 1988-2005 (checked 17 Oct 2026
    against the 2007 working paper and a course summary; the QJE text itself not yet read). The 4-month lower value is an
    ASSUMPTION for an emerging economy with more frequent price changes (Gagnon 2009, QJE 124(3), on Mexico, documents how
    the frequency rises with inflation but was not checked for a number). Philippine evidence (found 17 Oct, about 1:15 PM, in the BSP Working Paper Series): Basilio and Cacnio (2020), BSP WP 2020-02, p. 6: CPI items rise every 1.5 months and
    fall every 10.4 months on average (1994-2019), so stickiness for falls = 0.59: the high value (0.6) is the Philippine one. With a constant hazard and mean duration D months, the share of a cost change at the start of a year NOT yet in
    that year's average price is (D/12)(1 - exp(-12/D)): 0.32 for D = 4, 0.58 for D = 10. Rows: stickiness 0.3 and 0.6.
    Tried first (17 Oct, about 12:30 PM) and dropped: calibrating stickiness to the inflation VAR (public works alone lowering
    2026 consumer prices by 0.65%, Note C) is out of reach: even at stickiness 0.95 public works alone lower them by 1.16%,
    because farm and food prices (flexible) fall with demand, and at 1 the model does not solve.
    The wage curve is RECALIBRATED with the central run's target (labour input 2026 = Okun's e x the model's own 2026 growth
    effect; scenarios/calibrate_wage_curve.py), since its beta partly stood in for the missing price stickiness.
All variants: public capital low (central 2026 setting), 0.3 recommended, NOT FOR CITATION.
Run:  py scenarios/engine_sensitivities.py   (about 20-30 minutes)
"""
import sys

from _common import ROOT
import numpy as np
import pandas as pd

sys.path.insert(0, str(ROOT / "preshock"))
from infinity_gem import paths                                                     # noqa: E402
import calibrate_wage_curve as CW                                               # noqa: E402
import combined_revised as CR                                                   # noqa: E402
import okun                                                                     # noqa: E402
from infinity_gem import stickiness as STK                                          # noqa: E402
from infinity_gem.dynamic import PSA_INDUSTRIES                                     # noqa: E402

# 0.3.11 (19 Oct 2026, about 11:35 PM): the sticky-price activities (all but farm and mining, as DynamicCGE's default)
STICKY = [a for k, v in PSA_INDUSTRIES.items() if k not in ("Agriculture, forestry, and fishing", "Mining and quarrying") for a in v]

VARIANTS = {
    "central (setting of 17 Oct 2026)": {},
    "D1a: investment follows savings in 2028-2030": dict(investment_closure="savings"),
    "D2, low: prices rigid downward in 2025-2027, stickiness 0.3 (beta recalibrated)": dict(sr_pricing="sticky", sr_stickiness=0.3),
    "D2, high: stickiness 0.6 (beta recalibrated)": dict(sr_pricing="sticky", sr_stickiness=0.6),
    "D1a + D2 high": dict(investment_closure="savings", sr_pricing="sticky", sr_stickiness=0.6),
    # 0.3.11 (19 Oct 2026, about 11:35 PM): stickiness by sector from BSP WPS 2020-02 (infinity_gem/stickiness.py); appended
    # last, so the cached parts of the five rows above stay valid
    "D2, sectoral: stickiness by sector, BSP WPS 2020-02 (beta recalibrated)": dict(sr_pricing="sticky",
                                                                                    sr_stickiness=STK.sectoral(STICKY)),
}
# D1b (sr_fx="flexible": foreign borrowing fixed in 2025-2027, the peso adjusts) is NOT run on the combined shocks (17 Oct 2026):
# (i) in 2026 the employment cap does not settle (the floating peso pushes every skill level to full employment, which removes
# the nominal anchor; the peso then returns to its baseline and the cap releases again); (ii) the closure is rejected by the
# data: a 20% construction cut alone strengthens the model's peso by 12.7% (check IC1), while the actual peso was 2.0% weaker
# than forecast in January-September 2026 (Note C) and the current account absorbed the shocks, as the central closure assumes.
RECAL = {k for k, v in VARIANTS.items() if v.get("sr_pricing") == "sticky"}
CPI_TARGET = -0.65            # assumption: 'other domestic price shocks', January-September 2026 (inflation VAR)


def pw_cpi_2026(R, piece, theta):
    """Consumer prices 2026 (% vs the no-shock path) with public works alone, at stickiness theta."""
    R.d.a["sr_stickiness"] = theta
    clean = R.run(set(), piece=piece)
    pw = R.run({"public works"}, piece=piece)
    return float(pw.table.cpi[2026] / clean.table.cpi[2026] - 1) * 100


def calibrate_theta(R, piece, tol=2e-3):
    """Stickiness at which public works alone lower 2026 consumer prices by |CPI_TARGET| (bisection; 1 if out of reach)."""
    lo, hi = 0.0, 1.0
    if pw_cpi_2026(R, piece, hi) < CPI_TARGET:
        print("target out of reach at stickiness 1: reported as 1")
        return hi
    while hi - lo > tol:
        mid = (lo + hi) / 2
        if pw_cpi_2026(R, piece, mid) < CPI_TARGET:   # prices still fall too much: more stickiness
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def beta_without_engine(name):
    """(beta, file) for a D2 row from the latest run on the same SAM without INFINITY_GEM_SCENARIO_ENGINE settings (19 Oct 2026). With
    hoarding the recalibration target (labour input 2026 = Okun's e x the growth effect) is out of reach, because hoarded workers
    stay employed ('no root' at beta 0); the central row likewise keeps the beta calibrated without hoarding (calibration_file)."""
    tag = __import__("_common").sam_tag()
    files = sorted(paths.output_dir().glob("engine_sensitivities_" + "[0-9]" * 8 + "_" + "[0-9]" * 4 + tag + ".csv"))
    if not files:
        raise FileNotFoundError(f"no engine_sensitivities_*{tag}.csv without engine settings: run this script without INFINITY_GEM_SCENARIO_ENGINE first")
    return float(pd.read_csv(files[-1], index_col=0).loc[name, "wage-curve beta"]), files[-1].name


def labour_and_growth(R, piece, beta):
    """(labour input 2026 %, growth effect 2026 pp) at beta: calibrate_wage_curve.stats on this variant."""
    l, g26, g25, ge = CW.stats(R, piece, beta)
    return l, ge


def main():
    est = okun.estimates()
    e = float(est.loc["2006-2026, all quarters", "elasticity e"])
    cal = pd.read_csv(__import__("_common").calibration_file(), index_col=0)
    beta_c = float(cal.loc["central (e)", "beta"])
    rows = {}
    parts = paths.output_dir() / f"engine_sensitivities_parts{__import__('_common').out_tag()}"   # 0.3.10: SAM tag      # one file per finished variant (a restart skips them)
    parts.mkdir(exist_ok=True)
    for j, (name, kw) in enumerate(VARIANTS.items()):
        part = parts / f"variant_{j}.csv"
        if part.exists():
            rows[name] = pd.read_csv(part, index_col=0).iloc[:, 0].to_dict()
            print(f"--- {name}: read from {part.name}", flush=True)
            continue
        print(f"--- {name}", flush=True)
        R = CR.Runs("low", wage_curve=beta_c, **kw)
        piece, src = R.pieces()
        theta = kw.get("sr_stickiness", 0.0)                # a dict for the sectoral row: report its simple mean
        beta, theta = beta_c, float(np.mean(list(theta.values()))) if isinstance(theta, dict) else float(theta)
        if name in RECAL and __import__("_common").SCENARIO_ENGINE:   # e.g. hoarding: keep this row's beta from the run without it
            beta, cal_src = beta_without_engine(name)
            print(f"  stickiness {theta:.2f}: beta {beta:.3f} (as calibrated without the engine settings, {cal_src})", flush=True)
            R.d.a["wage_curve"] = beta
        elif name in RECAL:                            # the wage curve recalibrated to the central target at this stickiness
            beta = CW.calibrate(lambda s: s[0] - e * s[3], R, piece)
            print(f"  stickiness {theta:.2f}: beta {beta:.3f}", flush=True)
            R.d.a["wage_curve"] = beta
        pw = src["public works"]
        works = {2025: pw["2025"], 2026: pw["2026 central"], 2027: pw["2027 NEP x 2025 rate (central)"]}
        clean = R.run(set(), piece=piece)
        adv = R.run(set(CR.SHOCKS), piece=piece)
        out = R.measures(clean, adv, works=works, poor=True)[0]
        lab, ge = labour_and_growth(R, piece, beta)
        R.d.a["wage_curve"] = beta                          # stats() reset it; keep this variant's beta for what follows
        row = {"wage-curve beta": beta, "price stickiness": theta, "implied pay elasticity": -beta * 0.039 / (1 - 0.039),
               "peso 2026 (% weaker than no-shock path)": float(adv.table.exr[2026] / clean.table.exr[2026] - 1) * 100,
               "real investment 2030 (%)": float(adv.table.real_investment[2030] / clean.table.real_investment[2030] - 1) * 100,
               "labour input 2026 (%)": lab, "growth effect 2026 (pp)": ge}
        row.update({k: out[k] for k in ("GDP gap 2026 (%)", "GDP gap 2027 (%)", "GDP gap 2030 (%)",
                                        "cumulative GDP loss 2025-2030 (₱ bn)", "consumer prices 2026 (%)",
                                        "new poor 2026 (M, own baskets)", "new poor 2027 (M, own baskets)",
                                        "debt-to-GDP change 2030 (pp)")})
        for S in (("public works",), ("oil",)):
            o = R.measures(clean, R.run(set(S), piece=piece), works=works if S == ("public works",) else {}, poor=False)[0]
            row[f"{S[0]} alone: GDP gap 2026 (%)"] = o["GDP gap 2026 (%)"]
            row[f"{S[0]} alone: GDP gap 2030 (%)"] = o["GDP gap 2030 (%)"]
            row[f"{S[0]} alone: consumer prices 2026 (%)"] = o["consumer prices 2026 (%)"]
        for ms, label in (("A", "A (upper)"), ("B", "B"), ("C", "C")):
            p = R.measures(clean, R.run(set(CR.SHOCKS), ms, piece=piece), works=works,
                           extra_spend={2027: CR.CATCHUP} if ms == "C" else None)[0]
            cost = {"A": CR.equiv_2025(CR.AID_2026, 2026), "B": CR.equiv_2025(CR.AID_2027, 2027),
                    "C": CR.equiv_2025(CR.CATCHUP, 2027)}[ms]
            gain = out["cumulative GDP loss 2025-2030 (₱ bn)"] - p["cumulative GDP loss 2025-2030 (₱ bn)"]
            yr = 2027 if ms in "BC" else 2026
            row[f"{label}: poor protected {yr} (M)"] = out[f"new poor {yr} (M, own baskets)"] - p[f"new poor {yr} (M, own baskets)"]
            row[f"{label}: output recovered per peso"] = gain / cost
        rows[name] = row
        pd.Series(row, name=name).to_csv(part)
        print(pd.Series(row).to_string(), flush=True)
    t = pd.DataFrame(rows).T
    stamp = pd.Timestamp.today()
    f = paths.output_dir() / f"engine_sensitivities_{stamp:%Y%m%d_%H%M}{__import__('_common').out_tag()}"
    f = f.with_name(f.name + ".x")      # 19 Oct 2026: with_suffix() below must not eat the ".85" of a tag such as "_hoarding0.85"
    t.to_csv(f.with_suffix(".csv"))
    show = t.T
    L = [f"# Engine sensitivities D1-D2 on the combined 2026 run ({stamp:%d %B %Y, %H:%M})", "",
         "**NOT FOR CITATION** (Infinity GEM 0.3.8; code review of `dynamic.py`, 17 Oct 2026, D1-D2). "
         "Script: `scenarios/engine_sensitivities.py`. Public capital low (central 2026 setting). Every row is the 2026 scenarios' "
         "central run with one engine choice changed; the D2 rows recalibrate the wage curve to the central run's target "
         "(labour input 2026 = Okun's e x the model's own 2026 growth effect).", "",
         *([f"**Engine settings {__import__('_common').SCENARIO_ENGINE}** (INFINITY_GEM_SCENARIO_ENGINE) apply to every row. The D2 rows keep "
            "the wage-curve betas calibrated without them (latest run on this SAM without engine settings), as the central row "
            "keeps the 2026 scenarios' beta: with hoarding the Okun target is out of reach, since hoarded workers stay employed.", ""]
           if __import__('_common').SCENARIO_ENGINE else []),
         "- **D1a:** in 2028-2030 household saving rates stay at the baseline's and real investment follows savings, so lower "
         "income means less investment and less capital (the central 2026 setting holds investment on its baseline path).",
         "- **D1b (foreign borrowing fixed, the peso floats) is not run:** in 2026 the employment cap does not settle under it, "
         "and the data reject it: a 20% construction cut alone strengthens the model's peso by 12.7% (check IC1), while the "
         "actual peso was 2.0% weaker than forecast in January-September 2026 (Note C) and the current account absorbed the "
         "shocks, as the central closure assumes.",
         "- **D2:** in 2025-2027 non-farm prices are rigid downward: cost increases pass through in full, only part of a cost "
         "fall does (Peltzman 2000). Stickiness 0.3 and 0.6: the share of a cost change not yet in that year's average price "
         "when prices stay unchanged for 4 (assumption) or 10 months on average (US micro evidence: Nakamura and Steinsson "
         "2008, median 8-11 months). The wage curve is recalibrated to the central target; farm and mining prices stay flexible. "
         "Calibrating stickiness to the inflation VAR instead (public works alone lowering 2026 prices by 0.65%) is out of "
         "reach: at stickiness 0.95 they still fall 1.16%, from flexible farm and food prices.",
         "- **D2, sectoral (19 Oct 2026):** stickiness by sector from the months between price falls of each CPI group "
         "(Basilio and Cacnio 2020, BSP WPS 2020-02, Table 2, 2002-M9 2019; `infinity_gem/stickiness.py`): food 0.29, utilities "
         "and rents 0.56, transport 0.71, restaurants and financial services 0.87, education 0.89; refined petroleum flexible; "
         "the column 'price stickiness' shows the simple mean (value-added weighted: 0.62).", "",
         "Data checks: the peso was 2.0% weaker than forecast in January-September 2026 (2.5% for the year; Note C); the "
         "VAR's other domestic price shocks lowered 2026 inflation by about 0.65 points (the model's public works alone: "
         "row 'public works alone: consumer prices 2026').", "",
         show.to_markdown(floatfmt=".3f"), "",
         "Implied pay elasticity: the slope of pay on the unemployment rate the beta implies at 3.9% unemployment "
         "(Blanchflower and Oswald 1994: about -0.1)."]
    f.with_suffix(".md").write_text("\n".join(L), encoding="utf-8")
    print("saved", f.with_suffix(".md"))


if __name__ == "__main__":
    main()
