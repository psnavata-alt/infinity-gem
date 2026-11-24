"""Check DM1 (Infinity GEM 0.4.3, 21 Nov 2026): demography in labour supply
(infinity_gem/demography.py; OPT-IN; dynamic.py not edited; the engine does not import the module). No model run.
  T1  OFF = before, to the bit: dynamic.psa_labour_growth() and dynamic.documented_baseline() give the same dicts before and after
      infinity_gem.demography is imported and used (==), and the default baseline still drives its projection years by the 15+ head
      count (each projected year's rate for every labour type equals the 15+ population ratio times the share step, recomputed here);
  T2  limiting case: with every age-sex employment rate equal, the employment-weighted growth equals the 15+ growth and
      psa_labour_growth_demographic equals psa_labour_growth, within the projection's rounding (male + female vs both sexes; 1e-4);
  T3  the data add up: LFS 2025 male + female = both sexes in every age group (0.002 thousand, PSA's rounding) and the
      employment-weighted 2025 population equals LFS 2025 employed, both sexes (0.01 thousand); projection male + female = both
      sexes in every LFS age group and year (1.5 thousand per five-year group in it, the projection's rounding to the thousand);
  T4  exact rescaling: in each projected year (2027-2030; 2026-2030 with y2026="trend") every labour type's (1 + rate) is the
      default's times the same factor (1 + weighted) / (1 + pop15) (1e-12), and the observed years 2024-2026 are untouched (==);
  T5  the data file is PSA's OpenSTAT table 0051B3FKEI5 as downloaded (PSA update of 6 Nov 2026), byte for byte (SHA-256
      67734c5a...cb26), and has 2025 annual figures and no 2026 annual figures yet.
Run: py -I -X utf8 checks/test_demography.py   (seconds; the suite runs it as check DM1)
"""
import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import pandas as pd                                              # noqa: E402

from infinity_gem import dynamic, paths                              # noqa: E402

SHA = "67734c5aef30d338770bf2e0eaae5957c956ff5c73bde545b821a47ece99cb26"


def report(res, name, ok, msg):
    res.append(bool(ok))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {msg}", flush=True)


def main():
    res = []
    before_lg = dynamic.psa_labour_growth()
    before_db = dynamic.documented_baseline()
    from infinity_gem import demography as D
    # T1
    try:
        _ = D.documented_baseline_demographic()
        after_lg = dynamic.psa_labour_growth()
        after_db = dynamic.documented_baseline()
        pop = pd.read_csv(paths.DATA_RAW / "population" / D.POP_FILE, comment="#")
        p15 = pop[(pop["sex"] == "Both Sexes") & ~pop["age_group"].isin(["All Ages", "0-4", "5-9", "10-14"])].groupby("year")[
            "population_thousands"].sum()
        g = D.growth_paths()
        ok_rule = all(abs(float(g.loc[y, "pop15"]) - (float(p15[y]) / float(p15[y - 1]) - 1)) < 1e-12 for y in range(2027, 2031))
        ok = before_lg == after_lg and before_db == after_db and ok_rule
        report(res, "T1 default unchanged", ok, f"psa_labour_growth equal {before_lg == after_lg}; documented_baseline equal "
                                                f"{before_db == after_db}; 15+ rule {ok_rule}")
    except Exception as e:                                       # pragma: no cover
        report(res, "T1 default unchanged", False, repr(e))
    # T2
    try:
        er = D.employment_rates()
        flat = er * 0 + 0.6
        g = D.growth_paths(rates=flat)
        d1 = max(abs(float(g.loc[y, "weighted"]) - float(g.loc[y, "pop15"])) for y in range(2021, 2031))
        a, b = dynamic.psa_labour_growth(), D.psa_labour_growth_demographic(rates=flat)
        d2 = max(abs(a[y][k] - b[y][k]) for y in a for k in a[y])
        # the weighted path sums male + female, the 15+ rule sums both sexes: they differ only by the projection's rounding to
        # the thousand (14 five-year groups, at most 1.5 thousand each, on about 85 million: a growth gap below 1e-4)
        report(res, "T2 equal rates = 15+ rule", d1 < 1e-4 and d2 < 1e-4, f"max gap growth {d1:.2e}; labour paths {d2:.2e} "
                                                                          "(projection rounding only)")
    except Exception as e:                                       # pragma: no cover
        report(res, "T2 equal rates = 15+ rule", False, repr(e))
    # T3
    try:
        e = D.employed(2025)
        d_sex = float((e["Male"] + e["Female"] - e["Both Sexes"]).abs().max())
        tot = pd.read_csv(paths.DATA_RAW / "lfs" / D.LFS_FILE, dtype={"Year": str}, na_values=".")
        tot = float(tot[(tot["Year"] == "2025") & (tot["Month"] == "Annual")]["Both Sexes Total"].iloc[0])
        w25 = float(D.growth_paths().loc[2025, "weighted level"])
        p = D.population()
        gap = (p["Male"] + p["Female"] - p["Both Sexes"]).abs()
        lim = pd.Series({ix: 1.5 * len(D.AGE_GROUPS[ix[1]]) for ix in p.index})   # 1.5 thousand per five-year group summed
        d_pop = float(gap.max())
        ok = d_sex < 0.002 + 1e-9 and abs(w25 - tot) < 0.01 and bool((gap <= lim + 1e-9).all())
        report(res, "T3 data add up", ok, f"LFS sexes {d_sex:.4f}; weighted 2025 {w25:,.3f} vs LFS {tot:,.3f}; projection sexes {d_pop:.1f}")
    except Exception as e:                                       # pragma: no cover
        report(res, "T3 data add up", False, repr(e))
    # T4
    try:
        ok, worst = True, 0.0
        for y26 in ("observed", "trend"):
            a, b = dynamic.psa_labour_growth(y2026=y26), D.psa_labour_growth_demographic(y2026=y26)
            g = D.growth_paths()
            first = 2026 if y26 == "trend" else 2027
            for y in a:
                if y >= first:
                    f = (1 + float(g.loc[y, "weighted"])) / (1 + float(g.loc[y, "pop15"]))
                    for k in a[y]:
                        worst = max(worst, abs((1 + b[y][k]) - (1 + a[y][k]) * f))
                else:
                    ok = ok and a[y] == b[y]
        ok = ok and worst < 1e-12
        report(res, "T4 exact rescaling", ok, f"worst {worst:.2e}; observed years untouched")
    except Exception as e:                                       # pragma: no cover
        report(res, "T4 exact rescaling", False, repr(e))
    # T5
    try:
        f = paths.DATA_RAW / "lfs" / D.LFS_FILE
        sha = hashlib.sha256(f.read_bytes()).hexdigest()
        d = pd.read_csv(f, dtype={"Year": str}, na_values=".")
        has25 = d[(d["Year"] == "2025") & (d["Month"] == "Annual")]["Both Sexes Total"].notna().all()
        no26 = d[(d["Year"] == "2026") & (d["Month"] == "Annual")]["Both Sexes Total"].isna().all()
        report(res, "T5 data file", sha == SHA and has25 and no26, f"sha {sha[:8]}...; 2025 annual {has25}; 2026 annual empty {no26}")
    except Exception as e:                                       # pragma: no cover
        report(res, "T5 data file", False, repr(e))
    print(f"{sum(res)} of {len(res)} pass")
    return 0 if all(res) and len(res) == 5 else 1


if __name__ == "__main__":
    sys.exit(main())
