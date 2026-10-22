"""19 Oct 2026: the CGE's short-run industry pattern against PSA's 2026 data.

Why: the FIES-LFS earnings link (scenarios/lfs_link_row.py, 18 Oct) showed that the model puts a 26% job loss on construction
in 2026 while PSA's LFS shows construction employment almost unchanged. This script asks where the gap is, industry by
industry, for the central 2026 case (all four shocks against the no-shock path, 2026):
- output: the model's real value added against PSA's real GVA (0052B5BPRQ1, H1 2026 on H1 2025);
- jobs: the model's labour input against the LFS's employed persons (0101B3FEMP2, January-August);
- output per worker, and labour income against the LFS wage bill (employed persons x daily basic pay, where PSA has the pay).
The data mix the shocks with normal growth, so each change is also shown relative to the economy's total: what is common to
every industry drops out.
Run (Git Bash):  export INFINITY_GEM_SCENARIO_SAM=own; py scenarios/industry_pattern_vs_data.py [--hoard=0.85]
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import _common                                                       # noqa: E402
import combined_revised as CR                                        # noqa: E402
from lfs_link_row import lfs_2026_by_industry                        # noqa: E402
from infinity_gem import paths                                           # noqa: E402
from infinity_gem.dynamic import PSA_INDUSTRIES                          # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

GVA_FILE = HERE.parent / "data" / "raw" / "macro" / "PSA_OpenSTAT_0052B5BPRQ1_GDP_by_industry_quarterly.csv"   # downloaded 19 Oct 2026


def psa_gva_h1_2026() -> tuple[pd.Series, float]:
    """PSA real GVA (constant 2018 prices), H1 2026 against H1 2025, % by the 16 industries; and real GDP's."""
    d = pd.read_csv(GVA_FILE, comment="#").set_index("Industry")
    d.index = d.index.str.strip(". ")
    q = lambda y: d[[f"At Constant 2018 Prices {y} Q{i}" for i in (1, 2)]].apply(pd.to_numeric, errors="coerce").sum(axis=1)
    g = (q(2026) / q(2025) - 1) * 100
    return g.reindex(list(PSA_INDUSTRIES)), float(g["Gross Domestic Product"])


def model_pattern(m, b, s) -> tuple[pd.DataFrame, dict]:
    """Model, 2026, % against the no-shock path, by the 16 industries: real value added (base prices), labour input (all skills at
    base wages, hoarded workers included when the option is on), labour income, output per worker."""
    A, F = m.A, m.F
    labs = [i for i, f_ in enumerate(F) if f_.startswith("flab")]
    pva0 = np.asarray(b["PVA"], float)
    va0, va1 = pva0 * np.asarray(b["QVA"], float), pva0 * np.asarray(s["QVA"], float)
    emp = lambda sol: np.asarray(sol["QF"], float)[labs] + (np.asarray(sol["QFH"], float)[labs] if "QFH" in sol else 0.0)
    W0 = np.asarray(b["W"], float)[labs]
    E0, E1 = emp(b), emp(s)
    W1 = np.asarray(s["W"], float)[labs]
    rows = {}
    for name, acts in PSA_INDUSTRIES.items():
        ix = [A.index(a) for a in acts if a in A]
        if not ix:
            continue
        v = va1[ix].sum() / va0[ix].sum() - 1
        e = (W0[:, ix] * E1[:, ix]).sum() / (W0[:, ix] * E0[:, ix]).sum() - 1
        inc = (W1[:, ix] * E1[:, ix]).sum() / (W0[:, ix] * E0[:, ix]).sum() - 1
        rows[name] = {"model output (%)": v * 100, "model jobs (%)": e * 100, "model labour income (%)": inc * 100,
                      "model output per worker (%)": ((1 + v) / (1 + e) - 1) * 100}
    tot = {"output": (va1.sum() / va0.sum() - 1) * 100,
           "jobs": ((W0 * E1).sum() / (W0 * E0).sum() - 1) * 100,
           "labour income": ((W1 * E1).sum() / (W0 * E0).sum() - 1) * 100}
    return pd.DataFrame(rows).T, tot


def main():
    hoard = next((float(a.split("=", 1)[1]) for a in sys.argv if a.startswith("--hoard=")), 0.0)
    cal = pd.read_csv(_common.calibration_file(), index_col=0)
    beta = float(cal.loc["central (e)", "beta"])
    kw = {"hoarding": hoard} if hoard else {}
    R = CR.Runs("low", wage_curve=beta, **kw)
    piece, _ = R.pieces()
    clean, sim = R.run(set(), piece=piece), R.run(set(CR.SHOCKS), piece=piece)
    m, b, s = R.d.ms, clean.solutions[2026], sim.solutions[2026]
    mp, mt = model_pattern(m, b, s)
    gva, gdp = psa_gva_h1_2026()
    lfs = lfs_2026_by_industry()
    emp_tot = lfs.attrs["total employment 2026 (% y/y)"]
    pay_tot = lfs.attrs["total daily pay 2026 (% y/y)"]
    t = mp.copy()
    t["PSA output (%)"] = gva
    t["LFS jobs (%)"] = lfs["LFS employment 2026 (% y/y, Jan-Aug)"]
    t["PSA output per worker (%)"] = ((1 + t["PSA output (%)"] / 100) / (1 + t["LFS jobs (%)"] / 100) - 1) * 100
    t["LFS wage bill (%)"] = ((1 + t["LFS jobs (%)"] / 100) * (1 + lfs["LFS daily basic pay 2026 (% y/y, Jan/Apr/Jul)"] / 100) - 1) * 100
    rel = pd.DataFrame({
        "model output": t["model output (%)"] - mt["output"],
        "PSA output": t["PSA output (%)"] - gdp,
        "model jobs": t["model jobs (%)"] - mt["jobs"],
        "LFS jobs": t["LFS jobs (%)"] - emp_tot,
        "model labour income": t["model labour income (%)"] - mt["labour income"],
        "LFS wage bill": t["LFS wage bill (%)"] - ((1 + emp_tot / 100) * (1 + pay_tot / 100) - 1) * 100,
    })
    # how much jobs move with output across industries (slope of relative jobs on relative output), model and data
    ok = rel[["model output", "model jobs", "PSA output", "LFS jobs"]].dropna()
    slope = lambda y, x: float(np.polyfit(ok[x], ok[y], 1)[0])
    corr_o = float(np.corrcoef(ok["model output"], ok["PSA output"])[0, 1])
    corr_j = float(np.corrcoef(ok["model jobs"], ok["LFS jobs"])[0, 1])
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M")
    tag = _common.out_tag() + (f"_hoard{hoard:g}" if hoard else "")
    out = paths.output_dir() / f"industry_pattern_vs_data_{stamp}{tag}.md"
    L = [f"# Labour hoarding: the model's 2026 industry pattern against PSA's data ({dt.datetime.now():%d %B %Y, %H:%M})", "",
         f"**NOT FOR CITATION** (Infinity GEM 0.3). SAM: `{CR.SAM_VARIANT}`; wage-curve beta {beta:.3f}; labour hoarding "
         f"{hoard:g}. Model: the central 2026 case, all four shocks against the no-shock path, 2026. Data: PSA real GVA "
         f"H1 2026 on H1 2025 (`{GVA_FILE.name}`), LFS employed persons January-August, LFS daily basic pay (January, April, "
         "July; six industries). Script `scenarios/industry_pattern_vs_data.py`.", "",
         f"Totals: model output {mt['output']:+.2f}%, jobs {mt['jobs']:+.2f}%, labour income {mt['labour income']:+.2f}%; "
         f"PSA GDP {gdp:+.2f}%, LFS employment {emp_tot:+.2f}%, daily pay {pay_tot:+.2f}%.", "",
         "## Changes relative to the economy's total (percentage points)", "",
         rel.to_markdown(floatfmt="+.2f"), "",
         f"- Across industries, relative jobs move with relative output by a slope of **{slope('model jobs', 'model output'):.2f}** in the "
         f"model and **{slope('LFS jobs', 'PSA output'):.2f}** in the data.",
         f"- Correlation of the industry pattern, model against data: output {corr_o:.2f}; jobs {corr_j:.2f}.", "",
         "## Levels (% change)", "", t.to_markdown(floatfmt="+.2f")]
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    print("\nsaved", out)


if __name__ == "__main__":
    main()
