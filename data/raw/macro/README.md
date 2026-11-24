# Macro data

The series in this folder are included with their sources, licences and the publishers' citations (`data/DATA_INVENTORY.md`, `NOTICE.md`). These inputs are not:

## Two compiled panels (not distributed)

Some time-series checks and scripts read two compiled panels that are not public. Their layout, if you want to build your own from public series:

- `macro_panel_quarterly_2015Q1-2026Q2.xlsx` (`paths.MACRO_QUARTERLY`; check V1, `infinity_gem.var.load_macro`, check S3's peso rate): sheet `Sheet1`, rows 3-48 (46 quarters, 2015Q1-2026Q2), columns C-L, year-on-year growth rates of real GDP, gross fixed capital formation, exports, imports, the peso per US dollar, remittances, the government deficit (% of GDP), the geopolitical risk index, Dubai crude and FDI; and a sheet `FX` with the monthly peso rate. Sources: PSA national accounts (OpenSTAT), BSP (exchange rate, remittances, FDI), Caldara and Iacoviello (GPR), World Bank Pink Sheet (Dubai).
- `macro_panel_monthly.xlsx` (`paths.MACRO_MONTHLY`; check X1, the stochastic CGE, `infinity_gem.stochastic.load_task1_monthly`): sheet `Data monthly`, columns `month, oil, gpr, remit, fdi, fx` in levels.

Checks V1 and X1 report NOT RUN without them; check V6 compares with an earlier estimate that is not distributed.

## The World Uncertainty Index (download it yourself)

`preshock/domestic_politics_lp.py` (no check uses it) reads Ahir, Bloom and Furceri's World Uncertainty Index. Its site reserves all rights, so the workbooks are not included:

1. Go to https://worlduncertaintyindex.com/data/ and download the monthly and the quarterly WUI workbooks (Excel).
2. Save them in this folder as `WUI_Ahir_Bloom_Furceri_monthly_2026-09_downloaded_2026-10-15.xlsx` and `WUI_Ahir_Bloom_Furceri_quarterly_2026-10_downloaded_2026-10-15.xlsx` (the names the script looks for; a later release works the same way under these names). The script reads sheet `T1` of the monthly and sheet `T2` of the quarterly workbook.
3. Run `python preshock/domestic_politics_lp.py`. Without the files it stops and says which file is missing.

The WUI for the Philippines from FRED (series WUIPHL) is not included either: FRED's terms of use do not allow stored FRED content to be passed on.

## Two more downloads you can make yourself

- **IMF Investment and Capital Stock Dataset (ICSD)**, July 2025 release (data.imf.org, dataset IMF.FAD:ICSD): the IMF's terms do not allow redistribution. Two scenario scripts (`scenarios/infrastructure_full_dynamic.py`, `scenarios/infrastructure_public_capital.py`) read it as `IMF_ICSD_2025-07_all_countries_downloaded_2026-10-02.csv`; the two values the model uses (public capital as a share of GDP, 2019) are typed into `infinity_gem/settings.py` with their source.
- **Caldara and Iacoviello's full GPR file** (`data_gpr_export.xls`, https://www.matteoiacoviello.com/gpr.htm): `preshock/geopolitics_panel_lp.py` reads it as `Caldara_Iacoviello_data_gpr_export_downloaded_2026-10-14.xls`. The Philippine columns are included as `Caldara_Iacoviello_GPR_Philippines_monthly.csv`.

## Government debt and the balance of payments (0.4.3; download them yourself)

The opt-in modules `infinity_gem/debt.py` (check DB1) and `infinity_gem/bop.py` (with `debt.py`, check GF2) read official workbooks whose terms of redistribution are not confirmed, so they are not included. Save them under these names:

- **The Bureau of the Treasury's national government debt indicators, 1986-2025** (the Treasury's website, statistics on national government debt): `data/raw/fiscal/btr/Debt-Indicator-Annual-1986-2025.xlsx` (sheets `NG OS Debt 1986-2025` and `Debt Service 2004-2025`; the code finds the rows by their labels).
- **The Treasury's cash-operations financing, 1986-2025**: `data/raw/fiscal/btr/COR-Financing_Annual_1986-2025-1.xlsx` (sheet `2004-2025`).
- **The BSP's balance of payments, BPM6** (the BSP's website, statistics, external accounts): `Table1.xlsx`, `Table1.6.xlsx`, `Table1.7.xlsx`, `Table1.8.xlsx`, `Table1.9.xlsx` and `Table1.10.xlsx` in `data/raw/macro/bsp_bop/` (sheet `Annual`, US$ million).
- The 193rd DBCC joint statement of 8 July 2026 (PDF), if you want `debt.dbcc_fiscal_program()` to read its fiscal program from the PDF: `data/raw/oil/forecasts/DBCC_193rd_8Jul2026_joint_statement.pdf` (the code checks its SHA-256; without the PDF it uses the transcription typed into `debt.py`).

The checks DB1 and GF2 report NOT RUN until these files are present (GF2 also needs its standalone test, which is not in this release).
