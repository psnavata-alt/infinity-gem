"""A Leontief cost-push price model of the oil shock on the OECD ICIO 2022 Philippine block.

NOT FOR CITATION (research, 23 Oct 2026). Model-free check of oil's cost pass-through by industry, against the CGE's weak
short-run price response (a review note (not included)).

Run (data extracted under %TEMP%, never in this repository; python -I because the CSV is a third-party file):
    py -I research/icio/oil_cost_push_2022.py <path of 2022_SML.csv> [<path of 2018_SML.csv>]
The 2018 table is optional (a check: the OECD's 2018 Philippine block rests on PSA's 2018 I-O table).

Model (Miller and Blair 2009, Input-Output Analysis, 2nd ed., section 2.6: the price model; check I1's formula,
dp_r = (I - A_rr')^-1 A_Kr' dp_K). Unit cost of Philippine industry j, value added and taxes less subsidies fixed per unit:
    p_j = sum_i Ad_ij p_i + sum_k Am_kj pm_k + tls_j + va_j,
Ad = domestic intermediate coefficients (PHL rows, PHL columns), Am = imported intermediate coefficients by product (all other
areas' rows of product k, summed). The oil set K = {B06 crude petroleum and natural gas, C19 coke and refined petroleum}.
Domestic oil products are priced at import parity (the Philippine downstream oil industry is deregulated: RA 8479), so their
price is set equal to the shock. Four variants:
  V1 domestic inputs only:    the shock reaches users through DOMESTIC oil products only; all imports at fixed prices.
  V2 with imported oil:       V1 plus imported B06 and C19 inputs at the shocked price (other imports fixed).
  V3 PSA-style total table:   total coefficients A = Ad + Am, as in PSA's I-O table and infinity_gem/iomodel.py (imported
                              non-oil inputs move with the domestic price of the same product).
  V4 global value chains:     the whole 81-economy table: B06 and C19 prices in EVERY economy rise by the shock, every
                              other price in every economy follows its costs; Philippine prices then include the oil content
                              of imported non-oil inputs (chemicals, plastics, transport) from the countries that supply them.
Direct effect = the first round (each industry's own oil-input cost share x the shock); indirect = total - direct.
Consumer prices: household final consumption (HFCE) weights at basic prices, domestic and imported products (imports at
fixed prices except oil products in V2; at their origin's price change in V4; one price per product in V3, as PSA's model).
Shocks: +30% on both B06 and C19; and the central 2026 size (preshock/shock_paths.py oil_paths('central', 'EIA'), 2026:
calendar-year crude (Dubai) and imported fuel products (weighted) against the DBCC pre-conflict assumption). The model is
linear: other sizes scale.
Comparison: the project's I-O price model on PSA's 2018 80-industry table (infinity_gem/iomodel.IOTable.price; check I1), by
industry through a concordance to the ICIO industries, and observed 2026 CPI items (data/raw/macro, PSA OpenSTAT
0012M4ACP22: March-September 2026 average against January-February 2026, the oil shock's own window).
Caveats: current US dollars (cost shares only, so the currency does not matter here); 2022 cost shares carry 2022's high
oil prices (Dubai about US$96 a year on average against about US$66 in January-February 2026), so the 2022 pass-through per
% shock is on the high side: a price-adjusted 2022 variant rescales the oil rows to the pre-conflict price (volumes held);
basic prices: pump prices also carry excise taxes fixed in pesos per litre, VAT and retail margins, so their % change is
smaller; no substitution, full and immediate pass-through (an upper bound in the short run); the Philippine block rests on
PSA's benchmark tables (1995, 2000, 2006, 2012, 2018; ICIO annex Table 3), the 2022 one is the OECD's estimate.
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import numpy as np                                   # noqa: E402
import pandas as pd                                  # noqa: E402

import icio_common as IC                             # noqa: E402

ROOT = IC.ROOT
OIL = ("B06", "C19")


# ----------------------------------------------------------------------------- the Philippine block
def phl_block(t: IC.ICIO, area: str = "PHL") -> dict:
    b = t.block(area)
    X = t.X[b]
    Xs = np.where(X > 0, X, 1.0)
    rows_area, rows_ind = t.area_of_row(), t.ind_of_row()
    Ad = t.Z[np.ix_(b, b)] / Xs
    Am = np.zeros((len(t.inds), len(t.inds)))
    for k, ind in enumerate(t.inds):                  # imported intermediate inputs of product k, all origins
        r = np.where((rows_ind == ind) & (rows_area != area))[0]
        Am[k] = t.Z[np.ix_(r, b)].sum(axis=0) / Xs
    hf = t.fd_cols(area, ("HFCE",))
    hd = t.Y[np.ix_(b, hf)].sum(axis=1)               # households' purchases of domestic products
    hm = np.array([t.Y[np.ix_(np.where((rows_ind == ind) & (rows_area != area))[0], hf)].sum() for ind in t.inds])
    return dict(b=b, X=X, Ad=Ad, Am=Am, tls=t.TLS[b] / Xs, va=t.VA[b] / Xs, hd=hd, hm=hm,
                colsum=Ad.sum(axis=0) + Am.sum(axis=0) + t.TLS[b] / Xs + t.VA[b] / Xs)


def _solve_given(A: np.ndarray, K: list, dpK: np.ndarray, extra: np.ndarray | None = None) -> np.ndarray:
    """dp for all industries: dp_K given, dp_r = (I - A_rr')^-1 (A_Kr' dp_K + extra_r). `extra` = cost push from inputs
    outside A (imported oil in V2)."""
    n = A.shape[0]
    r = np.array([i for i in range(n) if i not in K])
    rhs = A[np.ix_(K, r)].T @ dpK + (0 if extra is None else extra[r])
    dp = np.zeros(n)
    dp[K] = dpK
    dp[r] = np.linalg.solve(np.eye(len(r)) - A[np.ix_(r, r)].T, rhs)
    return dp


def national_variants(blk: dict, inds: list, shock: dict) -> dict:
    """V1-V3 on one country's block. shock = {'B06': 0.30, 'C19': 0.30}. Returns per variant: total, direct, cpi."""
    K = [inds.index(k) for k in shock]
    s = np.zeros(len(inds))
    for k, v in shock.items():
        s[inds.index(k)] = v
    Ad, Am, hd, hm = blk["Ad"], blk["Am"], blk["hd"], blk["hm"]
    H = hd.sum() + hm.sum()
    out = {}
    # V1: domestic oil products only
    dp1 = _solve_given(Ad, K, s[K])
    out["V1 domestic inputs only"] = dict(total=dp1, direct=Ad.T @ s, cpi=float(hd @ dp1) / H)
    # V2: plus imported oil inputs at the shocked price
    push_m = Am.T @ s                                  # cost push from imported oil, by using industry
    dp2 = _solve_given(Ad, K, s[K], extra=push_m)
    out["V2 with imported oil inputs"] = dict(total=dp2, direct=(Ad + Am).T @ s, cpi=float(hd @ dp2 + hm @ s) / H)
    # V3: PSA-style total coefficients
    At = Ad + Am
    dp3 = _solve_given(At, K, s[K])
    out["V3 PSA-style total table"] = dict(total=dp3, direct=At.T @ s, cpi=float((hd + hm) @ dp3) / H)
    for v in out.values():
        v["ppi"] = float(blk["X"] @ v["total"] / blk["X"].sum())
    return out


def global_variant(t: IC.ICIO, shock: dict, area: str = "PHL") -> dict:
    """V4: the 81-economy price model; B06 and C19 in every economy at the shock, every other price endogenous."""
    X = np.where(t.X > 0, t.X, 1.0)
    A = t.Z / X[None, :]
    ind = t.ind_of_row()
    K = np.where(np.isin(ind, list(shock)))[0]
    dpK = np.array([shock[i] for i in ind[K]])
    dp = _solve_given(A, list(K), dpK)
    b = t.block(area)
    hf = t.fd_cols(area, ("HFCE",))
    h = t.Y[:, hf].sum(axis=1)                         # households' purchases from every origin
    s_full = np.zeros(len(ind))
    s_full[K] = dpK
    direct = (A[:, b].T @ s_full)                      # first round: own oil inputs, domestic and imported
    # import price change of each product as seen by Philippine users (intermediate + final use weights by origin)
    use = t.Z[:, b].sum(axis=1) + t.Y[:, t.fd_cols(area)].sum(axis=1)
    rows_area = t.area_of_row()
    imp_dp = {}
    for k in t.inds:
        r = np.where((ind == k) & (rows_area != area))[0]
        w = use[r]
        imp_dp[k] = float(w @ dp[r] / w.sum()) if w.sum() > 0 else np.nan
    return dict(total=dp[b], direct=direct, cpi=float(h @ dp / h.sum()),
                ppi=float(t.X[b] @ dp[b] / t.X[b].sum()), import_price=imp_dp)


def price_adjusted_block(blk: dict, inds: list, ratio: float) -> dict:
    """The block with the oil rows (domestic and imported B06, C19) valued at `ratio` x their price (volumes held); the
    difference goes to value added so every column still sums to one (first-order rescaling of the cost shares)."""
    out = dict(blk)
    Ad, Am = blk["Ad"].copy(), blk["Am"].copy()
    d_va = np.zeros(Ad.shape[1])
    for k in OIL:
        i = inds.index(k)
        d_va += (1 - ratio) * (Ad[i] + Am[i])
        Ad[i] *= ratio
        Am[i] *= ratio
    out.update(Ad=Ad, Am=Am, va=blk["va"] + d_va)
    hd, hm = blk["hd"].copy(), blk["hm"].copy()
    for k in OIL:                                      # households' fuel volumes held too
        i = inds.index(k)
        hd[i] *= ratio
        hm[i] *= ratio
    out.update(hd=hd, hm=hm)
    return out


# ----------------------------------------------------------------------------- comparisons
# PSA 2018 80-industry table (data/raw/io) -> comparison groups of ICIO industries (concordance by name)
CONCORDANCE = [
    ("Agriculture", ["A01"], list(range(0, 17)) + [19]), ("Forestry", ["A02"], [17]), ("Fishing", ["A03"], [18]),
    ("Coal", ["B05"], [20]), ("Crude petroleum and natural gas", ["B06"], [21]), ("Metal ores", ["B07"], [22, 23, 24]),
    ("Other mining", ["B08", "B09"], [25]), ("Food, beverages, tobacco", ["C10T12"], [26, 27, 28]),
    ("Textiles, apparel, leather", ["C13T15"], [29, 30, 31]), ("Wood products", ["C16"], [32]),
    ("Paper and printing", ["C17_18"], [33, 34]), ("Coke and refined petroleum", ["C19"], [35]), ("Chemicals", ["C20"], [36]),
    ("Pharmaceuticals", ["C21"], [37]), ("Rubber and plastics", ["C22"], [38]), ("Non-metallic minerals", ["C23"], [39]),
    ("Basic metals", ["C24A", "C24B"], [40]), ("Fabricated metals", ["C25"], [41]), ("Electronics", ["C26"], [42]),
    ("Electrical equipment", ["C27"], [43]), ("Machinery", ["C28"], [44]), ("Transport equipment", ["C29", "C301", "C302T309"], [45]),
    ("Furniture, other manufacturing", ["C31T33"], [46, 47]), ("Electricity, gas, steam", ["D"], [48, 49]),
    ("Water, sewerage, waste", ["E"], [50, 51]), ("Construction", ["F"], [52]), ("Trade", ["G"], [53, 54, 55]),
    ("Land transport", ["H49"], [56]), ("Water transport", ["H50"], [57]), ("Air transport", ["H51"], [58]),
    ("Warehousing", ["H52"], [59]), ("Postal and courier", ["H53"], [60]), ("Accommodation and food services", ["I"], [61, 62]),
    ("Information and communication", ["J58T60", "J61", "J62_63"], [63, 64]), ("Finance and insurance", ["K"], [65, 66, 67, 68]),
    ("Real estate", ["L"], [69, 70]), ("Professional and administrative", ["M", "N"], [71]),
    ("Public administration", ["O"], [72]), ("Education", ["P"], [73, 74]), ("Health and social work", ["Q"], [75, 76, 77]),
    ("Arts and recreation", ["R"], [78]), ("Other services", ["S", "T"], [79])]


def by_group_icio(dp: np.ndarray, X: np.ndarray, inds: list) -> pd.Series:
    out = {}
    for name, codes, _ in CONCORDANCE:
        i = [inds.index(c) for c in codes]
        w = X[i]
        out[name] = float(w @ dp[i] / w.sum()) if w.sum() > 0 else np.nan
    return pd.Series(out)


def by_group_psa(dp: np.ndarray, X: np.ndarray) -> pd.Series:
    out = {}
    for name, _, rows in CONCORDANCE:
        w = X[rows]
        out[name] = float(w @ dp[rows] / w.sum()) if w.sum() > 0 else np.nan
    return pd.Series(out)


def oil_shares_icio(blk: dict, inds: list) -> pd.DataFrame:
    i = [inds.index(k) for k in OIL]
    return pd.DataFrame({"domestic oil inputs (% of output)": blk["Ad"][i].sum(axis=0) * 100,
                         "imported oil inputs (% of output)": blk["Am"][i].sum(axis=0) * 100}, index=inds)


def cpi_observed() -> pd.DataFrame:
    """Observed CPI items: March-September 2026 average against January-February 2026 (PSA OpenSTAT 0012M4ACP22)."""
    f = ROOT / "data" / "raw" / "macro" / "PSA_OpenSTAT_0012M4ACP22_CPI_2018base_by_commodity_group_2018-latest.csv"
    d = pd.read_csv(f, comment="#")
    d = d.assign(item=d["Commodity Description"].astype(str).str.strip())
    items = {"0 - ALL ITEMS": "All items", "04.5.1 - Electricity (ND)": "Electricity",
             "04.5.2 - Gas (ND)": "Gas (LPG)", "04.5.3 - Liquid fuels (ND)": "Liquid fuels (kerosene)",
             "07.2.2 - Fuels and lubricants for personal transport equipment (ND)": "Fuels for personal transport",
             "07.2.2.1 - Diesel (ND)": "Diesel", "07.2.2.2 - Gasoline (ND)": "Gasoline",
             "07.3.2 - Passenger transport by road (S)": "Passenger transport by road",
             "07.3.3 - Passenger transport by air (S)": "Passenger transport by air",
             "07.3.4 - Passenger transport by sea and inland waterway (S)": "Passenger transport by sea",
             "07.4 - TRANSPORT SERVICES OF GOODS": "Transport services of goods", "07 - TRANSPORT": "Transport (division)",
             "01 - FOOD AND NON-ALCOHOLIC BEVERAGES": "Food and non-alcoholic beverages"}
    pre = [f"2026 {m}" for m in ("Jan", "Feb")]
    post = [f"2026 {m}" for m in ("Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep")]
    rows = []
    for code, label in items.items():
        r = d[d["item"] == code]
        if r.empty:
            continue
        r = r.iloc[0]
        a = pd.to_numeric(r[pre], errors="coerce").mean()
        bb = pd.to_numeric(r[post], errors="coerce")
        rows.append({"CPI item": label, "PSA code": code.split(" - ")[0],
                     "Mar-Sep 2026 vs Jan-Feb 2026 (%)": (bb.mean() / a - 1) * 100,
                     "September 2026 vs Jan-Feb 2026 (%)": (bb.iloc[-1] / a - 1) * 100,
                     "months": f"{int(bb.notna().sum())} of 7"})
    return pd.DataFrame(rows).set_index("CPI item")


def central_2026_sizes() -> dict:
    """The central 2026 oil shock: preshock/shock_paths.py oil_paths('central', 'EIA') (calendar-year averages of
    actual months and the EIA forecast, against the DBCC pre-conflict assumption)."""
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "preshock"))
    import shock_paths as SP                       # noqa: E402
    o = SP.oil_paths("central", "EIA").loc[2026]
    return {"B06": float(o["crude (Dubai)"]) / 100, "C19": float(o["fuel products, weighted"]) / 100}


def dubai_annual(year: int) -> float:
    w = pd.read_csv(ROOT / "data" / "raw" / "macro" / "WorldBank_PinkSheet_crude_oil_monthly_1960-2026.csv", comment="#")
    w["month"] = pd.PeriodIndex(w["month"], freq="M")
    return float(w.loc[w["month"].dt.year == year, "crude_dubai_usd_bbl"].mean())


def dubai_months(months: list) -> float:
    w = pd.read_csv(ROOT / "data" / "raw" / "macro" / "WorldBank_PinkSheet_crude_oil_monthly_1960-2026.csv", comment="#")
    w["month"] = pd.PeriodIndex(w["month"], freq="M").astype(str)
    return float(w.loc[w["month"].isin(months), "crude_dubai_usd_bbl"].mean())


# ----------------------------------------------------------------------------- main
def main():
    IC.utf8_stdout()
    args = [a for a in sys.argv[1:] if a.lower().endswith(".csv")]
    if not args:
        args = [str(IC.csv_path(2022))]
    t22 = IC.load(IC.csv_path(2022, [args[0]]), 2022)
    t18 = IC.load(IC.csv_path(2018, [args[1]]), 2018) if len(args) > 1 else None
    inds = t22.inds
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M")
    shocks = {"+30% (B06 and C19)": {"B06": 0.30, "C19": 0.30}}
    try:
        sz = central_2026_sizes()
        shocks[f"central 2026 (crude {sz['B06'] * 100:+.1f}%, fuel products {sz['C19'] * 100:+.1f}%)"] = sz
    except Exception as e:                            # the Pink Sheet or EIA file missing: say so, do not type a value
        print(f"(the central 2026 sizes not available: {e!r})")
    tables = {"2022": (t22, phl_block(t22))}
    if t18 is not None:
        tables["2018"] = (t18, phl_block(t18))
    # price-adjusted 2022: oil rows at the January-February 2026 Dubai price instead of 2022's average (volumes held)
    p22, p26 = dubai_annual(2022), dubai_months(["2026-01", "2026-02"])
    ratio = p26 / p22
    tables["2022 price-adjusted"] = (t22, price_adjusted_block(tables["2022"][1], inds, ratio))

    checks = {f"ICIO {y}": IC.balance_report(t) for y, (t, _) in tables.items() if "adjusted" not in y}
    for y, (t, blk) in tables.items():
        pos = blk["X"] > 0                            # T (households as employers) has no Philippine output
        checks.setdefault(f"ICIO {y}", {})["max |column sum - 1| of PHL coefficients (industries with output)"] = \
            float(np.abs(blk["colsum"][pos] - 1).max())
        checks[f"ICIO {y}"]["PHL industries without output"] = ", ".join(np.array(inds)[~pos]) or "none"

    # ---- results by variant, table and shock
    summary, by_ind = [], {}
    for sname, sh in shocks.items():
        for y, (t, blk) in tables.items():
            res = national_variants(blk, inds, sh)
            if "adjusted" not in y:
                res["V4 global value chains"] = global_variant(t, sh)
            for v, r in res.items():
                summary.append({"shock": sname, "table": f"ICIO {y}", "variant": v, "CPI (%)": r["cpi"] * 100,
                                "PPI, output-weighted (%)": r["ppi"] * 100})
                by_ind[(sname, f"ICIO {y}", v)] = r
    # PSA 2018, the project's I-O price model (infinity_gem.iomodel; check I1)
    sys.path.insert(0, str(ROOT))
    from infinity_gem.iomodel import IOTable           # noqa: E402
    io = IOTable()
    psa = {}
    for sname, sh in shocks.items():
        ps = io.price_summary({"Crude petroleum and natural gas": sh["B06"], "Coke and refined petroleum products": sh["C19"]})
        psa[sname] = ps
        summary.append({"shock": sname, "table": "PSA 2018 (80 industries)", "variant": "project's I-O price model (iomodel.price)",
                        "CPI (%)": ps["cpi"] * 100, "PPI, output-weighted (%)": ps["ppi"] * 100})
    i1 = io.price_summary({"Coke and refined petroleum products": 0.10})
    c19_only = {}
    for y, (t, blk) in tables.items():
        r = national_variants(blk, inds, {"C19": 0.10})["V3 PSA-style total table"]
        c19_only[f"ICIO {y}"] = (r["cpi"] * 100, r["ppi"] * 100)
    summ = pd.DataFrame(summary).set_index(["shock", "table", "variant"])

    # ---- by industry (2022, each shock): direct, indirect, total, per variant
    ind_rows = []
    for (sname, tab, v), r in by_ind.items():
        if tab != "ICIO 2022":
            continue
        for j, k in enumerate(inds):
            ind_rows.append({"shock": sname, "variant": v, "industry": k, "name": IC.INDUSTRY_NAMES[k],
                             "direct (%)": r["direct"][j] * 100, "indirect (%)": (r["total"][j] - r["direct"][j]) * 100,
                             "total (%)": r["total"][j] * 100})
    ind_df = pd.DataFrame(ind_rows)

    # ---- comparison by group with PSA 2018 (V3, the same formula as iomodel.price)
    first = next(iter(shocks))
    comp = pd.DataFrame({
        "PSA 2018: project's I-O model (%)": by_group_psa(psa[first]["dp"].values, io.X),
        **{f"ICIO {y}: V3 PSA-style (%)": by_group_icio(by_ind[(first, f"ICIO {y}", "V3 PSA-style total table")]["total"],
                                                         tables[y][1]["X"], inds) for y in tables},
        "ICIO 2022: V2 with imported oil (%)": by_group_icio(by_ind[(first, "ICIO 2022", "V2 with imported oil inputs")]["total"],
                                                              tables["2022"][1]["X"], inds),
        "ICIO 2022: V4 global (%)": by_group_icio(by_ind[(first, "ICIO 2022", "V4 global value chains")]["total"],
                                                  tables["2022"][1]["X"], inds),
    }) * 100
    # oil cost shares by group: PSA 2018 total coefficients, ICIO 2018 and 2022 (domestic + imported)
    psa_share = io.A[21] + io.A[35]
    shares = pd.DataFrame({"PSA 2018 (% of output)": by_group_psa(psa_share, io.X) * 100,
                           **{f"ICIO {y} (% of output)": by_group_icio(
                               sum(tables[y][1][m][inds.index(k)] for m in ("Ad", "Am") for k in OIL), tables[y][1]["X"], inds) * 100
                              for y in tables}})

    # electricity's fuel inputs: PSA 2018 (Electricity column) and the ICIO blocks (D column), domestic + imported
    je = io.names.index("Electricity")
    fuel = {"PSA 2018 (Electricity)": {"coal (% of output)": io.A[io.names.index("Coal"), je] * 100,
                                       "crude petroleum and natural gas (% of output)": io.A[21, je] * 100,
                                       "refined petroleum and coke (% of output)": io.A[35, je] * 100}}
    for y in tables:
        blk = tables[y][1]
        jd = inds.index("D")
        g = lambda k: (blk["Ad"][inds.index(k), jd] + blk["Am"][inds.index(k), jd]) * 100
        fuel[f"ICIO {y} (D)"] = {"coal (% of output)": g("B05"), "crude petroleum and natural gas (% of output)": g("B06"),
                                 "refined petroleum and coke (% of output)": g("C19")}
    fuel = pd.DataFrame(fuel)

    # ---- observed CPI and the model's matching items
    obs = cpi_observed()
    central = [s for s in shocks if s.startswith("central")]
    model_items = {}
    if central:
        sname = central[0]
        for tab in ("ICIO 2022", "ICIO 2022 price-adjusted") + (("ICIO 2018",) if t18 is not None else ()):
            for v in ("V2 with imported oil inputs", "V4 global value chains"):
                r = by_ind.get((sname, tab, v))
                if r is None:
                    continue
                g = lambda k: r["total"][inds.index(k)] * 100
                model_items[f"{tab}, {v}"] = {"All items (CPI)": r["cpi"] * 100, "Electricity (D)": g("D"),
                                              "Land transport (H49)": g("H49"), "Air transport (H51)": g("H51"),
                                              "Water transport (H50)": g("H50"), "Refined products (C19, basic prices)": g("C19"),
                                              "Food, beverages, tobacco (C10T12)": g("C10T12"), "Agriculture (A01)": g("A01")}
        ps = psa[sname]
        model_items["PSA 2018, project's I-O model"] = {
            "All items (CPI)": ps["cpi"] * 100, "Electricity (D)": float(ps["dp"]["Electricity"]) * 100,
            "Land transport (H49)": float(ps["dp"]["Land transport"]) * 100, "Air transport (H51)": float(ps["dp"]["Air transport"]) * 100,
            "Water transport (H50)": float(ps["dp"]["Water transport"]) * 100,
            "Refined products (C19, basic prices)": float(ps["dp"]["Coke and refined petroleum products"]) * 100,
            "Food, beverages, tobacco (C10T12)": float(ps["dp"]["Food products"]) * 100,
            "Agriculture (A01)": float(by_group_psa(ps["dp"].values, io.X)["Agriculture"]) * 100}
    model_items = pd.DataFrame(model_items)
    # electricity with domestic B06 (Malampaya gas) NOT shocked: sensitivity
    elec_note = ""
    if central:
        sh = dict(shocks[central[0]])
        blk = tables["2022"][1]
        K = [inds.index("C19")]
        s = np.zeros(len(inds))
        s[inds.index("C19")] = sh["C19"]
        s_imp = s.copy()
        s_imp[inds.index("B06")] = sh["B06"]
        dp = _solve_given(blk["Ad"], K, s[K], extra=blk["Am"].T @ s_imp)   # domestic B06 endogenous (cost-based), imports shocked
        elec_note = (f"Sensitivity: with domestic B06 (mostly Malampaya natural gas) priced at cost instead of at the oil shock, "
                     f"electricity (D) rises {dp[inds.index('D')] * 100:.2f}% instead of "
                     f"{by_ind[(central[0], 'ICIO 2022', 'V2 with imported oil inputs')]['total'][inds.index('D')] * 100:.2f}% (V2, 2022).")

    # ---- write the derived tables (small) and the report
    OUT = IC.OUT_DIR
    base = f"icio_oil_cost_push_{stamp}"
    summ.to_csv(OUT / f"{base}_summary.csv")
    ind_df.to_csv(OUT / f"{base}_by_industry_2022.csv", index=False)
    comp.to_csv(OUT / f"{base}_vs_psa2018_by_group.csv")
    shares.to_csv(OUT / f"{base}_oil_cost_shares_by_group.csv")
    fuel.to_csv(OUT / f"{base}_electricity_fuel_inputs.csv")
    obs.to_csv(OUT / f"{base}_cpi_observed_2026.csv")
    model_items.to_csv(OUT / f"{base}_model_items_vs_cpi.csv")

    top = ind_df[(ind_df["shock"] == (central[0] if central else first)) & (ind_df["variant"] == "V2 with imported oil inputs")]
    top = top.sort_values("total (%)", ascending=False).head(15).set_index(["industry", "name"])[["direct (%)", "indirect (%)", "total (%)"]]
    wide = ind_df[ind_df["shock"] == (central[0] if central else first)].pivot_table(index=["industry", "name"], columns="variant",
                                                                                values="total (%)", sort=False)
    L = [f"# Oil cost push on the OECD ICIO Philippine block (a), {dt.datetime.now():%d %b %Y %H:%M}", "",
         "**NOT FOR CITATION** (research). Script: `research/icio/oil_cost_push_2022.py`. Data: OECD (2025), OECD Inter-Country "
         "Input-Output Tables, https://oe.cd/icio (small version, read from a copy outside this repository; terms of use not stated, so no "
         "raw data are kept here). Method, variants and caveats: the script's notes.", "",
         "## Accounting checks", "", pd.DataFrame(checks).map(lambda x: f"{x:.3g}" if isinstance(x, float) else x).to_markdown(), "",
         f"Price adjustment for 2022: Dubai (World Bank Pink Sheet) 2022 average US${p22:.1f}/bbl, January-February 2026 "
         f"US${p26:.1f}/bbl: the oil rows are valued at {ratio:.3f} x their 2022 price (volumes held).", "",
         "## Consumer and producer prices, all variants (% change)", "", summ.to_markdown(floatfmt=".2f"), "",
         f"Check against I1: refined petroleum alone +10% gives CPI +{i1['cpi'] * 100:.4f} pp and PPI +{i1['ppi'] * 100:.4f} pp on "
         "PSA's 2018 table (regression values 0.6832 and 0.8051); the same shock on the ICIO blocks (V3): "
         + "; ".join(f"{k} CPI +{a:.3f}, PPI +{b:.3f}" for k, (a, b) in c19_only.items()) + ".", "",
         f"## By industry, {central[0] if central else first}, ICIO 2022 (% change, total)", "",
         wide.to_markdown(floatfmt=".2f"), "",
         "## Largest increases, V2 (domestic and imported oil inputs), ICIO 2022: direct and indirect", "",
         top.to_markdown(floatfmt=".2f"), "",
         f"## Against PSA's 2018 table (the project's I-O price model), {first}, by comparison group (% change)", "",
         comp.to_markdown(floatfmt=".2f"), "",
         "## Oil cost shares (B06 + C19 inputs, domestic and imported, % of output)", "", shares.to_markdown(floatfmt=".2f"), "",
         "## Electricity's fuel inputs (domestic and imported, % of output)", "", fuel.to_markdown(floatfmt=".2f"), "",
         "For comparison, DOE's gross generation by plant type (2025 Power Statistics, `data/raw/energy/`): 2018 coal 52%, "
         "natural gas 21%, oil-based 3%; 2022 coal 60%, natural gas 16%, oil-based 2%.", "",
         "## Observed 2026 consumer prices (PSA CPI, 2018 = 100)", "", obs.to_markdown(floatfmt=".1f"), "",
         "## The models' matching items for the 2026 scenarios' 2026 shock (% change, full pass-through)", "",
         model_items.to_markdown(floatfmt=".2f"), "", elec_note, "",
         f"Derived tables: `outputs/{base}_*.csv`.", ""]
    rep = OUT / f"{base}.md"
    rep.write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))
    print(f"\nWrote {rep}")


if __name__ == "__main__":
    main()
