# Research code: world coal and LNG price paths

`coal_lng_paths.py` writes `data/processed/coal_lng_price_paths_2026-2030.csv`, the calendar-year changes in world coal and LNG prices against their January-February 2026 level, from the World Bank Pink Sheet's monthly prices (`data/raw/macro/WorldBank_PinkSheet_coal_lng_monthly.csv`; CC BY 4.0). `infinity_gem/oil.py` (`coal_lng_paths`, `coal_lng_shock`) reads it for the opt-in coal and LNG part of the oil shock on the own SAM v0.7 and later, which have a coal account. Models without a coal account are unchanged. Research, NOT FOR CITATION.

Run: `python research/coal_lng_prices/coal_lng_paths.py`

**A Philippine coal price (option, 25 October 2026 build).** `python research/coal_lng_prices/coal_lng_paths.py --coal psa` writes a second file, `data/processed/coal_lng_price_paths_2026-2030_psa_coal.csv`, with the coal path built from what the Philippines pays for its coal: PSA OpenSTAT's monthly imports of HS 2701 (every coal line and country; PSA from Bureau of Customs entries), CIF value over gross weight, from `data/raw/macro/PSA_OpenSTAT_coal_imports_HS2701-2704_downloaded_2026-10-24/` (the download script is in that folder). The LNG path is the World Bank's as in the default file. `infinity_gem.oil.coal_lng_paths(coal_series="psa")` and `coal_lng_shock(..., coal_series="psa")` read it; the default (`"world_bank"`) reads exactly what it read before.

**Customs and input-output evidence behind the own SAM v0.8 and v0.9** (research, not for citation):

- `fuel_imports_2023_customs.py`: PSA's 2023 customs imports of mineral fuels (HS chapter 27) in pesos, against each own SAM's coal, mining and refined-petroleum imports.
- `download_psa_trade_hs.py`: downloads a PSA OpenSTAT annual trade table (imports or exports by commodity and country) keeping chosen HS prefixes; the three tables it made on 24 October 2026 are in `data/raw/macro/PSA_OpenSTAT_downloads_for_SAM_v0.9_20261024/`.
- `customs_inputs_v09.py`: writes `data/processed/fuel_trade_customs_2023_v0.9_inputs.csv`, every input of the own SAM v0.9 (coal, crude, LNG and refined imports and coal exports at customs values; coal volumes; the LNG price) with its source, which `tools/build_own_sam_2023.py` version 0.9 reads.
- `refined_row_content_2018.py`: what PSA's 2018 refined-petroleum input-output rows hold by SAM user (coal, crude oil and gas, refined products), from the Supply and Use Tables; writes `data/processed/refined_row_content_2018_v0.8_inputs.csv`, which version 0.8 reads.
- `cement_coal_2023.py`: cement's coal in 2023 at IEA volumes priced two ways, and PSA's coal imports against the SAMs. Its IEA-volume step reads the electricity fuel-mix inputs, which are not included (GTAP-based; see `docs/STATUS.md`).
