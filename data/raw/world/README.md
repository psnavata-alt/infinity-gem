# World activity

`research/dsge/ph_data.py` (`world_growth`) measures world output growth as the average quarterly growth of real GDP in the United States, the euro area and Japan.

- **Included:** `OECD_QNA_G3_real_GDP_downloaded_2026-10-22/`, the three quarterly real GDP series from the OECD's Quarterly National Accounts (OECD Data Explorer, accessed 22 October 2026; open data), made by `tools/download_oecd_g3_gdp.py`; its `SOURCE_NOTE.md` gives the query, the terms and a comparison with the FRED copies the code was first estimated on (G3 growth differs by 0.005 percentage point on average). Check X3 runs on these files.
- **Not included:** the FRED copies of the same series and of Kilian's index of global real economic activity (IGREA). FRED's terms of use do not allow stored FRED content to be passed on without the St. Louis Fed's consent. `ph_data.py` reads the FRED copies if you add them to `FRED_world_activity_downloaded_2026-10-20/` here, and the OECD files otherwise.
- **The `source="igrea"` robustness option** (no check uses it) needs Kilian's index: download it from the Federal Reserve Bank of Dallas (Index of Global Real Economic Activity) and save it as `FRED_world_activity_downloaded_2026-10-20/FRED_IGREA_Kilian_global_real_activity_monthly_2000-01_2026-08.csv`, with the columns `observation_date` (monthly) and `IGREA`. Without it the option stops and says so.
