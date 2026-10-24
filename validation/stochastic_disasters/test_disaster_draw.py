"""Standalone tests of the opt-in typhoon draw in the stochastic outlook (23 Oct 2026; research).

Not part of checks/run_all_checks.py (its owner adds a check if wanted; proposed text in the 23 Oct 2026 findings). Reads only;
writes nothing. Exit code 0 = all tests pass. About 3 minutes.
Run:  py validation/stochastic_disasters/test_disaster_draw.py

D1  Calibration: from_data() equals an independent recomputation from the data file and PSA GDP (frequency, log-severity
    mean and standard deviation, background, agriculture share).
D2  Tail check against PAGASA's own rankings of the 2019-2022 seasons (rank among all seasons since 1970 or 2000, inflation-
    adjusted): exceedance probability in the model within 0.10 of rank / (n + 1) for each season (2018 shown, not tested:
    its rank is among 19 seasons only).
D3  Centring and scale: 'mean' draws average zero, 'median' draws have median zero, 'none' draws average the expected
    season; scale 2 doubles the same draw exactly.
D4  Default off: disasters=None and a zero-damage draw (scale 0) give identical outlooks; the external shocks are identical
    with the typhoon draw on (it has its own random stream).
D5  Zero variance with the typhoon draw on reproduces the baseline exactly (check X1's property kept).
D6  Mapping, '0.3 recommended' with public capital (low): one typhoon year equals the dynamic scenario built by hand
    (agricultural productivity 1 - x; public capital destroyed through the engine's kg_loss), and the model's own public-
    capital settings are restored after the run.
D7  Signs: damage above the normal year lowers GDP that year and the next (public capital); a quiet year raises it.
D8  Mapping, published 0.2 settings (no public capital): the one-year stand-in (1 - d / kg_gdp) ** phi in every activity.
D9  Refusals: bad centre, agriculture share, frequency; a disasters argument that is not a DisasterDraw.
"""
import csv
import dataclasses
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import numpy as np                                    # noqa: E402
import pandas as pd                                   # noqa: E402

from infinity_gem import stochastic as SC                 # noqa: E402
from infinity_gem import macrolink as ML                  # noqa: E402
from infinity_gem.dynamic import DynamicCGE, PSA_INDUSTRIES   # noqa: E402
from infinity_gem.settings import dynamic_kwargs, PUBLIC_CAPITAL   # noqa: E402

RESULTS = []


def report(name, ok, msg):
    RESULTS.append(ok)
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {msg}", flush=True)


def gdp_independent():
    g = pd.read_csv(ROOT / "data" / "raw" / "macro" / "PSA_OpenSTAT_GDP_by_expenditure_quarterly_2000-2026.csv", comment="#")
    g = g[(g["valuation"] == "At Current Prices") & (g["expenditure"] == "Gross Domestic Product")]
    return {int(y): float(v.sum()) / 1000 for y, v in g.groupby("year")["value_million_php"] if len(v) == 4}


def d1(dd):
    gdp = gdp_independent()
    rows = [r for r in csv.reader(l for l in open(ROOT / "data" / "raw" / "disasters" / SC.DISASTER_FILE, encoding="utf-8")
                                  if not l.startswith("#"))]
    hdr, rows = rows[0], rows[1:]
    col = {h: i for i, h in enumerate(hdr)}
    ev = [r for r in rows if r[col["record"]] == "event"]
    se = {int(r[col["season"]]): float(r[col["total_php_bn"]]) for r in rows if r[col["record"]] == "season"}
    sh = [float(r[col["total_php_bn"]]) / gdp[int(r[col["season"]])] * 100 for r in ev]
    lx = np.log(sh)
    seasons = sorted({int(r[col["season"]]) for r in ev})
    lam = len(ev) / len(seasons)
    bg = np.mean([(se[y] - sum(float(r[col["total_php_bn"]]) for r in ev if int(r[col["season"]]) == y)) / gdp[y] * 100
                  for y in seasons])
    both = [r for r in ev if r[col["agriculture_php_bn"]] and r[col["infrastructure_php_bn"]]]
    agri = sum(float(r[col["agriculture_php_bn"]]) for r in both) / sum(float(r[col["total_php_bn"]]) for r in both)
    gaps = [abs(dd.lam - lam), abs(dd.mu - lx.mean()), abs(dd.sigma - lx.std(ddof=1)), abs(dd.background - bg),
            abs(dd.agri_share - agri)]
    fr = next(r for r in rows if r[col["record"]] == "frequency")
    long_run = float(fr[col["count"]]) / float(fr[col["seasons"]])
    dl = SC.DisasterDraw.from_data(frequency="2001-2019")
    season_mean = np.mean([v / gdp[y] * 100 for y, v in se.items()])
    report("D1 calibration", max(gaps) < 1e-12 and abs(dl.lam - long_run) < 1e-12,
           f"{len(ev)} destructive cyclones in {len(seasons)} seasons: lam {dd.lam:.3f} (2001-2019 names: {long_run:.3f}); "
           f"log damage per cyclone (% of GDP) mean {dd.mu:.3f}, sd {dd.sigma:.3f}; background {dd.background:.4f}% of GDP; "
           f"agriculture {dd.agri_share:.1%}; expected season {dd.expected():.3f}% of GDP against the 2017-2023 season mean "
           f"{season_mean:.3f}%; largest gap to the recomputation {max(gaps):.1e}")
    return gdp, se


def d2(dd, gdp, se):
    g = dd.gross(np.random.default_rng(11), 400_000)
    ranks = {2019: (15, 20), 2020: (12, 51), 2021: (6, 52), 2022: (23, 53)}     # ARTC: 2019 since 2000; 2020-2022 since 1970
    out, ok = [], True
    for y, (k, n) in ranks.items():
        p, emp = float((g > se[y] / gdp[y] * 100).mean()), k / (n + 1)
        ok &= abs(p - emp) < 0.10
        out.append(f"{y} {se[y] / gdp[y] * 100:.3f}% of GDP: model {p:.2f}, rank {emp:.2f}")
    p18 = float((g > se[2018] / gdp[2018] * 100).mean())
    report("D2 tail vs PAGASA's rankings", ok, "; ".join(out) + f"; (2018, 5th of 19 since 2000, not tested: model {p18:.2f}, "
           f"rank {5 / 20:.2f})")


def d3(dd):
    rng = lambda: np.random.default_rng(5)
    yrs = list(range(200_000))
    a = np.array(list(dd.draw(rng(), yrs).values()))
    dm = SC.DisasterDraw.from_data(centre="median")
    b = np.array(list(dm.draw(rng(), yrs).values()))
    dn = SC.DisasterDraw.from_data(centre="none")
    c = np.array(list(dn.draw(rng(), yrs).values()))
    d2_ = np.array(list(dataclasses.replace(dd, scale=2.0).draw(rng(), yrs).values()))
    se_ = a.std() / np.sqrt(len(a))
    ok = abs(a.mean()) < 4 * se_ and abs(np.median(b)) < 0.002 and abs(c.mean() - dd.expected()) < 4 * se_ \
        and float(np.abs(d2_ - 2 * a).max()) < 1e-12
    report("D3 centring and scale", ok, f"'mean': average {a.mean():+.5f} (s.e. {se_:.5f}); 'median': median {np.median(b):+.5f}; "
           f"'none': average {c.mean():.4f} against expected {dd.expected():.4f}; scale 2 = twice the draw "
           f"(gap {float(np.abs(d2_ - 2 * a).max()):.1e})")


def setup(setting):
    d = SC.load_task1_monthly()
    fx = float(d["fx"].dropna().iloc[-12:].mean())
    dyn = DynamicCGE(**dynamic_kwargs("0.3 recommended", public_capital="low")) if setting == "0.3" else DynamicCGE()
    dyn.baseline()
    return d, fx, dyn


def zero_changes(years):
    return {y: dict(oil_pct=0.0, remit_pct=0.0, fdi_usd_m=0.0) for y in years}


def gaps(dyn, sim):
    c = dyn.compare(dyn.base, sim)
    return np.array([c.loc[y, "gdp_gap_pct"] for y in (2027, 2028, 2029, 2030)])


def main():
    dd = SC.DisasterDraw.from_data()
    gdp, se = d1(dd)
    d2(dd, gdp, se)
    d3(dd)

    d, fx, dyn = setup("0.3")
    st_off = SC.StochasticCGE(dyn, d, php_per_usd=fx, oil="history")
    st_zero = SC.StochasticCGE(dyn, d, php_per_usd=fx, oil="history", disasters=dataclasses.replace(dd, scale=0.0))
    st_on = SC.StochasticCGE(dyn, d, php_per_usd=fx, oil="history", disasters=dd)
    r_off, r_zero, r_on = (s.run(n=3, seed=20261014) for s in (st_off, st_zero, st_on))
    ext = ["oil_pct", "remit_pct", "fdi_usd_m"]
    g1 = float((r_off.draws - r_zero.draws).abs().to_numpy().max())
    g2 = float((r_off.shocks[ext] - r_on.shocks[ext]).abs().to_numpy().max())
    moved = float((r_on.draws - r_off.draws).abs().to_numpy().max())
    report("D4 default off", g1 == 0.0 and g2 == 0.0 and moved > 0 and "typhoon_damage_pct_gdp" not in r_off.shocks,
           f"off vs zero damage: largest gap {g1:.1e}; external shocks with the draw on vs off: {g2:.1e}; the draw on moves "
           f"results by up to {moved:.3f} (so it is live); no typhoon column when off")

    rz = st_on.run(n=2, seed=20261014, zero_variance=True)
    gz = float(rz.draws.abs().to_numpy().max())
    report("D5 zero variance = baseline", gz < 1e-9 and "typhoon_damage_pct_gdp" not in rz.shocks,
           f"largest gap {gz:.1e} with the typhoon draw on (no damage drawn under zero variance)")

    s = 0.30                                          # a season 0.30% of GDP above the normal year (about 2021's size)
    m = dyn.m
    agri = [a for a in PSA_INDUSTRIES["Agriculture, forestry, and fishing"] if a in m.A]
    x = dd.agri_share * s / 100 / (sum(float(m.QA0[m.A.index(a)]) for a in agri) / ML.sam_gdp(m))
    kg = (1 - dd.agri_share) * s / 100 * float(dyn.base.table.loc[2027, "real_gdp"])
    had_kg = "kg_loss" in dyn.pc
    row = st_on.run_path(zero_changes(st_on.years), {2027: s})
    got = np.array([row[f"GDP gap % {y}"] for y in (2027, 2028, 2029, 2030)])
    restored = ("kg_loss" in dyn.pc) == had_kg
    dyn.pc["kg_loss"] = {2027: kg}
    try:
        ref = gaps(dyn, dyn.scenario({2027: {"tfp_scale": {a: 1 - x for a in agri}}}))
    finally:
        dyn.pc.pop("kg_loss", None)
    gap6 = float(np.abs(got - ref).max())
    report("D6 mapping, public capital on", gap6 < 1e-9 and restored,
           f"agricultural productivity {1 - x:.5f} (x = {x:.3%} of their output), public capital destroyed {kg:.2f} (SAM ₱ bn); "
           f"GDP gaps 2027-2030 {np.round(got, 4).tolist()} against the hand-built scenario (largest gap {gap6:.1e}); "
           f"the model's kg_loss restored: {restored}")
    neg = st_on.run_path(zero_changes(st_on.years), {2027: -0.10})
    report("D7 signs", got[0] < 0 and got[1] < 0 and neg["GDP gap % 2027"] > 0,
           f"+{s}% of GDP: GDP {got[0]:+.4f}% (2027), {got[1]:+.4f}% (2028); -0.10%: GDP {neg['GDP gap % 2027']:+.4f}% (2027)")

    d0, fx0, dyn2 = setup("0.2")
    st2 = SC.StochasticCGE(dyn2, d0, php_per_usd=fx0, oil="history", disasters=dd)
    m2 = dyn2.m
    agri2 = [a for a in PSA_INDUSTRIES["Agriculture, forestry, and fishing"] if a in m2.A]
    x2 = dd.agri_share * s / 100 / (sum(float(m2.QA0[m2.A.index(a)]) for a in agri2) / ML.sam_gdp(m2))
    f = (1 - (1 - dd.agri_share) * s / 100 / PUBLIC_CAPITAL["low"]["kg_gdp"]) ** PUBLIC_CAPITAL["low"]["phi"]
    row2 = st2.run_path(zero_changes(st2.years), {2027: s})
    got2 = np.array([row2[f"GDP gap % {y}"] for y in (2027, 2028, 2029, 2030)])
    ref2 = gaps(dyn2, dyn2.scenario({2027: {"tfp_scale": {a: (1 - x2 if a in agri2 else 1.0) * f for a in m2.A}}}))
    gap8 = float(np.abs(got2 - ref2).max())
    report("D8 mapping, 0.2 settings", gap8 < 1e-9 and not st2._pubcap,
           f"one-year productivity factor {f:.6f} in every activity, agriculture also {1 - x2:.5f}; GDP gaps "
           f"{np.round(got2, 4).tolist()} (largest gap to the hand-built scenario {gap8:.1e})")

    bad = 0
    for kw in (dict(centre="normal"), dict(agri_share=1.5), dict(scale=-1.0)):
        try:
            dataclasses.replace(dd, **kw)
        except ValueError:
            bad += 1
    try:
        SC.DisasterDraw.from_data(frequency="1970-2022")
    except ValueError:
        bad += 1
    try:
        SC.StochasticCGE(dyn, d, php_per_usd=fx, oil="history", disasters="pagasa")
    except TypeError:
        bad += 1
    report("D9 refusals", bad == 5, f"{bad} of 5 bad settings refused")

    print(f"\n{sum(RESULTS)} of {len(RESULTS)} tests passed.")
    sys.exit(0 if all(RESULTS) else 1)


if __name__ == "__main__":
    main()
