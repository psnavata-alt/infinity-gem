"""The rice-tariff guard (0.4.3, 21 Nov 2026; check S14).

The scenarios set the 2026 rice tariff of 15% (EO 105) by tm_scale = 0.15 / tm, where tm is the SAM's own 2023 duty rate on milled
rice and corn (cmric). That is right only if the SAM's rate is the 2023 rate: BOC's certified 2023 rice collections over PSA's 2023
customs CIF of milled rice and corn = 34.4% (the statutory 35%). Infinity GEM SAM v0.1-v1.0 have 44-49% (their imports came from the I-O
prior, not customs) and palay carries IFPRI's ₱9.76 bn duty; Infinity GEM SAM v1.1 fixes both (tools/build_own_sam_2023.py build("1.1")).

guard(m) REFUSES a model whose SAM's cmric rate is more than TOL (1 point) from the customs-based rate, or whose palay (crice)
carries a duty, UNLESS the SAM file is one of the files filed before the fix (LEGACY: their names and SHA-256, written below when the
fix was made; every result published before 21 Nov 2026 ran on one of them). A legacy file passes with one printed warning, so every
published number still reproduces exactly and no default changes; any NEW SAM (a rebuild, an update, an edited copy) must carry the
right rate. The reference rate is read from the rice-split SAM built from the customs records (paths.SAM_2023_RICE: tools/
build_sam_rice_split.py puts BOC's ₱29.93 bn on PSA customs' ₱87.00 bn of cmric imports), so no number is typed here.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from . import paths

TOL = 0.01
# Files filed before the fix (data/processed, 21 Nov 2026), SHA-256 of the bytes: cmric rate 33-49% and palay duty 9.8-12.4 bn.
# In this repository: the SHA-256 of each file as published here (its title line differs from the development copy's; the
# values are the same).
LEGACY = {
    "IFPRI_SAM_PHL_2023_SAM_petroleum_rice_split.csv": "eabb29031d34bc1af1e184ddfcee241eaf7672cafb4bb75f9f4b44b03b56e35e",   # tm 0.3440, palay duty 9.76
    "IFPRI_SAM_PHL_2023_SAM_petroleum_rice_split_io2018_imports.csv": "377468d25b6522b572a4a55b282903fa5cfec3fcb53a64f8e29bb43079ecce58",   # tm 1.0069, palay duty 9.76
    "InfinityGEM_SAM_PHL_2023_own_v0.1.csv": "56b6dbd029bf712f324df79f9a7df67a21c0d0f5dcccc69cf1426baf7019bf3b",   # tm 0.4556, palay duty 9.76
    "InfinityGEM_SAM_PHL_2023_own_v0.2.csv": "85ab0e405d0f0223acda67f13628aaa9eeb664dd984d818a090b908d89325930",   # tm 0.4518, palay duty 9.76
    "InfinityGEM_SAM_PHL_2023_own_v0.3.csv": "6391f0d44f93e5fd7b08c6db7e5c513755922e32ae49f10e7f98255e28cabb77",   # tm 0.4755, palay duty 9.76
    "InfinityGEM_SAM_PHL_2023_own_v0.4.csv": "1a15641fe5c43ef20d812b6bfd5177ca7e30e6acfa35e5ba057671b8e42d35de",   # tm 0.4755, palay duty 9.76
    "InfinityGEM_SAM_PHL_2023_own_v0.5.csv": "e58a722ff5dece4b534242e361250ced694ff1fb8ea8b1302d6a8066593508fb",   # tm 0.4813, palay duty 9.76
    "InfinityGEM_SAM_PHL_2023_own_v0.5e.csv": "bfbe8c08be510b2c87d469a3dd7ed81cbfd7c5d2d08524cc4bde633790f738fd",   # tm 0.4813, palay duty 9.76
    "InfinityGEM_SAM_PHL_2023_own_v0.6.csv": "657bbef2e8d8c5512f95ab0ce3406863178bd2879f23620716a88c341ee9e6ed",   # tm 0.4377, palay duty 9.76
    "InfinityGEM_SAM_PHL_2023_own_v0.6b.csv": "5df31f654903b388e248a9c705d29c9b563b0d0e899dab04870512d3d1263617",   # tm 0.4377, palay duty 9.76
    "InfinityGEM_SAM_PHL_2023_own_v0.6c.csv": "6a722e1ac8a2e5654400641fdef407565f2f14b9ee562baaaca7a85451f5f17a",   # tm 0.4886, palay duty 9.76
    "InfinityGEM_SAM_PHL_2023_own_v0.6e.csv": "512ddc2a66d273df0ee06ed72490369245aa63f1bc27e02d6215e22efd81bd2d",   # tm 0.4377, palay duty 9.76
    "InfinityGEM_SAM_PHL_2023_own_v0.7.csv": "b2ea31ac042a1bef670f3b555a504ef232cae631458f802688b4b9bda78261d1",   # tm 0.4813, palay duty 9.76
    "InfinityGEM_SAM_PHL_2023_own_v0.7b.csv": "f870ea51be19b53063ef01108cf6589f9875edbacdc8a04a7153d380ca875cab",   # tm 0.4825, palay duty 9.76
    "InfinityGEM_SAM_PHL_2023_own_v0.8.csv": "78f43f3ab6f6b93f9fd4fd0a0fbc6e6adbad24223cf2aee7e33e22113cb1a01c",   # tm 0.4825, palay duty 9.76
    "InfinityGEM_SAM_PHL_2023_own_v0.9.csv": "7a417d8eea999f891c897b2f6af4cce70017f27ac2220554c42532cff986559b",   # tm 0.4807, palay duty 9.76
    "InfinityGEM_SAM_PHL_2023_own_v1.0.csv": "0ba145e85fd910d749444accb5d32a95884c318ccd8c8436df3cdccdb1d40888",   # tm 0.4805, palay duty 9.76
    "InfinityGEM_SAM_PHL_2023_PSA_consistent_from_IFPRI_petroleum_rice_split.csv": "f35d2b1f7dee12eed4411df8c8347665f5fe4677c64260576cf2f90a432a35ad",   # tm 0.3440, palay duty 9.76
    "InfinityGEM_SAM_PHL_2024_updated_from_IFPRI_2023_petroleum_rice_split.csv": "04d146ce030c9834c82c5608423d2a411c56549bde858c64fc691ce559ede141",   # tm 0.3326, palay duty 10.27
    "InfinityGEM_SAM_PHL_2024_updated_from_PSA_consistent_2023.csv": "06b9d1ffd28c8383a191fdd6bac64027ee4f1392bfe5ab99f8924bd5529ca6c7",   # tm 0.3346, palay duty 10.33
    "InfinityGEM_SAM_PHL_2025_updated_from_IFPRI_2023_petroleum_rice_split.csv": "cad43250c6b0f0b461c0a2238941091449690dce43db504e800d28119dcfbfbb",   # tm 0.3613, palay duty 12.32
    "InfinityGEM_SAM_PHL_2025_updated_from_PSA_consistent_2023.csv": "8ef961bbfd267241bc6c4e2baba6a5712f7d12025c412df16f094326ba38e27a",   # tm 0.3625, palay duty 12.38
    "R1c_cmric_only_InfinityGEM_SAM_PHL_2023_own_v0.5.csv": "4a964e896c2b670ca1c4c452c63b4ec60e2bf28f3afcc56fa1464d04f44a8f29",   # tm 0.3440, palay duty 9.76
}
_WARNED = set()


@lru_cache(maxsize=1)
def reference_rate() -> float:
    """The customs-based 2023 cmric rate: duty / CIF imports of cmric in paths.SAM_2023_RICE (BOC / PSA customs, 34.4%)."""
    from .sam import SAM
    t = SAM.load(paths.SAM_2023_RICE).table
    return float(t.loc["mtax", "cmric"]) / float(t.loc["row", "cmric"])


@lru_cache(maxsize=64)
def _file_sha(path: str) -> str:
    from .sam import sha256
    return sha256(path)


def guard(m, where: str = "") -> dict:
    """Check model m's SAM before a rice-tariff scenario uses tm_scale = 0.15 / tm. Returns the rates; raises ValueError for a
    non-legacy SAM whose cmric rate is more than TOL from reference_rate() or whose palay has a duty."""
    C = list(m.C)
    if "cmric" not in C:
        raise ValueError("rice_tariff.guard: the model has no milled-rice account (cmric); the 2026 tariff needs the rice-split SAM")
    tm = float(m.tm[C.index("cmric")])
    tp = float(m.tm[C.index("crice")]) if "crice" in C else 0.0
    ref = reference_rate()
    src = str(getattr(getattr(m, "sam", None), "source", ""))
    out = {"cmric tm": tm, "crice tm": tp, "reference": ref, "sam": Path(src).name if src else "(unknown)", "legacy": False}
    if abs(tm - ref) <= TOL and abs(tp) < 1e-12:
        return out
    name = Path(src).name if src else ""
    if name in LEGACY and Path(src).exists() and _file_sha(src) == LEGACY[name]:
        out["legacy"] = True
        if name not in _WARNED:
            _WARNED.add(name)
            print(f"rice_tariff.guard{(' (' + where + ')') if where else ''}: {name} is a file filed before the rice tariff fix "
                  f"(cmric {tm:.1%} against the customs-based {ref:.1%}; palay duty rate {tp:.0%}): kept so published results "
                  "reproduce; Infinity GEM SAM v1.1 (INFINITY_GEM_SAM_VERSION=1.1) carries the 2023 rate", flush=True)
        return out
    raise ValueError(f"rice_tariff.guard{(' (' + where + ')') if where else ''}: the SAM {name or '(unknown)'} gives milled rice and "
                     f"corn a 2023 duty rate of {tm:.4f} and palay {tp:.4f}; the 2026 tariff (tm_scale = 0.15 / tm) needs the "
                     f"customs-based {ref:.4f} (within {TOL:.2f}) and no palay duty (infinity_gem/rice_tariff.py)")
