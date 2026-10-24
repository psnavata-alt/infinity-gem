# Research code: world coal and LNG price paths

`coal_lng_paths.py` writes `data/processed/coal_lng_price_paths_2026-2030.csv`, the calendar-year changes in world coal and LNG prices against their January-February 2026 level, from the World Bank Pink Sheet's monthly prices (`data/raw/macro/WorldBank_PinkSheet_coal_lng_monthly.csv`; CC BY 4.0). `infinity_gem/oil.py` (`coal_lng_paths`, `coal_lng_shock`) reads it for the opt-in coal and LNG part of the oil shock on the own SAM v0.7 and later, which have a coal account. Models without a coal account are unchanged. Research, NOT FOR CITATION.

Run: `python research/coal_lng_prices/coal_lng_paths.py`
