"""El Nino 2026-27 through the whole chain: estimated crop loss -> Infinity GEM CGE -> FIES families.

0.3.7, 15 Oct 2026: the three upgrades the diagnostic run of 14 Oct asked for are built, so this is no longer a
diagnostic (still NOT FOR CITATION until reviewed):
  1. milled rice and corn split from processed food, with rice imports at PSA's 2023 customs value and the BOC's 2023
     rice tariff collections (tools/build_sam_rice_split.py; settings rice=True): imported milled rice now competes with
     domestic milled rice, so a palay shortfall is partly met by imports at the world price;
  2. drought as lost EFFECTIVE LAND of rice and maize (CGE land='fixed', shock 'lscale'), not as a productivity cut:
     with land tied to each crop for the season, farms lose land and water, not efficiency;
  3. rice and maize sized JOINTLY (one 2-D solve), so both the model's rice and maize output fall by the estimated shares.

Shock (preshock/agri_elnino.py, province panel 1987-2026): palay and corn production lost in the 2026 wet-season crop
(semester 2; ONI from NOAA, seasons observed so far) and the 2027 dry-season crop (semester 1; ONI scenario: the CCSR/IRI
plume of 21 Sept 2026 points to a strong El Nino into early 2027; 2.0 central, 1.5 and 2.5 as the range), as a share of a
crop year's production (2023-2025 average).
Policy baseline for 2026: the rice tariff at 15% (EO 105, price-indexed 15-35%; 15% through March 2026 and at its floor
while world prices rise: a reference copy (not distributed)), against 34.4% in the 2023 SAM (BOC collections / PSA imports of milled rice and corn). Both the
baseline and the shocked run carry it, so the results are El Nino's effect under 2026 policy.
Variants: El Nino alone (world rice price unchanged), and with the measured 2026 world rice price (Viet Nam 5%, conflict
period vs Jan-Feb 2026: preshock/agri_price_shock_size.py), which is partly a separate shock.
Model: '0.3 recommended' with rice=True, short run with all skill levels able to lose jobs, land fixed by crop.
For the over-time run, calendar_year_losses() gives 2026 (semester 2) and 2027 (semester 1) separately, and land_cuts()
the matching land factors.
NOT FOR CITATION until reviewed. Run:  py preshock/elnino_to_cge.py
"""
import datetime as dt
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import root

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT), str(Path(__file__).resolve().parent)]
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import agri_elnino as A                                   # noqa: E402
from agri_price_shock_size import shock_sizes as agri_prices   # noqa: E402
from infinity_gem.microlink import MicroLink                  # noqa: E402
from infinity_gem.settings import cge_model, short_run_closure   # noqa: E402

ACT = {"palay": ("arice", ["Irrigated Palay", "Rainfed Palay"]), "corn": ("amaiz", ["Corn"])}
ONI_S1 = {"central": 2.0, "low": 1.5, "high": 2.5}
TARIFF_2026 = 0.15                        # EO 105 floor (USDA FAS GAIN RP2026-0004; a reference copy (not distributed))
CENTRAL = "conflict period (Mar 2026 to latest)"


def _fits():
    d = A.panel()
    fits = {e: A.estimate(d, e, "production")[0] for e in ["Irrigated Palay", "Rainfed Palay", "Corn"]}
    return d, fits


def _lost(d, fits, oni_s2, oni_s1):
    """Production lost by crop and semester (t) and the crop-year level (t), from the panel's El Nino elasticities."""
    out = {}
    for crop, (_, ecos) in ACT.items():
        lost = {1: 0.0, 2: 0.0}
        level = {1: 0.0, 2: 0.0}
        for e in ecos:
            b = fits[e].params["oni_plus"]
            for sem, o in ((2, oni_s2), (1, oni_s1)):
                q = d[(d["crop"] == e) & (d["sem"] == sem) & (d["year"] >= 2023) & (d["year"] <= 2025)]
                lvl = q.groupby("year")["v_q"].sum().mean()
                lost[sem] += lvl * (1 - np.exp(b * max(o, 0)))
                level[sem] += lvl
        out[crop] = {"lost": lost, "level": level}
    return out


def oni_s2_observed() -> float:
    oni = A.oni_by_semester().set_index(["year", "sem"])
    return float(oni.loc[(2026, 2), "oni"])


def crop_year_loss(oni_s1=2.0) -> dict:
    """Share of a crop year's production lost (2026 S2 + 2027 S1), palay and corn."""
    d, fits = _fits()
    L = _lost(d, fits, oni_s2_observed(), oni_s1)
    return {crop: sum(v["lost"].values()) / sum(v["level"].values()) for crop, v in L.items()}


def calendar_year_losses(oni_s1=2.0) -> dict:
    """{2026: {'arice': share, 'amaiz': share}, 2027: {...}}: semester 2 of 2026 and semester 1 of 2027, each as a share
    of a calendar year's production (both semesters), for the over-time run."""
    d, fits = _fits()
    L = _lost(d, fits, oni_s2_observed(), oni_s1)
    yr = {2026: 2, 2027: 1}
    return {y: {ACT[c][0]: v["lost"][s] / sum(v["level"].values()) for c, v in L.items()} for y, s in yr.items()}


def policy_2026(m) -> dict:
    """The 2026 rice tariff as a shock spec on the rice-split model (tariff rate from the SAM's 34.4% to 15%)."""
    i = m.C.index("cmric")
    return {"tm_scale": {"cmric": TARIFF_2026 / float(m.tm[i])}}


def land_cuts(m, b, target: dict, base_spec=None, extra=None) -> dict:
    """Effective-land factors {activity: f} such that the model's output of each activity falls by target[activity]
    (shares), solved jointly. base_spec: the spec of the baseline b (e.g. the 2026 tariff); extra: other shocks applied
    together with the drought (e.g. the world rice price), so the sizing holds in that run."""
    acts = list(target)
    idx = [m.A.index(a) for a in acts]
    spec0 = dict(base_spec or {}, **(extra or {}))
    state = {"x": b.x}

    def resid(z):
        s = m.solve(dict(spec0, lscale={a: float(np.exp(v)) for a, v in zip(acts, z)}), x_start=state["x"])
        if not s.ok:
            return np.full(len(acts), 1e3)
        state["x"] = s.x
        return np.array([s["QA"][i] / b["QA"][i] - (1 - target[a]) for a, i in zip(acts, idx)])

    z0 = np.log(np.clip([1 - 3 * target[a] for a in acts], 0.2, 1.0))
    out = root(resid, z0, method="hybr", options={"xtol": 1e-12})
    if np.abs(out.fun).max() > 1e-8:
        raise RuntimeError(f"land sizing failed: {out.fun}")
    return {a: float(np.exp(v)) for a, v in zip(acts, out.x)}


def run_one(m, b, ml, base_spec, loss, world_rice=0.0):
    target = {"arice": loss["palay"], "amaiz": loss["corn"]}
    extra = {"pwm_scale": {"cmric": 1 + world_rice}} if world_rice else {}
    cuts = land_cuts(m, b, target, base_spec, extra)
    spec = dict(base_spec, lscale=cuts, **extra)
    s = m.solve(spec)
    assert s.ok, s.message
    link = ml.link_variables(m, b, s)
    exp = ml.expected_results(link)["value"]
    com, ind = link["commodities"], link["industries"]
    A_, C_ = m.A.index, m.C.index
    pct = lambda v, i: (float(s[v][i]) / float(b[v][i]) - 1) * 100
    lab = [m.F.index(f) for f in ("flab-n", "flab-p", "flab-s")]
    farm = [A_("arice"), A_("amaiz")]
    G = "group inflation (Infinity GEM published method)"
    R = "family inflation, reconciled to the SAM (recommended)"
    row = {
        "palay lost, % of a crop year (target)": loss["palay"] * 100,
        "corn lost, % of a crop year (target)": loss["corn"] * 100,
        "effective land left, rice / maize": f"{cuts['arice']:.3f} / {cuts['amaiz']:.3f}",
        "rice (palay) output in the model (%)": pct("QA", A_("arice")),
        "maize output in the model (%)": pct("QA", A_("amaiz")),
        "milled rice and corn: domestic output (%)": pct("QA", A_("amric")),
        "milled rice and corn: imports (%)": pct("QM", C_("cmric")),
        "palay: producer price (%)": com.loc["crice", "producer_price_px_pct"],
        "milled rice and corn: consumer price (%)": com.loc["cmric", "consumer_price_pq_pct"],
        "real GDP (%)": (m.gdp(s)["real"] / m.gdp(b)["real"] - 1) * 100,
        "consumer prices, all families (%)": (float(s["CPI"]) / float(b["CPI"]) - 1) * 100,
        "rice and maize farm labour (%)": (s["QF"][np.ix_(lab, farm)].sum() / b["QF"][np.ix_(lab, farm)].sum() - 1) * 100,
        "agriculture employment, PSA industry (%)": float(ind.iloc[0]["employment_pct"]),
        "inflation, bottom 30%: own baskets / group (pp)": f"{exp[f'{R}: Bottom 30% (deciles 1-3): inflation (pp)']:.2f} / "
                                                          f"{exp[f'{G}: Bottom 30% (deciles 1-3): inflation (pp)']:.2f}",
        "new poor persons: own baskets (recommended)": exp[f"{R}: change in poor persons"],
        "new poor persons: group method": exp[f"{G}: change in poor persons"],
        "new food-poor persons: own baskets": exp[f"{R}: change in food-poor persons"],
    }
    return row, link, cuts


def main():
    m = cge_model("0.3 recommended", rice=True, sam_variant="ifpri", **short_run_closure("0.3 recommended"), land="fixed")   # 0.3.10: IFPRI, as run (the 2026 scenarios)
    base_spec = policy_2026(m)
    b = m.solve(base_spec)
    assert b.ok, b.message
    ml = MicroLink(m)
    rice_w = float(agri_prices().loc[CENTRAL, "rice, Viet Nam 5% (central)"]) / 100
    o2 = oni_s2_observed()
    cols, links, cut_tab = {}, {}, {}
    for name, o1 in ONI_S1.items():
        loss = crop_year_loss(o1)
        row, link, cuts = run_one(m, b, ml, base_spec, loss)
        cols[f"El Nino alone, ONI {o1:g} ({name})"] = row
        links[name] = link
        cut_tab[o1] = cuts
    loss = crop_year_loss(ONI_S1["central"])
    row, link_w, _ = run_one(m, b, ml, base_spec, loss, world_rice=rice_w)
    cols[f"El Nino (ONI 2) + world rice price +{rice_w * 100:.1f}%"] = row
    t = pd.DataFrame(cols)
    print(t.to_string())
    cal = calendar_year_losses(ONI_S1["central"])
    fmt = lambda v: v if isinstance(v, str) else (f"{v:,.0f}" if abs(v) >= 1000 else f"{v:,.2f}")
    L = [f"# El Nino 2026-27 through Infinity GEM: crop loss, economy, households ({dt.date.today():%d %B %Y})", "",
         "**NOT FOR CITATION** until reviewed (Infinity GEM 0.3.7). Script: `preshock/elnino_to_cge.py`. One crop "
         "year (2026 wet season + 2027 dry season), short run, against a 2026 baseline with the 15% rice tariff (EO 105). Replaces "
         "the diagnostic run of 14 Oct: milled rice split from processed food with PSA's 2023 import value, drought as lost "
         "effective land of rice and maize (land tied to each crop for the season), rice and maize sized jointly.", "",
         f"**Shock:** 2026 wet-season crop at ONI {o2:.2f} (NOAA, seasons observed so far); 2027 dry-season crop at the ONI shown "
         "(scenario; CCSR/IRI plume of 21 Sept 2026: strong El Nino into early 2027). Province panel 1987-2026 "
         "(`outputs/elnino_panel_20261014.md`), whose El Nino effect may lean high (its section 2).", "",
         "| Result | " + " | ".join(t.columns) + " |", "|---|" + "---|" * len(t.columns)]
    L += [f"| {k} | " + " | ".join(fmt(v) for v in t.loc[k]) + " |" for k in t.index]
    L += ["", "## For the over-time (combined) run: calendar-year losses, ONI 2.0", "",
          "| Year | palay lost (% of a year's production) | corn lost (%) |", "|---|---|---|"]
    L += [f"| {y} | {v['arice'] * 100:.2f} | {v['amaiz'] * 100:.2f} |" for y, v in cal.items()]
    L += ["", "**Reading.** Imported milled rice now absorbs much of the shortfall (imports rise), so the palay price rises far less "
          "than in the 14 Oct diagnostic (+70%). Effective land falls by more than output because farms add labour and inputs "
          "to the land they still have. The world rice price variant adds the 2026 rise in the Viet Nam 5% price, which comes "
          "partly from El Nino elsewhere in Asia and partly from other causes; the combined run carries it once, as a world "
          "food price. EO 118's 30-day ₱50/kg price cap on imported rice (May 2026) is not modelled."]
    out = ROOT / "outputs" / f"elnino_2026-27_cge_households_{dt.date.today():%Y%m%d}.md"
    out.write_text(chr(10).join(L) + chr(10), encoding="utf-8")
    ml.write(links["central"], ROOT / "outputs" / f"Infinity_GEM_micro_link_elnino_2026-27_oni2_{dt.date.today():%Y%m%d}.xlsx")
    print("saved", out)


if __name__ == "__main__":
    main()
