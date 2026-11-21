"""Check TS1 (11 Nov 2026, 0.3.13): a scenario's amounts in the dynamic CGE grow with the baseline (transfer_scaling).

The defect (found 11 Nov 2026 in a rerun of earlier scenarios on "0.3 recommended", confirmed by an independent check;
a review note (not included)): DynamicCGE._spec scales every baseline level with
the year's index Y_index (government consumption, the investment level, the SAM's own transfers through trg_scale, foreign
flows), but a scenario's AMOUNTS ('trg_h_add', 'sav_add', 'grow_out_add', in ₱ bn) entered the year's solve at the 2023 SAM's
scale. An amount entered as a share of year y's GDP (scenarios/_common.to_sam_units) was therefore only 1 / Y_index of that
share of the model's year-y economy (1 / 1.21 in 2027 on the DBCC path). The fix (11 Nov 2026): DynamicCGE(transfer_scaling="baseline"), the default, multiplies them by Y_index, as the SAM's
own transfers are; transfer_scaling="legacy" keeps the old behaviour exactly.

Tests (each prints [PASS] or [FAIL]; exit 0 only if all pass):
  T1 share: an amount entered as the share s of year y's GDP is the share s of the model's year-y baseline real GDP in the
     year's solve, in a long-run year and in a short-run (hybrid) year; 'legacy' gives s / Y_index (the defect, shown).
  T2 deficit: the government's spending includes exactly that amount times the CPI (the GEXP identity rebuilt from the
     solution), so the deficit counts the same pesos the households receive.
  T3 legacy = pre-fix, bit for bit: with 'legacy' the amounts reach each year's solve exactly as entered, and the paths equal
     those of the pre-fix engine. Since 12 Nov 2026 the
     pre-fix reference is COMPUTED AT TEST TIME, on the computer running the test, from the pre-fix code path itself:
     checks/reference_dynamic_prefix_708fe51.py, infinity_gem/dynamic.py exactly as in the development snapshot 708fe51 (git blob c7ab809...,
     checked below before it is used), loaded as a module of the package beside today's infinity_gem/cge.py. The 11 Nov reference
     was a file frozen on one computer (checks/reference_transfer_legacy.json), and a second computer differed from it by round-off (relative 1.3e-12, also on the pre-fix engine there). The frozen file is still read, for
     information only. Pass: at most 1e-12 relative (unchanged); on one computer the two code paths should agree bit for bit.
  T4 no amount, no change: a scenario of factors only gives bit-identical paths under both options (R0's kind of run).
  T5 amounts the engine derives itself (public_capital leakage, already at the year's scale) are not scaled: a leakage run is
     bit-identical under both options and its transfers equal the leaked amount; a scenario transfer beside it is scaled.
  T6 sav_add and grow_out_add scale too; mpsadj (a rate), factors and other keys do not.
  T7 an unknown transfer_scaling is refused, at construction and when set afterwards.

Run:  py -B -X utf8 checks/test_transfer_scaling.py            (about 6 minutes: T3 also builds the pre-fix engine)
      py -B -X utf8 checks/test_transfer_scaling.py --freeze   (ONLY on the pre-fix engine: rewrites the reference file)
"""
from __future__ import annotations

import datetime as dt
import json
import platform
import sys
import warnings
from pathlib import Path
import os
os.environ["INFINITY_GEM_FIES_BASE"] = "fies2023"   # 18 Nov 2026: this file reproduces results on the FIES 2023 base (its references); FIES 2025 is the default base since 18 Nov 2026 (check R41F)

import numpy as np

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
REF = Path(__file__).resolve().parent / "reference_transfer_legacy.json"
# 12 Nov 2026: the pre-fix code path, infinity_gem/dynamic.py of the development snapshot 708fe51, byte for byte (git blob id below)
PREFIX = Path(__file__).resolve().parent / "reference_dynamic_prefix_708fe51.py"
# public version: the git blob id of this repository's copy (its comments reworded, its code unchanged; the development
# copy's file: c7ab809802119d093ef08d7a8c4cc563a72c48d6)
PREFIX_BLOB = "2547e6b4aa30af5641292b3d4f2153775cc12d2a"

from infinity_gem.dynamic import DBCC_GROWTH, DynamicCGE      # noqa: E402

# The small cases. Amounts in ₱ bn at the 2023 SAM's scale, as a scenario script enters them (to_sam_units). 2026 and 2027
# carry transfers (2027 with a factor beside them), 2028 the two other amounts.
SHOCKS = {2026: {"trg_h_add": {"hhd-r1": 10.0, "hhd-u1": 5.0}},
          2027: {"trg_h_add": {"hhd-r1": -20.0}, "qinv_scale": {"ccons": 0.97}},
          2028: {"sav_add": 3.0, "grow_out_add": 2.0}}
FACTORS = {2026: {"qinv_scale": {"ccons": 0.95}}, 2027: {"remit_scale": 0.97}}
KEYS = ("QA", "YH", "EH", "QH", "GSAV", "GEXP", "CPI", "EXR")
results = []


def report(name, ok, detail):
    results.append(bool(ok))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")


def y_index(d, t):
    """The engine's own index of year t, computed in the engine's order (dynamic.py _run)."""
    y = 1.0
    for s in d.years[1:]:
        y *= 1 + d.growth[s] / 100
        if s == t:
            return y
    raise KeyError(t)


def models(cls=DynamicCGE, growth=DBCC_GROWTH):
    lr = cls(growth=growth)                               # long-run closure every year (as R0's dynamic run)
    lr.baseline()
    hy = cls(growth=growth, hybrid=True)                  # short-run closure in the shock years
    hy.baseline()
    return {"long run": lr, "hybrid": hy}


def prefix_module():
    """12 Nov 2026: the pre-fix dynamic engine, loaded from checks/reference_dynamic_prefix_708fe51.py as the
    module infinity_gem._dynamic_prefix_708fe51 (so its relative imports find today's infinity_gem.cge and infinity_gem.paths). The file
    must be the 708fe51 dynamic.py byte for byte: its git blob id is computed here and compared before the module is run."""
    import hashlib
    import importlib.util
    data = PREFIX.read_bytes()
    blob = hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()
    if blob != PREFIX_BLOB:
        raise SystemExit(f"{PREFIX.name} is not the pre-fix dynamic.py (git blob {blob}, expected {PREFIX_BLOB})")
    name = "infinity_gem._dynamic_prefix_708fe51"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, PREFIX)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    if "transfer_scaling" in mod.DEFAULT_ASSUMPTIONS:
        raise SystemExit(f"{PREFIX.name} has the transfer_scaling option: it is not the pre-fix engine")
    return mod


def record(path):
    """The numbers T3 compares: real GDP, CPI and the peso by year, and the listed variables in each shock year."""
    t = path.table
    out = {"real_gdp": [float(v) for v in t.real_gdp], "cpi": [float(v) for v in t.cpi], "exr": [float(v) for v in t.exr]}
    for y in SHOCKS:
        s = path.solutions[y]
        for k in KEYS:
            out[f"{y}:{k}"] = [float(v) for v in np.atleast_1d(np.asarray(s[k], float)).ravel()]
    return out


def run(d, shocks, option=None):
    if option is not None:
        d.a["transfer_scaling"] = option
    try:
        return d.scenario(shocks)
    finally:
        if option is not None:
            d.a["transfer_scaling"] = "baseline"


def freeze():
    if "transfer_scaling" in __import__("infinity_gem.dynamic", fromlist=["DEFAULT_ASSUMPTIONS"]).DEFAULT_ASSUMPTIONS:
        raise SystemExit("--freeze must run on the PRE-FIX engine (no transfer_scaling option); the reference stays as it is")
    ms = models()
    ref = {"note": "Pre-fix engine (the development snapshot 708fe51, 11 Nov 2026, before the transfer-scaling fix); written by "
                   "checks/test_transfer_scaling.py --freeze. Do not edit by hand.",
           "frozen": dt.datetime.now().strftime("%Y-%m-%d %H:%M"), "computer": platform.node(),
           "python": sys.version.split()[0], "numpy": np.__version__, "shocks": {str(k): v for k, v in SHOCKS.items()},
           "cases": {name: record(d.scenario(SHOCKS)) for name, d in ms.items()}}
    REF.write_text(json.dumps(ref, indent=1), encoding="utf-8")
    print(f"Saved {REF}")


def amounts_used(sol, key):
    v = sol.shocks.get(key)
    return dict(v) if isinstance(v, dict) else v


def main():
    from infinity_gem.dynamic import _grow_amounts
    ms = models()
    ref = json.loads(REF.read_text(encoding="utf-8"))

    # T1 share, T2 deficit: the 2027 NEP aid cut (₱90.21 bn, 2027 GDP ₱33,180 bn: scenarios/_common.PSA_GDP) entered as to_sam_units
    # does, here on the model's own benchmark GDP; 2027 is a long-run year in the long-run model and a short-run year in the hybrid
    X, GDP27, y = -90.21, 33180.0, 2027
    for name, d in ms.items():
        sam_gdp = float(d.base.table.loc[d.years[0], "real_gdp"])
        entered = X / GDP27 * sam_gdp
        sh = {y: {"trg_h_add": {"hhd-r1": 0.6 * entered, "hhd-u1": 0.4 * entered}}}
        Y = y_index(d, y)
        p_new, p_old = run(d, sh), run(d, sh, "legacy")
        used_new = sum(amounts_used(p_new.solutions[y], "trg_h_add").values())
        used_old = sum(amounts_used(p_old.solutions[y], "trg_h_add").values())
        base_gdp = float(d.base.table.loc[y, "real_gdp"])
        s_want = X / GDP27
        s_new, s_old = used_new / base_gdp, used_old / base_gdp
        closure = str(p_new.table.loc[y, "closure"]) if "closure" in p_new.table.columns else "long run"
        exact = all(amounts_used(p_new.solutions[y], "trg_h_add")[h] == v * Y for h, v in sh[y]["trg_h_add"].items())
        as_entered = amounts_used(p_old.solutions[y], "trg_h_add") == sh[y]["trg_h_add"]
        ok1 = exact and abs(s_new / s_want - 1) < 1e-8 and as_entered and abs(s_old * Y / s_want - 1) < 1e-8
        report(f"T1 share ({name}; {y} {closure})", ok1,
               f"entered {s_want:.6%} of {y} GDP: in the model {s_new:.6%} of the year's baseline GDP (amount x Y_index "
               f"{Y:.6f}, exact: {exact}); legacy {s_old:.6%} = {s_old / s_want:.4f} of the intended share (1 / Y_index = {1 / Y:.4f})")
        # T2: GEXP rebuilt from the solution and the model's parameters (cge.py, government block)
        sol, m = p_new.solutions[y], (d.ms if closure == "short run" else d.m)
        cpi, exr = float(sol["CPI"]), float(sol["EXR"])
        trg_scale = Y                                                     # _spec: trg_scale = Y_index (no factor on it here)
        add = np.array([amounts_used(sol, "trg_h_add").get(h, 0.0) for h in m.H])
        gexp = (float(np.asarray(sol["PQ"]) @ np.asarray(sol["QG"])) + float(((m.trg_h * trg_scale + add) * cpi).sum())
                + float(m.trg_ent) * trg_scale * cpi + float(m.grow_out) * exr)
        gap = abs(gexp - float(sol["GEXP"])) / abs(float(sol["GEXP"]))
        report(f"T2 deficit ({name})", gap < 1e-12, f"government spending rebuilt with the scaled amount x CPI: relative gap {gap:.1e}")

    # T3 legacy = pre-fix, bit for bit. 12 Nov 2026: the reference is computed now, on this computer, by the pre-fix code path
    # (prefix_module); the file frozen on 11 Nov on one computer is compared for information only
    def diffs(now, other):
        dabs = max(float(np.max(np.abs(np.asarray(now[k]) - np.asarray(other[k])))) for k in other)
        drel = max(float(np.max(np.abs(np.asarray(now[k]) - np.asarray(other[k])) / np.maximum(np.abs(np.asarray(other[k])), 1e-9)))
                   for k in other)
        return dabs, drel
    pre = prefix_module()
    pms = models(pre.DynamicCGE, pre.DBCC_GROWTH)
    for name, d in ms.items():
        p = run(d, SHOCKS, "legacy")
        asis = all(amounts_used(p.solutions[t], k) == v for t, sp in SHOCKS.items() for k, v in sp.items()
                   if k in ("trg_h_add", "sav_add", "grow_out_add"))
        now, old = record(p), record(pms[name].scenario(SHOCKS))
        dabs, drel = diffs(now, old)
        same_keys = set(now) == set(old)
        frz = ref["cases"][name]
        fabs, frel = diffs(now, frz) if set(frz) == set(now) else (float("nan"), float("nan"))
        report(f"T3 legacy = pre-fix ({name})", asis and same_keys and drel <= 1e-12,
               f"amounts as entered: {asis}; {sum(len(v) for v in old.values())} numbers against the pre-fix engine computed now on "
               f"this computer ({PREFIX.name}, blob {PREFIX_BLOB[:7]}): largest difference {dabs:.1e} (relative {drel:.1e}); "
               f"bit for bit: {dabs == 0.0}. For information, against the file frozen {ref['frozen']} on {ref['computer']}: "
               f"{fabs:.1e} (relative {frel:.1e})")
        p_new = run(d, SHOCKS)
        moved = max(abs(float(p_new.table.loc[t, "real_gdp"]) / float(p.table.loc[t, "real_gdp"]) - 1) for t in SHOCKS)
        print(f"       (default against legacy, same case: real GDP differs by up to {moved:.2e} in the shock years)")

    # T4 factors only: the option changes nothing
    d = ms["long run"]
    a, b = run(d, FACTORS), run(d, FACTORS, "legacy")
    dx = max(float(np.max(np.abs(a.solutions[t].x - b.solutions[t].x))) for t in d.years)
    report("T4 factors only", dx == 0.0, f"every year's solution vector, default against legacy: largest difference {dx:.1e}")

    # T5 leakage (the engine's own amounts) and a scenario transfer beside it, in a short-run year
    hy = ms["hybrid"]
    pc = dict(phi=0.1, kg_gdp=1.0, leakage={2026: 0.2}, leak_to={"hhd-u5": 0.5, "saved": 0.25, "abroad": 0.25},
              ig_public_share=0.4)                                         # test values only (as check CR1)
    d5 = DynamicCGE(growth=DBCC_GROWTH, hybrid=True, public_capital=pc)
    d5.base = hy.base
    L = 0.2 * 0.4 * float(hy.base.solutions[2026]["QINV"][hy.m.C.index("ccons")])
    l_new, l_old = run(d5, {2026: {}}), run(d5, {2026: {}}, "legacy")
    dx5 = max(float(np.max(np.abs(l_new.solutions[t].x - l_old.solutions[t].x))) for t in d5.years)
    s26 = l_new.solutions[2026]
    leak_ok = (abs(amounts_used(s26, "trg_h_add")["hhd-u5"] / (0.5 * L) - 1) < 1e-12 and abs(s26.shocks["sav_add"] / (0.25 * L) - 1) < 1e-12
               and abs(s26.shocks["grow_out_add"] / (0.25 * L) - 1) < 1e-12)
    Y26 = y_index(d5, 2026)
    mix = run(d5, {2026: {"trg_h_add": {"hhd-r1": 10.0}}}).solutions[2026]
    mixed = amounts_used(mix, "trg_h_add")
    mix_ok = mixed["hhd-r1"] == 10.0 * Y26 and abs(mixed["hhd-u5"] / (0.5 * L) - 1) < 1e-12
    report("T5 leakage not scaled", dx5 == 0.0 and leak_ok and mix_ok,
           f"leakage run, default against legacy: {dx5:.1e}; leaked transfer, saving and money abroad = their shares of L "
           f"(₱{L:.2f} bn, SAM units): {leak_ok}; with a ₱10 bn scenario transfer beside it: scaled to {mixed['hhd-r1']:.4f} "
           f"(x {Y26:.6f}), leakage unscaled: {mix_ok}")

    # T6 the other amounts scale; a rate, factors and other keys do not
    d = ms["long run"]
    p28, o28 = run(d, SHOCKS).solutions[2028], run(d, SHOCKS, "legacy").solutions[2028]
    Y28 = y_index(d, 2028)
    other = p28.shocks["sav_add"] == 3.0 * Y28 and p28.shocks["grow_out_add"] == 2.0 * Y28 and \
        o28.shocks["sav_add"] == 3.0 and o28.shocks["grow_out_add"] == 2.0
    spec = {"trg_h_add": {"hhd-r1": 2.0}, "trg_h_add_note": "x", "mpsadj": 0.1, "qinv_scale": {"ccons": 0.9}, "trg_scale": 1.1,
            "sav_add": 1.0}
    g = _grow_amounts(spec, 1.5)
    pure = (g["trg_h_add"] == {"hhd-r1": 3.0} and g["sav_add"] == 1.5 and g["mpsadj"] == 0.1 and g["qinv_scale"] == {"ccons": 0.9}
            and g["trg_scale"] == 1.1 and spec["trg_h_add"] == {"hhd-r1": 2.0} and spec["sav_add"] == 1.0
            and _grow_amounts(FACTORS[2026], 1.5) is FACTORS[2026] and _grow_amounts({"trg_h_add": 4.0}, 1.5)["trg_h_add"] == 6.0)
    report("T6 which keys scale", other and pure,
           f"2028 saving and money abroad x Y_index {Y28:.6f} (legacy as entered): {other}; a rate (mpsadj), factors and "
           f"trg_scale untouched, the caller's dict not changed, a dict without amounts returned as it is: {pure}")

    # T7 refusals
    refused = 0
    try:
        DynamicCGE(growth=DBCC_GROWTH, transfer_scaling="growth")
    except ValueError:
        refused += 1
    d = ms["long run"]
    d.a["transfer_scaling"] = "Legacy"
    try:
        d.scenario({2026: {"trg_h_add": {"hhd-r1": 1.0}}})
    except ValueError:
        refused += 1
    finally:
        d.a["transfer_scaling"] = "baseline"
    report("T7 refusals", refused == 2, f"refused {refused}/2 (an unknown value at construction; one set afterwards)")

    n = sum(results)
    print(f"{n} of {len(results)} transfer-scaling tests pass")
    return n == len(results)


if __name__ == "__main__":
    if "--freeze" in sys.argv[1:]:
        freeze()
    else:
        sys.exit(0 if main() else 1)
