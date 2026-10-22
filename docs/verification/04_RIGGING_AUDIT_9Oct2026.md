# Could Infinity GEM's results have been rigged? An audit you can rerun

**Date:** 9 October 2026. **Version audited:** Infinity GEM 0.3.2 (released). The same audit was also run on the development copy 0.3.3.dev0, with the same results; the differences are listed in section 6.
**Written by:** an AI coding assistant. The audit is AI-written, about AI-written code. That is why it rests on tests anyone can rerun and on comparisons with programs and data that no AI wrote, not on the auditor's word.

## 1. What "rigging" would look like

Code that gives the answers someone wants, instead of the answers the equations give. In practice:

| Way to rig | Example | What catches it here |
|---|---|---|
| **Answer typed in** | A line that sets the GDP effect to −0.28% | Part A: every expected result is searched for in the code |
| **Plug term** | An extra "missing demand" amount that makes the accounts close (the archived AI-written R scripts had one, `Missing_Demand_0`) | Part C: plug names searched; Walras slack measured; tamper test 3 |
| **Error hidden** | A failed calculation replaced by a default number | Part B: every error handler read |
| **Unconverged result used** | The solver stops early and the numbers are reported anyway | Part E; tamper test 4 |
| **Weak or empty test** | A check so loose it always passes, or that passes without testing | Part D; part H: the checks must fail when the model is broken |
| **Story not matching output** | A report that quotes numbers the run did not produce | Part F |
| **Fitting to a target** | Parameters searched until the answer looks right | Part G |
| **Data edited** | One cell of the SAM changed | Check D1 (checksums); tamper test 7 |

## 2. Run it yourself

1. From the repository folder, run `python docs/verification/rigging_audit/rigging_audit.py` (about three minutes).
2. It writes a report named `RIGGING_AUDIT_RUN_<date>_<time>.md`. If you cannot write to this folder, the report goes to `Documents\Infinity GEM - my runs\rigging_audit`.

**Running it does not change the model.** The audit only reads Infinity GEM. For the tamper tests it copies the model to a temporary folder, breaks that copy, and deletes it afterwards. The script, `rigging_audit.py`, is about 700 lines. A human programmer can read it in an hour: each part is one function, and the seven deliberate breaks are listed in plain text in `TAMPERS`.

Tonight's runs:
- `rigging_audit/RIGGING_AUDIT_RUN_20261009_2219.md` (released 0.3.2);
- `rigging_audit/RIGGING_AUDIT_RUN_20261009_2224.md` (development version 0.3.3.dev0).

## 3. The strongest evidence: break the model and see whether the checks notice

If the checks were for show, a broken model would still pass them. The audit copies the model, breaks it on purpose in seven ways and runs eight checks on each broken copy: D1, D2, C1, C3, C4, C5, A1 and R0.

| # | Deliberate break | Caught by |
|---|---|---|
| 0 | None (control copy) | All eight checks PASS, as they should |
| 1 | Tariff revenue left out of government income | C1, C4 |
| 2 | An error that shows only after a shock: imports paid at pre-shock world prices. The base year is still reproduced exactly | C4 (Walras' law), R0 |
| 3 | A hidden plug: 0.1% extra demand in every factor market | C1, C3, R0 |
| 4 | Solver stopped after 3 steps but reports "solved" | C3, C4, C5, A1, R0 |
| 5 | Headline rigged: the Simulator's GDP effect multiplied by 0.9 | A1, R0 |
| 6 | A parameter changed quietly: Armington elasticity 2.0 → 2.2 | A1, R0 |
| 7 | One SAM cell changed by ₱1 bn | D1 (checksum), D2 (balance), R0 |

**7 of 7 caught.** Breaks 2 and 6 matter most. In both, the model is still internally consistent and reproduces its base year, so a check of the base year alone would miss them:
- Break 2 is caught by Walras' law. Every account must close after a shock, and an error anywhere leaves a gap.
- Break 6 is caught by R0, which compares 21 key results with the frozen results of version 0.2.

Note that a parameter change can only be caught by comparing with earlier results. No internal test can tell a "wrong" elasticity from a "right" one. That is why every parameter must have a source (`docs/guides/08_PARAMETERS_AND_SOURCES.md`).

## 4. Results, part by part

| Part | Result | Plain reading |
|---|---|---|
| A. Results typed into code | The checks' 98 expected numbers (incl. the R0 results) searched among the 144 numbers with 3 or more digits in the model code. 39 matches: **0 unexplained** | Every match is an input or a quoted reference. Inputs: the ₱238.3 bn construction cut, the ₱90.21 bn Ayuda cut, a 10% default shock. Quoted references: help text quoting an earlier estimate's +0.683 pp and an earlier estimate's 156,329 / 835,400, so users can compare. Also an earlier VAR coefficient −0.0600, used as an input and re-estimated from the data by check V1. Each match is labelled in the run report |
| B. Error handlers | 12 in the model code. None turns a failed calculation into a reported number | Details below |
| C. Plugs and slack | One slack variable only: WALRAS, the gap between total saving and total investment. In 18 shocked solutions (6 shocks × 3 closures) it is at most **3.8 × 10⁻¹² of investment**, i.e. zero. No safety clamp binds; no negative quantities; all 18 converged | The model closes its accounts without a plug |
| D. Test strength | 110 tolerances: 82 are below 0.001; the 28 others are explained below. **One check can pass without testing (H3)** | A real weakness: finding 1 |
| E. Convergence | 16 places solve the model. 14 act on the convergence flag; 2 do not | Finding 3; no result affected |
| F. Numbers in report text | 77 numbers typed into report or screen text, read one by one. They are inputs, sources and labels. **The few results typed in (three scenario reports) were checked tonight against the model and the data: all match** | Finding 4: they would not update by themselves |
| G. Fitting and randomness | 6 solver/optimiser calls, all explained below; 1 random draw (VAR confidence bands), with a fixed seed so results are reproducible | No result is fitted to a desired answer |

**What looks like rigging but is not:**
- **The WALRAS variable.** It is the standard check variable of the IFPRI model (Lofgren et al. 2002, eq. 45, savings-investment balance; concordance row 45). It must be zero in every solution, and check C4 forces it to zero.
- **Calibration.** The model's parameters are computed from the SAM, so that the base year reproduces the SAM exactly (check C2). This is the definition of calibration. Results are always changes from that base year, so calibration cannot steer them.
- **The dynamic baseline.** Productivity is chosen each year so that the baseline follows the official growth path: DBCC targets, and PSA's actual growth by industry for 2024-2025 (checks Y1, Y5). Shocks are measured against that baseline. The search is for the baseline only and never sees the shock.
- **Frisch parameter** (household demand, `demand.py`). It is fitted to published own-price elasticities (Briones et al. 2023) within fixed bounds, and check H1 confirms it lands in the literature's range.
- **Re-exports** (₱345.1 bn, electronics). Recorded exports above domestic output pass through at world prices (documented in `docs/guides/02_CGE_GUIDE.md`).
- **2018 SAM balancing.** IFPRI publishes the 2018 SAM in whole billions, so it does not balance exactly. It is balanced by weighted least squares: largest cell change ₱1.94 bn, total ₱57 bn out of ₱148,751 bn. The 2023 SAM is used as published.
- **Silent error handlers.** All 12 were read:
  - `paths.py`: two handlers test whether a folder can be written (the read-only saving of 0.3.2).
  - `_common.py`: one handler makes saving the Word copy of a report optional.
  - `simulator.py`: one handler makes the logo optional.
  - `household.py`: one handler marks an unreadable industry code as "unknown"; check H3 counts these and requires zero.
  - `dynamic.py`: two handlers try a wider search before stopping with an error. If no answer is found, the run stops with "TFP search: no bracket found".
  - `engines.py`: one handler reports "The model did not solve" to the Simulator.
  - `var.py`: one handler drops a failed bootstrap draw (finding 5).
  - The other three switch warnings off, which keeps output readable; the checks test residuals directly.
- **Wide tolerances.** Each has a reason:
  - D2: up to 6, because the 2018 SAM rounds to ₱1 bn.
  - I1: 0.05, because the September 2026 results published −161.5 to one decimal.
  - I2: 0.5%, against an earlier Excel workbook.
  - A1: ±1 person, rounding.
  - V2/V3/V4: 0.01 pp on GDP against IFPRI's GAMS model; the larger gaps on some prices are traced to measurement conventions in `validation/ifpri/README.md`.
  - Y4 (5-9%) and Y5 (±15%, ±0.2 pp): plausibility ranges, not tests of exactness.
  - H2: ±2 persons, rounding.
  - H3: 2%, against PSA's LFS total.

## 5. What the audit found: weaknesses to fix

None of these changed a published number. Each was checked tonight. Fixes were proposed for the development version.

**Update, 10 October 2026: all five are fixed in the development version (0.3.3.dev0).** Its checks: 41 of 41 passed, 1 not run on this computer (H3, now reported as "NOT RUN"), including a new check D3 that an edited SAM is refused. Check R0 confirms that the published results are unchanged. **Released as version 0.3.3 the same day**: the released version's checks: 41 of 41 passed, 1 not run (H3, which needs licensed microdata); the audit rerun on the released version finds no check that can pass without testing, no unguarded solve, and 7 of 7 deliberate breaks caught (`rigging_audit/RIGGING_AUDIT_RUN_20261010_1258.md`). A sixth item was fixed at the same time: results are saved in the "Documents" folder that Windows actually uses, which on many PCs is often moved to a cloud-synced folder.

A seventh weakness was found by the tamper test itself when it was rerun on the fixed version. Checks C3, C4 and C5 test the models that check C1 builds. If C1 failed, they found no models and reported PASS without testing anything. Because the checks run in order, this could only happen after C1 had already failed, so no report was affected. They now fail with the reason. On the development version all 7 deliberate breaks are caught; the edited data cell is now caught by 8 checks instead of 3 (`rigging_audit/RIGGING_AUDIT_RUN_20261010_1228.md`).

1. **Check H3 counts as passed when it cannot run.**
   - On a computer without PSA's licensed FIES-LFS member file, H3 prints "NOT RUN" but is counted as PASS. That is every computer except the one where the file was saved: today's "38 of 38" (`outputs/validation_report_20261009.md`) really means 37 passed and 1 did not run.
   - *Fix:* report it as "NOT RUN", counted separately ("37 passed, 1 not run on this computer").
2. **A SAM that does not balance is balanced without a warning.**
   - `SAM.load_for_model` balances any unbalanced SAM before calibrating, not only the 2018 one. In tamper test 7, the edited SAM was caught by D1, D2 and R0. But the model itself ran on it (C1 passed) after quietly balancing away the ₱1 bn.
   - *Fix:* balance only a SAM declared as published in rounded figures (the 2018 SAM). Otherwise stop with an error that gives the size of the imbalance.
3. **Two places solve the model without stopping on failure.**
   - a development script (not in this repository) prints "solved=True/False" but carries on either way. Rerun tonight in a scratch copy: both closures solved (residuals 7e-15 and 1e-15), and every table of the 29 Sept report came out the same; only a "−0.00" now prints as "0.00".
   - In `dynamic.py` (`__init__`), the benchmark solve is unguarded. The benchmark solves at its starting point (check C1), so the risk is nil.
   - *Fix:* add the stop.
4. **A few results are typed into report text instead of computed:**
   - the four-shock report's investment mix (65.5 / 33.3 / 1.2%) and its ₱25.39 bn;
   - the Cororaton benchmark's −0.6 / −0.4 vs −1.5 / −1.2%, ₱2,921 bn, 3.3% vs 8.1%;
   - the settings comparison's −₱336 bn (quoted from guide 09).

   All match the model and the data tonight. The only slip: "14% of household spending", which is 14.6%. *Fix:* compute them in the text so they cannot go stale.
5. **VAR confidence bands drop failed bootstrap draws without counting them** (`var.py`). *Fix:* report how many were dropped.

## 6. The limits of this audit, stated plainly

- **Some checks compare Infinity GEM with itself.** R0, M1 and A1 compare Infinity GEM with its own earlier results. They prove that *nothing changed*, not that *it was right*. Correctness rests on comparisons with work no AI wrote:
  - IFPRI's own GAMS model (V2, V3, V4);
  - pycge, a human-written Python port of Hosoe's model (V5);
  - the human-written Julia/MPSGE version of the IFPRI model (`validation/julia_mpsge/`; not yet a check);
  - PSA's published Leontief inverse (I1, I5);
  - an earlier Excel workbook (earlier fixed-price estimates; I1, I2);
  - an earlier VAR (V1);
  - PSA's official poverty count (P1);
  - the Excel workbook, the Stata do-files and the blind tests in `docs/verification/`.
- **The data checksums were recorded by the same agent.** A doubter can download the SAM from IFPRI and the I-O tables from PSA and compare the SHA-256 fingerprints with those listed in `data/DATA_INVENTORY.md`.
- **A scanner can miss a trick it was not written for.** That is why part H tests what the checks *do*, not what the code *looks like*. A programmer who wants to test another kind of break can copy the `rigging_audit` folder to their own computer and add it to the `TAMPERS` list in *their* copy. It still breaks only a temporary copy of the model on their own computer; the shared Infinity GEM stays untouched.
- **No audit can say whether an assumption is right**: the elasticities, the closures, the use of a 2023 SAM for 2026. That is a question for an economist reviewer.
- **development version 0.3.3.dev0** gives the same results, plus three items in its new VAR code, all benign:
  - `macrolink.py` leaves the CGE's exchange rate blank in one comparison table if it cannot be read;
  - `macrolink.py` has one unguarded benchmark solve;
  - `svar.py` has three random draws, all with fixed seeds.
