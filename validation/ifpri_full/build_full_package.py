"""Outside review: IFPRI's own model at FULL size on the 2023 Philippine SAM, for a partner who has
a GAMS licence, and Infinity GEM's results on exactly the same data for a blind comparison. (0.3.4, 14 Oct 2026)

Our own IFPRI comparison (validation/ifpri/, check V2) had to run on a 9-sector condensed SAM under the GAMS demo
licence's size limit. Everything here is the same steps WITHOUT the aggregation: 41 activities, 10 household
groups. Writes, into this folder:
  out/sam2023_full.csv            the 2023 SAM with home consumption moved to market (as Infinity GEM uses it)
  gams_ph/sam_netted.csv          after IFPRI's netting rules (both models use this)
  gams_ph/ph_data.gms             IFPRI's data file (sets, SAM, elasticities, population) for this SAM
  gams_ph/1DMODEL_PH.GMS          IFPRI's model with our validation block (copied from validation/ifpri/; only shock
                                  T4 changed: all agricultural activities, not the condensed 'aagri'); GNU GPL v2,
                                  changes marked
  gams_ph/*.inc                   IFPRI's include files, unchanged
  out/infinity_gem_results_full.csv   Infinity GEM's levels for BASE and T1-T4 under both closures, in the format the GAMS
                                  run writes (closure, shock, group, item, value)
The partner runs: gams ph_data.gms; gams 1DMODEL_PH.GMS (writes gams_ph/ifpri_results.csv); then
py compare_full.py. Same settings as the condensed run (validation/ifpri/README.md): IFPRI netting, margins split
for IFPRI, one region, Leontief top level, LES with unit elasticities (= Cobb-Douglas), elasticities 0.8/2.0/2.0.
Run:  py validation/ifpri_full/build_full_package.py
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from infinity_gem import paths                     # noqa: E402
from infinity_gem.cge import CGE                    # noqa: E402
from infinity_gem.sam import SAM                    # noqa: E402

OUT, GP = HERE / "out", HERE / "gams_ph"
OUT.mkdir(exist_ok=True); GP.mkdir(exist_ok=True)
SRC = ROOT / "external" / "IFPRI_model-main" / "src" / "gams" / "algebraic"
SMALL = ROOT / "validation" / "ifpri" / "gams_ph"

# sector groups for IFPRI's report sets (the same groups as the condensed run, validation/ifpri/build_condensed_sam.py)
AGRI = ["maiz", "rice", "ocer", "puls", "oils", "root", "vege", "sugr", "toba", "cott", "frui", "coff", "ocrp",
        "catt", "poul", "oliv", "fore", "fish"]
MINE = ["mine"]
IND = ["food", "beve", "chem", "text", "wood", "nmet", "metl", "mach", "oman", "elec", "watr", "cons"]
SER = ["trad", "tran", "hotl", "comm", "fsrv", "real", "bsrv", "padm", "educ", "heal", "osrv"]

# ---- 1. the full SAM, as Infinity GEM uses it
sam = SAM.load(paths.SAM_2023).move_home_consumption_to_market()
sam.table.to_csv(OUT / "sam2023_full.csv")
t0 = sam.table.copy()
codes = list(t0.index)
A = [c for c in codes if c.startswith("a")]
C = [c for c in codes if c.startswith("c")]
F = ["flab-n", "flab-p", "flab-s", "flnd", "fcap"]
H = [c for c in codes if c.startswith("hhd")]
INSD, INSDNG = ["ent"] + H + ["gov"], ["ent"] + H
grp = {g: [p + x for x in xs if p + x in codes] for g, xs, p in
       [("AAGR", AGRI, "a"), ("AMIN", MINE, "a"), ("AIND", IND, "a"), ("ASER", SER, "a"),
        ("CAGR", AGRI, "c"), ("CMIN", MINE, "c"), ("CIND", IND, "c"), ("CSER", SER, "c")]}
left = sorted(set(A) - set(sum((grp[k] for k in ("AAGR", "AMIN", "AIND", "ASER")), [])))
assert not left, f"activities not in any report group: {left}"
assert all(("c" + a[1:]) in C for a in A), "every activity must have its own commodity (IFPRI's MAPA2C)"

# ---- 2. IFPRI's netting rules (as validation/ifpri/build_ifpri_inputs.py)
t = t0.copy()
for i in INSD:
    t.loc[i, "row"] -= t.loc["row", i]; t.loc["row", i] = 0.0
for f in F:
    t.loc["row", f] -= t.loc[f, "row"]; t.loc[f, "row"] = 0.0
for i in INSDNG:
    t.loc[i, "gov"] -= t.loc["gov", i]; t.loc["gov", i] = 0.0
for k in codes:
    t.loc[k, k] = 0.0
assert (t.sum(axis=1) - t.sum(axis=0)).abs().max() < 1e-6
t.to_csv(GP / "sam_netted.csv")

# ---- 3. IFPRI layout: margins split into domestic and import accounts
s = t.copy()
dom = (s.loc[A, C].sum() - s.loc[C, "row"]).clip(lower=0)
imp = s.loc["row", C]
share_d = (dom / (dom + imp)).fillna(1.0)
s["trcdom"] = 0.0; s["trcimp"] = 0.0; s.loc["trcdom"] = 0.0; s.loc["trcimp"] = 0.0
s.loc["trcdom", C] = s.loc["trc", C] * share_d
s.loc["trcimp", C] = s.loc["trc", C] * (1 - share_d)
supp = s.loc[C, "trc"]
s.loc[C, "trcdom"] = supp * s.loc["trcdom", C].sum() / supp.sum()
s.loc[C, "trcimp"] = supp * s.loc["trcimp", C].sum() / supp.sum()
s = s.drop(index="trc", columns="trc")
assert (s.sum(axis=1) - s.sum(axis=0)).abs().max() < 1e-6
AC = list(s.index)

pop = pd.read_csv(ROOT / "data" / "raw" / "sam" / "003_IFPRI_SAM_PHL_2023_POP.csv", encoding="utf-8-sig", skiprows=1)
pop.columns = ["name", "code", "num", "shr"][: len(pop.columns)]
popmap = {}
for _, r in pop.iterrows():
    c = str(r["code"]).lower()
    for a, full in (("r", "rur"), ("u", "urb")):
        for q in range(1, 6):
            if c in (f"h_{full}{q}", f"hhd-{a}{q}"):
                popmap[f"hhd-{a}{q}"] = float(str(r["num"]).replace(",", ""))
assert len(popmap) == 10, popmap

IFPRI_LABELS = ['instax', 'factax', 'imptax', 'exptax', 'vatax', 'acttax', 'comtax', 'trncstdom', 'trncstexp', 'trncstimp', 'dum']
q = lambda x: "'" + x + "'"
L = lambda xs: ", ".join(q(x) for x in xs)
lines = ["$ontext", "Philippine data for IFPRI's model (Infinity GEM outside review). Generated by build_full_package.py.",
         f"FULL IFPRI 2023 Philippine SAM ({len(A)} activities, {len(C)} commodities, {len(H)} households), IFPRI's netting rules applied. Pesos bn.",
         "$offtext", "$onempty",
         f"SET AC / {L(AC + IFPRI_LABELS + ['total'])} /;",
         f"SET A(AC) / {L(A)} /;", f"SET AAG(AC) / {L(A)} /;", f"SET C(AC) / {L(C)} /;",
         f"SET MAPAAGA(AAG,A) / {', '.join(q(a) + '.' + q(a) for a in A)} /;",
         f"SET MAPA2C(A,C) / {', '.join(q(a) + '.' + q('c' + a[1:]) for a in A)} /;",
         f"SET AAGR(A) / {L(grp['AAGR'])} /; SET AMIN(A) / {L(grp['AMIN'])} /;",
         f"SET AIND(A) / {L(grp['AIND'])} /; SET ASER(A) / {L(grp['ASER'])} /;",
         f"SET CAGR(C) / {L(grp['CAGR'])} /; SET CMIN(C) / {L(grp['CMIN'])} /;",
         f"SET CIND(C) / {L(grp['CIND'])} /; SET CSER(C) / {L(grp['CSER'])} /;",
         f"SET F(AC) / {L(F)} /; SET FAGG(F) / /; SET FLAB(F) / 'flab-n', 'flab-p', 'flab-s' /;",
         "SET FCAP(F) / 'fcap' /; SET FLND(F) / 'flnd' /;",
         f"SET INS(AC) / {L(INSD + ['row'])} /; SET INSD(AC) / {L(INSD)} /; SET INSDNG(AC) / {L(INSDNG)} /;",
         "SET EN(AC) / 'ent' /;", f"SET H(AC) / {L(H)} /;",
         f"SET HURB(AC) / {L([h for h in H if '-u' in h])} /; SET HRUR(AC) / {L([h for h in H if '-r' in h])} /;",
         "SET CTD(AC) / 'trcdom' /; SET CTE(AC) / /; SET CTM(AC) / 'trcimp' /;",
         "SET R(AC) / 'row' /;", "SET GOVF / 'gfun' /;",
         "SET TRDELAS / SIGMAQ, SIGMAT, REGIMP, REGEXP /; SET PRDELAS / PRODELAS, PRODELAS2 /;",
         "PARAMETER NEST(F,F) / /;", "PARAMETER SAM(AC,AC) /"]
for i in AC:
    for j in AC:
        v = float(s.loc[i, j])
        if abs(v) > 1e-12:
            lines.append(f"  {q(i)}.{q(j)} {v:.10g}")
lines += ["/;",
          "PARAMETER TRADELAS(AC,TRDELAS) / " + ", ".join(f"{q(c)}.SIGMAQ 2.0, {q(c)}.SIGMAT 2.0" for c in C) + " /;",
          "PARAMETER PRODELASTAB(A,PRDELAS) / " + ", ".join(f"{q(a)}.PRODELAS 0.8, {q(a)}.PRODELAS2 0.6" for a in A) + " /;",
          "PARAMETER LESELAS1(H,C) / " + ", ".join(f"{q(h)}.{q(c)} 1" for h in H for c in C if s.loc[c, h] > 0) + " /;",
          "PARAMETER QFINPUT(F,AAG) / /; PARAMETER WFINPUT(F,AAG) / /;",
          "PARAMETER REGIMP(C,R) / " + ", ".join(f"{q(c)}.'row' 100" for c in C) + " /;",
          "PARAMETER REGTAR(C,R) / " + ", ".join(f"{q(c)}.'row' 100" for c in C) + " /;",
          "PARAMETER REGEXP(C,R) / " + ", ".join(f"{q(c)}.'row' 100" for c in C) + " /;",
          "PARAMETER REGETX(C,R) / " + ", ".join(f"{q(c)}.'row' 100" for c in C) + " /;",
          "PARAMETER POPTAB(AC,*) / " + ", ".join(f"{q(h)}.SURVEY {popmap[h]:.6g}" for h in H) + " /;",
          "PARAMETER GOVFSHR2(GOVF,*) / 'gfun'.'GOV' 1 /;",
          "execute_unload 'ph.gdx';"]
(GP / "ph_data.gms").write_text("\n".join(lines) + "\n", encoding="utf-8")
for f in ("1diagnostics.inc", "1varinit.inc", "1varlow.inc", "1repbase.inc"):
    shutil.copy(SRC / f, GP / f)
dat = (SMALL / "1MODEL_PH.DAT").read_text(encoding="utf-8", errors="replace")    # the GPL change notices name this SAM
(GP / "1MODEL_PH.DAT").write_text(dat.replace(
    "replaced by a condensed IFPRI 2023\nPhilippine SAM (9 sectors, 10 households).",
    "replaced by an IFPRI 2023\nPhilippine SAM (in this full-size package the full SAM of ph_data.gms: 41 activities, 42 "
    "commodities, 10 households)."), encoding="utf-8")
gms = (SMALL / "1DMODEL_PH.GMS").read_text(encoding="utf-8", errors="replace")
gms = gms.replace("1MODEL_PH.DAT (condensed Philippine SAM)",
                  "1MODEL_PH.DAT (in this full-size package with the full Philippine SAM of ph_data.gms)")
old = "IF(SAMEAS(SHK,'T4'), ALPHAVAADJ.FX('aagri') = 1.05; );"
assert gms.count(old) == 1
gms = gms.replace(old, "IF(SAMEAS(SHK,'T4'), ALPHAVAADJ.FX(AAGR) = 1.05; );   "
                       "* Infinity GEM (14 Oct 2026): all agricultural activities of the full SAM")
(GP / "1DMODEL_PH.GMS").write_text(gms, encoding="utf-8")

# ---- 4. Infinity GEM on the same netted SAM, both closures, in the GAMS run's output format
SHOCKS = {"T1": {"pwm_scale": {"cchem": 1.10}}, "T2": {"qinv_scale": {"ccons": 0.90}},
          "T3": {"remit_scale": 0.90}, "T4": {"tfp_scale": {a: 1.05 for a in grp["AAGR"]}}}
CLOS = {"SAV": "savings", "INV": "investment"}
full = SAM(t, {}, "full 2023 SAM, IFPRI netting")
rows = []
for cl, closure in CLOS.items():
    m = CGE(full, closure=closure)
    for sh, spec in [("BASE", {})] + list(SHOCKS.items()):
        s_ = m.solve(spec)
        assert s_.ok and s_.residual_max < 1e-7, (cl, sh, s_.message)
        out = [("STATUS", "WALRAS", float(s_["WALRAS"])), ("MACRO", "RGDP", m.gdp(s_)["real"]),
               ("MACRO", "RCONS", float(s_["QH"].sum())), ("MACRO", "REXP", float(s_["QE"].sum())),
               ("MACRO", "RIMP", float(s_["QM"].sum())), ("MACRO", "EXR", float(s_["EXR"]))]
        out += [("WF", f, float(s_["WF"][k])) for k, f in enumerate(m.F)]
        out += [("QA", a, float(s_["QA"][i])) for i, a in enumerate(m.A)]
        out += [("RCONSH", h, float(s_["QH"][:, i].sum())) for i, h in enumerate(m.H)]
        rows += [dict(closure=cl, shock=sh, group=g, item=it, value=v) for g, it, v in out]
pd.DataFrame(rows).to_csv(OUT / "infinity_gem_results_full.csv", index=False)
print(f"Full package: {len(A)} activities, {len(C)} commodities, {len(H)} households, {len(AC)} IFPRI accounts; "
      f"Infinity GEM results for {len(CLOS)} closures x {len(SHOCKS) + 1} runs written.")
