"""The macro-micro link file: what one CGE run hands to a household microsimulation (0.3.5, 14 Oct 2026).

The macro-micro framework (Bourguignon, Bussolo and Pereira da Silva, eds., World Bank 2008) passes a small set of
"link variables" from the model to the household survey. This module computes them from a solved CGE run, writes them
to a workbook and CSV files that Stata reads (a do-file applies them to FIES-LFS), and gives each FIES
family its OWN inflation from its own spending mix.

    from infinity_gem.microlink import MicroLink
    ml = MicroLink(model)                      # FIES 2023 categories <-> SAM commodities, fixed for this model
    link = ml.link_variables(model, base, sim) # dict of tables (prices, industries, groups, factors, concordance)
    pi = ml.family_inflation(link)             # % per FIES family, its own basket
    ml.poverty(link, pi); ml.deciles(link, pi) # new poor and deciles with family inflation (HouseholdDetail rules)
    ml.write(link, "outputs/Infinity_GEM_micro_link_<scenario>_<date>.xlsx")

Link variables (sheets of the workbook; same names as the CSV files):
  fies_categories  FIES 2023 spending categories: national spending, budget share, price change (%) and the SAM
                   commodities behind each one. Each family's inflation = its budget shares x these changes.
  commodities      the 42 SAM commodities: household budget share, consumer price PQ (%), producer price PX (%).
  industries       PSA's 16 industries (as in the LFS, LC16_PKB): labour income (%), employment (%), average wage (%).
  household_groups the SAM's 10 household groups (urban/rural x quintile): inflation, nominal income and spending (%),
                   and the real-consumption factor that Infinity GEM's poverty count uses.
  factors          average price change of each factor (low/medium/high-skill labour, land, capital).
  net_seller       producer-price change of crops, livestock and fish (the net-seller adjustment).
  concordance      the FIES category x SAM commodity weights (see below).
  expected_results new poor and decile losses computed here, for a Stata run to be checked against.

FIES categories <-> SAM commodities. FIES records spending by COICOP-type group (BREAD, MEAT, ... TRANSPORT); the SAM
has 42 commodities, and most food is bought as processed food ('cfood': milled rice, meat products, ...), not as farm
produce. Each category is mapped to the commodities it can contain (CATEGORY_MAP, a judgement written out in full).
With the "0.3 recommended" SAM, refined petroleum (cpetr, split from chemicals: infinity_gem/oil.py) goes to UTILITIES
(LPG, kerosene) and TRANSPORT (vehicle fuel), the categories that hold fuel inside cchem in the default SAM (0.3.6,
15 Oct 2026; before, the link refused the 0.3 SAM). Commodities a model does not have are ignored, so default results
are unchanged. With the rice-split SAM (0.3.7) milled rice and corn (cmric) goes to BREAD. Infinity GEM's own SAM (0.3.9) has small household purchases of fibres, mining products, non-metallic minerals and metals, as PSA's I-O does; they go to
CLOTH, UTILITIES and FURNISHING (IFPRI's SAM has none, so its weights and results are unchanged).
fuel_split_map (0.3.9, 18 Oct 2026): on SAMs where refined petroleum is its own commodity, chemicals ('cchem') are no
longer attributed to UTILITIES and TRANSPORT (see category_map). The DEFAULT since 18 Oct 2026, about 8:20 AM; fuel_split_map=False gives the old map (the 2026 scenario numbers of 17 Oct 2026).
Each commodity's household consumption in the SAM is then shared among its categories in proportion to their FIES
spending (one proportional step of the biproportional/RAS family), giving weights W[k, c]. A category's price change is
the W-weighted average of its commodities' consumer-price changes. Two properties are tested (check ML1): if every
price rises x%, every category and every family rises x%; and the W matrix uses all household consumption in the SAM.
HOUSING_WATER is split into RENT (actual and imputed rent, FIES RENTVAL) and UTILITIES (the rest: electricity, water,
fuel, repairs), because imputed rent is half of it and moves with the real-estate price, not with fuel.

Labour channel: the industries table gives employment and wage changes separately, so a microsimulation can either cut
earnings in proportion (HouseholdDetail's LFS link) or draw which workers lose their jobs. The draws need the licensed
FIES-LFS member file and are built where it is (14 Oct 2026).
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd

from . import paths
from .household import HouseholdDetail, NET_SELLER, PSA16

# FIES 2023 categories (Household Sum file) -> SAM commodities they can contain. RENT and UTILITIES are derived (above).
CATEGORY_MAP = {
    "BREAD": ["cfood", "crice", "cmaiz", "cocer", "cmric"],        # bread and cereals, incl. rice and corn (cmric: rice-split SAM)
    "MEAT": ["cfood", "ccatt", "cpoul", "coliv"],
    "FISH": ["cfish", "cfood"],
    "MILK": ["cfood", "cpoul", "coliv"],                           # milk, cheese and eggs
    "OIL": ["cfood", "coils", "cocrp"],                            # oils and fats (coconut)
    "FRUIT": ["cfrui", "cfood", "cocrp"],
    "VEG": ["cvege", "croot", "cpuls", "cfood"],
    "SUGAR": ["cfood", "csugr"],                                   # sugar, jam, confectionery
    "FOOD_NEC": ["cfood"],
    "FRUIT_VEG": ["cbeve", "cfood"],
    "OTHER_VEG": ["cvege"],
    "COFFEE": ["ccoff", "cfood", "cbeve"],
    "TEA": ["cbeve", "cfood"],
    "COCOA": ["cbeve", "cfood"],
    "WATER": ["cbeve"],                                            # bottled water (piped water is in UTILITIES)
    "SOFTDRINKS": ["cbeve"],
    "OTHER_NON_ALCOHOL": ["cbeve"],
    "SERVICES_PRIMARY_GOODS": ["cosrv"],
    "ALCOHOL_PROCDUCTION_SERVICES": ["cosrv"],                     # PSA's spelling
    "ALCOHOL": ["cbeve"],
    "TOBACCO": ["cbeve", "cfood", "ctoba"],
    "FOOD_OUTSIDE": ["chotl"],
    "FOOD_ACCOM_SRVC": ["chotl"],
    "CLOTH": ["ctext", "ccott"],                                   # ccott: fibres (0.3.9, Infinity GEM SAM)
    "RENT": ["creal"],
    "UTILITIES": ["celec", "cwatr", "cchem", "cpetr", "ccons", "cfore",    # electricity, water, LPG/kerosene, repairs, firewood
                  "cnmet", "cmetl", "cmine"],                     # repair materials, coal (0.3.9: households buy them in PSA's I-O)
    "FURNISHING": ["coman", "cwood", "ctext", "cmach", "cchem", "cosrv", "cnmet", "cmetl"],   # + glassware, utensils (0.3.9)
    "HEALTH": ["cheal", "cchem"],
    "TRANSPORT": ["ctran", "cchem", "cpetr", "cmach"],             # fares, fuel, vehicles
    "COMMUNICATION": ["ccomm"],
    "RECREATION": ["cosrv", "ccomm", "coman"],
    "EDUCATION": ["ceduc"],
    "INSURANCE": ["cfsrv"],
    "MISCELLANEOUS": ["cchem", "cosrv", "cfsrv", "coman", "cbsrv"],  # personal care, other goods and services
    "DURABLE": ["cmach", "coman", "cwood"],
    "OCCASION": ["cfood", "chotl", "cbeve"],
    "OTHER_EXPENDITURE": ["cosrv", "cfsrv", "cpadm", "cbsrv"],
}
CATEGORIES = list(CATEGORY_MAP)
_RAW = [k for k in CATEGORIES if k not in ("RENT", "UTILITIES")] + ["HOUSING_WATER", "RENTVAL"]


def category_map(commodities, fuel_split_map: bool = True) -> dict:
    """CATEGORY_MAP as before, or (fuel_split_map=True, 0.3.9, 18 Oct 2026) the same map without chemicals ('cchem') in
    UTILITIES and TRANSPORT when the model has refined petroleum ('cpetr') as its own commodity. CATEGORY_MAP keeps 'cchem'
    there because fuel was inside chemicals before the split (0.3.6); on the split SAMs it attributes soaps, medicines
    and other chemicals to utilities and transport in proportion to FIES spending, which dilutes those categories' fuel price
    changes. Found by scenarios/oil_passthrough_by_sam.py: for a 30% oil shock the 2026 scenarios' reconciled baskets move by 0.3%
    with the fix, raw FIES baskets by 17%. Without 'cpetr' (fuel inside 'cchem') the map is unchanged. Default since 18 Oct
    2026; False = the old map."""
    if not fuel_split_map or "cpetr" not in commodities:
        return CATEGORY_MAP
    out = {k: list(v) for k, v in CATEGORY_MAP.items()}
    for k in ("UTILITIES", "TRANSPORT"):
        out[k] = [c for c in out[k] if c != "cchem"]
    return out


def fies_spending(puf=None) -> pd.DataFrame:
    """FIES 2023 family spending by CATEGORIES (₱ a year), rows in the order of HouseholdDetail().f."""
    s = pd.read_csv(puf or paths.FIES_PUF, usecols=_RAW)
    s["RENT"] = s["RENTVAL"].clip(lower=0)
    s["UTILITIES"] = (s["HOUSING_WATER"] - s["RENTVAL"]).clip(lower=0)
    return s[CATEGORIES].clip(lower=0)


def _pct(new, old):
    return (np.asarray(new, float) / np.asarray(old, float) - 1) * 100


class MicroLink:
    def __init__(self, model, hd: HouseholdDetail | None = None, puf=None, fuel_split_map: bool = True):
        self.hd = hd or HouseholdDetail(puf=puf)
        self.spend = fies_spending(puf)
        if len(self.spend) != len(self.hd.f):
            raise ValueError("FIES spending and HouseholdDetail rows differ")
        self.C = list(model.C)
        self.cmap = category_map(self.C, fuel_split_map)       # default: chemicals out of the fuel categories (0.3.9)
        self.hh_cons = pd.Series(np.asarray(model.beta, float) @ np.asarray(model.EH0, float), index=self.C)
        self.W = self._weights()
        # Reconciliation (default): FIES and the SAM weigh the basket differently (e.g. rent 13.6% of FIES spending vs
        # 'creal' 8.2% of SAM household consumption). lam[k] rescales every family's spending on category k so that the
        # national FIES basket equals the SAM's; each family keeps its own deviation from the average.
        sam_k = self.W.sum(axis=1)
        self.lam = (sam_k / sam_k.sum()) / (self.national / self.national.sum())

    def _weights(self) -> pd.DataFrame:
        """W[k, c]: SAM household consumption of commodity c attributed to FIES category k (SAM units)."""
        w = self.hd.f["RFACT"].values
        r = pd.Series((self.spend.values * w[:, None]).sum(axis=0), index=CATEGORIES)       # national FIES spending
        unmapped = [c for c in self.C if self.hh_cons[c] > 1e-12 and not any(c in v for v in self.cmap.values())]
        if unmapped:
            raise ValueError(f"household consumption with no FIES category: {unmapped}")
        W = pd.DataFrame(0.0, index=CATEGORIES, columns=self.C)
        for c in self.C:
            ks = [k for k, v in self.cmap.items() if c in v]
            if not ks or self.hh_cons[c] <= 0:
                continue
            W.loc[ks, c] = self.hh_cons[c] * r[ks] / r[ks].sum()
        empty = [k for k in CATEGORIES if W.loc[k].sum() <= 0]
        for k in empty:                     # a category whose commodities households do not buy in the SAM: equal weights
            W.loc[k, [c for c in self.cmap[k] if c in W.columns]] = 1e-12   # only commodities this model has
        self.national = r
        return W

    # ------------------------------------------------------------------ link variables
    def category_prices(self, model, base, sim) -> pd.Series:
        dp = pd.Series(_pct(sim["PQ"], base["PQ"]), index=self.C)
        return (self.W * dp).sum(axis=1) / self.W.sum(axis=1)

    @staticmethod
    def industries(model, base, sim) -> pd.DataFrame:
        """PSA's 16 industries: labour income, employment (labour of all skills at base wages) and average wage, % change."""
        from .dynamic import PSA_INDUSTRIES
        labs = [i for i, f_ in enumerate(model.F) if f_.startswith("flab")]
        emp = lambda sol: np.asarray(sol["QF"], float) + (np.asarray(sol["QFH"], float) if "QFH" in sol else 0.0)  # 0.3.11
        W0, Q0, W1, Q1 = (np.asarray(x, float)[labs] for x in (base["W"], emp(base), sim["W"], emp(sim)))
        rows = {}
        for name, acts in PSA_INDUSTRIES.items():
            ix = [model.A.index(a) for a in acts if a in model.A]
            inc0 = (W0[:, ix] * Q0[:, ix]).sum()
            if not ix or inc0 <= 0:
                rows[name] = {"labour_income_pct": 0.0, "employment_pct": 0.0, "avg_wage_pct": 0.0}
                continue
            inc = (W1[:, ix] * Q1[:, ix]).sum() / inc0
            emp = (W0[:, ix] * Q1[:, ix]).sum() / inc0
            rows[name] = {"labour_income_pct": (inc - 1) * 100, "employment_pct": (emp - 1) * 100, "avg_wage_pct": (inc / emp - 1) * 100}
        out = pd.DataFrame(rows).T
        out.index.name = "industry"
        return out.reindex([n for n in PSA16 if n in out.index] + [n for n in out.index if n not in PSA16])

    @staticmethod
    def factors(model, base, sim) -> pd.Series:
        W0, Q0, W1 = (np.asarray(x, float) for x in (base["W"], base["QF"], sim["W"]))
        return pd.Series({f_: ((W1[i] * Q0[i]).sum() / (W0[i] * Q0[i]).sum() - 1) * 100 if (W0[i] * Q0[i]).sum() else 0.0
                          for i, f_ in enumerate(model.F)}, name="price_change_pct")

    def link_variables(self, model, base, sim, scenario: str = "", settings: str = "") -> dict:
        g = HouseholdDetail.group_effects(model, base, sim)
        cat = self.category_prices(model, base, sim)
        tot = self.national.sum()
        fc = pd.DataFrame({"fies_spending_php_bn": self.national / 1e9, "budget_share_pct": self.national / tot * 100,
                           "price_change_pct": cat,
                           "reconciliation_factor": self.lam,
                           "sam_commodities": [" ".join(c for c in self.cmap[k] if c in self.W.columns and self.W.loc[k, c] > 0) for k in CATEGORIES]})
        fc.index.name = "fies_category"
        com = pd.DataFrame({"household_budget_share_pct": self.hh_cons / self.hh_cons.sum() * 100,
                            "consumer_price_pq_pct": _pct(sim["PQ"], base["PQ"]),
                            "producer_price_px_pct": _pct(sim["PX"], base["PX"])}, index=self.C)
        com.index.name = "sam_commodity"
        grp = g.copy()
        grp.index.name = "household_group"
        ns = pd.Series({k: g.attrs[f"dp_{k}"] * 100 for k in NET_SELLER}, name="producer_price_change_pct")
        ns.index.name = "fies_income_source"
        conc = self.W.stack().rename("weight_sam_units").reset_index()
        conc.columns = ["fies_category", "sam_commodity", "weight_sam_units"]
        conc = conc[conc.weight_sam_units > 1e-12]
        conc["share_of_category"] = conc.weight_sam_units / conc.groupby("fies_category").weight_sam_units.transform("sum")
        meta = {"scenario": scenario, "settings": settings, "created": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
                "model_solved": bool(getattr(sim, "ok", True)), "fies": "FIES 2023 public-use file (PSA), Household Sum"}
        return {"fies_categories": fc, "commodities": com, "industries": self.industries(model, base, sim),
                "household_groups": grp, "factors": self.factors(model, base, sim).to_frame(), "net_seller": ns.to_frame(),
                "concordance": conc, "_g": g, "_meta": meta}

    # ------------------------------------------------------------------ families
    def family_inflation(self, link: dict, reconcile: bool = True) -> pd.Series:
        """Each family's inflation (%): its FIES budget shares over CATEGORIES x the categories' price changes.
        reconcile=True (default): shares rescaled so the national basket is the SAM's (self.lam); False: raw FIES shares."""
        s = self.spend.values * (self.lam.reindex(CATEGORIES).values if reconcile else 1.0)
        tot = s.sum(axis=1)
        pi = link["fies_categories"]["price_change_pct"].reindex(CATEGORIES).values
        out = np.where(tot > 0, (s @ pi) / np.where(tot > 0, tot, 1), np.nan)
        grp_infl = self.hd.f["grp"].map(link["_g"]["inflation_pct"]).values        # no spending recorded: group inflation
        return pd.Series(np.where(np.isnan(out), grp_infl, out), index=self.hd.f.index, name="family_inflation_pct")

    def _effects(self, link, pi_family, lfs=False, net_seller=False) -> pd.DataFrame:
        e = self.hd._family_effects(link["_g"], net_seller=net_seller, lfs=lfs)
        e["infl"] = pi_family
        e["price"] = self.hd.f["TOTEX"] * pi_family / 100
        e["total"] = e["price"] + e["income"]
        return e

    def deciles(self, link, pi_family, ranking="psa", lfs=False, net_seller=False) -> pd.DataFrame:
        return self.hd._decile_table(self._effects(link, pi_family, lfs, net_seller), ranking)

    def poverty(self, link, pi_family, lfs=False) -> pd.DataFrame:
        """As HouseholdDetail.poverty, but each family's spending is deflated by its own price index:
        PCI x (group nominal spending change) / (1 + family inflation)."""
        f, g = self.hd.f, link["_g"]
        eh_ratio = f["grp"].map(g["real_factor"] * (1 + g["inflation_pct"] / 100)).fillna(1.0)
        pci = f["PCI"] * eh_ratio / (1 + pi_family / 100)
        if lfs:
            pci = pci + self.hd._lfs_adjustment(g) / f["FSIZE"] / (1 + pi_family / 100)
        return self.hd._before_after(pci)

    def expected_results(self, link) -> pd.DataFrame:
        """The numbers a Stata run should reproduce (same inputs, same rules)."""
        g, pi, pr = link["_g"], self.family_inflation(link), self.family_inflation(link, reconcile=False)
        variants = {"group inflation (Infinity GEM published method)": (self.hd.poverty(g), self.hd.deciles(g)),
                    "family inflation, reconciled to the SAM (recommended)": (self.poverty(link, pi), self.deciles(link, pi)),
                    "family inflation, raw FIES shares": (self.poverty(link, pr), self.deciles(link, pr))}
        rows = {}
        for lab, (p, _) in variants.items():
            for k in ("Poor persons", "Poor families", "Food-poor persons", "Food-poor families"):
                rows[f"{lab}: change in {k.lower()}"] = float(p.loc[k, "Change"])
        for lab, (_, d) in variants.items():
            for r in ("Bottom 30% (deciles 1-3)", "All families"):
                rows[f"{lab}: {r}: total loss per family (PHP a year)"] = float(d.loc[r, "Total loss: average per family (₱)"])
                rows[f"{lab}: {r}: inflation (pp)"] = float(d.loc[r, "Inflation (pp)"])
        w = self.hd.f["RFACT"]
        rows["family inflation (reconciled): mean, families weighted by spending (pp)"] = float(np.average(pi, weights=w * self.hd.f["TOTEX"]))
        rows["family inflation (reconciled): weighted mean (pp)"] = float(np.average(pi, weights=w))
        o = np.argsort(pi.values); cw = np.cumsum(w.values[o]) / w.sum()
        for q in (10, 90):                                      # weighted percentiles of families
            rows[f"family inflation (reconciled): {q}th percentile of families (pp)"] = float(pi.values[o][np.searchsorted(cw, q / 100)])
        return pd.Series(rows, name="value").to_frame()

    # ------------------------------------------------------------------ writing
    def write(self, link: dict, xlsx, csv_dir=None, expected: pd.DataFrame | None = None) -> Path:
        """Workbook (README + one sheet per table) and, beside it, one CSV per table with plain ASCII names for Stata."""
        xlsx = Path(xlsx)
        csv_dir = Path(csv_dir) if csv_dir else xlsx.with_suffix("")
        csv_dir.mkdir(parents=True, exist_ok=True)
        expected = self.expected_results(link) if expected is None else expected
        tables = {k: v for k, v in link.items() if not k.startswith("_")}
        tables["expected_results"] = expected
        m = link["_meta"]
        readme = pd.DataFrame({"item": ["What", "Scenario", "Settings", "Created", "Model solved", "Household data", "Units",
                                        "How to use", "Not for citation"],
                               "value": ["Infinity GEM macro-micro link file: what one CGE run hands to a FIES-LFS microsimulation",
                                         m["scenario"], m["settings"], m["created"], str(m["model_solved"]), m["fies"],
                                         "All changes in % against the no-shock baseline (pp for inflation); FIES 2023 pesos",
                                         "Stata: a Stata do-file (not included) reads the CSV files in the folder beside this workbook",
                                         "Model results for one year, not forecasts; not for citation"]})
        with pd.ExcelWriter(xlsx) as w:
            readme.to_excel(w, sheet_name="README", index=False)
            for k, v in tables.items():
                v.to_excel(w, sheet_name=k[:31])
        for k, v in tables.items():
            t = v.copy()
            if not isinstance(t.index, pd.RangeIndex):
                t = t.reset_index()
            t.columns = [str(c).replace("₱", "PHP") for c in t.columns]
            t.to_csv(csv_dir / f"{k}.csv", index=False, encoding="ascii", errors="replace")
        readme.to_csv(csv_dir / "README.csv", index=False, encoding="ascii", errors="replace")
        return xlsx
