# Research code: the OECD inter-country input-output tables

Research code, not used by any default result; NOT FOR CITATION. Data: OECD (2025), OECD Inter-Country Input-Output Tables, 2025 edition, https://oe.cd/icio. The OECD states no terms of use beyond its citation line, so the tables are not in this repository: download the small CSV version for 2022 (and 2018 if wanted) and pass the file paths to the scripts.

| File | What it does |
|---|---|
| `icio_common.py` | Loader (81 areas x 50 industries; taxes less subsidies, value added and output rows; six final-demand columns per area), accounting checks, partner groups |
| `oil_cost_push_2022.py` | A Leontief cost-push price model of an oil shock on the Philippine block, four variants, compared with PSA's 2018 table (`infinity_gem/iomodel.py`, check I1) |
| `partner_demand_exposure_2022.py` | Philippine value added embedded in each partner's final demand, by partner and by Philippine industry |

Run: `python research/icio/<script>.py <path of 2022_SML.csv> [<path of 2018_SML.csv>]` (about 30 seconds each). Outputs go to `outputs/`.
