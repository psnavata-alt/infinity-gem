"""Labour hoarding: test three alternatives to paid labour hoarding against PSA data (0.3.11.dev0, 19 Oct 2026).

Why: PSA's 2026 data show construction output falling much more than construction jobs (real GVA H1 2026 -9.5% y/y,
LFS jobs Jan-Aug -0.8%). The 19 Oct night read this as paid labour hoarding
(a review note (not included)). Most Philippine construction workers are project
employees (DOLE DO 19, 1993), the workers least likely to be hoarded, so the literature note
(a reference copy (not distributed) section 3) lists three other explanations:
  A. mix: the fall is in public works (more machines and materials per worker); private building held up;
  B. own-account work: displaced wage workers stay in construction (or elsewhere) as self-employed, on lower pay;
  C. measurement/timing: PSA's construction output and the LFS cover different months, or output is measured from
     spending data that fell more than work on site.
Published PSA tables only (no microdata; OpenSTAT has no industry x class-of-worker or industry x hours table).

Run:  py scenarios/labour_hoarding_alternatives.py   -> outputs/labour_hoarding_alternatives_<stamp>.md
"""
import datetime as dt
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "outputs"
sys.stdout.reconfigure(encoding="utf-8")

MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"]


def wide_quarterly(path, label_col):
    """PSA quarterly table (rows = items, columns = '<price basis> YYYY Qn') -> long frame."""
    df = pd.read_csv(path, comment="#")
    df[label_col] = df[label_col].str.replace(r"^\.+", "", regex=True).str.strip()
    long = df.melt(id_vars=label_col, var_name="col", value_name="value")
    m = long["col"].str.extract(r"^(?P<basis>.*?)\s+(?P<year>\d{4})\s+Q(?P<q>\d)$")
    long = pd.concat([long, m], axis=1).dropna(subset=["year"])
    long["year"] = long["year"].astype(int)
    long["q"] = long["q"].astype(int)
    long["value"] = pd.to_numeric(long["value"], errors="coerce")
    return long


def monthly_lfs(path):
    df = pd.read_csv(path, comment="#")
    df["Year"] = df["Year"].astype(int)
    df["m"] = df["Month"].map({name: i + 1 for i, name in enumerate(MONTHS)})
    for c in df.columns[2:]:
        if c != "m":
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df.dropna(subset=[df.columns[2]])


def pct(a, b):
    return 100.0 * (a / b - 1.0)


lines = []


def say(text=""):
    print(text)
    lines.append(text)


stamp = dt.datetime.now().strftime("%Y%m%d_%H%M")
say("# Labour hoarding: three alternatives to paid labour hoarding, tested on PSA's published tables")
say("")
say(f"Run {dt.datetime.now():%Y-%m-%d %H:%M} by `scenarios/labour_hoarding_alternatives.py` (Infinity GEM 0.3). "
    "Data: PSA OpenSTAT files already in `data/raw/` (sources and download times in each file's header).")

# ---------------------------------------------------------------- A. public vs private construction
gf = wide_quarterly(RAW / "macro" / "PSA_OpenSTAT_0542B5BCNQ1_construction_GFCF_by_sector_quarterly_2000-2026.csv",
                    "Institutional Sector")
bases = sorted(gf["basis"].unique())
const = [b for b in bases if "Constant" in b]
basis = const[0] if const else bases[0]
g = gf[gf["basis"] == basis].pivot_table(index=["year", "q"], columns="Institutional Sector", values="value")
last_year = int(g.dropna(how="all").index.get_level_values(0).max())
q_last = int(g.loc[last_year].dropna(how="all").index.max())
quarters = list(range(1, q_last + 1))
say("")
say(f"## A. Mix: public and private construction ({basis}, million pesos; PSA 0542B5BCNQ1)")
say("")
say(f"Same quarters each year: Q1-Q{q_last}.")
say("")
cols = list(g.columns)
say("| Item | " + " | ".join(str(y) for y in range(last_year - 3, last_year + 1)) + f" | y/y {last_year} | y/y {last_year - 1} |")
say("|---|" + "---|" * 6)
share_rows = {}
for c in cols:
    vals = {y: g.loc[(y, quarters), c].sum() for y in range(last_year - 3, last_year + 1)}
    share_rows[c] = vals
    say(f"| {c} | " + " | ".join(f"{vals[y]:,.0f}" for y in vals) +
        f" | {pct(vals[last_year], vals[last_year - 1]):+.1f}% | {pct(vals[last_year - 1], vals[last_year - 2]):+.1f}% |")
tot_key = next(c for c in cols if c.startswith("Gross Fixed Capital Formation"))
gov_key = next(c for c in cols if c.startswith("General government"))
priv_keys = [c for c in cols if c.startswith("Financial") or c.startswith("Households")]
gov = share_rows[gov_key]
tot = share_rows[tot_key]
priv = {y: sum(share_rows[k][y] for k in priv_keys) for y in tot}
d_tot = tot[last_year] - tot[last_year - 1]
d_gov = gov[last_year] - gov[last_year - 1]
d_priv = priv[last_year] - priv[last_year - 1]
gshare = gov[last_year - 1] / tot[last_year - 1]
say("")
say(f"- Government's share of construction in {last_year - 1}: **{100 * gshare:.1f}%**. "
    f"Change {last_year - 1} to {last_year}: government {pct(gov[last_year], gov[last_year - 1]):+.1f}%, "
    f"private (corporations + households) {pct(priv[last_year], priv[last_year - 1]):+.1f}%, "
    f"total {pct(tot[last_year], tot[last_year - 1]):+.1f}%.")
say(f"- Share of the total change due to government: {100 * d_gov / d_tot:.0f}% "
    f"(private: {100 * d_priv / d_tot:.0f}%).")

# What labour intensity of public works would reconcile jobs with output?
emp = monthly_lfs(RAW / "lfs" / "PSA_OpenSTAT_0101B3FEMP2_LFS_employed_by_major_industry_2012-2026.csv")
last_m = int(emp[emp["Year"] == emp["Year"].max()]["m"].max())
months = list(range(1, last_m + 1))
ey = emp["Year"].max()


def lfs_avg(df, col, year):
    sub = df[(df["Year"] == year) & (df["m"].isin(months))]
    return sub[col].mean(), len(sub)


c_now, n_now = lfs_avg(emp, "Construction", ey)
c_prev, _ = lfs_avg(emp, "Construction", ey - 1)
t_now, _ = lfs_avg(emp, "TOTAL", ey)
t_prev, _ = lfs_avg(emp, "TOTAL", ey - 1)
jobs_g = pct(c_now, c_prev)
gov_g = pct(gov[last_year], gov[last_year - 1]) / 100
priv_g = pct(priv[last_year], priv[last_year - 1]) / 100
# jobs growth = w*gov_g + (1-w)*priv_g, where w = public works' share of construction JOBS; solve for w
w_needed = (jobs_g / 100 - priv_g) / (gov_g - priv_g) if gov_g != priv_g else np.nan
say("")
say(f"- LFS construction jobs, average of {n_now} survey months Jan-{MONTHS[last_m - 1][:3]} {ey}: "
    f"{c_now:,.0f} thousand, **{jobs_g:+.1f}% y/y** (all jobs {pct(t_now, t_prev):+.1f}%).")
say(f"- **If jobs simply followed each sector's output** (no hoarding), the LFS change needs public works to hold "
    f"**{100 * w_needed:.0f}% of construction jobs** against {100 * gshare:.0f}% of construction spending, "
    f"i.e. public works about {(w_needed / (1 - w_needed)) / (gshare / (1 - gshare)):.2f} times as labour-intensive "
    "per peso as private building. Values far below 1 favour the mix explanation; about 1 or more rule it out.")

# ---------------------------------------------------------------- B. own-account absorption (economy-wide)
cw = monthly_lfs(RAW / "lfs" / "PSA_OpenSTAT_0131B3FEMP5_LFS_employed_by_class_of_worker_2005-2026.csv")
say("")
say(f"## B. Own-account work: class of worker, all industries (PSA 0131B3FEMP5; thousands; Jan-{MONTHS[last_m - 1][:3]} averages)")
say("")
say(f"| Class of worker | {ey - 2} | {ey - 1} | {ey} | change {ey} (thousand) | y/y {ey} | y/y {ey - 1} |")
say("|---|---|---|---|---|---|---|")
for col in cw.columns[2:]:
    if col == "m":
        continue
    v = {y: lfs_avg(cw, col, y)[0] for y in (ey - 2, ey - 1, ey)}
    say(f"| {col} | {v[ey - 2]:,.0f} | {v[ey - 1]:,.0f} | {v[ey]:,.0f} | {v[ey] - v[ey - 1]:+,.0f} | "
        f"{pct(v[ey], v[ey - 1]):+.1f}% | {pct(v[ey - 1], v[ey - 2]):+.1f}% |")
model_job_loss = 0.257 * c_prev  # the model's construction job loss at h = 0 (relative -25.7 pp), in thousands
say("")
say(f"- For scale: the central 2026 setting of 18 Oct 2026 (h = 0) removes about 26% of construction jobs, about **{model_job_loss:,.0f} "
    "thousand** workers. Under explanation B, most of them would show up as self-employed or unpaid family workers.")

# ---------------------------------------------------------------- C. timing: monthly construction jobs, quarterly output
say("")
say("## C. Timing: construction jobs by survey month and construction output by quarter")
say("")
gva = wide_quarterly(RAW / "macro" / "PSA_OpenSTAT_0052B5BPRQ1_GDP_by_industry_quarterly.csv", "Industry")
gb = sorted(gva["basis"].unique())
gbasis = next((b for b in gb if "Constant" in b), gb[0])
gq = gva[(gva["basis"] == gbasis)].pivot_table(index=["year", "q"], columns="Industry", values="value")
con_col = next(c for c in gq.columns if c == "Construction")
gdp_col = next((c for c in gq.columns if re.match(r"(?i)^gross domestic product", c)), None)
say(f"| Quarter | Construction GVA y/y ({gbasis}) | GDP y/y | LFS construction jobs y/y (months in quarter) | LFS all jobs y/y |")
say("|---|---|---|---|---|")
for y in (ey - 1, ey):
    for q in range(1, 5):
        if (y, q) not in gq.index or (y - 1, q) not in gq.index or pd.isna(gq.loc[(y, q), con_col]):
            continue
        cg = pct(gq.loc[(y, q), con_col], gq.loc[(y - 1, q), con_col])
        dg = pct(gq.loc[(y, q), gdp_col], gq.loc[(y - 1, q), gdp_col]) if gdp_col else np.nan
        ms = [3 * (q - 1) + k for k in (1, 2, 3)]
        a = emp[(emp["Year"] == y) & emp["m"].isin(ms)]
        b = emp[(emp["Year"] == y - 1) & emp["m"].isin(ms)]
        jm = a.merge(b, on="m", suffixes=("", "_p"))
        if len(jm):
            jg = pct(jm["Construction"].mean(), jm["Construction_p"].mean())
            tg = pct(jm["TOTAL"].mean(), jm["TOTAL_p"].mean())
            say(f"| {y} Q{q} | {cg:+.1f}% | {dg:+.1f}% | {jg:+.1f}% ({len(jm)}) | {tg:+.1f}% |")
        else:
            say(f"| {y} Q{q} | {cg:+.1f}% | {dg:+.1f}% | (no LFS months) | |")
say("")
say("Monthly LFS construction jobs (thousands):")
say("")
say("| Month | " + " | ".join(str(y) for y in (ey - 2, ey - 1, ey)) + " |")
say("|---|---|---|---|")
for m in range(1, 13):
    vals = []
    for y in (ey - 2, ey - 1, ey):
        r = emp[(emp["Year"] == y) & (emp["m"] == m)]
        vals.append(f"{r['Construction'].iloc[0]:,.0f}" if len(r) else "")
    if any(vals):
        say(f"| {MONTHS[m - 1][:3]} | " + " | ".join(vals) + " |")

# ---------------------------------------------------------------- D. construction pay vs all
pay = pd.read_csv(RAW / "lfs" / "PSA_OpenSTAT_0161B3FADB2_LFS_average_daily_basic_pay_by_industry_2016-2026.csv",
                  comment="#")
pay["Major Industry Group"] = pay["Major Industry Group"].str.replace(r"^\.+", "", regex=True).str.strip()
pay = pay.set_index("Major Industry Group")
say("")
say("## D. Pay of construction wage and salary workers (PSA 0161B3FADB2, average daily basic pay, pesos)")
say("")
rounds = [c for c in pay.columns if re.match(r"\d{4} (January|April|July|October)$", c)]
say("| Round | All industries | Construction | Construction y/y | All y/y |")
say("|---|---|---|---|---|")
for c in rounds:
    y, mon = c.split()
    prev = f"{int(y) - 1} {mon}"
    if int(y) < ey - 1 or prev not in pay.columns:
        continue
    a, k = float(pay.loc["TOTAL", c]), float(pay.loc["Construction", c])
    if a == 0:
        continue
    ap, kp = float(pay.loc["TOTAL", prev]), float(pay.loc["Construction", prev])
    say(f"| {c} | {a:,.2f} | {k:,.2f} | {pct(k, kp):+.1f}% | {pct(a, ap):+.1f}% |")

# ---------------------------------------------------------------- E. history: jobs per peso, public vs private
# y/y growth of LFS construction jobs on the contributions of public and private construction (constant prices):
#   g_jobs = a + b_pub * (share_pub[t-4] * g_pub) + b_priv * (share_priv[t-4] * g_priv) + e
# Equal labour intensity per peso means b_pub = b_priv; b_pub / b_priv is public works' relative jobs per peso.
import statsmodels.api as sm  # noqa: E402

qrows = []
for (y, q) in g.index:
    if y < 2013 or (y - 1, q) not in g.index:
        continue
    ms = [3 * (q - 1) + k for k in (1, 2, 3)]
    a = emp[(emp["Year"] == y) & emp["m"].isin(ms)]
    b = emp[(emp["Year"] == y - 1) & emp["m"].isin(ms)]
    jm = a.merge(b, on="m", suffixes=("", "_p"))  # same survey months in both years
    if not len(jm):
        continue
    gv, pv = g.loc[(y, q)], g.loc[(y - 1, q)]
    pub0, priv0 = pv[gov_key], sum(pv[k] for k in priv_keys)
    pub1, priv1 = gv[gov_key], sum(gv[k] for k in priv_keys)
    tot0 = pub0 + priv0
    qrows.append({
        "year": y, "q": q, "months": len(jm),
        "g_jobs": np.log(jm["Construction"].mean() / jm["Construction_p"].mean()),
        "g_all_jobs": np.log(jm["TOTAL"].mean() / jm["TOTAL_p"].mean()),
        "c_pub": (pub0 / tot0) * np.log(pub1 / pub0),
        "c_priv": (priv0 / tot0) * np.log(priv1 / priv0),
        "g_tot": np.log((pub1 + priv1) / tot0),
    })
H = pd.DataFrame(qrows)
H["covid"] = ((H["year"] == 2020) & (H["q"] >= 2)) | (H["year"] == 2021)
say("")
say("## E. History: how construction jobs followed public and private construction, 2013-2026")
say("")
say(f"Quarterly y/y log changes, same LFS survey months in both years ({len(H)} quarters, "
    f"{int(H['year'].min())}Q{int(H.loc[H.index[0], 'q'])}-{int(H['year'].max())}Q{int(H.loc[H.index[-1], 'q'])}). "
    "Contributions = previous-year share x growth. Newey-West (4 lags) standard errors. "
    "Before 2021 the LFS has one survey month per quarter (January, April, July, October), so jobs are noisy.")
say("")
say("| Specification | b_pub (s.e.) | b_priv (s.e.) | b_pub / b_priv | Wald b_pub = b_priv (p) | b_total (s.e.) | quarters |")
say("|---|---|---|---|---|---|---|")
specs = {
    "excluding COVID (2020Q2-2021Q4)": H[~H["covid"]],
    "excluding COVID, controlling for all-jobs growth": H[~H["covid"]],
    "all quarters, COVID dummy": H,
}
for name, d in specs.items():
    X = d[["c_pub", "c_priv"]].copy()
    if "controlling" in name:
        X["g_all_jobs"] = d["g_all_jobs"]
    if "dummy" in name:
        X["covid"] = d["covid"].astype(float)
    X = sm.add_constant(X)
    res = sm.OLS(d["g_jobs"], X).fit(cov_type="HAC", cov_kwds={"maxlags": 4})
    w = res.wald_test("c_pub = c_priv", scalar=True)
    Xt = sm.add_constant(d[["g_tot"]].assign(**({"covid": d["covid"].astype(float)} if "dummy" in name else {})))
    if "controlling" in name:
        Xt["g_all_jobs"] = d["g_all_jobs"]
    rt = sm.OLS(d["g_jobs"], Xt).fit(cov_type="HAC", cov_kwds={"maxlags": 4})
    bp, bv = res.params["c_pub"], res.params["c_priv"]
    say(f"| {name} | {bp:.2f} ({res.bse['c_pub']:.2f}) | {bv:.2f} ({res.bse['c_priv']:.2f}) | "
        f"{bp / bv:.2f} | {float(w.pvalue):.2f} | {rt.params['g_tot']:.2f} ({rt.bse['g_tot']:.2f}) | {len(d)} |")
say("")
say("Reading: b_total is the elasticity of construction jobs to construction spending; 1 = jobs follow output "
    "one for one (the central 2026 setting of 18 Oct 2026 behaves like about 2: the model's construction jobs fall about twice as much as its "
    "output). b_pub / b_priv about 0.2 would be needed for the mix alone to explain 2026 (section A).")
H.to_csv(OUT / f"labour_hoarding_alternatives_{stamp}_history.csv", index=False)

OUT.mkdir(exist_ok=True)
path = OUT / f"labour_hoarding_alternatives_{stamp}.md"
path.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"\nSaved {path}")
