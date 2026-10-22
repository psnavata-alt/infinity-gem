# 5. Checking, verifying and maintaining Infinity GEM

A model is only as trustworthy as the routine around it. This guide sets out that routine.

## 5.1 The validation suite

`py checks/run_all_checks.py` runs 30 checks (version 0.3; 16 in version 0.2) and writes `outputs/validation_report_<date>.md`. **If any check fails, no result from the toolkit may be used until the failure is explained and fixed.**

| Check | What it guards against |
|---|---|
| D1 data checksums | A data file silently changed or replaced (CSV: file hash; Excel: cell-value hash, because a file-sharing service rewrites Office files) |
| D2 SAM balance | A corrupted or misread SAM |
| M1 multipliers | Drift from the published September 2026 figures (2.170 / 2.200 / 2.162 / 2.197) |
| C1 benchmark residuals | Calibration errors: the model must hold exactly at the SAM |
| C2 SAM replication | The model's accounts must rebuild the SAM cell by cell |
| C3 homogeneity | Money illusion: doubling all prices must change nothing real |
| C4 Walras' law | Accounts that do not close after a shock |
| C5 GDP identity | Expenditure and income measures of GDP must agree |
| C6 direction | Effects with the wrong sign |
| C7 bounds | CGE results outside the range between zero and the fixed-price multiplier |
| Y1 dynamic | Baseline off its growth path; scenarios that differ from the baseline without a shock |
| P1 microsimulation | Poverty baseline not matching PSA |
| V1 VAR | Drift in the reference VAR's coefficients the geopolitics shock uses (a regression guard; the outside check is V7, statsmodels) |
| I1 input-output | The Leontief inverse drifting from PSA's published Table B.3 (validation); price and demand results drifting from their regression values (refined petroleum +10%: CPI +0.683 pp; construction −₱238.3 bn: GDP −₱161.5 bn). Equal values with an earlier workbook show equal arithmetic only |
| I2 job-equivalents | Drift from the regression values (within 0.5%); job-equivalents are a fixed-price upper bound |
| A1 simulator | The Simulator giving different numbers from the scenario scripts |
| **R0 regression (0.3)** | An upgrade changing a published result: 21 key results must equal Infinity GEM 0.2's (the published results, frozen in `checks/reference_live.json`) to nine decimals with every new switch off |
| **I3, I4 I-O identities (0.3)** | Arithmetic errors in the I-O model: all input costs +10% must raise every price 10%; one peso of demand must return one peso of income |
| **C8 2018 SAM (0.3)** | The CGE failing on the IFPRI 2018 SAM (after balancing): C1-C5 must hold |
| **Y2 hybrid closure (0.3)** | Job-gap dynamics: zero shock = baseline; the gap decays as specified |
| **Y3 public capital (0.3)** | The infrastructure productivity channel: phi = 0 equals the model without it; effects proportional to phi |
| **Y4 capital by industry (0.3)** | The putty-clay allocation and the documented baseline: DBCC path hit, valid shares, plausible capital growth, stable omega range |
| **Y5 industry baseline (0.3)** | Each PSA industry's real GVA growth 2024-2025 reproduced exactly; real GDP within 0.2 pp of PSA; zero shock reproduces the baseline; productivity and demand levers within plausible bounds |
| **L1 labour growth by skill (0.3)** | `psa_labour_growth()` reproduces PSA LFS growth by skill (2024-2025) and population-15+ growth for total employment (2027-2030); the model's labour supply follows it |
| **S1 petroleum-split SAM (0.3)** | Rebuilds the split SAM and compares with the saved file; balance; all other accounts identical to the IFPRI 2023 SAM; the CGE reproduces it and passes homogeneity; fuel price rises with an oil shock |
| **H1 LES household demand (0.3)** | Reproduces the SAM and passes homogeneity in both closures; Engel aggregation; subsistence below benchmark; Frisch between −0.5 and −3; food falls less than with Cobb-Douglas under an oil shock |
| **V2 IFPRI benchmark (0.3)** | Drift from IFPRI's own standard CGE on the condensed Philippine SAM (saved GAMS results; GDP and consumption within 0.01 pp) |
| **E1 elasticity sets (0.3)** | A sourced elasticity set that fails to calibrate or is not homogeneous |

**Reproducing is not validating.** A check that gets back someone's earlier number (M1, V1, I1, I2, A1) proves the code computes what that method computes; it does not prove the method is right. That needs an independent source (e.g. PSA's published inverse), textbook identities, and judgement about the assumptions. See the assessment of the I-O methods in `01_SAM_AND_MULTIPLIERS.md`.

## 5.2 Before any figure is published ("definition of done")

1. The script that produced it is in `scenarios/` and the report in `outputs/`, or it is a Simulator run saved with **Save this run** (`outputs/simulator/`, inputs included).
2. The validation suite passed on the same day.
3. Every input number has a dated source written in the script or report.
4. The closure, elasticities and conversions are stated.
5. At least two models were compared, or the reason for using one is stated.
6. A second person reran the script and got the same numbers.
7. The figure is recorded with its source (the script and report).

## 5.3 Changing code

- Change code only with a reason, a date and a note in `CHANGELOG.md`.
- Rerun the checks after every change. If a check's expected value must change (for example, a data update), change it deliberately, record why, and keep the old report.
- Prefer version control: put the `infinity_gem/`, `scenarios/` and `checks/` folders under git (a private repository or a network drive). Every change then has an author, a date and a way back.
- Never "fix" a failing check by loosening its tolerance without understanding why it failed.

## 5.4 Updating data

1. Save the new file in `data/raw/` under a new name; never overwrite.
2. Add a row to `data/DATA_INVENTORY.md` with the source, notes and checksum (`infinity_gem.sam.file_checksum`).
3. Point `infinity_gem/paths.py` (or the scenario) to the new file.
4. Rerun the checks; expect M1/C-series values to change if the SAM changes, and record the new expected values with the reason.

## 5.5 Routine

| When | What |
|---|---|
| Before each use | Run the checks |
| Monthly | Run the checks and all scenarios; file the reports |
| When PSA, DBM or BSP release new data | Update the dynamic baseline and data files (5.4) |
| Quarterly | Team review of one scenario against published estimates (DEPDev, PIDS, BSP, IMF/World Bank/ADB) |
| Yearly | External review (PIDS/UP); refresh elasticities; review the roadmap |

## 5.6 Benchmarking against others

- **IFPRI: done (2 Oct 2026; part of 0.3).** IFPRI's own GAMS code (Extended Standard CGE v2.00, GPL), run with the GAMS demo on a condensed Philippine SAM, matches Infinity GEM within 0.005 pp for GDP and consumption (`validation/ifpri/README.md`; check V2). Next: confirm the trade-margin explanation of the largest gap; a full-size run (Julia/MPSGE port) and the World Bank MANAGE-WB are further options.
- **Published studies:** keep a table of published Philippine CGE and VAR results (DEPDev, PIDS, BSP, IMF Article IV, World Bank PEU, ADB ADO) and compare like with like.
- **The multiplier bound (C7):** a CGE demand shock should never exceed the fixed-price multiplier.

## 5.7 Known issues (26 September 2026)

- statsmodels' Monte Carlo IRF bands were unreliable; `var.irf_table` uses its own bootstrap.
- The 2023 SAM records ₱103.7 bn of government transfers to households, far below cash-transfer budgets; Ayuda scenarios use `trg_h_add` in pesos.
- Petroleum is combined with chemicals (`cchem`); oil scenarios need an assumed petroleum share of `cchem` imports (0.6 by default).
- Re-exports are assumed for machinery and electronics (`cmach`, ₱345 bn).
- Elasticities: the default set is still literature defaults (0.8 / 2.0 / 2.0) so published results do not change; sourced sets exist in 0.3 (`08_PARAMETERS_AND_SOURCES.md` §3). No Philippine estimate exists for value-added substitution or export transformation.
- **(0.3)** Infinity GEM charges trade margins on the composite good, IFPRI on imports and domestic sales separately: the main source of the remaining gap with IFPRI (to be confirmed).
- **(0.3)** The IFPRI 2018 SAM has no household purchases of chemicals and petroleum or of fish (IFPRI's published file): do not use it for oil-price work.
- **(0.3)** Investment mobility omega above about 5 makes the putty-clay rule overshoot; use 1-5.
- **(0.3)** Labour force growth (1.5%) and the job-gap persistence (0.5) are placeholders.
- I-O job-equivalents use PSA LFS 2025 employment as compiled from PSA OpenSTAT (`data/raw/lfs/`); verify against OpenSTAT before publishing a job figure. They assume employment moves one-for-one with output (an upper bound).
