# Status of this repository

**Version 0.4.2, built 21 November 2026 from version 0.4.2 of the code base (18 November 2026). Research code, published for outside review.**

Infinity GEM is an independent research project by Paolo Navata, developed in his own time. It is not an official publication of any government office or other institution, and nothing in it states the position of any institution. Results produced with this code are research results, for discussion: they are not forecasts and not official statistics. The code was written by the author with AI coding assistants, and it is checked by the validation suite (`checks/`), including comparisons with implementations written by people (IFPRI's GAMS code, pycge, statsmodels). The comments keep the dates and reasons of the development history (2025-2026 analyses of the Philippine economy).

## What is included

- **All the model code** (`infinity_gem/`): SAM tools and multipliers, the static and recursive-dynamic CGE with every opt-in upgrade, household demand, elasticity sets, oil shocks, the input-output models, the poverty microsimulation and macro-micro link, the time-series tools, the stochastic CGE.
- **The validation suite** (`checks/`, 102 checks) and the frozen reference results of version 0.2.
- **The validation studies** (`validation/`): IFPRI's standard CGE model in GAMS (GPL v2) with its saved results on a condensed and on the full 2023 SAM, with and without home consumption; the cross-check with pycge; a Julia/MPSGE comparison; labour-closure and backtest studies.
- **The scenarios** (`scenarios/`, `preshock/`): the 2026 shock scenarios (world oil and fertilizer prices, the fall in public construction, El Nino, and their combination with a costed response; since 0.4.2 also the central 2026 case under the 0.4 settings, `scenarios/central_case_04.py`, and its one-at-a-time sensitivity, `scenarios/sensitivity_oat_041.py`), their sensitivity analyses, and the models that size each shock from data; the earlier oil, infrastructure and cash-transfer scenarios; a template for your own shock.
- **Research code** (`research/`): the DSGE model with Bayesian estimation, with the posterior draws of its first estimation on public data (`research/dsge/draws/`, read by one test of check X3); the forward-looking CGE; scripts for the OECD inter-country input-output tables (the tables themselves are not included), the world coal and LNG price paths and the Philippine coal import price, the customs and input-output evidence behind the own SAM v0.8 and v0.9, and the evidence on electricity's fuel mix in PSA's 2018 tables.
- **The Simulator** (`app/`) and the **SAM builders and tools** (`tools/`).
- **Documentation** (`docs/`): guides 01-06, 08, 10, 11 and 11b; the equation concordance with the published model and IFPRI's GAMS code; the audit for rigging and its run of 21 October 2026 (the development copy's later runs are not included); a Stata check of the equations.
- **Data that may be redistributed**, each file with its source, licence and checksum (`data/DATA_INVENTORY.md`), with each publisher's citation and terms (`NOTICE.md`), among them the Philippine Statistics Authority's 2018 input-output tables (16, 80 and 240 industries: transactions tables and the published Leontief inverses the checks compare with) and supply-use tables, and the LFS 2025 employment by major industry group used for the input-output job-equivalents (PSA's terms of use: cite PSA as the source).

## What is not included, and why

| Not included | Why | What to do |
|---|---|---|
| PSA's FIES 2023 and FIES-LFS 2023 microdata, and anything derived from them at household level | Licensed by PSA to each user; no sharing | Download from PSA (`data/raw/fies/README.md`) |
| GTAP data (the GTAP 10A package and the parameters extracted from it) | GTAP licence | With your own GTAP licence: `tools/gtap10_philippines.py` (`data/raw/elasticities/README.md`) |
| The IMF Investment and Capital Stock Dataset | IMF terms; the two values used are typed into the code with their source | Download from the IMF (`data/raw/macro/README.md`) |
| Weekly fuel prices compiled from sources that may not be redistributed | Their sources' terms | The 2026 oil shock is measured from public series instead (below) |
| FRED series (US, euro-area and Japanese real GDP; Kilian's index of global real economic activity; the World Uncertainty Index for the Philippines) | FRED's terms of use do not allow stored FRED content to be passed on without the St. Louis Fed's consent | The DSGE reads the same GDP series from the OECD's Quarterly National Accounts (included, `data/raw/world/`); for the `igrea` robustness option, download Kilian's index from the Federal Reserve Bank of Dallas (`data/raw/world/README.md`) |
| The World Uncertainty Index workbooks (Ahir, Bloom and Furceri) | "All Rights Reserved"; no permission to redistribute | Download them from https://worlduncertaintyindex.com/data/ (`data/raw/macro/README.md`); only `preshock/domestic_politics_lp.py` reads them, and no check |
| PSA's published table of 2023 provincial poverty lines (Table 16 of the 2023 poverty statistics) | PSA's terms for its publications | No code reads it; it is on PSA's website |
| Two compiled macro panels (quarterly and monthly), and an earlier decile table and an earlier VAR estimate used as references by checks H2 and V6 | Not public | Build your own panels from public series (`data/raw/macro/README.md`) |
| BSP balance-of-payments workbooks, PSA price-situationer tables, DOE, DBM, DBCC and PAGASA documents, a third-party procurement extract | Redistribution terms not confirmed, or documents rather than data | The values used are typed into the code with their sources |
| A table of typhoon damage compiled from PAGASA's Annual Reports on Philippine Tropical Cyclones | The reports may not be reproduced without PAGASA's written permission | Compile it from the reports (`data/raw/disasters/README.md`); check SD1 and the opt-in typhoon draw need it |
| The electricity fuel-mix inputs of the own SAM v0.6e and later | They include GTAP 10A energy volumes (GTAP licence) | `research/electricity_fuel_mix/fuel_mix_evidence.py` writes them from your own GTAP package; the SAM files built with them are included |
| The OECD inter-country input-output tables (2025 edition) | The OECD states no terms beyond a citation line | Download them from https://oe.cd/icio (`research/icio/README.md`) |
| The own SAM's standalone rebuild tests (v0.5e to v0.9) | They rebuild the SAM files from the licensed FIES and FIES-LFS aggregates, and their comparison modes belong to the development copy | The SAM files are included; checks S7, S10, S11 and S12 report NOT RUN |
| The standalone test of the elasticity sensitivity sets `ph_va72b`, `ph_va72b_low` and `ph_cet72c` | Its comparison modes import the own SAM's tests (above) and use the development copy's labels | The sets are in `infinity_gem/elasticities.py` (`elasticity_set("ph_va72b")` etc.); no check needs the test |
| PSA's FIES 2025 public-use file (Volume 1) and the 2025 poverty thresholds by province and urban/rural (from PSA's 2025 Table 16), and the tool that builds and checks the thresholds file | Licensed by PSA to each user; PSA's terms for its publications; the tool reads files that are not distributed | Download the survey from PSA and build the thresholds file (`data/raw/fies/README.md`); checks FB1 and R41F report NOT RUN |
| The reference tests of the central 2026 case under the 0.4 settings and their reference results (checks R4, R41, R42, R41F) | Not in this release: their reference values are the development copy's results for that case, poverty counts included, which are not published here | The case runs with `scenarios/central_case_04.py` and its one-at-a-time sensitivity with `scenarios/sensitivity_oat_041.py` (both need the FIES files); the settings are in `infinity_gem/settings.py`; MC1 and MT1 test the two pieces 0.4.1 adds |
| The standalone tests of checks EF1, CET1, IS1 and ERP1 | They compare with saved results of earlier development runs and with estimation scripts that are not in this release | The options they test are included, with their estimates typed into the code with the source |
| Research and forecasting scripts of November 2026 (`preshock/`: GDP and inflation forecasts, the estimates behind the accelerator, the short-run export elasticity and the peso pass-through, rainfall extremes, shock sizes; `scenarios/`: re-fits and comparisons on the central 2026 case; the regional research and its check RG1; the research batch of check RB1) | Work for other documents, or research in progress | A later version |
| The scripts that compiled the own SAM v1.0's input table | They read files that are not distributed (a PDF fact sheet, a PSA establishment-survey workbook) | The table is included, with the source of every row (`data/processed/fuel_tax_and_coal_gva_2023_v1.0_inputs.csv`) |
| MBIE's methodology note and the copy of Figure.NZ's web page kept beside the MBIE weekly table | Documents, read by no code | Figure.NZ's page for the table (https://figure.nz/table/iojOhrNyYOwt9Syp) states the licence (CC BY 3.0 NZ) |
| PSA's input-output coefficient tables, the 240-industry Leontief inverse, the industry classification and the press release | No code reads them | Download them from PSA (`data/raw/io/README.md`) |
| The original Excel and .xls downloads of two series whose CSV extracts are included (USDA ERS tables, the full geopolitical-risk file) | They carried metadata from a document library | Download them from the publishers (the CSV extracts are included) |
| The copyrighted papers in the reference library | Copyright | Each is cited where it is used |
| Working notes, plans, logs and design notes of the development, and two guides to an Excel verification workbook that is not included | Not part of the public code | The equation concordance, the Stata check and the validation suite cover the same ground |

Excel files that are included were cleaned of the metadata a document library adds (customXml parts, the content-type property, the record of the folder last saved in); their cell values are unchanged (check D1 hashes the cell values).

## Changes from the development copy

- The package is named `infinity_gem` (it was developed under another name); data files built by the project are named `InfinityGEM_SAM_...`, and the own-SAM option is `sam_variant="own"`.
- **The 2026 oil shock.** Since 0.3.13 the default oil series of the 2026 scenarios (`preshock/shock_paths.py`, `DEFAULT_OIL_SOURCE = "public-mbie"`) is public: New Zealand MBIE's weekly Dubai and importer costs, included here, so the default oil paths are the development copy's. Only the option `"tracker"`, a weekly tracker that cannot be shared (the default before 0.3.13), is replaced: in this repository it reads the World Bank Pink Sheet's monthly Dubai price and the EIA Short-Term Energy Outlook's US wholesale diesel and gasoline prices (`preshock/oil_shock_size.py`, `shock_paths.oil_actual_monthly`). Monthly averages smooth the March 2026 spike, so that option's 2026 oil shock is smaller here than the tracker's.
- Checks that need files that are not distributed report NOT RUN, with the file and where to get it (below). The checks' own tests are unchanged; a crash is still a failure.
- Absolute paths were replaced by paths relative to the repository. Comments and report text were rewritten in neutral terms: they name no people, organizational units, working documents or planning lists, and they keep the technical content, the sources, the dates and the version notes. The code is unchanged by this rewriting (the build checks that every Python file's syntax tree, apart from its text, is identical).
- `research/dsge/link_cge.py` reads the posterior draws saved with the repository when `outputs/` holds none of its own.

## Checks that need files that are not distributed

| Check | Needs |
|---|---|
| P1, A1, A2, ML1, ML2, PC1 | the FIES 2023 microdata |
| H2 | the FIES 2023 microdata, and an earlier decile table used as a reference |
| H3 | the FIES and FIES-LFS 2023 microdata |
| S6 | the FIES and FIES-LFS 2023 microdata (it rebuilds the own SAM, which is included) |
| S3 | the quarterly macro panel (it rebuilds the rice-split SAM, which is included) |
| V1 | the quarterly macro panel |
| X1 | the monthly macro panel |
| V6 | an earlier VAR estimate used as a regression reference |
| S7, S10, S11, S12 | the FIES and FIES-LFS 2023 microdata and the own SAM's standalone rebuild tests (not included); S10, S11 and S12 also the electricity fuel-mix inputs (GTAP-based) |
| SD1 | the table of typhoon damage compiled from PAGASA's reports |
| S13 | as S12 (the own SAM v1.0's standalone rebuild test, not included) |
| FB1 | the FIES 2023 microdata, PSA's FIES 2025 public-use file and the 2025 thresholds file, and the tool that builds the thresholds file (not included) |
| R4, R41, R42 | the reference tests of the central 2026 case (not in this release) and the FIES 2023 microdata |
| R41F | as R41, on the FIES 2025 base (the FIES 2025 files) |
| EF1, CET1, IS1, ERP1 | their standalone tests, which compare with saved results of earlier runs (not in this release); EF1 also the FIES 2023 microdata |
| RG1 | the regional research code and its test (not in this release) and the FIES 2023 microdata |
| RB1 | the standalone tests of a research batch of 12 November 2026 (not in this release) |
| R0 (in part) | its Simulator poverty result needs the FIES microdata; R0 compares every other result (the input-output results included) and names the ones it could not compute |
| H1 (in part) | its GTAP benchmark needs the GTAP 10 parameters; H1 runs its other parts and says so |
| X3 (in part) | one test each of DSGE milestones 27 and 28 (T27f, T28e: the estimation set-up of the new models, checked against the posterior mean of an earlier run) and the test of milestone 30 (`research/dsge/test_milestone30.py`) need the particle cloud of a long SMC estimation run (written to `outputs/`, not distributed); milestone 30's also needs Kanzig's oil supply news shocks (CC BY 4.0, from https://github.com/dkaenzig/oilsupplynews, saved as `data/raw/oil/Kanzig_oil_supply_news_downloaded_2026-11-12/oilSupplyNewsShocks_2025M12.xlsx`); X3 runs its other tests and says so |

## The validation suite in a clean clone

Run on 21 November 2026, 13:53 on a fresh `git clone` of this repository (672 files), Windows 11, Python 3.14.4, one processor core, without any of the files that are not distributed; 63 minutes.

**72 of the 72 checks that could run passed**. 30 checks reported NOT RUN because they need files that are not distributed, or (since 0.4.2) standalone tests that are not in this release (the tables above): P1, V1, A1, H2, H3, A2, V6, X1, ML1, S3, S6, ML2, PC1, S7, SD1, S10, S11, S12, S13, RB1, R4, R41, EF1, CET1, IS1, ERP1, R42, FB1, RG1, R41F.

R0 compared the results it could compute and named the others; H1 ran without its GTAP benchmark; X3 ran without the DSGE tests that need a long estimation run's saved particles. Add the files the README files in `data/raw/` describe and the checks that need only those files run; NOT RUN is never counted as a pass.
