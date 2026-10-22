"""Folder locations, resolved from this file so scripts work from any working directory."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
OUTPUTS = ROOT / "outputs"

SAM_2023 = DATA_RAW / "sam" / "002_IFPRI_SAM_PHL_2023_SAM.csv"
SAM_2018 = DATA_RAW / "sam" / "002_IFPRI_SAM_PHL_2018_SAM.csv"
# 0.3: 2023 SAM with refined petroleum split from chemicals (built by tools/build_sam_petroleum_split.py)
SAM_2023_PETR = DATA_PROCESSED / "IFPRI_SAM_PHL_2023_SAM_petroleum_split.csv"
# 0.3.7: the same, with milled rice and corn split from processed food, imports at PSA 2023 customs values
# (built by tools/build_sam_rice_split.py); selected with settings rice=True
SAM_2023_RICE = DATA_PROCESSED / "IFPRI_SAM_PHL_2023_SAM_petroleum_rice_split.csv"
POP_2023 = DATA_RAW / "sam" / "003_IFPRI_SAM_PHL_2023_POP.csv"


def sam_updated(year: int, base: str = "ifpri") -> Path:
    """0.3.8: the rice-split 2023 SAM updated to PSA's nominal totals of `year` by cross-entropy
    (tools/update_sam.py; 2024 and 2025 built). Opt-in through settings (sam_year=...). base='psa' (0.3.9): updated from the PSA-consistent 2023 SAM instead (settings sam_year=... with sam_variant='psa')."""
    if base == "psa":
        return DATA_PROCESSED / f"InfinityGEM_SAM_PHL_{year}_updated_from_PSA_consistent_2023.csv"
    return DATA_PROCESSED / f"InfinityGEM_SAM_PHL_{year}_updated_from_IFPRI_2023_petroleum_rice_split.csv"
# 0.3.9: the rice-split 2023 SAM with taxes on products counted once and household consumption = PSA's 2023
# HFCE (tools/build_sam_psa_consistent.py). Opt-in through settings (sam_variant="psa").
SAM_2023_RICE_PSA = DATA_PROCESSED / "InfinityGEM_SAM_PHL_2023_PSA_consistent_from_IFPRI_petroleum_rice_split.csv"
# 0.3.9: Infinity GEM's own 2023 SAM, latest version (0.3, 18 Oct 2026 about 3:15 AM: household consumption by purpose
# = PSA's 2023 HFCE by purpose; 0.2: PSA's 2018 I-O moved to 2023; PSA national accounts, BESF 2023 taxes and FIES/FIES-LFS
# 2023 as controls; tools/build_own_sam_2023.py; versions 0.1 and 0.2 kept as _v0.1 and _v0.2). Opt-in through settings
# (sam_variant="own").
SAM_2023_OWN = DATA_PROCESSED / "InfinityGEM_SAM_PHL_2023_own_v0.5.csv"   # 0.3.10 (18 Oct 2026): v0.5 (LFS services split, PSA refining); the default for rice=True runs (settings.DEFAULT_SAM_VARIANT)


def sam_own(version: str) -> Path:
    """Infinity GEM's own 2023 SAM file of one version ('0.1', '0.2', '0.3'). SAM_2023_OWN is the latest one in use."""
    return DATA_PROCESSED / f"InfinityGEM_SAM_PHL_2023_own_v{version}.csv"
IO_2018 =DATA_RAW / "io" / "80-Industry20Table202018.csv"
# 0.3: PSA's 16-industry table (Table A.1), same layout; built by tools/build_io16_csv.py
IO_2018_16 = DATA_RAW / "io" / "16-Industry_Table_2018.csv"
FIES_PUF = DATA_RAW / "fies" / "FIES-LFS PUF 2023 Household Sum.csv"
FIES_POVLINES = DATA_RAW / "fies" / "FIES2023_official_poverty_lines_extract.csv"
# PSA's FIES-LFS 2023 public-use file with household MEMBERS (industry, class of worker, pay, hours). Licensed by PSA to
# the person who downloaded it, so it is NOT distributed: keep your own copy and point Infinity GEM to it (environment
# variable INFINITY_GEM_FIES_LFS, or the default folder data/raw/fies/fies_lfs_2023/). If absent, the LFS link in
# infinity_gem/household.py is simply unavailable.
import os as _os
FIES_LFS_DIR = Path(_os.environ.get("INFINITY_GEM_FIES_LFS", str(DATA_RAW / "fies" / "fies_lfs_2023")))
FIES_LFS_MEMBERS = FIES_LFS_DIR / "FIES-LFS PUF 2023 Household Members.CSV"
# Compiled macro panels (quarterly growth rates, 2015Q1-2026Q2; monthly levels of oil, GPR, remittances, FDI and the
# peso): built from PSA, BSP and world series. Not distributed with Infinity GEM; data/raw/macro/README.md gives the
# layout. The checks that need them (V1, X1, S3) report NOT RUN without them.
MACRO_QUARTERLY = DATA_RAW / "macro" / "macro_panel_quarterly_2015Q1-2026Q2.xlsx"
MACRO_MONTHLY = DATA_RAW / "macro" / "macro_panel_monthly.xlsx"

# Where results are saved: the repository's outputs folder when it can be written, and otherwise the person's own
# folder, Documents/Infinity GEM - my runs (or the environment variable INFINITY_GEM_MY_RUNS). Results are computed the same way
# wherever they are saved.
def _documents() -> Path:
    """The Documents folder Windows actually uses (it may have been moved), else ~/Documents."""
    if _os.name == "nt":
        import ctypes
        buf = ctypes.create_unicode_buffer(32768)
        if ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, buf) == 0 and buf.value:   # 5 = CSIDL_PERSONAL
            return Path(buf.value)
    return Path.home() / "Documents"


MY_RUNS = Path(_os.environ.get("INFINITY_GEM_MY_RUNS", str(_documents() / "Infinity GEM - my runs")))


def can_write(folder: Path) -> bool:
    """True if this person can create files in `folder` (tested by writing and deleting a small .tmp file; os.access
    cannot see every permission system on Windows)."""
    try:
        folder.mkdir(parents=True, exist_ok=True)
        probe = folder / f"~infinity_gem_write_test_{_os.getpid()}.tmp"
        probe.write_text("x", encoding="ascii")
        probe.unlink()
        return True
    except OSError:
        return False


def output_dir(*sub: str) -> Path:
    """Folder to SAVE results in: outputs/<sub> if this person can write there, else MY_RUNS/<sub> (created)."""
    shared = OUTPUTS.joinpath(*sub)
    if can_write(shared):
        return shared
    mine = MY_RUNS.joinpath(*sub)
    mine.mkdir(parents=True, exist_ok=True)
    return mine


def output_dirs(*sub: str) -> list[Path]:
    """Folders to READ saved results from: outputs/<sub> and this person's own MY_RUNS/<sub>, if they exist."""
    return [d for d in dict.fromkeys((OUTPUTS.joinpath(*sub), MY_RUNS.joinpath(*sub))) if d.is_dir()]


for _p in (DATA_PROCESSED, OUTPUTS):
    try:
        _p.mkdir(parents=True, exist_ok=True)
    except OSError:          # a read-only copy without the folder: reading still works; saving uses MY_RUNS
        pass
