"""Household detail on consistent model results (0.3.1): deciles, families and persons in poverty,
food equivalents, an optional net-seller adjustment, and the price-only method kept as a check.

    from infinity_gem.household import HouseholdDetail
    hd = HouseholdDetail()
    g = hd.group_effects(model, base, sim)        # one CGE run: prices AND incomes by the SAM's ten household groups
    hd.deciles(g); hd.poverty(g); hd.food_equivalents(hd.deciles(g))
    hd.price_only(0.0154)                         # the price-only method (check)

Why: The "hybrid" method combines CGE or I-O inflation with a price-only FIES count and separate I-O jobs, so its
prices and incomes come from different models. Here every number comes from ONE model run: each FIES 2023 family carries
its SAM group's inflation (the group's own budget shares) and its group's nominal income change (as in an earlier decile analysis).
  Price effect  = family spending (TOTEX) x group inflation: the extra cost of the same basket.
  Income effect = family income (TOINC) x the fall in the group's nominal income YH (lost wages, profits, transfers).
  Total loss    = price effect + income effect. FIES 2023 pesos, one year.
Poverty uses the same real-consumption factor as infinity_gem.microsim (spending EH over the group price index), so the
persons count equals Infinity GEM's published "new poor"; families are counted with RFACT, persons with MEM_RFACT.
Deciles: PSA's per-person income deciles (NPCINC) by default; ranking="total_income" ranks families by total income
(weighted, as Stata's xtile [pw=rfact] in a do-file).

Net-seller adjustment (optional; the "net benefit ratio" idea usually credited to Deaton 1989, Economic Journal, on Thai
rice prices: cited from memory, the paper is not on file yet): farm and fishing families gain when the prices of what they sell rise.
FIES records net entrepreneurial income by activity (NET_CFG crops, NET_LPR livestock, NET_FISH fishing). The group's
income change already contains its AVERAGE farm income, so the adjustment only moves income WITHIN each group: a family
gains (NET_x - group average NET_x) x the producer-price change of x. Group totals are unchanged. An approximation: net
income is assumed to move with the output price (costs held), so it is an upper bound on the redistribution.

LFS link (0.3.1, 8 Oct 2026): PSA's own FIES-LFS 2023 public-use file has every household
member's industry (LC16_PKB, 2009 PSIC), class of worker, basic pay and hours (January 2024 LFS round). It is licensed
to the person who downloaded it, so it is read from paths.FIES_LFS_DIR (outside the repository); without it the LFS
options are unavailable. Each family's labour earnings are split by PSA's 16 industries:
  - wages (FIES WAGES) over its wage-earning members (private household, private establishment, government, paid family
    work), in proportion to their basic pay per day (equal shares where pay is missing);
  - entrepreneurial income by the activity FIES records it under: crops, livestock, fishing, forestry -> agriculture;
    trade, manufacturing, transport -> those industries; "not elsewhere classified" -> the industries of the family's
    self-employed, employer and unpaid family members (equal shares; other services if none). Losses (negatives) -> 0.
A model run gives each industry's change in labour income (CGE: wages x employment by activity; I-O: output change):
  - CGE: the change moves income WITHIN each household group (as the net-seller adjustment): a family whose workers are
    in hard-hit industries loses more than its group average, others less; group totals stay as the model has them;
  - I-O (16 industries; no household incomes in the model): the earnings change is the income effect itself, an upper
    bound (output change applied to earnings one for one), with no price effect.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import paths

# Retail prices for the food equivalents (8 Oct 2026): PSA's statistical tables
# of the Price Situationer, second phase of September 2026 (released 30 Sept 2026), national averages, extracted by
# tools/extract_psa_price_tables.py. Until 8 Oct the first phase (1-5 Sept, special release 2026-SSO-155, file
# PSA_retail_prices_2026-09_phase1.csv) was used; PSA later revised most of those values slightly. An earlier chicken price, PHP 212.70/kg, is almost certainly PSA's original first-phase figure (revised to 212.77; second phase 212.24).
PRICES = paths.DATA_RAW / "prices" / "PSA_retail_prices_2026-09_statistical_tables.csv"
PRICE_COLUMN = "price_php_second_phase_sep_2026"
PRICE_PERIOD = "second phase of September 2026 (PSA Price Situationer statistical tables, released 30 Sept 2026)"
FOOD_ITEMS = ["Rice, regular milled", "Chicken egg, medium", "Galunggong", "Dressed chicken"]
# SAM commodities whose producer price moves the net income of each FIES activity (net-seller adjustment)
NET_SELLER = {"NET_CFG": ["cmaiz", "crice", "cpuls", "coils", "croot", "cvege", "csugr", "ctoba", "ccott", "cfrui", "ccoff", "cocrp"],
              "NET_LPR": ["ccatt", "cpoul", "coliv"],
              "NET_FISH": ["cfish"]}
COLS = ["W_REGN", "W_PROV", "SEQ_NO", "FSIZE", "TOINC", "TOTEX", "FOOD", "RFACT", "MEM_RFACT", "URB", "NPCINC", "WAGES",
        "NET_CFG", "NET_LPR", "NET_FISH", "NET_FOR", "NET_RET", "NET_MFG", "NET_TRANS", "NET_NEC_A8", "NET_NEC_A9", "NET_NEC_A10"]

# PSA's 16 industries (as infinity_gem.dynamic.PSA_INDUSTRIES and the GVA tables) from 2009 PSIC divisions (first two digits;
# sections as in ISIC Rev. 4, which PSIC 2009 follows)
PSA16 = ["Agriculture, forestry, and fishing", "Mining and quarrying", "Manufacturing",
         "Electricity, steam, water and waste management", "Construction",
         "Wholesale and retail trade; repair of motor vehicles and motorcycles", "Transportation and storage",
         "Accommodation and food service activities", "Information and communication", "Financial and insurance activities",
         "Real estate and ownership of dwellings", "Professional and business services",
         "Public administration and defense; compulsory social activities", "Education",
         "Human health and social work activities", "Other services"]
_DIV = [(1, 3, 0), (5, 9, 1), (10, 33, 2), (35, 39, 3), (41, 43, 4), (45, 47, 5), (49, 53, 6), (55, 56, 7), (58, 63, 8),
        (64, 66, 9), (68, 68, 10), (69, 82, 11), (84, 84, 12), (85, 85, 13), (86, 88, 14), (90, 99, 15)]
ENTREPRENEURIAL = {"NET_CFG": 0, "NET_LPR": 0, "NET_FISH": 0, "NET_FOR": 0, "NET_RET": 5, "NET_MFG": 2, "NET_TRANS": 6}
NEC = ["NET_NEC_A8", "NET_NEC_A9", "NET_NEC_A10"]


def psic_to_psa16(code) -> int:
    """Index in PSA16 of a 4-digit 2009 PSIC code (string or number); -1 if missing or unknown."""
    try:
        div = int(str(code).strip().zfill(4)[:2])
    except ValueError:
        return -1
    return next((k for lo, hi, k in _DIV if lo <= div <= hi), -1)


def norm_industry(name: str) -> str:
    """Match industry names across PSA tables (the I-O table writes 'Public Administration and Defense; Compulsory
    social security')."""
    n = name.lower()
    return PSA16[12] if n.startswith("public administration") else next((p for p in PSA16 if p.lower() == n), name)


def weighted_deciles(x: pd.Series, w: pd.Series, q: int = 10) -> pd.Series:
    """Weighted quantile groups, as Stata's xtile with [pw=]: sort, cumulate weights, cut at equal shares."""
    o = np.argsort(x.values, kind="mergesort")
    cw = np.cumsum(w.values[o]) / w.sum()
    d = np.empty(len(x), int)
    d[o] = np.minimum((cw * q - 1e-12).astype(int) + 1, q)
    return pd.Series(d, index=x.index)


class HouseholdDetail:
    def __init__(self, puf=None, povlines=None):
        f = pd.read_csv(puf or paths.FIES_PUF, usecols=COLS)
        p = pd.read_csv(povlines or paths.FIES_POVLINES, usecols=["w_prov", "toinc", "pline_2023", "fline_2023"])
        if len(f) != len(p) or (f["W_PROV"].values != p["w_prov"].values).any() or np.abs(f["TOINC"].values - p["toinc"].values).max() > 1e-6:
            raise ValueError("The FIES household file and the poverty-line extract are not in the same order")
        f["PLINE"], f["FLINE"] = p["pline_2023"].values, p["fline_2023"].values
        f["PCI"] = f["TOINC"] / f["FSIZE"]
        f["grp"] = np.where(f["URB"] == 1, "hhd-u", "hhd-r") + np.ceil(f["NPCINC"] / 2).astype(int).astype(str)
        f["dec_total"] = weighted_deciles(f["TOINC"], f["RFACT"])
        self.f = f
        self._earn = None

    # ------------------------------------------------------------------ LFS link
    @staticmethod
    def lfs_available() -> bool:
        return paths.FIES_LFS_MEMBERS.exists()

    def members(self) -> pd.DataFrame:
        """PSA FIES-LFS 2023 household members (licensed; read from paths.FIES_LFS_DIR), with PSA-16 industry index."""
        if not self.lfs_available():
            raise FileNotFoundError(f"PSA's FIES-LFS member file is not on this computer ({paths.FIES_LFS_MEMBERS}); "
                                    "download it from PSADA (FIES-LFS Merge, 2023) and set INFINITY_GEM_FIES_LFS")
        cols = ["W_REGN", "W_PROV", "SEQ_NO", "LC101_LNO", "LC16_PKB", "LC23_PCLASS", "LC25_PBASIC", "LC28_THOURS",
                "NEWEMPSTAT", "PWGTPRV"]
        m = pd.read_csv(paths.FIES_LFS_MEMBERS, usecols=cols, dtype=str, encoding="utf-8-sig")
        for c in ("W_REGN", "W_PROV", "SEQ_NO"):
            m[c] = m[c].astype(int)
        m["emp"] = m["NEWEMPSTAT"].str.strip() == "1"
        m["ind"] = m["LC16_PKB"].map(psic_to_psa16)
        m["cls"] = pd.to_numeric(m["LC23_PCLASS"], errors="coerce")
        m["pay"] = pd.to_numeric(m["LC25_PBASIC"], errors="coerce")
        m["w"] = pd.to_numeric(m["PWGTPRV"], errors="coerce")
        return m

    def earnings_by_industry(self) -> pd.DataFrame:
        """Each family's labour earnings by PSA industry (₱ a year, FIES 2023), rows aligned with self.f. See the module
        notes for the allocation of wages and entrepreneurial income."""
        if self._earn is not None:
            return self._earn
        f, m = self.f, self.members()
        key = ["W_REGN", "W_PROV", "SEQ_NO"]
        hid = pd.Series(np.arange(len(f)), index=pd.MultiIndex.from_frame(f[key].astype(int)))
        m["h"] = hid.reindex(pd.MultiIndex.from_frame(m[key])).values
        if m["h"].isna().any():
            raise ValueError(f"{int(m['h'].isna().sum())} members do not match a FIES household")
        m["h"] = m["h"].astype(int)
        E = np.zeros((len(f), len(PSA16)))
        # wages over wage earners, by basic pay (households' mean pay where missing; equal shares if none reported)
        wm = m[m["emp"] & m["cls"].isin([0, 1, 2, 5]) & (m["ind"] >= 0)].copy()
        wm["pay"] = wm["pay"].fillna(wm.groupby("h")["pay"].transform("mean")).fillna(1.0).clip(lower=1e-9)
        wm["share"] = wm["pay"] / wm.groupby("h")["pay"].transform("sum")
        wages = f["WAGES"].clip(lower=0).values
        np.add.at(E, (wm["h"].values, wm["ind"].values), wages[wm["h"].values] * wm["share"].values)
        no_wage_earner = np.setdiff1d(np.flatnonzero(wages > 0), wm["h"].unique())
        E[no_wage_earner, 15] += wages[no_wage_earner]           # wages but no wage earner recorded: other services
        # entrepreneurial income by activity
        for c, k in ENTREPRENEURIAL.items():
            E[:, k] += f[c].clip(lower=0).values
        sm = m[m["emp"] & m["cls"].isin([3, 4, 6]) & (m["ind"] >= 0)].copy()
        sm["share"] = 1.0 / sm.groupby("h")["ind"].transform("size")
        nec = f[NEC].clip(lower=0).sum(axis=1).values
        np.add.at(E, (sm["h"].values, sm["ind"].values), nec[sm["h"].values] * sm["share"].values)
        no_self = np.setdiff1d(np.flatnonzero(nec > 0), sm["h"].unique())
        E[no_self, 15] += nec[no_self]
        self._earn = pd.DataFrame(E, columns=PSA16, index=f.index)
        return self._earn

    @staticmethod
    def industry_change_from_cge(model, base, sim) -> pd.Series:
        """% change in labour income (wage x employment, all labour types) paid by each PSA industry in a CGE run."""
        from .dynamic import PSA_INDUSTRIES
        labs = [i for i, f_ in enumerate(model.F) if f_.startswith("flab")]
        emp = lambda sol: sol["QF"][labs] + (sol["QFH"][labs] if "QFH" in sol else 0.0)   # 0.3.11: hoarded workers are paid
        b = (base["W"][labs] * emp(base)).sum(axis=0)              # W: factor price by activity (F x A); QF: quantities
        s = (sim["W"][labs] * emp(sim)).sum(axis=0)
        out = {}
        for name, acts in PSA_INDUSTRIES.items():
            ix = [model.A.index(a) for a in acts if a in model.A]
            out[name] = (s[ix].sum() / b[ix].sum() - 1) * 100 if ix and b[ix].sum() else 0.0
        return pd.Series(out)

    def lfs_earnings_change(self, ind_pct: pd.Series) -> pd.Series:
        """Change in each family's labour earnings (₱ a year) for industry changes in % (PSA-16 names)."""
        E = self.earnings_by_industry()
        pct = pd.Series({norm_industry(k): v for k, v in ind_pct.items()}).reindex(PSA16).fillna(0.0)
        return pd.Series(E.values @ (pct.values / 100), index=self.f.index)

    # ------------------------------------------------------------------ model results by household group
    @staticmethod
    def group_effects(model, base, sim) -> pd.DataFrame:
        """For each SAM household group: inflation (its own price index, %), nominal income change (YH, %), nominal
        spending change (EH, %), the real-consumption factor used for poverty (as infinity_gem.microsim), and producer-price
        changes for the net-seller adjustment."""
        rows = {}
        for i, h in enumerate(model.H):
            w = model.beta[:, i]
            p_b, p_s = float(w @ base["PQ"]), float(w @ sim["PQ"])
            wh = getattr(model, "beta_h", None)                    # own produce (home="separate"), at producer prices
            if wh is not None and wh[:, i].any():
                p_b += float(wh[:, i] @ base["PX"])
                p_s += float(wh[:, i] @ sim["PX"])
            rows[h] = {"inflation_pct": (p_s / p_b - 1) * 100,
                       "income_pct": (sim["YH"][i] / base["YH"][i] - 1) * 100,
                       "spending_pct": (sim["EH"][i] / base["EH"][i] - 1) * 100,
                       "real_factor": (sim["EH"][i] / base["EH"][i]) / (p_s / p_b)}
        g = pd.DataFrame(rows).T
        for k, coms in NET_SELLER.items():           # output-weighted producer-price change of what each activity sells
            ix = [model.C.index(c) for c in coms if c in model.C]
            wq = model.QX0[ix] if hasattr(model, "QX0") else np.ones(len(ix))
            g.attrs[f"dp_{k}"] = float((sim["PX"][ix] / base["PX"][ix] - 1) @ wq / wq.sum()) if ix else 0.0
        g.attrs["industry_pct"] = HouseholdDetail.industry_change_from_cge(model, base, sim).to_dict()   # for the LFS link
        return g

    def _lfs_adjustment(self, g: pd.DataFrame) -> pd.Series:
        """Within-group redistribution of the labour-income change by each family's industries (₱; a gain is positive).
        Group totals are unchanged: sum over a group of RFACT x adjustment = 0."""
        f = self.f
        dE = self.lfs_earnings_change(pd.Series(g.attrs["industry_pct"]))
        r = (dE * f["RFACT"]).groupby(f["grp"]).sum() / (f["TOINC"] * f["RFACT"]).groupby(f["grp"]).sum()
        return dE - f["TOINC"] * f["grp"].map(r)

    def _family_effects(self, g: pd.DataFrame, net_seller: bool = False, lfs: bool = False) -> pd.DataFrame:
        f = self.f
        e = pd.DataFrame(index=f.index)
        e["infl"] = f["grp"].map(g["inflation_pct"])
        e["price"] = f["TOTEX"] * e["infl"] / 100
        e["income"] = -f["TOINC"] * f["grp"].map(g["income_pct"]) / 100
        if net_seller:
            for k in NET_SELLER:
                dp = g.attrs.get(f"dp_{k}", 0.0)
                avg = (f[k] * f["RFACT"]).groupby(f["grp"]).sum() / f["RFACT"].groupby(f["grp"]).sum()
                e["income"] -= (f[k] - f["grp"].map(avg)) * dp        # a gain lowers the loss; group totals unchanged
        if lfs:
            e["income"] -= self._lfs_adjustment(g)                     # 0.3.1: by each family's industries (LFS link)
        e["total"] = e["price"] + e["income"]
        return e

    # ------------------------------------------------------------------ deciles
    def deciles(self, g: pd.DataFrame, ranking: str = "psa", net_seller: bool = False, lfs: bool = False) -> pd.DataFrame:
        """Per decile: inflation, price effect, lost income and total loss (per family, total, % of income).
        ranking: 'psa' (PSA per-person income deciles, NPCINC) or 'total_income' (families ranked by total income).
        lfs: lost earnings follow each family's industries within its group (LFS link; needs the FIES-LFS member file)."""
        return self._decile_table(self._family_effects(g, net_seller, lfs), ranking)

    def _decile_table(self, e: pd.DataFrame, ranking: str) -> pd.DataFrame:
        if ranking not in ("psa", "total_income"):
            raise ValueError("ranking must be 'psa' or 'total_income'")
        f = self.f
        dec = f["NPCINC"] if ranking == "psa" else f["dec_total"]
        groups = [(f"{d}" + (" (poorest 10%)" if d == 1 else " (richest 10%)" if d == 10 else ""), dec == d) for d in range(1, 11)]
        groups += [("Bottom 30% (deciles 1-3)", dec <= 3), ("All families", dec > 0)]
        rows = {}
        for name, sel in groups:
            w = f.loc[sel, "RFACT"]
            wsum, inc = w.sum(), (f.loc[sel, "TOINC"] * w).sum()
            d = e[sel]
            rows[name] = {
                "Families (million)": wsum / 1e6,
                "Average income per family (₱)": inc / wsum,
                "Inflation (pp)": (d["infl"].fillna(0) * f.loc[sel, "TOTEX"] * w).sum() / (f.loc[sel, "TOTEX"] * w).sum(),
                "Price effect: average per family (₱)": (d["price"] * w).sum() / wsum,
                "Price effect: total (₱ million)": (d["price"] * w).sum() / 1e6,
                "Price effect (% of income)": (d["price"] * w).sum() / inc * 100,
                "Lost income: average per family (₱)": (d["income"] * w).sum() / wsum,
                "Total loss: average per family (₱)": (d["total"] * w).sum() / wsum,
                "Total loss: total (₱ million)": (d["total"] * w).sum() / 1e6,
                "Total loss (% of income)": (d["total"] * w).sum() / inc * 100,
            }
        return pd.DataFrame(rows).T

    # ------------------------------------------------------------------ poverty, families and persons
    def _counts(self, pci) -> dict:
        f = self.f
        poor, fpoor = pci < f["PLINE"], pci < f["FLINE"]
        return {"Poor families": float(f.loc[poor, "RFACT"].sum()), "Poor persons": float(f.loc[poor, "MEM_RFACT"].sum()),
                "Food-poor families": float(f.loc[fpoor, "RFACT"].sum()), "Food-poor persons": float(f.loc[fpoor, "MEM_RFACT"].sum())}

    def poverty(self, g: pd.DataFrame, lfs: bool = False) -> pd.DataFrame:
        """Families and persons below the official 2023 poverty and food lines, before and after (real-consumption factor
        by group, as infinity_gem.microsim). lfs: plus each family's within-group earnings adjustment (LFS link), deflated by
        its group's price index. Rows: baseline, after, change."""
        f = self.f
        pci = f["PCI"] * f["grp"].map(g["real_factor"]).fillna(1.0)
        if lfs:
            pci = pci + self._lfs_adjustment(g) / f["FSIZE"] / (1 + f["grp"].map(g["inflation_pct"]) / 100)
        return self._before_after(pci)

    def _before_after(self, pci) -> pd.DataFrame:
        b, s = self._counts(self.f["PCI"]), self._counts(pci)
        return pd.DataFrame({"Baseline (FIES 2023)": b, "After the shock": s,
                             "Change": {k: s[k] - b[k] for k in b}})

    # ------------------------------------------------------------------ I-O runs: earnings only (LFS link)
    def earnings_only(self, ind_pct, ranking: str = "psa") -> dict:
        """For a model without household incomes or prices (the 16-industry I-O demand model): each family's labour
        earnings change by its industries' output change (%), applied one for one (an upper bound, like job-equivalents).
        Returns {'deciles', 'poverty', 'earnings_change'}. ind_pct: {industry name: %} (I-O or PSA names)."""
        f = self.f
        dE = self.lfs_earnings_change(pd.Series(ind_pct))
        e = pd.DataFrame({"infl": 0.0, "price": 0.0, "income": -dE}, index=f.index)
        e["total"] = e["income"]
        dec = self._decile_table(e, ranking).drop(columns=["Inflation (pp)", "Price effect: average per family (₱)",
                                                           "Price effect: total (₱ million)", "Price effect (% of income)"])
        return {"deciles": dec, "poverty": self._before_after(f["PCI"] + dE / f["FSIZE"]), "earnings_change": dE}

    # ------------------------------------------------------------------ food equivalents
    @staticmethod
    def retail_prices() -> pd.DataFrame:
        pr = pd.read_csv(PRICES, comment="#").set_index("item")
        return pr.assign(price_php=pr[PRICE_COLUMN])

    def food_equivalents(self, dec: pd.DataFrame, row: str = "Bottom 30% (deciles 1-3)", items=FOOD_ITEMS) -> pd.DataFrame:
        """The monthly loss of an average family in `row`, in quantities of food at PSA's retail prices (national averages,
        PRICE_PERIOD). Losses are in FIES 2023 pesos; the prices are 2026 prices (state this)."""
        pr = self.retail_prices()
        out = {}
        for label, col in (("Price effect", "Price effect: average per family (₱)"), ("Total loss", "Total loss: average per family (₱)")):
            monthly = float(dec.loc[row, col]) / 12
            out[label] = {"Monthly loss per family (₱)": monthly,
                          **{f"{it} ({pr.loc[it, 'unit']}, at ₱{pr.loc[it, 'price_php']:.2f})": monthly / pr.loc[it, "price_php"] for it in items}}
        return pd.DataFrame(out)

    # ------------------------------------------------------------------ the price-only method (a check)
    def price_only(self, pi_b30: float, pi_rest: float | None = None, ranking: str = "total_income") -> dict:
        """The price-only method, reproduced exactly from public FIES 2023 (8 Oct 2026, 32 of 32 figures):
        purchasing-power loss = TOINC x pi / (1 + pi), deciles ranked by total family income (the original do-file); poverty and
        food lines raised by (1 + pi_b30) for everyone; monthly loss per bottom-30% family by PSA's per-person definition.
        Prices only: lost earnings are left out. pi as a fraction (0.0154 = +1.54 pp)."""
        f = self.f
        pi_rest = pi_b30 if pi_rest is None else pi_rest
        dec = f["dec_total"] if ranking == "total_income" else f["NPCINC"]
        pi = np.where(dec <= 3, pi_b30, pi_rest)
        loss = f["TOINC"] * pi / (1 + pi)
        w = f["RFACT"]
        tab = pd.DataFrame({"Loss: average per family (₱)": (loss * w).groupby(dec).sum() / w.groupby(dec).sum(),
                            "Loss: total (₱ million)": (loss * w).groupby(dec).sum() / 1e6})
        tab.index = [f"{d}" + (" (poorest 10%)" if d == 1 else " (richest 10%)" if d == 10 else "") for d in tab.index]
        b30 = dec <= 3
        tab.loc["Bottom 30% (deciles 1-3)"] = [float((loss * w)[b30].sum() / w[b30].sum()), float((loss * w)[b30].sum() / 1e6)]
        tab.loc["All families"] = [float((loss * w).sum() / w.sum()), float((loss * w).sum() / 1e6)]
        base = self._counts(f["PCI"])
        pf = f["PCI"] < f["PLINE"] * (1 + pi_b30)
        ff = f["PCI"] < f["FLINE"] * (1 + pi_b30)
        new = {"New poor families": float(f.loc[pf, "RFACT"].sum()) - base["Poor families"],
               "New poor persons": float(f.loc[pf, "MEM_RFACT"].sum()) - base["Poor persons"],
               "New food-poor families": float(f.loc[ff, "RFACT"].sum()) - base["Food-poor families"],
               "New food-poor persons": float(f.loc[ff, "MEM_RFACT"].sum()) - base["Food-poor persons"]}
        b30pc = f["NPCINC"] <= 3
        inc = float(np.average(f.loc[b30pc, "TOINC"], weights=w[b30pc]))
        monthly = inc * pi_b30 / (1 + pi_b30) / 12
        return {"deciles": tab, "poverty": new, "monthly_loss_b30_per_person_def": monthly, "b30_average_income": inc}
