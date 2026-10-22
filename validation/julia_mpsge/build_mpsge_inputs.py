"""Julia/MPSGE comparison, step 1: the Philippine 2023 SAM in the input format of Rutherford's MPSGE formulation of the
IFPRI standard model, as ported to Julia by M. Phillipson (WiNDC, GitHub uw-windc/IFPRI_model, `src/model.jl`).

The data step reproduces Rutherford's `ifprimpsge.gms` (December 2006, lines 268-480), account by account, on the
Philippine SAM instead of the 2004 Peru SAM. Two exact aggregations are needed because his formulation assumes them,
and BOTH models are then run on the same aggregated SAM:
  - one margin commodity (his GAMS aborts otherwise): trade (ctrad) and transport (ctran) merged -> 'trad';
  - one producing activity per commodity (sets g and s are aliases): 'other cereals' (cocer, imported only) merged
    into rice -> 'rice'.
Home consumption is moved to market purchases (as in Infinity GEM's default); re-exports (cmach) are netted out of exports
and imports (his formulation has no re-export account; Infinity GEM passes them through, which is equivalent unless the
world price of that good changes). Margins: same rate per unit on domestic sales and imports, as in Infinity GEM's
margins="split" (IFPRI eq. 1, 3, 27). Elasticities: Infinity GEM's defaults (value added 0.8, Armington 2, CET 2).
Values in ₱ trillion (the SAM's ₱ bn / 1000) to keep numbers near one, as Rutherford scales his.

Run:  py validation/julia_mpsge/build_mpsge_inputs.py [output folder]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from infinity_gem import paths  # noqa: E402
from infinity_gem.cge import CGE  # noqa: E402
from infinity_gem.sam import SAM  # noqa: E402

MERGE = {"atran": "atrad", "ctran": "ctrad", "cocer": "crice"}
SCALE = 1000.0
ELAST = dict(sigma_va=0.8, sigma_q=2.0, omega_t=2.0)


def comparison_sam() -> SAM:
    return SAM.load_for_model(paths.SAM_2023).aggregate(MERGE)


def comparison_model(**kw) -> CGE:
    """Infinity GEM on the same aggregated SAM, IFPRI-style margins."""
    return CGE(comparison_sam(), margins="split", **kw)


def build(out: Path):
    m = comparison_model()
    T = m.sam.table / SCALE                      # SAM as calibrated by Infinity GEM (home consumption at market)
    A, C, F, H = list(m.A), list(m.C), list(m.F), list(m.H)
    nm = lambda code: code[1:]                   # arice -> rice, crice -> rice
    G = [nm(c) for c in C]
    assert sorted(G) == sorted(nm(a) for a in A), "one activity per commodity needed"
    rex = pd.Series(m.rex / SCALE, index=C)
    p = {}
    p["id0"] = {(nm(c), nm(a)): T.loc[c, a] for c in C for a in A if T.loc[c, a]}
    p["fd0"] = {(f, nm(a)): T.loc[f, a] for f in F for a in A if T.loc[f, a]}
    # Factor ownership. Rutherford: fe0(row,f) = factor income paid abroad net of income from abroad. The Philippines
    # RECEIVES more factor income from abroad than it pays (net -₱293 bn, mainly labour), and an owner cannot hold a
    # negative endowment in MPSGE (the rest of the world's income would be set to zero). Equivalent mapping: the rest of
    # the world owns only the factor services it is paid for (T[row,f]); income received from abroad (T[f,row]) is
    # removed from each domestic owner's endowment in proportion to its share of factor f's payments, so it reaches
    # them through Rutherford's implicit transfer (trn0, valued in foreign exchange: as Infinity GEM values it).
    owners = H + ["ent"]
    fe0 = {}
    for f in F:
        pay = {i: T.loc[i, f] for i in owners if T.loc[i, f]}
        tot = sum(pay.values())
        for i, v in pay.items():
            fe0[(i, f)] = v - (v / tot) * T.loc[f, "row"]
        fe0[("row", f)] = T.loc["row", f]
    s0 = {(nm(a), nm(c)): T.loc[a, c] for a in A for c in C if T.loc[a, c]}
    cm0 = {(nm(c), h): T.loc[c, h] for c in C for h in H if T.loc[c, h]}
    for a in A:
        for h in H:
            assert abs(T.loc[a, h]) < 1e-12, "home consumption should be at market"
    gd0 = {nm(c): T.loc[c, "gov"] for c in C}
    i0 = {nm(c): T.loc[c, "s-i"] for c in C}
    stk0 = {nm(c): T.loc[c, "dstk"] for c in C}
    ms0 = {nm(c): T.loc[c, "trc"] for c in C}
    x0 = {nm(c): T.loc[c, "row"] - rex[c] for c in C}
    m0 = {nm(c): T.loc["row", c] - rex[c] for c in C}
    tm0 = {nm(c): T.loc["mtax", c] for c in C}
    ta0 = {nm(c): T.loc["stax", c] for c in C}
    marg = {nm(c): T.loc["trc", c] for c in C}
    ym0 = {g: sum(v for (s, gg), v in s0.items() if gg == g) for g in G}
    d0 = {g: ym0[g] - x0[g] for g in G}
    mdd0 = {g: (marg[g] * d0[g] / (d0[g] + m0[g]) if d0[g] + m0[g] > 0 else 0.0) for g in G}   # same rate per unit
    mdm0 = {g: marg[g] - mdd0[g] for g in G}
    for g in G:                                  # tariff revenue on a good without imports -> indirect tax (as GAMS)
        if m0[g] <= 1e-12 and tm0[g]:
            ta0[g] += tm0[g]; tm0[g] = 0.0
    a0 = {g: gd0[g] + i0[g] + stk0[g] + ms0[g] + sum(v for (gg, s), v in p["id0"].items() if gg == g)
          + sum(v for (gg, h), v in cm0.items() if gg == g) for g in G}
    chk = {g: a0[g] - m0[g] - d0[g] - tm0[g] - ta0[g] - mdd0[g] - mdm0[g] for g in G}
    assert max(abs(v) for v in chk.values()) < 1e-9, chk
    hp0 = {h: T.loc[h, "ent"] for h in H}
    hs0 = {h: T.loc["s-i", h] for h in H}
    hs0["ent"] = T.loc["s-i", "ent"]
    dtax0 = {h: T.loc["dtax", h] for h in H}
    dtax0["ent"] = T.loc["dtax", "ent"]
    dtax0["govt"] = dtax0["ent"] + sum(dtax0[h] for h in H)
    fsav0 = T.loc["s-i", "row"]
    gsav0 = sum(i0.values()) - fsav0 - sum(hs0[h] for h in H) - hs0["ent"]
    tm = {g: (tm0[g] / m0[g] if tm0[g] else 0.0) for g in G}
    ta = {g: (ta0[g] / a0[g] if ta0[g] else 0.0) for g in G}
    c0 = {h: sum(v for (g, hh), v in cm0.items() if hh == h) for h in H}
    trn0 = {h: c0[h] + hs0[h] + dtax0[h] - sum(v for (hh, f), v in fe0.items() if hh == h) - hp0[h] for h in H}
    trn0["ent"] = sum(hp0.values()) + dtax0["ent"] + hs0["ent"] - sum(v for (i, f), v in fe0.items() if i == "ent")
    trn0["row"] = fsav0 - sum(fe0[("row", f)] for f in F)
    for f in F:                                  # government factor income, implicit (e.g. the capital tax)
        fe0[("govt", f)] = round(sum(v for (ff, s), v in p["fd0"].items() if ff == f) - sum(fe0.get((h, f), 0.0) for h in H)
                                 - fe0.get(("ent", f), 0.0) - fe0[("row", f)], 12)
    g0 = gd0
    govdef = (sum(g0[g] + stk0[g] for g in G) + gsav0 - sum(m0[g] * tm[g] + a0[g] * ta[g] for g in G)
              - dtax0["govt"] - sum(fe0[("govt", f)] for f in F))
    mg = [g for g in G if ms0[g] > 0]
    assert len(mg) == 1, mg

    out.mkdir(parents=True, exist_ok=True)
    w = lambda name, df: df.to_csv(out / f"{name}.csv", index=False)
    for sname, elems in (("s", G), ("g", G), ("h", H), ("f", F), ("mg", mg), ("gs", G)):
        w(sname, pd.DataFrame({"uni" if sname not in ("mg",) else "g": elems, "element_text": ""}))
    def d1(name, dom, dct):
        w(name, pd.DataFrame([{dom: k, "value": v} for k, v in dct.items()]))
    def d2(name, doms, dct):
        w(name, pd.DataFrame([{doms[0]: k[0], doms[1]: k[1], "value": v} for k, v in dct.items()]))
    # the Julia loader adds an empty 'govt' row to fe0 itself (Rutherford's Peru data have no government factor
    # income), so government factor income goes in its own file and the run script fills that row after loading
    d2("id0", ("g", "s"), p["id0"]); d2("fd0", ("f", "s"), p["fd0"])
    d2("fe0", ("uni", "f"), {k: v for k, v in fe0.items() if k[0] != "govt"})
    d1("fe0_govt", "f", {k[1]: v for k, v in fe0.items() if k[0] == "govt"})
    d2("s0", ("s", "g"), s0); d2("cm0", ("g", "h"), cm0)
    for name, dct in (("i0", i0), ("stk0", stk0), ("x0", x0), ("d0", d0), ("m0", m0), ("mdd0", mdd0), ("mdm0", mdm0),
                      ("a0", a0), ("g0", g0), ("tm", tm), ("ta", ta), ("pm0", {g: 1 + tm[g] for g in G}),
                      ("eta", {g: ELAST["omega_t"] for g in G}), ("sigma", {g: ELAST["sigma_q"] for g in G})):
        d1(name, "g", dct)
    d1("esub", "s", {g: 0.0 for g in G}); d1("esubv", "s", {g: ELAST["sigma_va"] for g in G})
    d1("hs0", "uni", hs0); d1("dtax0", "uni", dtax0); d1("trn0", "uni", trn0); d1("hp0", "h", hp0); d1("c0", "h", c0)
    for name, v in (("govdef", govdef), ("gsav0", gsav0), ("fsav0", fsav0)):
        w(name, pd.DataFrame({"value": [v]}))
    info = {"sets": {"f": [], "h": [], "g": [], "mg": [], "gs": [], "s": ["g"]},
            "parameters": {"sh0": ["s"], "s0": ["s", "g"], "i0": ["g"], "stk0": ["g"], "x0": ["g"], "d0": ["g"], "m0": ["g"],
                           "mdd0": ["g"], "mdm0": ["g"], "cn0": ["g", "h"], "cm0": ["g", "h"], "id0": ["g", "s"],
                           "fd0": ["f", "s"], "fe0": ["uni", "f"], "hs0": ["uni"], "hp0": ["h"], "a0": ["g"],
                           "dtax0": ["uni"], "g0": ["g"], "esub": ["s"], "esubv": ["s"], "govdef": [], "eta": ["g"],
                           "sigma": ["g"], "trn0": ["uni"], "gsav0": [], "fsav0": [], "c0": ["h"], "pm0": ["g"],
                           "tm": ["g"], "ta": ["g"], "tva": ["s"], "tva0": ["s"]}}
    (out / "value_info.json").write_text(json.dumps(info), encoding="utf-8")
    summary = dict(sectors=len(G), households=len(H), factors=len(F), margin_commodity=mg[0], gsav0=gsav0, fsav0=fsav0,
                   govdef=govdef, max_absorption_check=max(abs(v) for v in chk.values()),
                   rex_netted=float(rex.sum()), gdp_trillion=float(m.gdp(m.solve())["nominal_expenditure"] / SCALE))
    (out / "SUMMARY.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    return summary


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "pre_model_phl40"
    print(json.dumps(build(out), indent=1))
