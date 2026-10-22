"""Engines behind the Infinity GEM Simulator. Plain Python (no Streamlit), so every result the app shows can be
reproduced and tested from a script:

    from app.engines import Shocks, run_cge, run_sam, run_io_quantity, run_io_price
    s = Shocks(construction_bn=-238.3)
    run_cge(s, "short run")["summary"]

All peso inputs are in the pesos of the year whose nominal GDP is given (default: PSA 2025 GDP). They are
converted to the same share of GDP in each model's base year (2023 SAM, 2018 I-O table) and results are
converted back, as in the scenario scripts (scenarios/_common.py).
"""
from __future__ import annotations

import sys
import warnings
from dataclasses import dataclass, field, asdict
from pathlib import Path

import pandas as pd

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
for p in (ROOT, ROOT / "scenarios"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from _common import PSA_GDP, SAM_GDP_2023, population_shares      # noqa: E402
from infinity_gem import paths                                          # noqa: E402
from infinity_gem.cge import CGE, DEFAULT_ELASTICITIES                  # noqa: E402
from infinity_gem.iomodel import IOTable                                # noqa: E402
from infinity_gem.microsim import Microsim                              # noqa: E402
from infinity_gem.multiplier import SAMMultiplier                       # noqa: E402
from infinity_gem.sam import SAM                                        # noqa: E402
from infinity_gem import settings as ST                                 # noqa: E402  (0.3.1)

CLOSURES = {
    "short run": dict(closure="keynesian", unemployed=("flab-n", "flab-p"), capital="fixed"),
    "long run": {},
    # 0.3.1: the engine's other closures, exposed on the CGE page
    "short run, all skill levels can lose jobs": dict(closure="keynesian", unemployed=("flab-n", "flab-p", "flab-s"), capital="fixed"),
    "medium run: full employment, capital stays in its industry": dict(capital="fixed"),
    "long run, savings-driven": dict(closure="savings"),
}
MAIN_CLOSURES = ("short run", "long run")          # the pair "Compare all models" runs
CLOSURE_TEXT = {
    "short run": "Short run (about one year): capital stays where it is, exchange rate fixed; who can lose jobs depends on "
                 "the setting: all skill levels under '0.3 recommended' (PSA data: about ₱1.1 of GDP per peso of public "
                 "construction), low- and medium-skill workers under '0.2 published'. The central case for a one-year shock.",
    "long run": "Long run (several years): everyone stays employed, capital moves between industries, "
                "prices and the exchange rate adjust. A lower bound for demand shocks.",
    "short run, all skill levels can lose jobs": "As the short run, but high-skill workers' real wages are fixed too, so "
                "they can also lose jobs. An upper bound on job losses.",
    "medium run: full employment, capital stays in its industry": "Everyone employed; capital cannot move between industries "
                "(rental rates differ); investment-driven. Between the short and long run.",
    "long run, savings-driven": "As the long run, but saving rates are fixed and investment adjusts to available savings "
                "(the neoclassical closure), instead of investment fixed and saving adjusting.",
}
HOUSEHOLDS = [f"hhd-{a}{q}" for a in "ru" for q in range(1, 6)]
HH_LABEL = {f"hhd-{a}{q}": f"{'Rural' if a == 'r' else 'Urban'} Q{q}" for a in "ru" for q in range(1, 6)}
ALLOCATIONS = {
    "Bottom 40% (rural and urban Q1-Q2, by population)": ["hhd-r1", "hhd-u1", "hhd-r2", "hhd-u2"],
    "Bottom 20% (rural and urban Q1, by population)": ["hhd-r1", "hhd-u1"],
    "All households (by population)": HOUSEHOLDS,
}
PETROLEUM_SHARE_DEFAULT = 0.6      # assumed petroleum share of 'cchem' imports (scenarios/oil_price_shock.py)
IO_PETROLEUM = "Coke and refined petroleum products"


@dataclass
class Shocks:
    """Engine-neutral shock description. Pesos: ₱ bn in the pesos of the GDP year (see gdp_bn)."""
    construction_bn: float = 0.0          # change in public/private construction spending (negative = cut)
    govcons_bn: float = 0.0               # change in government consumption (spread over the goods it buys)
    transfers_bn: float = 0.0             # change in government cash transfers to households (Ayuda)
    transfers_to: str = next(iter(ALLOCATIONS))
    remit_pct: float = 0.0                # change in remittances, %
    oil_pct: float = 0.0                  # change in world oil prices, %
    petroleum_share: float = PETROLEUM_SHARE_DEFAULT
    import_price_pct: dict = field(default_factory=dict)   # {SAM commodity: %}   CGE only
    tariff_pct: dict = field(default_factory=dict)         # {SAM commodity: % change in the tariff rate}   CGE only
    tfp_pct: dict = field(default_factory=dict)            # {SAM activity: %}   CGE only
    other_demand_bn: dict = field(default_factory=dict)    # {SAM commodity: ₱ bn}   SAM multiplier only
    gdp_bn: float = PSA_GDP[2025]                          # nominal GDP of the year the pesos are in
    levers: list = field(default_factory=list)             # 0.3.1: [[lever label (LEVERS), code or "ALL", % change], ...]   CGE only

    def to_sam(self, x):
        return x / self.gdp_bn * SAM_GDP_2023

    def from_sam(self, x):
        return x / SAM_GDP_2023 * self.gdp_bn

    def describe(self) -> list[str]:
        out = []
        if self.construction_bn: out.append(f"Construction spending {self.construction_bn:+,.1f} ₱ bn")
        if self.govcons_bn: out.append(f"Government consumption {self.govcons_bn:+,.1f} ₱ bn")
        if self.transfers_bn: out.append(f"Cash transfers {self.transfers_bn:+,.1f} ₱ bn to {self.transfers_to}")
        if self.remit_pct: out.append(f"Remittances {self.remit_pct:+.1f}%")
        if self.oil_pct: out.append(f"World oil prices {self.oil_pct:+.1f}% (petroleum share of chemicals imports {self.petroleum_share:.0%})")
        for k, v in self.import_price_pct.items(): out.append(f"World import price of {k} {v:+.1f}%")
        for k, v in self.tariff_pct.items(): out.append(f"Tariff rate on {k} {v:+.1f}%")
        for k, v in self.tfp_pct.items(): out.append(f"Productivity of {k} {v:+.1f}%")
        for k, v in self.other_demand_bn.items(): out.append(f"Final demand for {k} {v:+,.1f} ₱ bn")
        for lever, code, v in self.levers: out.append(f"{lever.replace(' (%)', '')}, {'all' if code == 'ALL' else code}: {v:+.1f}%")
        return out or ["No shock"]

    def as_dict(self):
        return asdict(self)


# 0.3.1: every lever of the CGE (infinity_gem.cge.CGE.make_shocks) as a % change: label -> (shock key, kind of item).
# Kinds: c commodity, a industry (activity), f factor, h household group; "+all" = the item may also be "ALL";
# "all" = economy-wide only.
LEVERS = {
    "World import price (%)": ("pwm_scale", "c"),
    "World export price (%)": ("pwe_scale", "c"),
    "Tariff rate (%)": ("tm_scale", "c+all"),
    "Sales tax rate (%)": ("tq_scale", "c+all"),
    "Productivity, TFP (%)": ("tfp_scale", "a+all"),
    "Real investment demand (%)": ("qinv_scale", "c+all"),
    "Real government consumption (%)": ("qg_scale", "c+all"),
    "Factor supply: labour, land or capital (%)": ("qfs_scale", "f"),
    "Remittances received (%)": ("remit_scale", "h+all"),
    "Government transfers received (%)": ("trg_h_scale", "h+all"),
    "Direct (income) tax rate (%)": ("tins_scale", "h+all"),
    "Foreign savings, capital inflow (%)": ("fsav_scale", "all"),
}


def _lever_items(m, kind: str) -> list:
    return {"c": m.C, "a": m.A, "f": m.F, "h": m.H}[kind[0]]


def apply_levers(m, spec: dict, levers: list) -> tuple[dict, list]:
    """Add lever rows [label, code or 'ALL', % change] to a CGE shock spec; factors multiply with what is already there.
    Returns (spec, problems) - rows that do not fit the lever are skipped and reported."""
    problems = []
    for label, code, pct in levers:
        if label not in LEVERS or pct is None or pct == 0:
            continue
        key, kind = LEVERS[label]
        f = 1 + float(pct) / 100
        if kind == "all":
            spec[key] = float(spec.get(key, 1.0)) * f
            continue
        items = list(_lever_items(m, kind))
        if code == "ALL" and "+all" not in kind:
            problems.append(f"{label}: pick one item (this lever has no 'all')"); continue
        if code != "ALL" and code not in items:
            problems.append(f"{label}: '{code}' is not {dict(c='a commodity', a='an industry', f='a factor', h='a household group')[kind[0]]}"); continue
        cur = spec.get(key)
        if not isinstance(cur, dict):              # a scalar already there (e.g. remittances box) applies to every item
            cur = {i: float(cur) for i in items} if cur is not None else {}
        for t in (items if code == "ALL" else [code]):
            cur[t] = cur.get(t, 1.0) * f
        spec[key] = cur
    return spec, problems


def allocation(name: str) -> dict:
    ps = population_shares()
    hh = ALLOCATIONS[name]
    tot = sum(ps[h] for h in hh)
    return {h: ps[h] / tot for h in hh}


def sam_gdp(sam: SAM) -> float:
    """Nominal GDP by expenditure in a SAM (C + G + I + X - M), ₱ bn. Home consumption (activity -> household) counts in C."""
    t = sam.table
    C, A, H = sam.accounts("c"), sam.accounts("a"), sam.accounts("hhd")
    cons = t.loc[C, H].values.sum() + t.loc[A, H].values.sum()
    return float(cons + t.loc[C, "gov"].sum() + t.loc[C, "s-i"].sum() + t.loc[C, "dstk"].sum()
                 + t.loc[C, "row"].sum() - t.loc["row", C].sum())


# ====================================================================== CGE
_CGE_CACHE: dict = {}
_MS: list = []


def microsim() -> Microsim:
    if not _MS:
        _MS.append(Microsim())
    return _MS[0]


def cge_model(closure: str, elasticities: dict | None = None, setting: str = "0.2 published") -> CGE:
    """A calibrated CGE. setting (0.3.1): '0.2 published' (default, so saved runs rerun as saved) or
    '0.3 recommended' (infinity_gem/settings.py). Elasticities given here (uniform numbers from the sliders) replace the
    setting's own (0.2: 0.8/2.0/2.0; 0.3: the Philippine set by sector)."""
    kw = ST.cge_kwargs(setting)
    path = kw.pop("path")
    if elasticities is not None or setting == "0.2 published":
        kw["elasticities"] = dict(DEFAULT_ELASTICITIES, **(elasticities or {}))
    key = (closure, setting, tuple(sorted(kw["elasticities"].items())) if elasticities is not None or setting == "0.2 published" else None)
    if key not in _CGE_CACHE:
        cl = ST.short_run_closure(setting) if closure == "short run" else CLOSURES[closure]   # 0.3.6: setting's short run
        _CGE_CACHE[key] = CGE.from_sam(path, **kw, **cl)
    return _CGE_CACHE[key]


def cge_spec(m: CGE, s: Shocks) -> dict:
    spec = {}
    pwm = {}
    if s.oil_pct and "cpetr" in m.C:     # petroleum-split SAM (0.3 recommended): refined products and crude, sourced shares
        from infinity_gem.oil import cge_oil_shock
        pwm.update(cge_oil_shock(m, s.oil_pct / 100)["pwm_scale"])
    elif s.oil_pct:
        pwm["cchem"] = 1 + s.oil_pct / 100 * s.petroleum_share
    for c, v in s.import_price_pct.items():
        pwm[c] = pwm.get(c, 1.0) * (1 + v / 100)
    if pwm: spec["pwm_scale"] = pwm
    if s.construction_bn:
        q0 = m.qinv[m.C.index("ccons")]
        spec["qinv_scale"] = {"ccons": 1 + s.to_sam(s.construction_bn) / q0}
    if s.govcons_bn:
        spec["qg_scale"] = 1 + s.to_sam(s.govcons_bn) / m.qg.sum()
    if s.transfers_bn:
        spec["trg_h_add"] = {h: s.to_sam(s.transfers_bn) * w for h, w in allocation(s.transfers_to).items()}
    if s.remit_pct:
        spec["remit_scale"] = 1 + s.remit_pct / 100
    if s.tariff_pct:
        spec["tm_scale"] = {c: 1 + v / 100 for c, v in s.tariff_pct.items()}
    if s.tfp_pct:
        spec["tfp_scale"] = {a: 1 + v / 100 for a, v in s.tfp_pct.items()}
    if s.levers:
        spec, _ = apply_levers(m, spec, s.levers)
    return spec


def run_cge(s: Shocks, closure: str = "short run", elasticities: dict | None = None,
            setting: str = "0.2 published") -> dict:
    m = cge_model(closure, elasticities, setting)
    b = m.solve()
    spec = cge_spec(m, s)
    _, problems = apply_levers(m, {}, s.levers)
    sim = m.solve(spec)
    if not sim.ok:
        return dict(ok=False, message=f"The model did not solve ({sim.message}). Try a smaller shock.", spec=spec)
    gb, gs = m.gdp(b), m.gdp(sim)
    pov = microsim().from_cge(m, b, sim)
    pct = lambda new, old: (new / old - 1) * 100
    emp = {f: pct(sim["EMP"][k], b["EMP"][k]) for k, f in enumerate(m.F)}
    summary = {
        "Real GDP (%)": pct(gs["real"], gb["real"]),
        "Real GDP (₱ bn)": s.from_sam(gs["real"] - gb["real"]),
        "Consumer prices, CPI (%)": pct(sim["CPI"], b["CPI"]),
        "Real household consumption (%)": pct(sim["QH"].sum(), b["QH"].sum()),
        "Real investment (%)": pct(sim["QINV"].sum(), b["QINV"].sum()),
        "Real exports (%)": pct(sim["QE"].sum(), b["QE"].sum()),
        "Real imports (%)": pct(sim["QM"].sum(), b["QM"].sum()),
        "Exchange rate, ₱ per foreign currency (%)": pct(sim["EXR"], b["EXR"]),
        "Employment, low-skill (%)": emp["flab-n"],
        "Employment, medium-skill (%)": emp["flab-p"],
        "Government savings (₱ bn)": s.from_sam(sim["GSAV"] - b["GSAV"]),
        "New poor (persons, FIES 2023 base)": pov["new_poor"],
        "New food poor (persons)": pov["new_food_poor"],
    }
    hh = pd.DataFrame({"Real consumption (%)": {HH_LABEL[h]: (v - 1) * 100 for h, v in pov["group_factors"].items()}})
    ind = pd.DataFrame({"Output (%)": pct(sim["QA"], b["QA"]),
                        "Output (₱ bn)": [s.from_sam(x) for x in (sim["QA"] - b["QA"])]},
                       index=[m.sam.labels.get(a, a).replace("Activities - ", "") for a in m.A])
    notes = [f"Shock row skipped: {p}" for p in problems]
    if setting != "0.2 published":
        notes.append(f"Model setting: {setting}. {ST.DESCRIPTION[setting]}")
    return dict(ok=True, engine="CGE", variant=closure, summary=summary, households=hh, industries=ind, spec=spec,
                poverty=pov, walras=float(sim["WALRAS"]), residual=sim.residual_max, notes=notes, setting=setting,
                model=m, base=b, sim=sim,                                      # 0.3.1: for the household-detail panel
                sam_before=m.rebuild_sam(b), sam_after=m.rebuild_sam(sim))     # 0.3: full SAMs (₱ bn, 2023 SAM units)


# ====================================================================== SAM multiplier
_SAM_CACHE: dict = {}


def sam_model(year: int = 2023) -> SAMMultiplier:
    if year not in _SAM_CACHE:
        _SAM_CACHE[year] = SAMMultiplier(SAM.load(paths.SAM_2023 if year == 2023 else paths.SAM_2018))
    return _SAM_CACHE[year]


def run_sam(s: Shocks, year: int = 2023) -> dict:
    sm = sam_model(year)
    t = sm.sam.table
    gdp_sam = sam_gdp(sm.sam)
    to_sam = lambda x: x / s.gdp_bn * gdp_sam
    back = lambda x: x / gdp_sam * s.gdp_bn
    inj: dict = {}
    add = lambda k, v: inj.__setitem__(k, inj.get(k, 0.0) + v)
    notes = []
    if s.construction_bn:
        add("ccons", to_sam(s.construction_bn))
    if s.govcons_bn:
        g = t.loc[sm.sam.accounts("c"), "gov"]
        for c, x in (g / g.sum()).items():
            if x: add(c, to_sam(s.govcons_bn) * x)
    if s.transfers_bn:
        for h, w in allocation(s.transfers_to).items():
            add(h, to_sam(s.transfers_bn) * w)
    if s.remit_pct:
        for h in HOUSEHOLDS:
            add(h, t.loc[h, "row"] * s.remit_pct / 100)
    for c, v in s.other_demand_bn.items():
        add(c, to_sam(v))
    if s.oil_pct or s.import_price_pct or s.tariff_pct or s.tfp_pct or s.levers:
        notes.append("Price, tariff and productivity shocks cannot be run in a fixed-price SAM multiplier; they were "
                     "left out. Use the CGE or the I-O price model for those.")
    dy = sm.shock(inj)
    F = [f for f in ("flab-n", "flab-p", "flab-s", "flnd", "fcap") if f in sm.endo]
    va = float(sum(dy[f] for f in F))
    hh_inc = {h: dy[h] for h in HOUSEHOLDS}
    hh_pct = {h: dy[h] / t.loc[h].sum() for h in HOUSEHOLDS}
    pov = microsim().simulate(pd.Series({h: 1 + v for h, v in hh_pct.items()}))
    summary = {
        "GDP (value added, %)": va / gdp_sam * 100,
        "GDP (value added, ₱ bn)": back(va),
        "Household income (₱ bn)": back(sum(hh_inc.values())),
        "Labour income (₱ bn)": back(sum(dy[f] for f in F if f.startswith("flab"))),
        "New poor (persons, FIES 2023 base)": pov["new_poor"],
        "New food poor (persons)": pov["new_food_poor"],
    }
    hh = pd.DataFrame({"Income (%)": {HH_LABEL[h]: v * 100 for h, v in hh_pct.items()},
                       "Income (₱ bn)": {HH_LABEL[h]: back(v) for h, v in hh_inc.items()}})
    A = sm.sam.accounts("a")
    ind = pd.DataFrame({"Output (%)": [dy[a] / t.loc[a].sum() * 100 for a in A], "Output (₱ bn)": [back(dy[a]) for a in A]},
                       index=[sm.sam.labels.get(a, a).replace("Activities - ", "") for a in A])
    return dict(ok=True, engine="SAM multiplier", variant=f"{year} SAM", summary=summary, households=hh, industries=ind,
                injections={k: back(v) for k, v in inj.items()}, poverty=pov, notes=notes, gdp_sam=gdp_sam)


# ====================================================================== input-output (Leontief)
_IO: dict = {}


def io_table(industries: int = 80) -> IOTable:
    """PSA's 2018 I-O table: 80 industries (default) or 16 (0.3; matches the LFS industry groups)."""
    if industries not in _IO:
        _IO[industries] = IOTable(paths.IO_2018_16) if industries == 16 else IOTable()
    return _IO[industries]


def run_io_quantity(demand_bn: dict, gdp_bn: float = PSA_GDP[2025], inverse: str = "domestic",
                    with_jobs: bool = True, industries: int = 80) -> dict:
    io = io_table(industries)
    q = io.quantity(demand_bn, inverse, gdp_other_year=gdp_bn)
    summary = {
        "GDP (value added, ₱ bn)": q["va_bn"],
        "GDP (value added, %)": q["va_pct_gdp"],
        "Gross output (₱ bn)": q["output_bn"],
        "Compensation of employees (₱ bn)": q["coe_bn"],
        "Imported inputs (₱ bn)": q["imports_bn"],
        "Output multiplier (per peso)": q["output_multiplier"],
        "GDP multiplier (per peso)": q["va_multiplier"],
    }
    jobs = None
    if with_jobs:
        jobs = io.jobs(q["industries"]["output (%)"])
        summary["Job-equivalents (persons)"] = float(jobs["job-equivalents"].sum())
    return dict(ok=True, engine="Input-output (quantity)", variant=f"PSA 2018, {industries} industries, {inverse} inverse",
                summary=summary, industries=q["industries"], jobs=jobs)


def io_demand_from_shocks(s: Shocks) -> tuple[dict, list]:
    """Translate the engine-neutral demand shocks into I-O final demand by industry (₱ bn). Returns (demand, left out)."""
    io = io_table()
    d, left = {}, []
    if s.construction_bn:
        d["Construction"] = s.construction_bn
    if s.govcons_bn:
        g = io.fd["Government Final Consumption Expenditure"]
        for name, x in (g / g.sum()).items():
            if x: d[name] = d.get(name, 0.0) + s.govcons_bn * x
    if s.transfers_bn: left.append("cash transfers (the I-O table has no household incomes)")
    if s.remit_pct: left.append("remittances (the I-O table has no household incomes)")
    if s.import_price_pct or s.tariff_pct or s.tfp_pct or s.other_demand_bn or s.levers:
        left.append("CGE- or SAM-only shocks")
    return d, left


COMMON_ROWS = ["Real GDP (%)", "Real GDP (₱ bn)", "Consumer prices (%)", "Real household consumption (%)",
               "Household income (₱ bn)", "Employment, low-skill (%)", "Job-equivalents (persons)",
               "New poor (persons)"]


def common_row(r: dict) -> dict:
    """Map an engine's summary onto the rows used to compare engines side by side."""
    s = r["summary"]
    pick = lambda *keys: next((s[k] for k in keys if k in s), float("nan"))
    return {"Real GDP (%)": pick("Real GDP (%)", "GDP (value added, %)"),
            "Real GDP (₱ bn)": pick("Real GDP (₱ bn)", "GDP (value added, ₱ bn)"),
            "Consumer prices (%)": pick("Consumer prices, CPI (%)", "Consumer prices, CPI (percentage points)"),
            "Real household consumption (%)": pick("Real household consumption (%)"),
            "Household income (₱ bn)": pick("Household income (₱ bn)"),
            "Employment, low-skill (%)": pick("Employment, low-skill (%)"),
            "Job-equivalents (persons)": pick("Job-equivalents (persons)"),
            "New poor (persons)": pick("New poor (persons, FIES 2023 base)")}


def compare_all(s: Shocks, elasticities: dict | None = None, sam_year: int = 2023,
                setting: str = "0.2 published") -> tuple[pd.DataFrame, list, list]:
    """Run the same shocks through every engine that can take them. Returns (table, results, notes)."""
    results, notes = [], []
    for c in MAIN_CLOSURES:
        results.append(run_cge(s, c, elasticities, setting))
    if s.construction_bn or s.govcons_bn or s.transfers_bn or s.remit_pct or s.other_demand_bn:
        results.append(run_sam(s, sam_year))
    else:      # a price-only shock: the fixed-price SAM multiplier would show zeros, which reads as "no effect"
        notes.append("SAM multiplier left out: it holds prices fixed, so it cannot take price, tariff or productivity shocks.")
    d, left = io_demand_from_shocks(s)
    if d:
        results.append(run_io_quantity(d, s.gdp_bn))
    if s.oil_pct:
        from infinity_gem.oil import io_refined_passthrough
        pt = io_refined_passthrough(io_table())["passthrough"]
        results.append(run_io_price({IO_PETROLEUM: s.oil_pct * pt}))
        notes.append(f"I-O price model: refined petroleum prices raised by the oil-price change x {pt:.3f}, the crude-to-refined "
                     "pass-through from PSA's 2018 I-O and Supply tables (infinity_gem/oil.py). Fixed input shares, imported inputs "
                     "passing on price rises: an upper bound. Prices only; GDP and jobs come from the CGE.")
    if left and d:
        notes.append("Left out of the I-O quantity model: " + "; ".join(left) + ".")
    notes += list(dict.fromkeys(n for r in results for n in r.get("notes", [])))     # once each (0.3.1: setting note)
    ok = [r for r in results if r.get("ok")]
    table = pd.DataFrame({f"{r['engine']}, {r['variant']}": common_row(r) for r in ok})
    return table, results, notes


def run_io_price(price_pct: dict) -> dict:
    """Prices only (0.3.6: the CPI x assumed-elasticity GDP shortcut was removed; GDP comes from the CGE)."""
    io = io_table()
    ps = io.price_summary({k: v / 100 for k, v in price_pct.items()})
    summary = {"Consumer prices, CPI (percentage points)": ps["cpi"] * 100,
               "Producer prices (percentage points)": ps["ppi"] * 100}
    ind =pd.DataFrame({"Price change (%)": ps["dp"] * 100, "Contribution to CPI (pp)": ps["cpi_contrib"] * 100})
    return dict(ok=True, engine="Input-output (price)", variant="PSA 2018, cost push", summary=summary, industries=ind)


# ====================================================================== run stamp (0.3)
def run_stamp() -> dict:
    """What produced a result: model version, a fingerprint of the model code, a fingerprint of the recorded data
    checksums (data/DATA_INVENTORY.md; check D1 verifies the files against them), and the time."""
    import datetime as _dt
    import hashlib
    import re as _re
    import infinity_gem
    h = hashlib.sha256()
    for p in sorted(list((ROOT / "infinity_gem").glob("*.py")) + [ROOT / "app" / "engines.py"]):
        h.update(p.name.encode())
        h.update(p.read_bytes())
    hashes = _re.findall(r"`([0-9a-f]{64})`", (ROOT / "data" / "DATA_INVENTORY.md").read_text(encoding="utf-8"))
    return {"model_version": infinity_gem.__version__, "code_fingerprint": h.hexdigest()[:16],
            "data_fingerprint": hashlib.sha256("".join(hashes).encode()).hexdigest()[:16] + f" ({len(hashes)} recorded files)",
            "run_at": f"{_dt.datetime.now():%Y-%m-%d %H:%M:%S}"}


# ====================================================================== dynamic CGE (0.3)
_DYN: dict = {}


def dynamic_model(hybrid: bool = True, persistence: float = 0.5, setting: str = "0.2 published",
                  public_capital: str = "off", industry_baseline: bool = False):
    """Dynamic CGE with its baseline calibrated (slow the first time: about a minute; 0.3 recommended: a few minutes)."""
    from infinity_gem.dynamic import DynamicCGE
    key = (bool(hybrid), round(float(persistence), 4), setting, public_capital, bool(industry_baseline))
    if key not in _DYN:
        if setting == "0.2 published":
            d = DynamicCGE(hybrid=hybrid, gap_persistence=persistence) if hybrid else DynamicCGE()
        else:
            d = DynamicCGE(gap_persistence=persistence, **ST.dynamic_kwargs(setting, public_capital, industry_baseline, hybrid))
        d.baseline()
        _DYN[key] = d
    return _DYN[key]


def run_dynamic(construction_by_year: dict, gdp_bn: float = PSA_GDP[2025], hybrid: bool = True, persistence: float = 0.5,
                setting: str = "0.2 published", public_capital: str = "off", industry_baseline: bool = False,
                levers_by_year: dict | None = None) -> dict:
    """Construction spending changes by year (₱ bn in the pesos of gdp_bn's year, converted to the same share of GDP in
    the 2023 SAM, as in scenarios/infrastructure_catchup.py), solved year by year to 2030 against the baseline.
    levers_by_year (0.3.1): {year: [[lever label (LEVERS), code or 'ALL', % change], ...]}, any CGE lever in any year;
    each multiplies that year's baseline level."""
    d = dynamic_model(hybrid, persistence, setting, public_capital, industry_baseline)
    q0 = d.m.qinv[d.m.C.index("ccons")]
    shocks = {int(y): {"qinv_scale": {"ccons": 1 + (v / gdp_bn * SAM_GDP_2023) / q0}}
              for y, v in construction_by_year.items() if v and int(y) in d.years[1:]}
    problems = []
    for y, rows in (levers_by_year or {}).items():
        if int(y) in d.years[1:] and rows:
            sp, pr = apply_levers(d.m, shocks.get(int(y), {}), rows)
            problems += [f"{y}: {p}" for p in pr]
            if sp:
                shocks[int(y)] = sp
    if not shocks:
        return dict(ok=False, message="Enter at least one non-zero change in a year from 2024 to 2030.")
    try:
        sim = d.scenario(shocks)
    except RuntimeError as e:
        return dict(ok=False, message=f"The model did not solve: {e}. Try a smaller shock.")
    c = d.compare(d.base, sim)
    to_pesos = gdp_bn / SAM_GDP_2023
    path = pd.DataFrame({"Real GDP vs baseline (%)": c["gdp_gap_pct"].drop("cumulative"),
                         "Real GDP vs baseline (₱ bn)": c["gdp_gap_bn"].drop("cumulative") * to_pesos,
                         "Real household consumption vs baseline (%)": c["consumption_gap_pct"].drop("cumulative"),
                         "Capital stock vs baseline (%)": c["capital_gap_pct"].drop("cumulative"),
                         "GDP growth, baseline (%)": c["base_growth_pct"].drop("cumulative"),
                         "GDP growth, scenario (%)": c["sim_growth_pct"].drop("cumulative")})
    if hybrid:
        path["Low-skill employment gap (%)"] = sim.table["employment_gap_low_skill_pct"]
        path["Closure used"] = sim.table["closure"]
    summary = {"Cumulative GDP vs baseline, 2024-2030 (₱ bn)": float(c.loc["cumulative", "gdp_gap_bn"]) * to_pesos,
               "Real GDP vs baseline in 2030 (%)": float(c.loc[2030, "gdp_gap_pct"]),
               "Capital stock vs baseline in 2030 (%)": float(c.loc[2030, "capital_gap_pct"])}
    notes = [f"Shock row skipped: {p}" for p in problems] + ["Dynamic CGE (infinity_gem/dynamic.py), 2023 SAM. Pesos are converted to the same share of GDP in the 2023 SAM and back; "
             "the GDP gap in pesos is in 2023 SAM prices scaled to the chosen GDP year.",
             ("Hybrid closure: short run in years with a shock; the low/medium-skill employment gap then shrinks to "
              f"{persistence:.0%} of itself each year (an assumption)." if hybrid else
              "Long-run closure every year: everyone stays employed, so the shock-year job loss is not shown."),
             ("Placeholder assumptions: growth path from 2026, depreciation 5%, labour growth 1.5% (infinity_gem/dynamic.py). "
              "No public-capital productivity channel, so long-run costs and benefits of infrastructure are lower bounds."
              if setting == "0.2 published" else
              f"Model setting: {setting}. {ST.DESCRIPTION[setting]} Baseline: DBCC growth, PWT depreciation and capital, PSA labour "
              "growth by skill" + ("; each PSA industry grows as PSA reports for 2024-2025 (this baseline already contains the actual "
              "2025 construction slump: do not add a 2025 freeze on top of it)" if industry_baseline else "") + ". Public capital: "
              + {"off": "off (long-run infrastructure effects are lower bounds).",
                 "low": "low end (phi 0.083, public capital 0.397 x GDP).",
                 "high": "high end (phi 0.122, public capital 0.296 x GDP)."}[public_capital])]
    return dict(ok=True, engine="Dynamic CGE", variant="hybrid" if hybrid else "long run", summary=summary, path=path, notes=notes,
                shocks_sam=shocks)
