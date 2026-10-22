"""Infinity GEM Simulator: a point-and-click front end to the Infinity GEM models.

Start it from the repository folder with:  python -m streamlit run app/simulator.py
Every number comes from app/engines.py, which calls the tested infinity_gem package; nothing is typed in here.
"""
from __future__ import annotations

import datetime as dt
import io as _io
import json
import re
import subprocess
import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from app import engines as E                     # noqa: E402
from infinity_gem import paths as P                  # noqa: E402  (0.3.2: where to save; see paths.output_dir)

BRAND = ROOT / "docs" / "branding"                 # banner, lockup and icon (docs/branding/make_banner.py)


def _brand(name):
    """A branding image, or None if the file is missing (the page still works without it)."""
    try:
        from PIL import Image
        return Image.open(BRAND / name)
    except Exception:
        return None


st.set_page_config(page_title="Infinity GEM Simulator", page_icon=_brand("infinity_gem_icon.png") or "📊", layout="wide")

UP, DOWN, MID = "#2a78d6", "#e34948", "#898781"   # diverging pair (gain / loss) and axis grey
GDP_CHOICES = {
    f"2025 pesos · GDP ₱{E.PSA_GDP[2025] / 1000:,.2f}T": E.PSA_GDP[2025],
    f"H1 2025 pesos · GDP ₱{E.PSA_GDP['H1_2025'] / 1000:,.2f}T": E.PSA_GDP["H1_2025"],
}
ENGINES = {
    "Compare all models": "Runs the same shock through every model that can take it and puts the answers side by side. Start here.",
    "CGE": "The central model: a computable general equilibrium model of the IFPRI standard type (Lofgren, Harris and Robinson 2002) "
           "on the 2023 SAM. Prices, wages, jobs, trade and the exchange rate respond; households by group. Short and long run.",
    "SAM multiplier": "Fixed prices, every round of spending counted, household incomes by group (Pyatt and Round). An upper bound "
                      "for demand shocks; no price response.",
    "Input-output (Leontief)": "Leontief models on PSA's 2018 tables (80 industries, or 16 = the LFS major groups): supply-chain detail "
                               "with prices or quantities held fixed. Upper bounds; for GDP, jobs and households use the CGE.",
    "Over time (dynamic)": "The CGE solved year by year to 2030: how long the effect of construction spending changes lasts, "
                           "and what a later catch-up recovers. New in 0.3.",
    "Quick calculator": "Bring your own multiplier or coefficient: shock x multiplier, with Infinity GEM's own multipliers shown beside it.",
    "Money and the BSP (research)": "What a BSP rate rise, or the BSP's response to an oil shock, does to output, prices and "
                                    "the poor, from the research DSGE linked to the CGE (Stage 3). Research results, "
                                    "read from the newest saved runs; not for citation. New in 0.3.12.",
}
PRESETS = {
    "(none)": {},
    "Infrastructure freeze, H2 2025 (−₱238.3 bn construction; DBM)": dict(construction=-238.3),
    "Ayuda cut, FY 2027 NEP vs FY 2026 GAA (−₱90.21 bn to the bottom 40%; DBM D.3)": dict(transfers=-90.21),
    "World oil prices +20%": dict(oil=20.0),
    "Remittances −10% (illustrative)": dict(remit=-10.0),
}


# ---------------------------------------------------------------------- helpers
@st.cache_resource(show_spinner="Loading the data and calibrating the models (first time only)…")
def warm_up(setting: str = "0.2 published"):
    E.microsim(); E.io_table(); E.sam_model(2023)
    for c in E.MAIN_CLOSURES:
        E.cge_model(c, None, setting)
    return True


@st.cache_resource(show_spinner="Loading the FIES 2023 households (first time only)…")
def household_detail():
    from infinity_gem.household import HouseholdDetail
    return HouseholdDetail()


def show_household(r: dict, key: str):
    """0.3.1: deciles, poor families and persons, food equivalents, from the same CGE run."""
    if not r.get("ok") or r.get("model") is None:
        return
    with st.expander("👪 Household detail: deciles, poor families and persons, food equivalents (new in 0.3.1)"):
        hd = household_detail()
        g = hd.group_effects(r["model"], r["base"], r["sim"])
        c1, c2 = st.columns(2)
        rank = c1.radio("Deciles", ["PSA per-person income deciles (PSA's definition)",
                                    "Families ranked by total family income"], key=f"hd_rank_{key}")
        ns = c2.toggle("Net-seller adjustment", key=f"hd_ns_{key}",
                       help="Farm and fishing families gain when the prices of what they sell rise (FIES net income from crops, "
                            "livestock and fishing). Moves income within each household group only; national totals do not change. "
                            "An approximation (an upper bound on the redistribution).")
        lfs = False
        if hd.lfs_available():
            lfs = st.toggle("Lost earnings by each worker's industry (LFS link)", key=f"hd_lfs_{key}",
                            help="PSA's FIES-LFS 2023 file (January 2024 LFS round): each family's wages and business income "
                                 "by industry. Families whose workers are in the hardest-hit industries lose more than their "
                                 "group's average, others less; group totals stay as the model has them.")
        else:
            st.caption("LFS link (lost earnings by each worker's industry): needs PSA's FIES-LFS 2023 member file on this "
                       "computer (licensed to whoever downloads it from PSADA; see infinity_gem/paths.py, FIES_LFS_DIR).")
        dec = hd.deciles(g, "psa" if rank.startswith("PSA") else "total_income", ns, lfs)
        st.markdown("**Loss by decile** (FIES 2023 families and pesos, one year). Price effect = family spending × its group's "
                    "inflation; lost income = family income × its group's fall in nominal income; both from this one model run.")
        st.dataframe(dec.round(2), width="stretch")
        if lfs:
            st.caption("Labour income by industry in this run (%), applied to each family's earnings: "
                       + "; ".join(f"{k.split(';')[0].split(',')[0]} {v:+.2f}" for k, v in g.attrs["industry_pct"].items()))
        pov = hd.poverty(g, lfs)
        st.markdown("**Families and persons below the official 2023 lines**")
        st.dataframe(fmt_table(pov.rename(index=lambda i: i + " (persons)" if "persons" in i else i)), width="stretch")
        fe = hd.food_equivalents(dec)
        st.markdown("**Food equivalents of the monthly loss of an average bottom-30% family**")
        st.dataframe(fe.round(2), width="stretch")
        st.caption("Prices: PSA, Price Situationer of Selected Agricultural Commodities, statistical tables, second phase of "
                   "September 2026 (national averages; released 30 Sept 2026). The losses are in FIES 2023 pesos, the prices are "
                   "September 2026 prices. "
                   "Not yet in: lost earnings by each worker's industry (LFS link).")
        groups = g[["inflation_pct", "income_pct", "spending_pct", "real_factor"]].rename(index=E.HH_LABEL)
        st.download_button("⬇️ Download the household detail (Excel)",
                           excel_bytes({"Deciles": dec, "Poverty": pov, "Food equivalents": fe, "Household groups": groups}),
                           file_name=f"Infinity_GEM_household_detail_{dt.date.today():%Y%m%d}.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=f"hd_dl_{key}")


def fmt(label: str, v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "–"
    if "persons" in label:
        return f"{v:,.0f}"
    return f"{v:,.2f}"


def fmt_table(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({c: [fmt(i, df.loc[i, c]) for i in df.index] for c in df.columns}, index=df.index)


def bars(df: pd.DataFrame, col: str, title: str, top: int = 12) -> alt.Chart:
    """Horizontal bars of the largest changes; blue = increase, red = decrease."""
    d = df[[col]].dropna().copy()
    d = d.reindex(d[col].abs().sort_values(ascending=False).index).head(top)
    d["name"] = d.index
    d["direction"] = d[col].apply(lambda x: "increase" if x >= 0 else "decrease")
    base = alt.Chart(d, title=title).encode(y=alt.Y("name:N", sort=alt.EncodingSortField(col, op="sum", order="ascending"), title=None,
                                                             axis=alt.Axis(labelLimit=320)))
    b = base.mark_bar(cornerRadiusEnd=4, height={"band": 0.7}).encode(
        x=alt.X(f"{col}:Q", title=col),
        color=alt.Color("direction:N", scale=alt.Scale(domain=["increase", "decrease"], range=[UP, DOWN]), legend=alt.Legend(title=None, orient="top")),
        tooltip=[alt.Tooltip("name:N", title=""), alt.Tooltip(f"{col}:Q", format=",.3f")])
    rule = alt.Chart(pd.DataFrame({"x": [0]})).mark_rule(color=MID, strokeWidth=1).encode(x="x:Q")
    return (b + rule).properties(height=alt.Step(28))   # a fixed pixel height collapses the chart in Streamlit 1.64


def validation_status():
    # only the dated reports written by checks/run_all_checks.py (validation_report_YYYYMMDD.md; since 0.3.7 _HHMM added), newest last;
    # copies such as validation_report_20261008_DEV_premerge.md sort after the date and must not be read (fixed 8 Oct 2026)
    # 0.3.2: the outputs folder and this person's own folder (users who cannot write to the repository folder save their reports there)
    reps = sorted((p for d in P.output_dirs() for p in d.glob("validation_report_*.md")
                   if re.fullmatch(r"validation_report_\d{8}(_\d{4})?\.md", p.name)), key=lambda p: (p.name, p.stat().st_mtime))
    if not reps:
        return None, "No validation report yet."
    rep = reps[-1]
    txt = rep.read_text(encoding="utf-8")
    m = re.search(r"\*\*(\d+) of (\d+) checks passed", txt)
    stamp = re.search(r"validation report, ([\d\- :]+)", txt)
    newest = max(p.stat().st_mtime for p in list((ROOT / "infinity_gem").glob("*.py")) + list((ROOT / "data" / "raw").rglob("*.*"))
                 + [ROOT / "app" / "engines.py"])
    stale = newest > rep.stat().st_mtime
    ok = bool(m) and m.group(1) == m.group(2) and not stale
    nr = re.search(r"\((\d+) not run on this computer: ([^)]*)\)", txt)       # 0.3.3: e.g. H3 without the licensed file
    msg = (f"{m.group(1)} of {m.group(2)} checks passed" + (f", {nr.group(1)} not run here ({nr.group(2)})" if nr else "")
           + f" ({stamp.group(1) if stamp else rep.name}).") if m else "Report unreadable."
    if stale:
        msg += " Code or data changed since then: run the checks again."
    return ok, msg


def excel_bytes(sheets: dict) -> bytes:
    buf = _io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        for name, df in sheets.items():
            df.to_excel(xw, sheet_name=name[:31])
    return buf.getvalue()


def save_run(kind: str, inputs: dict, tables: dict, notes: list, page: str = "") -> Path:
    out = P.output_dir("simulator")          # 0.3.2: outputs/simulator, or Documents\Infinity GEM - my runs\simulator if read-only
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    p = out / f"{stamp}_{re.sub(r'[^a-z0-9]+', '_', kind.lower()).strip('_')}.md"
    run = E.run_stamp()
    lines = [f"# Infinity GEM Simulator run: {kind}", "", f"Saved {dt.datetime.now():%Y-%m-%d %H:%M}. Model results, not forecasts.",
             f"Validation: {validation_status()[1]}",
             f"Model version {run['model_version']}; code fingerprint {run['code_fingerprint']}; data fingerprint {run['data_fingerprint']}.",
             "", "## Inputs", "", "```json", json.dumps(inputs, indent=1, ensure_ascii=False, default=str), "```", ""]
    # 0.3: a small scenario file next to the report, so the run can be reopened and rerun (sidebar)
    if page:
        p.with_suffix(".scenario.json").write_text(json.dumps({"page": page, "kind": kind, "inputs": inputs, "stamp": run},
                                                              indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    for name, df in tables.items():
        lines += [f"## {name}", "", df.to_markdown(floatfmt=",.3f"), ""]
    if notes:
        lines += ["## Notes", ""] + [f"- {n}" for n in notes]
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p


def result_downloads(kind: str, inputs: dict, tables: dict, notes: list, key: str, extra_sheets: dict | None = None):
    c1, c2 = st.columns(2)
    sheets = dict(tables)
    sheets.update(extra_sheets or {})
    sheets["Run stamp"] = pd.DataFrame({"value": E.run_stamp()})
    sheets["Inputs"] = pd.DataFrame({"value": {k: json.dumps(v, ensure_ascii=False, default=str) for k, v in inputs.items()}})
    if notes:
        sheets["Notes"] = pd.DataFrame({"note": notes})
    c1.download_button("⬇️ Download results (Excel)", excel_bytes(sheets), file_name=f"Infinity_GEM_{kind.replace(' ', '_')}_{dt.date.today():%Y%m%d}.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=f"dl_{key}", width="stretch")
    if c2.button("💾 Save this run", key=f"save_{key}", width="stretch"):
        p = save_run(kind, inputs, tables, notes, page=key.removeprefix("rr_"))
        c2.success(f"Saved: {p}")


def apply_preset():
    p = PRESETS[st.session_state["preset"]]
    for k in ("construction", "govcons", "transfers", "remit", "oil"):
        st.session_state[k] = float(p.get(k, 0.0))


# ---------------------------------------------------------------------- sidebar
with st.sidebar:
    _lk = _brand("infinity_gem_lockup.png")
    if _lk is not None:
        st.image(_lk, width=190)
    else:
        st.title("Infinity GEM Simulator")
    st.caption("Infinity GEM · research results, not forecasts and not official statistics")
    ok, msg = validation_status()
    (st.success if ok else st.warning)(("✅ " if ok else "⚠️ ") + msg)
    st.divider()
    gdp_label = st.selectbox("Peso amounts are in", list(GDP_CHOICES), help=f"PSA nominal GDP: 2025 ₱{E.PSA_GDP[2025]:,.2f} bn; H1 2025 ₱{E.PSA_GDP['H1_2025']:,.2f} bn. Peso shocks are "
                             "converted to the same share of GDP in each model's base year (2023 SAM, 2018 I-O table), and peso "
                             "results are converted back to these pesos.")
    GDP = GDP_CHOICES[gdp_label]
    st.divider()
    SETTING = st.radio("Model setting (CGE and over time)", list(E.ST.SETTINGS), key="setting",
                       captions=[E.ST.DESCRIPTION[s] for s in E.ST.SETTINGS],
                       help="0.3.1. '0.2 published' reproduces every result published up to 7 October 2026. "
                            "Details: infinity_gem/settings.py and outputs/settings_comparison_*.md.")
    st.divider()
    st.markdown("**Guides**: `docs/guides/02_CGE_GUIDE.md`, `docs/guides/06_GLOSSARY.md`, `docs/STATUS.md`")
    with st.expander("🔁 Rerun a saved scenario"):
        saved = {p.name.removesuffix(".scenario.json"): p                  # 0.3.2: saved runs in outputs/ and in the person's own folder
                 for p in sorted((p for d in P.output_dirs("simulator") for p in d.glob("*.scenario.json")),
                                 key=lambda p: p.name, reverse=True)}
        if not saved:
            st.caption("Saved runs appear here (press 💾 Save under any result).")
        else:
            pick = st.selectbox("Saved scenario", list(saved), key="rerun_pick")
            if st.button("Rerun it exactly", width="stretch"):
                spec = json.loads(saved[pick].read_text(encoding="utf-8"))
                st.session_state["rerun_request"] = (pick, spec)          # run below, once the page functions exist
    with st.expander("⚙️ System checks"):
        st.caption("Reruns all validation checks (takes a few minutes). Run them after any change to the code or data.")
        if st.button("Run the validation checks now", width="stretch"):
            with st.spinner("Running the checks…"):
                r = subprocess.run([sys.executable, str(ROOT / "checks" / "run_all_checks.py")], capture_output=True, text=True,
                                   cwd=str(ROOT), encoding="utf-8", errors="replace")
            st.code(r.stdout[-3000:] or r.stderr[-3000:])
            st.rerun()

warm_up(SETTING)
for _k in ("construction", "govcons", "transfers", "remit", "oil"):
    st.session_state.setdefault(_k, 0.0)

_banner = _brand("infinity_gem_app_banner.png")
if _banner is not None:
    st.image(_banner, width="stretch")
st.header("What happens to the economy if…")
st.session_state.setdefault("engine", "Compare all models")
engine = st.segmented_control("Choose a model", list(ENGINES), key="engine", required=True, width="stretch") or "Compare all models"
st.info(ENGINES[engine], icon="ℹ️")
st.divider()




# ---------------------------------------------------------------------- shock form (CGE, SAM, compare)
def shock_form(kind: str) -> E.Shocks:
    st.selectbox("Start from a preset (optional)", list(PRESETS), key="preset", on_change=apply_preset)
    st.caption("Negative numbers are cuts. Leave a box at 0 to leave that shock out. Shocks you fill in are applied together.")
    c1, c2, c3 = st.columns(3)
    construction = c1.number_input("Construction spending (₱ bn)", step=10.0, key="construction", format="%.2f",
                                   help="Change in spending on construction (e.g. infrastructure disbursements).")
    govcons = c1.number_input("Government consumption (₱ bn)", step=10.0, key="govcons", format="%.2f",
                              help="Change in government consumption, spread in the same proportions as government's purchases "
                                   "in the model's base year (2023 SAM; 2018 I-O table in the I-O model).")
    transfers = c2.number_input("Cash transfers to households, Ayuda (₱ bn)", step=10.0, key="transfers", format="%.2f")
    to = c2.selectbox("Who receives the transfers", list(E.ALLOCATIONS), key="transfers_to")
    remit = c3.number_input("Remittances (%)", step=1.0, key="remit", format="%.2f")
    oil = c3.number_input("World oil prices (%)", step=5.0, key="oil", format="%.2f",
                          disabled=(kind == "SAM multiplier"),
                          help="Not available in the SAM multiplier, which holds prices fixed." if kind == "SAM multiplier" else None)
    s = E.Shocks(construction_bn=construction, govcons_bn=govcons, transfers_bn=transfers, transfers_to=to,
                 remit_pct=remit, oil_pct=0.0 if kind == "SAM multiplier" else oil, gdp_bn=GDP)
    # 0.3.1: commodity and industry lists from the model of the chosen setting (0.3: refined petroleum is its own account)
    sam = E.sam_model(2023).sam if kind == "SAM multiplier" else E.cge_model("short run", None, SETTING).sam
    comm = {sam.labels.get(c, c).replace("Commodities - ", ""): c for c in sam.accounts("c")}
    acts = {sam.labels.get(a, a).replace("Activities - ", ""): a for a in sam.accounts("a")}

    def several(label, names, col, key, help_=None):
        """A small table: one row per item; the + under it adds a row (0.3.1; was one drop-down per kind of shock)."""
        st.markdown(f"**{label}**", help=help_)
        t = st.data_editor(pd.DataFrame({"item": pd.Series([], dtype="object"), col: pd.Series([], dtype="float")}),
                           num_rows="dynamic", width="stretch", key=key,
                           column_config={"item": st.column_config.SelectboxColumn(options=list(names), required=True, width="large"),
                                          col: st.column_config.NumberColumn(format="%.2f", required=True)})
        t = t.dropna()
        return {names[i]: float(v) for i, v in t.groupby("item")[col].sum().items() if v}

    if kind != "SAM multiplier":
        st.markdown("**Any other shock (CGE)**: one row per shock; press **+** under the table to add rows. Every lever of the "
                    "model, on any commodity, industry, factor or household group (or *All*). Changes are in %: a tariff "
                    "−100% abolishes it; a factor supply −2% removes 2% of that labour, land or capital.")
        m_ = E.cge_model("short run", None, SETTING)
        hh = {f"Household · {E.HH_LABEL.get(h, h)}": h for h in m_.H}
        fac = {f"Factor · {sam.labels.get(f_, f_).replace('Factors - ', '')}": f_ for f_ in m_.F}
        items = {"All": "ALL", **{f"Commodity · {k}": v for k, v in comm.items()},
                 **{f"Industry · {k}": v for k, v in acts.items()}, **fac, **hh}
        t = st.data_editor(pd.DataFrame({"lever": pd.Series([], dtype="object"), "item": pd.Series([], dtype="object"),
                                         "change (%)": pd.Series([], dtype="float")}),
                           num_rows="dynamic", width="stretch", key=f"levers_{kind}_{SETTING}",
                           column_config={"lever": st.column_config.SelectboxColumn(options=list(E.LEVERS), required=True, width="medium"),
                                          "item": st.column_config.SelectboxColumn(options=list(items), required=True, width="large"),
                                          "change (%)": st.column_config.NumberColumn(format="%.2f", required=True)})
        rows = [[r["lever"], items[r["item"]], float(r["change (%)"])] for _, r in t.dropna().iterrows() if r["change (%)"]]
        _, problems = E.apply_levers(m_, {}, rows)
        for pr in problems:
            st.warning(f"This row will be skipped: {pr}.")
        s.levers = rows
        with st.expander("Which lever takes which item"):
            st.markdown("\n".join(f"- **{k}**: " + {"c": "a commodity", "c+all": "a commodity or All", "a+all": "an industry or All",
                                                       "f": "a factor (labour by skill, land, capital)", "h+all": "a household group or All",
                                                       "all": "All (economy-wide)"}[v[1]] for k, v in E.LEVERS.items()))
    with st.expander("More shocks (₱ bn of final demand)" if kind == "SAM multiplier" else "Assumptions"):
        if kind != "SAM multiplier" and SETTING != "0.2 published":
            st.caption("Oil prices (0.3 recommended): the SAM has refined petroleum as its own commodity, so an oil-price change "
                       "raises refined-petroleum import prices one for one and crude imports inside mining by their PSA 2018 share "
                       "(infinity_gem/oil.py); no assumed petroleum share is needed.")
        elif kind != "SAM multiplier":
            s.petroleum_share = st.slider("Petroleum share of 'chemicals and petroleum' imports", 0.2, 1.0, E.PETROLEUM_SHARE_DEFAULT, 0.05,
                                          help="The 2023 SAM combines petroleum with chemicals. An oil-price change is applied to that "
                                               "commodity's import price times this share. 0.6 is an assumption, to be replaced with BOC/PSA "
                                               "import data (HS 27 vs 28-38).")
        if kind == "SAM multiplier":
            s.other_demand_bn.update(several("Other final demand (e.g. exports)", comm, "change (₱ bn)", "oth_tbl"))
    return s


def elasticity_form() -> dict | None:
    """None = the setting's own elasticities (0.3 recommended: the Philippine set by sector)."""
    if SETTING != "0.2 published":
        with st.expander("Elasticities (CGE): the Philippine set by sector, or your own numbers"):
            st.caption("0.3 recommended uses the sourced Philippine set (GTAP value-added elasticities; Kapuscinski and Warr 1999 "
                       "for import substitution, where significant): docs/guides/08_PARAMETERS_AND_SOURCES.md.")
            if not st.toggle("Use my own numbers for every sector instead (sensitivity test)", key="el_own"):
                return None
            e1, e2, e3 = st.columns(3)
            sva = e1.slider("Value added: labour–capital substitution (σ_va)", 0.2, 2.0, 0.8, 0.1, key="el3_va")
            sq = e2.slider("Imports vs domestic goods (σ_q, Armington)", 0.3, 5.0, 2.0, 0.1, key="el3_q")
            om = e3.slider("Exports vs domestic sales (ω, CET)", 0.3, 5.0, 2.0, 0.1, key="el3_om")
        fix = lambda x: 0.99 if abs(x - 1.0) < 1e-9 else x
        return {"sigma_va": fix(sva), "sigma_q": fix(sq), "omega_t": om}
    with st.expander("Elasticities (CGE): change them to test how sensitive the answer is"):
        st.caption("Defaults (0.8, 2.0, 2.0) are common in the literature, not estimated for the Philippines (Roadmap Phase 1). "
                   "If a result moves a lot when you change them, say so when you report results.")
        e1, e2, e3 = st.columns(3)
        sva = e1.slider("Value added: labour–capital substitution (σ_va)", 0.2, 2.0, 0.8, 0.1)
        sq = e2.slider("Imports vs domestic goods (σ_q, Armington)", 0.3, 5.0, 2.0, 0.1)
        om = e3.slider("Exports vs domestic sales (ω, CET)", 0.3, 5.0, 2.0, 0.1)
    fix = lambda x: 0.99 if abs(x - 1.0) < 1e-9 else x      # 1.0 is Cobb-Douglas; the CES formula needs ≠ 1
    return {"sigma_va": fix(sva), "sigma_q": fix(sq), "omega_t": om}


def show_single(r: dict, key: str, inputs: dict):
    if not r.get("ok"):
        st.error(r.get("message", "The model did not solve."))
        return
    s = r["summary"]
    slots = (("Real GDP (%)", "GDP (value added, %)"), ("Real GDP (₱ bn)", "GDP (value added, ₱ bn)"),
             ("Consumer prices, CPI (%)", "Consumer prices, CPI (percentage points)", "Household income (₱ bn)"),
             ("New poor (persons, FIES 2023 base)", "Job-equivalents (persons)", "Real household consumption (%)"))
    heads = [k for k in (next((k for k in grp if k in s), None) for grp in slots) if k]
    cols = st.columns(len(heads))
    for c, k in zip(cols, heads):
        c.metric(k, fmt(k, s[k]))
    t1, t2, t3 = st.tabs(["All results", "Households", "Industries"])
    t1.dataframe(fmt_table(pd.DataFrame({"value": s})), width="stretch")
    if r.get("households") is not None:
        h = r["households"]
        t2.altair_chart(bars(h, h.columns[0], f"{h.columns[0]} by household group (quintiles of income per person)", top=10), width="stretch")
        t2.dataframe(h.round(3), width="stretch")
    else:
        t2.info("This model has no household groups.")
    ind = r["industries"]
    t3.altair_chart(bars(ind, ind.columns[0], f"{ind.columns[0]}: largest changes"), width="stretch")
    t3.dataframe(ind.round(3), width="stretch")
    for n in r.get("notes", []):
        st.info(n)
    tables = {"Summary": pd.DataFrame({"value": s}), "Industries": ind}
    if r.get("households") is not None:
        tables["Households"] = r["households"]
    extra = {"SAM before shock": r["sam_before"], "SAM after shock": r["sam_after"]} if r.get("sam_after") is not None else None
    if extra:
        st.caption("The Excel download includes the full SAM before and after the shock (₱ bn, 2023 SAM units), rebuilt from the solution.")
    result_downloads(f"{r['engine']} {r['variant']}", inputs, tables, r.get("notes", []), key, extra)


def show_dynamic(r: dict, key: str, inputs: dict):
    if not r.get("ok"):
        st.error(r.get("message", "The model did not solve."))
        return
    cols = st.columns(len(r["summary"]))
    for c, (k, v) in zip(cols, r["summary"].items()):
        c.metric(k, fmt(k, v))
    path = r["path"].copy()
    d = path[["Real GDP vs baseline (%)"]].reset_index()
    d["year"] = d["year"].astype(str)
    line = alt.Chart(d, title="Real GDP vs baseline (%)").mark_line(point=True, color=DOWN).encode(
        x=alt.X("year:O", title=None), y=alt.Y("Real GDP vs baseline (%):Q"),
        tooltip=["year", alt.Tooltip("Real GDP vs baseline (%):Q", format=",.3f")])
    rule = alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(color=MID).encode(y="y:Q")
    st.altair_chart((line + rule).properties(height=260), width="stretch")
    num = path.select_dtypes("number").round(3)
    st.dataframe(path.assign(**{c: num[c] for c in num.columns}), width="stretch")
    for n in r.get("notes", []):
        st.info(n)
    result_downloads(f"{r['engine']} {r['variant']}", inputs, {"Summary": pd.DataFrame({"value": r["summary"]}), "Path": path},
                     r.get("notes", []), key)


def rerun_saved(spec: dict):
    """Rerun a saved scenario file exactly (0.3)."""
    pg, i = spec["page"], spec["inputs"]
    st_ = i.get("setting", "0.2 published")            # runs saved before 0.3.1 used the 0.2 settings
    if pg == "cge":
        return E.run_cge(E.Shocks(**i["shocks"]), i["closure"], i["elasticities"], st_)
    if pg == "sam":
        return E.run_sam(E.Shocks(**i["shocks"]), i["sam_year"])
    if pg == "cmp":
        return E.compare_all(E.Shocks(**i["shocks"]), i["elasticities"], 2023, st_)
    if pg == "ioq":
        return E.run_io_quantity(i["final_demand_bn"], i["gdp_bn"], i["inverse"], True, i.get("industries", 80))
    if pg == "iop":
        # runs saved before 0.3.6 may hold an elasticity for the removed GDP shortcut: prices are rerun, the shortcut is not
        return E.run_io_price(i["price_change_pct"])
    if pg == "dyn":
        return E.run_dynamic({int(k): v for k, v in i["construction_by_year"].items()}, i["gdp_bn"], i["hybrid"], i["persistence"],
                             st_, i.get("public_capital", "off"), i.get("industry_baseline", False),
                             {int(k): v for k, v in i.get("levers_by_year", {}).items()})
    raise ValueError(f"Unknown page '{pg}'")


if "rerun_request" in st.session_state:
    _pick, _spec = st.session_state.pop("rerun_request")
    with st.spinner("Rerunning the saved scenario…"):
        st.session_state["rerun"] = (_pick, _spec, rerun_saved(_spec))
if "rerun" in st.session_state:
    _name, _spec, _res = st.session_state["rerun"]
    st.subheader(f"🔁 Rerun of the saved scenario {_name}")
    _old = _spec.get("stamp", {})
    _now = E.run_stamp()
    if _old.get("code_fingerprint") and _old.get("code_fingerprint") != _now["code_fingerprint"]:
        st.warning(f"The model code has changed since this run was saved (version {_old.get('model_version')} → {_now['model_version']}); "
                   "differences from the saved report come from that change.")
    if _spec["page"] == "cmp":
        _table, _results, _notes = _res
        st.dataframe(fmt_table(_table), width="stretch")
        result_downloads("Compare all models (rerun)", _spec["inputs"], {"Comparison": _table}, _notes, "rr_cmp")
    elif _spec["page"] == "dyn":
        show_dynamic(_res, "rr_dyn", _spec["inputs"])
    else:
        show_single(_res, f"rr_{_spec['page']}", _spec["inputs"])
        if _spec["page"] == "cge":
            show_household(_res, "rr_cge")
    if st.button("Close the rerun"):
        del st.session_state["rerun"]
        st.rerun()
    st.divider()


# ---------------------------------------------------------------------- pages
if engine == "Compare all models":
    s = shock_form("compare")
    el = elasticity_form()
    if st.button("▶ Run all models", type="primary"):
        with st.spinner("Running the models…"):
            st.session_state["cmp"] = (E.compare_all(s, el, 2023, SETTING), s.as_dict(), el, SETTING)
    if "cmp" in st.session_state:
        (table, results, notes), sd, el_used, set_used = (st.session_state["cmp"] + ("0.2 published",))[:4]
        st.subheader("Same shock, different models")
        st.caption("Shocks: " + "; ".join(E.Shocks(**sd).describe()))
        if "Real GDP (%)" in table.index and table.loc["Real GDP (%)"].notna().any():
            g = table.loc[["Real GDP (%)"]].T.rename(columns={"Real GDP (%)": "Real GDP (%)"})
            st.altair_chart(bars(g, "Real GDP (%)", "Change in GDP (%) by model"), width="stretch")
        st.dataframe(fmt_table(table), width="stretch")
        st.markdown(
            "**How to read this.** The SAM multiplier holds prices fixed and counts every round of spending: an upper bound for "
            "demand shocks. The long-run CGE keeps everyone employed: a lower bound. The short-run CGE is the usual central case "
            "for a one-year shock. The I-O quantity model counts supply-chain effects only (no household spending round). "
            "Report the range, not one number.")
        for n in notes:
            st.info(n)
        for r in results:
            if not r.get("ok"):
                st.error(f"{r.get('engine', 'CGE')}: {r.get('message')}")
        result_downloads("Compare all models", {"shocks": sd, "elasticities": el_used, "setting": set_used}, {"Comparison": table}, notes, "cmp")

elif engine == "CGE":
    s = shock_form("CGE")
    el = elasticity_form()
    closure = st.radio("Closure (time horizon and how markets adjust)", list(E.CLOSURES), horizontal=False,
                       captions=[E.CLOSURE_TEXT[c] for c in E.CLOSURES])
    if st.button("▶ Run the CGE", type="primary"):
        with st.spinner("Solving…"):
            st.session_state["cge"] = (E.run_cge(s, closure, el, SETTING), s.as_dict(), el, closure, SETTING)
    if "cge" in st.session_state:
        r, sd, el_used, cl, set_used = (st.session_state["cge"] + ("0.2 published",))[:5]
        st.subheader(f"CGE, {cl} ({set_used})")
        st.caption("Shocks: " + "; ".join(E.Shocks(**sd).describe()))
        show_single(r, "cge", {"shocks": sd, "elasticities": el_used, "closure": cl, "setting": set_used})
        if r.get("ok"):
            st.caption(f"Model check: Walras slack {r['walras']:.1e}, largest equation error {r['residual']:.1e} (both should be about zero).")
            # 0.3.9 (17 Oct 2026): job figures for a single shock depend on the short-run wage rule
            st.caption("Job figures for a single shock depend on the short-run wage rule: read them as a range, not a point. Example: "
                       "a construction freeze costs low-skill jobs of −1.8% with CPI-indexed pay and −2.7% with pay fixed in pesos; "
                       "a 20% oil-price rise −1.1% and −0.3% (validation/labour_closures/README.md). GDP and household results "
                       "move much less. Disaster damage: report output, incomes and poverty, not job counts.")
            show_household(r, "cge")

elif engine == "SAM multiplier":
    s = shock_form("SAM multiplier")
    year = st.radio("SAM", [2023, 2018], horizontal=True, captions=["IFPRI 2023 SAM (PSA 2018 I-O, FIES 2023). Recommended.",
                                                                   "IFPRI 2018 SAM (PSA 2012 I-O, FIES 2015). For comparison."])
    if st.button("▶ Run the SAM multiplier", type="primary"):
        st.session_state["sam"] = (E.run_sam(s, year), s.as_dict(), year)
    if "sam" in st.session_state:
        r, sd, yr = st.session_state["sam"]
        st.subheader(f"SAM multiplier, {yr} SAM")
        st.caption("Shocks: " + "; ".join(E.Shocks(**sd).describe()))
        show_single(r, "sam", {"shocks": sd, "sam_year": yr})

elif engine == "Input-output (Leontief)":
    io = E.io_table()
    mode = st.radio("Which I-O model?", ["Demand (quantity) model", "Price (cost-push) model"], horizontal=True,
                    captions=["A change in final demand for some industries: output, GDP, imports, jobs through the supply chain.",
                              "A price rise in some industries (e.g. refined petroleum) passed on to everyone who buys from them."])
    if mode.startswith("Demand"):
        detail = st.radio("Industry detail", ["80 industries", "16 industries (LFS groups, for microsimulation)"], horizontal=True,
                          captions=["PSA's 80-industry table (default).",
                                    "PSA's own 16-industry table, whose industries match the LFS major industry groups. Coarser: "
                                    "usually a little larger than with 80."])
        n_ind = 16 if detail.startswith("16") else 80
        io = E.io_table(n_ind)
        st.caption("Add one row per industry. Negative = less demand. Pesos as chosen in the sidebar.")
        ed = st.data_editor(pd.DataFrame({"industry": ["Construction"], "change (₱ bn)": [0.0]}), num_rows="dynamic", width="stretch",
                            column_config={"industry": st.column_config.SelectboxColumn(options=io.names, required=True, width="large"),
                                           "change (₱ bn)": st.column_config.NumberColumn(format="%.2f", required=True)},
                            key=f"io_dem_{n_ind}")
        inv = st.radio("Inverse", ["domestic", "total"], horizontal=True,
                       captions=["Imported inputs removed (recommended: the standard choice).",
                                 "PSA's published inverse. Counts imported inputs as if made at home: every peso returns one peso of GDP."])
        jobs = st.toggle("Job-equivalents by industry (PSA LFS 2025 employment; upper bound)", value=True)
        if st.button("▶ Run the I-O demand model", type="primary"):
            d = ed.dropna().groupby("industry")["change (₱ bn)"].sum().to_dict()
            d = {k: v for k, v in d.items() if v}
            if d:
                st.session_state["ioq"] = (E.run_io_quantity(d, GDP, inv, jobs, n_ind), d, inv, n_ind)
            else:
                st.warning("Enter at least one non-zero change in the table first.")
        if "ioq" in st.session_state:
            r, d, inv_used, n_used = (st.session_state["ioq"] + (80,))[:4]
            st.subheader(f"I-O demand model, {n_used} industries, {inv_used} inverse")
            show_single(r, "ioq", {"final_demand_bn": d, "inverse": inv_used, "gdp_bn": GDP, "industries": n_used})
            if r.get("jobs") is not None:
                with st.expander("Job-equivalents by industry group", expanded=n_used == 16):
                    st.dataframe(r["jobs"].round(1), width="stretch")
                    st.caption("Job-equivalents: employment moves one-for-one with output, so these are an upper bound: in practice "
                               "part of the adjustment is fewer hours or lower pay. Employment: PSA LFS 2025 (preliminary)"
                               + (", summed into the 16 I-O industries." if n_used == 16 else "."))
            st.caption("Household effects (prices and incomes from one consistent run) come from the CGE page → Household detail, "
                       "not from the fixed-price I-O model.")
        with st.expander(f"Multipliers for all {io.n} industries (per peso of final demand)"):
            st.dataframe(io.multipliers(inv).round(3), width="stretch")
    else:
        st.caption("Set the price change of one or more industries. The others follow through their input costs.")
        ed = st.data_editor(pd.DataFrame({"industry": [E.IO_PETROLEUM], "price change (%)": [10.0]}), num_rows="dynamic",
                            width="stretch",
                            column_config={"industry": st.column_config.SelectboxColumn(options=io.names, required=True, width="large"),
                                           "price change (%)": st.column_config.NumberColumn(format="%.2f", required=True)}, key="io_pr")
        if st.button("▶ Run the I-O price model", type="primary"):
            p = ed.dropna().groupby("industry")["price change (%)"].sum().to_dict()
            st.session_state["iop"] = (E.run_io_price(p), p)
        if "iop" in st.session_state:
            r, p = st.session_state["iop"][:2]
            st.subheader("I-O price model (cost push)")
            show_single(r, "iop", {"price_change_pct": p})
            st.caption("Leontief price model: full pass-through at fixed input shares, with imported inputs passing on price rises; no "
                       "substitution, no wage response, no change in demand. An upper bound on the first-round price effect. It gives "
                       "prices only: for GDP, jobs and households from a price shock use the CGE, which computes the terms-of-trade "
                       "loss itself.")

elif engine == "Over time (dynamic)":
    st.caption("Change in construction spending by year (₱ bn, pesos as chosen in the sidebar). Negative = less spending. "
               "Years 2024-2030. The first run calibrates the baseline path (about a minute).")
    p1, p2 = st.columns(2)
    if p1.button("Preset: freeze in 2025 (−₱238.3 bn)"):
        st.session_state["dyn_rows"] = {2025: -238.3}
    if p2.button("Preset: freeze in 2025, catch-up in 2027 (+₱208.7 bn)"):
        st.session_state["dyn_rows"] = {2025: -238.3, 2027: 208.7}
    rows = st.session_state.get("dyn_rows", {2025: 0.0})
    ed = st.data_editor(pd.DataFrame({"year": list(rows), "construction change (₱ bn)": list(rows.values())}), num_rows="dynamic",
                        width="stretch", key=f"dyn_ed_{abs(hash(tuple(rows.items())))}",
                        column_config={"year": st.column_config.NumberColumn(min_value=2024, max_value=2030, step=1, format="%d"),
                                       "construction change (₱ bn)": st.column_config.NumberColumn(format="%.2f")})
    # 0.3.1: any CGE lever in any year, not only construction
    st.markdown("**Other shocks by year** (any lever of the model; press **+** to add rows). Each row changes that year's "
                "baseline level by the % given; enter the same row for several years for a lasting change.")
    _md = E.cge_model("short run", None, SETTING)
    _sam = _md.sam
    _items = {"All": "ALL", **{f"Commodity · {_sam.labels.get(c, c).replace('Commodities - ', '')}": c for c in _md.C},
              **{f"Industry · {_sam.labels.get(a, a).replace('Activities - ', '')}": a for a in _md.A},
              **{f"Factor · {_sam.labels.get(f_, f_).replace('Factors - ', '')}": f_ for f_ in _md.F},
              **{f"Household · {E.HH_LABEL.get(h, h)}": h for h in _md.H}}
    lv = st.data_editor(pd.DataFrame({"year": pd.Series([], dtype="Int64"), "lever": pd.Series([], dtype="object"),
                                      "item": pd.Series([], dtype="object"), "change (%)": pd.Series([], dtype="float")}),
                        num_rows="dynamic", width="stretch", key=f"dyn_levers_{SETTING}",
                        column_config={"year": st.column_config.NumberColumn(min_value=2024, max_value=2030, step=1, format="%d", required=True),
                                       "lever": st.column_config.SelectboxColumn(options=list(E.LEVERS), required=True, width="medium"),
                                       "item": st.column_config.SelectboxColumn(options=list(_items), required=True, width="large"),
                                       "change (%)": st.column_config.NumberColumn(format="%.2f", required=True)})
    lev_by_year = {}
    for _, r in lv.dropna().iterrows():
        if r["change (%)"]:
            lev_by_year.setdefault(int(r["year"]), []).append([r["lever"], _items[r["item"]], float(r["change (%)"])])
    h1, h2 = st.columns(2)
    hybrid = h1.toggle("Short run in shock years (hybrid closure)", value=True,
                       help="On: years with a shock use the short-run model (jobs can be lost), and the job gap then closes gradually. "
                            "Off: long-run closure every year (everyone employed), as in Infinity GEM 0.2.")
    pers = h2.slider("Share of the job gap left the next year", 0.0, 0.9, 0.5, 0.1, disabled=not hybrid,
                     help="0.5: half the gap is left after one year, an eighth after three. An assumption until  "
                          "(labour-market evidence) is done.")
    pc, ib = "off", False
    if SETTING == "0.2 published":
        st.caption("Public-capital channel (lost roads lowering productivity) and the documented baseline: switch the model setting "
                   "in the sidebar to '0.3 recommended'. Long-run infrastructure effects shown here are lower bounds.")
    else:
        k1, k2 = st.columns(2)
        pc = k1.radio("Productivity value of public infrastructure", ["off", "low", "high"], horizontal=True, key="dyn_pc",
                      captions=["Lower bound", "φ 0.083, public capital 0.397 × GDP", "φ 0.122, public capital 0.296 × GDP"],
                      help="φ: output elasticity of public capital, Bom and Ligthart (2014) meta-analysis (short and long run). "
                           "Public capital / GDP: IMF Investment and Capital Stock Dataset, 2019. Report low and high as a range.")
        ib = k2.toggle("Baseline: each industry grows as PSA reports for 2024-2025", key="dyn_ib",
                       help="This baseline already contains the actual 2025 construction slump: use it for the 2027 "
                            "catch-up, and do not add a 2025 freeze on top of it.")
        if ib and any(float(v or 0) for y, v in zip(ed["year"], ed["construction change (₱ bn)"]) if y == 2025):
            st.warning("The industry baseline already contains the 2025 slump: a 2025 change on top of it counts the freeze twice.")
        st.caption("0.3 recommended: the first run calibrates the baseline with every upgrade on (a few minutes).")
    if st.button("▶ Run the dynamic model", type="primary"):
        d = {int(r["year"]): float(r["construction change (₱ bn)"]) for _, r in ed.dropna().iterrows()}
        with st.spinner("Solving 2023-2030…"):
            st.session_state["dyn"] = (E.run_dynamic(d, GDP, hybrid, pers, SETTING, pc, ib, lev_by_year),
                                       {"construction_by_year": d, "gdp_bn": GDP, "hybrid": hybrid, "persistence": pers,
                                        "setting": SETTING, "public_capital": pc, "industry_baseline": ib,
                                        "levers_by_year": lev_by_year})
    if "dyn" in st.session_state:
        r, inp = st.session_state["dyn"]
        st.subheader("Dynamic CGE, 2023-2030: scenario vs baseline")
        show_dynamic(r, "dyn", inp)

elif engine == "Money and the BSP (research)":
    # 0.3.12 (20 Oct 2026, guide 11 §7): the DSGE results in plain words. Nothing is solved here: the page reads
    # the newest saved outputs of research/dsge/ and scenarios/qpm_cge_link.py, so what it shows is what the notes cite.
    from infinity_gem import paths as _paths
    _OUT = Path(_paths.__file__).resolve().parents[1] / "outputs"

    def _md_tables(path):
        """Every Markdown table in a file, as DataFrames (first column = index)."""
        out, cur = [], []
        for ln in path.read_text(encoding="utf-8").splitlines() + [""]:
            if ln.strip().startswith("|"):
                cur.append(ln)
            elif cur:
                rows = [[c.strip() for c in r.strip().strip("|").split("|")] for r in cur]
                rows = [r for r in rows if not all(re.fullmatch(r":?-+:?", c) for c in r)]
                out.append(pd.DataFrame(rows[1:], columns=rows[0]).set_index(rows[0][0]))
                cur = []
        return out

    def _newest(pattern):
        f = sorted(_OUT.glob(pattern))
        return f[-1] if f else None

    st.markdown("**What this page is.** The central 2026 setting model has no interest rate or central bank (its limits say so). The project's "
                "research DSGE, a small New Keynesian model of the Philippines estimated on 2002-2026 data (`research/dsge/`, guide 11), "
                "supplies two things the CGE cannot: the BSP's policy rate and the inflation it reacts to. Its results are fed into the "
                "CGE through investment's response to the real interest rate. **Everything below is research, not for citation:** the "
                "candidate model rests on one estimation sample and the investment response is not identified by Philippine data.")
    srcs = []
    # 1. a 100 bp tightening
    f = _newest("dsge_rate_path_review_*.md")
    st.subheader("1. A BSP rate rise of 100 basis points")
    if f is None:
        st.caption("No saved rate-path review (research/dsge/rate_path_review.py) found in outputs/.")
    else:
        srcs.append(f.name)
        tb = _md_tables(f)[0]
        keep = [c for c in tb.columns if any(k in c for k in ("rate q1-q4", "output gap 2026", "output gap 2027", "inflation 2026", "CPI 2026", "draws"))]
        st.markdown("Each model is given the same rate paths: its own response, the BSP's PAMPh path, and the rate held up one point for a "
                    "year. Output gaps are percent of GDP; the PAMPh row is the BSP's own published model.")
        st.dataframe(tb[keep] if keep else tb, width="stretch")
        st.caption(f"Source: `{f.name}`. The 100 bp held for a year costs 2026 output 0.4% (PAMPh-type model) to 0.9% (the project's DSGE).")
    # 2. the 100 bp through the CGE
    rows = {}
    for g in sorted(_OUT.glob("qpm_cge_link_*_100bp_*pathhold4*.md")):
        tb = _md_tables(g)
        if tb:
            lab = "the project's DSGE" if "dsge" in g.name else "QPM (PAMPh-type)"
            rows[lab] = {"CGE GDP gap 2026 (%)": tb[0].loc["CGE GDP gap (%)", "2026"], "new poor 2026 (M)": tb[0].loc["CGE new poor (M)", "2026"],
                         "new poor 2027 (M)": tb[0].loc["CGE new poor (M)", "2027"], "file": g.name}
            srcs.append(g.name)
    if rows:
        st.markdown("**Through the CGE** (the rate held one point higher for a year; real investment moves with the real rate gap, "
                    "hoarding 0.85, Infinity GEM's own SAM):")
        st.dataframe(pd.DataFrame(rows).T, width="stretch")
    # 3. the BSP's response to the 2026 oil shock
    st.subheader("2. The BSP's response to the 2026 oil-price shock")
    f = _newest("dsge_oil_policy_*oilw*thfix*.md") or _newest("dsge_oil_policy_*.md")
    if f is None:
        st.caption("No saved oil-policy run (research/dsge/oil_policy.py) found in outputs/.")
    else:
        srcs.append(f.name)
        txt = f.read_text(encoding="utf-8")
        m = re.search(r"Output cost of the BSP's response\*\*[^:]*: year 1 ([-\d.]+)%, year 2 ([-\d.]+)%", txt)
        st.markdown("In the model as estimated, domestic prices change so rarely that an oil supply shock raised output; with price "
                    "stickiness taken from the BSP's own micro price data (a price cut about every 10 months) the shock is contractionary, "
                    "and the BSP's tightening against it costs output in exchange for lower inflation."
                    + (f" **Output cost of the response: {m.group(1)}% in year 1, {m.group(2)}% in year 2.**" if m else ""))
        tb = _md_tables(f)
        if tb:
            st.dataframe(tb[0], width="stretch")
        st.caption(f"Source: `{f.name}` (annual averages of the quarterly responses; 'rate held' = no response for four quarters).")
    rows = {}
    for g in sorted(_OUT.glob("qpm_cge_link_*dsge_oil36*thfix*.md")):
        mt = re.search(r"elastic([\d.]+)_", g.name)
        tb = _md_tables(g)
        if mt and tb:
            rows[f"investment response {float(mt.group(1)):g}% per pp"] = {
                "CGE GDP gap 2026 (%)": tb[0].loc["CGE GDP gap (%)", "2026"], "new poor 2026 (M)": tb[0].loc["CGE new poor (M)", "2026"],
                "new poor 2027 (M)": tb[0].loc["CGE new poor (M)", "2027"], "file": g.name}
            srcs.append(g.name)
    if rows:
        st.markdown("**Through the CGE:** the cost of the BSP's oil response in new poor, for three values of investment's response to "
                    "the real rate (the Philippine data cannot pin it down; the central value, 2% per point, is matched to the DSGE):")
        st.dataframe(pd.DataFrame(rows).T.sort_index(), width="stretch")
    # 4-6 (20 Oct 2026, evening): the two checks asked for before any monetary number is cited, and the closed loop
    st.subheader("3. What the poverty figures include: the price benefit is netted")
    f = _newest("bsp_oil_response_netting_*.md")
    if f is None:
        st.caption("No saved decomposition (scenarios/bsp_oil_response_netting.py) found in outputs/.")
    else:
        srcs.append(f.name)
        tb = _md_tables(f)
        st.markdown("The poor are counted from each family's own basket prices and its group's nominal income, so the figures above "
                    "already net the lower prices the BSP's tightening brings against the income it costs. The table separates the two: "
                    "'incomes only' holds every family's prices at the baseline, 'prices only' holds nominal incomes; columns are the "
                    "investment response (0.55, 2, 3.3) and the channel (both, investment only, peso only).")
        if len(tb) > 1:
            st.dataframe(tb[1], width="stretch")
        st.caption(f"Source: `{f.name}`. At the central investment response the gross income loss alone would add about twice the "
                   "published count and the lower prices alone would take out more than half of it; the published figure is the net.")
    st.subheader("4. The estimated rule against the BSP's actual 2026 decisions")
    f = _newest("dsge_rule_check_2026_*.md")
    if f is None:
        st.caption("No saved rule check (research/dsge/rule_check_2026.py) found in outputs/.")
    else:
        srcs.append(f.name)
        txt = f.read_text(encoding="utf-8")
        bullets = [ln for ln in txt.splitlines() if ln.startswith("- ")]
        st.markdown("The model reads the 2002-2026 data quarter by quarter: what its rule prescribes from inflation, the output gap and the "
                    "peso, and the part of the actual rate it does not explain (the policy 'shock', in units of its usual size).")
        if bullets:
            st.markdown("\n".join(bullets))
        tb = _md_tables(f)
        if tb:
            st.dataframe(tb[0], width="stretch")
        st.caption(f"Source: `{f.name}`. In the first half of 2026 the BSP sat about half a point below the rule (shocks of about one "
                   "usual size, not unusual); by the third quarter it had raised the rate to about the rule's level. The rule's own "
                   "response to the 2026 oil shock is of the same size as the BSP's 2026 increases.")
    st.subheader("5. The money block: the rule inside the dynamic model (closed loop)")
    # 21 Oct 2026: the central 2026 setting is the file whose name ends in the SAM tag; the price-side variants of the same script
    # (sticky, energy, observed inflation; a review note (not included)) carry a further tag
    f = _newest("monetary_check_*_own.md") or _newest("monetary_check_*_ifpri.md") or _newest("monetary_check_*.md")
    if f is None:
        st.caption("No saved closed-loop run (scenarios/monetary_check.py) found in outputs/.")
    else:
        srcs.append(f.name)
        tb = _md_tables(f)
        st.markdown("Instead of feeding the DSGE's paths into the CGE from outside, the CGE's own inflation and output gaps feed a BSP rule "
                    "within each year, the rule's real rate scales investment, and the path is solved as a fixed point "
                    "(`DynamicCGE.monetary_scenario`, check MP1). The four 2026 shocks with and without the rule; rules from PAMPh "
                    "and from the project's estimated models.")
        if len(tb) > 2:
            st.markdown("Levels:")
            st.dataframe(tb[1], width="stretch")
            st.markdown("Differences from the 2026 scenarios' no-rule path (with the rule minus without):")
            st.dataframe(tb[2], width="stretch")
        elif tb:
            st.dataframe(tb[0], width="stretch")
        st.caption(f"Source: `{f.name}`. The rule sees an inflation gap only in the short-run years (2025-2027), where the peso is the "
                   "numeraire; in later years the CPI is the numeraire by construction.")
    st.subheader("Read before using any number")
    st.markdown("- **Research only.** The candidate DSGE (`soe_htmu.py`) converged on three chains; the oil model with calibrated price "
                "stickiness fits the data less well and its chains are fewer. \n"
                "- **The investment channel carries almost all of the poverty effect**, and its size is an assumption (1.9-3.3% of real "
                "investment per point of real rate; central about 2).\n"
                "- **Where the numbers come from:** guide 11 (`docs/guides/11_DSGE_GUIDE.md`), `research/dsge/README.md`, and the files "
                "named under each table. Rerun them to refresh this page; it shows the newest file of each kind.")
    if srcs:
        st.caption("Files read: " + ", ".join(f"`{s}`" for s in dict.fromkeys(srcs)))

else:   # Quick calculator
    st.markdown("**Shock × multiplier.** Use this when you have a multiplier or coefficient from a study (cite it). Infinity GEM's own I-O "
                "multipliers for the industry you pick are shown beside it for comparison.")
    io = E.io_table()
    q1, q2, q3 = st.columns(3)
    shock = q1.number_input("Shock (₱ bn)", value=-100.0, step=10.0, format="%.2f")
    mult = q2.number_input("Your multiplier (GDP per peso of shock)", value=None, step=0.05, format="%.3f", placeholder="required")
    src = q3.text_input("Source of your multiplier", placeholder="author, year, table")
    jobs_per = st.number_input("Optional: jobs per ₱1 bn of GDP change", value=None, step=100.0, format="%.0f", placeholder="leave empty to skip")
    ind = st.selectbox("Compare with the I-O multipliers for", io.names, index=io.names.index("Construction"))
    m = io.multipliers("domestic").loc[ind]
    mt = io.multipliers("total").loc[ind]
    if mult is None:
        st.info("Enter your multiplier to compute the result.")
    else:
        res = {"GDP change (₱ bn)": shock * mult}
        if jobs_per is not None:
            res["Jobs (persons)"] = shock * mult * jobs_per
        cols = st.columns(len(res))
        for c, (k, v) in zip(cols, res.items()):
            c.metric(k, fmt(k, v))
        st.caption(f"Source stated: {src or '(none – add one before using this number)'}")
    st.dataframe(fmt_table(pd.DataFrame({"I-O, domestic inverse": {"GDP multiplier": m['value-added multiplier'],
                                                                     "Output multiplier": m['output multiplier'],
                                                                     "GDP change for your shock (₱ bn)": shock * m['value-added multiplier']},
                                         "I-O, total inverse": {"GDP multiplier": mt['value-added multiplier'],
                                                                    "Output multiplier": mt['output multiplier'],
                                                                    "GDP change for your shock (₱ bn)": shock * mt['value-added multiplier']}})),
                 width="stretch")


st.divider()
st.caption("Infinity GEM · every result is reproducible from app/engines.py and the infinity_gem package · data sources in data/DATA_INVENTORY.md. "
           "Results are research results, not for citation.")
