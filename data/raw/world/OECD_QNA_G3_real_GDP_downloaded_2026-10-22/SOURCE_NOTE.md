# Quarterly real GDP of the United States, the euro area and Japan (OECD Quarterly National Accounts)

Downloaded 22 October 2026 by `tools/download_oecd_g3_gdp.py` from the OECD Data Explorer's SDMX API:

`https://sdmx.oecd.org/public/rest/data/OECD.SDD.NAD,DSD_NAMAIN1@DF_QNA,1.1/Q.Y.USA+EA+JPN.S1.S1.B1GQ._Z._Z._Z.XDC.L.N.T0102?startPeriod=2000-Q1&dimensionAtObservation=AllDimensions&format=csvfilewithlabels`

Dataflow OECD.SDD.NAD:DSD_NAMAIN1@DF_QNA(1.1); gross domestic product (B1GQ); chain-linked volume (price base L);
national currency, millions; calendar and seasonally adjusted; not annualised; table T0102. The euro area is
the OECD's 'EA' aggregate (the current 20 members).

| File | Area | Quarters | Observations |
|---|---|---|---|
| `OECD_QNA_USA_real_GDP_quarterly_2000Q1-2026Q2.csv` | USA | 2000Q1-2026Q2 | 106 |
| `OECD_QNA_EA20_euro_area_real_GDP_quarterly_2000Q1-2026Q2.csv` | EA | 2000Q1-2026Q2 | 106 |
| `OECD_QNA_JPN_real_GDP_quarterly_2000Q1-2026Q2.csv` | JPN | 2000Q1-2026Q2 | 106 |

**Source and terms.** OECD (2026), Quarterly National Accounts, OECD Data Explorer (accessed on the date above).
The OECD's data are open (OECD press release, 1 July 2024:
https://www.oecd.org/en/about/news/press-releases/2024/07/oecd-data-publications-and-analysis-become-freely-accessible.html).
The national sources: U.S. Bureau of Economic Analysis (a US government work, public domain); Eurostat
(reuse authorised provided the source is acknowledged); Cabinet Office, Government of Japan (numerical data
are not subject to copyright). Values are as published, rounded to 0.1 million; only the layout was changed
(observation_date, value).

**Use.** `research/dsge/ph_data.py` (`world_growth`): world output growth = the simple average of the three
series' quarterly log growth.

**Against the FRED copies** (quarterly log growth x 100, percentage points):

| Series | Quarters | Correlation | Mean absolute difference | Largest difference |
|---|---|---|---|---|
| USA | 105 | 1.00000 | 0.000 | 0.000 |
| EA | 105 | 0.99994 | 0.014 | 0.073 |
| JPN | 105 | 1.00000 | 0.000 | 0.000 |
| G3 average | 105 | 0.99999 | 0.005 | 0.024 |
