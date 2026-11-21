# Public weekly oil prices (the default oil series since version 0.3.13)

`MBIE_Weekly_Fuel_Price_Monitoring_4_November_2026_via_FigureNZ.csv`: the Ministry of Business, Innovation and Employment of New Zealand (MBIE), *Weekly Fuel Price Monitoring*, weekly table, release of 4 November 2026 (weeks to Friday 30 October 2026), as published by Figure.NZ (https://figure.nz/table/iojOhrNyYOwt9Syp; "Data provided by Ministry of Business, Innovation, and Employment"). Downloaded 11 November 2026; values unchanged. Licence: Creative Commons Attribution 3.0 New Zealand (CC BY 3.0 NZ), as stated on Figure.NZ's page for the table.

Long format: Week, Date (MBIE's Friday), Fuel, Variable, Value, Unit, Status. `preshock/shock_paths.py` (`mbie_weekly()`, `oil_public_monthly()`, `oil_monthly(source="public-mbie")`, the default) reads:
- `Dubai crude price` (USD/bbl): MBIE's weekly Dubai. MBIE describes it only as "a medium sour crude oil extracted from Dubai";
- `Importer cost` (NZD c/L) of `Diesel` and `Regular Petrol`, and the `Exchange rate` (USD/NZD): their product per week gives US cents per litre. MBIE's importer cost is "the cost of importing the fuel to New Zealand. It includes the cost of purchasing the fuel in Singapore, shipping it to New Zealand, insurance and losses, and wharfage and handling", so it serves as a proxy for Singapore product prices.

A week belongs to the month of its starting Tuesday (MBIE's Friday date minus 3 days). MBIE marks every week from 30 June 2026 "Provisional"; it paused the importer-cost series from 18 March to 1 July 2026 and revised it on 23 September 2026 to include a risk premium. Check OL1 tests the reader.

The other public variant, `oil_monthly(source="public-worldbank")`, takes the World Bank Pink Sheet's monthly Dubai (`data/raw/macro/inflation_forecast_downloads_2026-11-05/WorldBank_PinkSheet_crude_oil_monthly_1960-2026.csv`, CC BY 4.0) with MBIE's importer costs.

Cite: Ministry of Business, Innovation and Employment (New Zealand), Weekly Fuel Price Monitoring, via Figure.NZ, CC BY 3.0 NZ.
