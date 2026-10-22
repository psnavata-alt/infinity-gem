# World Bank WDI: natural-resource rents, Philippines (downloaded 17 Oct 2026, evening)

- Source: World Bank API, `https://api.worldbank.org/v2/country/PHL/indicator/<code>?format=json&date=2010:2024` (WDI, last updated 2026-10-08). Data available to 2021.
- Codes: NY.GDP.MINR.RT.ZS (mineral rents), NY.GDP.NGAS.RT.ZS (natural gas), NY.GDP.PETR.RT.ZS (oil), NY.GDP.COAL.RT.ZS (coal), NY.GDP.FRST.RT.ZS (forest), NY.GDP.TOTL.RT.ZS (total); all % of GDP.
- Used in `research/intertemporal/pf_cge9.py` (`MINING_RENT_PCT_GDP` = 0.409, the 2016 minimum of mineral + gas + oil + coal rents over 2012-2021; the 2012-2021 average is 0.87%).
- Method caveat: rents = (world price - world-average unit cost) x production (Lange, Wodon and Carey 2018, *The Changing Wealth of Nations 2018*), so they can exceed what the national accounts record as mining's operating surplus.
