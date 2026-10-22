# Notice: licences in this repository

| What | Licence |
|---|---|
| The code (`infinity_gem/`, `checks/`, `app/`, `scenarios/`, `preshock/`, `research/`, `tools/`, the Python and Julia scripts in `validation/` and `data/`) | MIT License (`LICENSE`), copyright (c) 2026 Paolo Navata |
| The documentation (`README.md`, `docs/`, the README files in other folders) | Creative Commons Attribution 4.0 International (CC BY 4.0), https://creativecommons.org/licenses/by/4.0/ : you may share and adapt it, with credit to Paolo Navata (Infinity GEM) |
| `CODE_OF_CONDUCT.md` | Adapted from the Contributor Covenant, version 2.1 (its attribution is at the end of the file) |
| IFPRI's standard CGE model code in `validation/ifpri/gams_ph/`, `validation/ifpri_home/gams_ph/` and `validation/ifpri_full/gams_ph/` (the `.GMS`, `.DAT` and `.inc` files) | GNU General Public License, version 2, as IFPRI released it; the full text is in `LICENSES/GPL-2.0-only.txt`, and the `NOTICE.md` in each of those folders lists the changes |
| Data files | Their own licences and terms, listed file by file in `data/DATA_INVENTORY.md` with each publisher's citation (below) |

## Data: credits and terms

- **IFPRI's social accounting matrices** (CC BY 4.0): International Food Policy Research Institute (IFPRI). 2025. *2023 Social Accounting Matrix for Philippines*. Harvard Dataverse, doi:10.7910/DVN/WQXUQW; and International Food Policy Research Institute. 2025. *2023 Social Accounting Matrix for Philippines: A Nexus Project SAM*. Data Paper. Washington, DC: IFPRI. https://hdl.handle.net/10568/176224. IFPRI. 2021. *2018 Social Accounting Matrix for the Philippines*. Harvard Dataverse, doi:10.7910/DVN/XSEXEP. The SAMs built from them (`data/processed/`) are CC BY 4.0 with credit to IFPRI.
- **Philippine Statistics Authority (PSA)** (public statistics; cite PSA as the source): OpenSTAT tables, "Source: Philippine Statistics Authority, OpenSTAT, table [ID], retrieved [date]" (terms: https://openstat.psa.gov.ph/Terms); the 2018 input-output and supply-use tables, "Source: Philippine Statistics Authority, [table title], retrieved [date]" (terms: https://psa.gov.ph/terms-of-use). Tidy copies of OpenSTAT tables were reshaped to long format, values unchanged; Excel files had their workbook metadata removed, cell values unchanged.
- **The World Bank** (CC BY 4.0; datasets terms https://www.worldbank.org/ext/en/legal/terms-conditions/datasets): "The World Bank: Commodity Price Data (The Pink Sheet), October 2026: Bloomberg Finance L.P.; Energy Intelligence Group; OPEC; World Bank" (crude oil; other commodities have the sources the Pink Sheet lists); "The World Bank: World Development Indicators: [the indicator's source]". The MANAGE-WB parameter extracts are MIT, copyright (c) 2026 World Bank (`data/raw/elasticities/LICENSE-MANAGE-WB.txt`).
- **OECD** (open data): OECD (2026), Quarterly National Accounts, OECD Data Explorer, accessed 22 October 2026; national sources U.S. Bureau of Economic Analysis, Eurostat and the Cabinet Office of Japan.
- **Bank for International Settlements**: "Source: BIS, [dataset code], retrieved [date]". **U.S. Energy Information Administration**: "Source: U.S. Energy Information Administration, Short-Term Energy Outlook (February 2026)" and "(October 2026)". **Penn World Table 11.0** (CC BY 4.0): Feenstra, Inklaar and Timmer (2015), Groningen Growth and Development Centre. **Geopolitical risk**: Caldara and Iacoviello (2022); data downloaded from https://www.matteoiacoviello.com/gpr.htm on 14 October 2026.
- **geoBoundaries** (CC BY 3.0 IGO): Runfola et al. (2020); original data from NAMRIA, PSA and OCHA Philippines via the Humanitarian Data Exchange; simplified. **CHIRPS** v2.0 (public domain); **NOAA** Climate Prediction Center (public domain); **USDA ERS** (public domain).

*This data was provided by the International Food Policy Research Institute (IFPRI). IFPRI bears no responsibility for the analyses or interpretations of the data presented here.*

Infinity GEM is an independent research project by Paolo Navata, developed in his own time. It is not an official publication of any government office or other institution, and nothing in this repository states the position of any institution.
