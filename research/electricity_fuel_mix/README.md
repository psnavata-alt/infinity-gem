# Research code: electricity's fuel mix in PSA's 2018 tables

`fuel_mix_evidence.py` compares the fuels that PSA's 2018 supply-use and input-output tables give the electricity industry with DOE's generation mix and with GTAP 10A's IEA-based energy volumes, and writes the inputs of the electricity fuel-mix correction in the own SAM v0.6e and later (`data/processed/electricity_fuel_mix_inputs_2014-2023.csv`). Research, NOT FOR CITATION.

Two of its inputs are not in this repository: GTAP 10A (licensed; the GTAP licence does not allow redistribution) and DOE's 2025 Power Statistics summary table (a DOE publication). For the same reason the inputs file it writes is not included, and checks S10 and S11, which rebuild the SAM files from it, report NOT RUN without it. The SAM files themselves are included (`data/processed/`).
