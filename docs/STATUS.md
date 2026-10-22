# Status of this repository

**Version 0.3.13.dev1, built 23 October 2026. Research code, published for outside review.**

Infinity GEM is an independent research project by Paolo Navata, developed in his own time. It is not an official publication of any government office or other institution, and nothing in it states the position of any institution. Results produced with this code are research results, for discussion: they are not forecasts and not official statistics. The code was written by the author with AI coding assistants, and it is checked by the validation suite (`checks/`), including comparisons with implementations written by people (IFPRI's GAMS code, pycge, statsmodels). The comments keep the dates and reasons of the development history (2025-2026 analyses of the Philippine economy).

## What is included

- **All the model code** (`infinity_gem/`): SAM tools and multipliers, the static and recursive-dynamic CGE with every opt-in upgrade, household demand, elasticity sets, oil shocks, the input-output models, the poverty microsimulation and macro-micro link, the time-series tools, the stochastic CGE.
- **The validation suite** (`checks/`, 75 checks) and the frozen reference results of version 0.2.
- **The validation studies** (`validation/`): IFPRI's standard CGE model in GAMS (GPL v2) with its saved results on a condensed and on the full 2023 SAM, with and without home consumption; the cross-check with pycge; a Julia/MPSGE comparison; labour-closure and backtest studies.
- **The scenarios** (`scenarios/`, `preshock/`): the 2026 shock scenarios (world oil and fertilizer prices, the fall in public construction, El Nino, and their combination with a costed response), their sensitivity analyses, and the models that size each shock from data; the earlier oil, infrastructure and cash-transfer scenarios; a template for your own shock.
- **Research code** (`research/`): the DSGE model with Bayesian estimation, with the posterior draws of its first estimation on public data (`research/dsge/draws/`, read by one test of check X3); the forward-looking CGE.
- **The Simulator** (`app/`) and the **SAM builders and tools** (`tools/`).
- **Documentation** (`docs/`): guides 01-06, 08, 10, 11 and 11b; the equation concordance with the published model and IFPRI's GAMS code; the audit for rigging and its latest run; a Stata check of the equations.
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
| PSA's input-output coefficient tables, the 240-industry Leontief inverse, the industry classification and the press release | No code reads them | Download them from PSA (`data/raw/io/README.md`) |
| The original Excel and .xls downloads of two series whose CSV extracts are included (USDA ERS tables, the full geopolitical-risk file) | They carried metadata from a document library | Download them from the publishers (the CSV extracts are included) |
| The copyrighted papers in the reference library | Copyright | Each is cited where it is used |
| Working notes, plans, logs and design notes of the development, and two guides to an Excel verification workbook that is not included | Not part of the public code | The equation concordance, the Stata check and the validation suite cover the same ground |

Excel files that are included were cleaned of the metadata a document library adds (customXml parts, the content-type property, the record of the folder last saved in); their cell values are unchanged (check D1 hashes the cell values).

## Changes from the development copy

- The package is named `infinity_gem` (it was developed under another name); data files built by the project are named `InfinityGEM_SAM_...`, and the own-SAM option is `sam_variant="own"`.
- **The 2026 oil shock** (`preshock/oil_shock_size.py`, `preshock/shock_paths.py`) is measured from the World Bank Pink Sheet's monthly Dubai price and the EIA Short-Term Energy Outlook's US wholesale diesel and gasoline prices, instead of a weekly tracker that cannot be shared. Monthly averages smooth the March 2026 spike, so the 2026 oil shock here is smaller (conflict-period Dubai about +31% against January-February 2026, instead of about +49% with weekly data), and the 2026 scenario results differ from the development copy's.
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
| R0 (in part) | its Simulator poverty result needs the FIES microdata; R0 compares every other result (the input-output results included) and names the ones it could not compute |
| H1 (in part) | its GTAP benchmark needs the GTAP 10 parameters; H1 runs its other parts and says so |

## The validation suite in a clean clone

Run on 23 October 2026, 05:56 on a fresh `git clone` of this repository (552 files), Windows 11, Python 3.14.4, one processor core, without any of the files that are not distributed; 9 minutes.

**62 of the 62 checks that could run passed**. 13 checks reported NOT RUN because they need files that are not distributed (the table above): P1, V1, A1, H2, H3, A2, V6, X1, ML1, S3, S6, ML2, PC1.

R0 compared the results it could compute and named the others; H1 ran without its GTAP benchmark. Add the files the README files in `data/raw/` describe and the NOT RUN checks run; NOT RUN is never counted as a pass.
