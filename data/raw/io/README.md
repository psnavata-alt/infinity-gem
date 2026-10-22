# PSA input-output tables

The input-output model (`infinity_gem.iomodel`), the oil import shares, the SAM builders and several checks use the Philippine Statistics Authority's **2018 Input-Output Tables of the Philippines** (released 9 December 2021) and its 2018 supply and use tables, downloaded from PSA's [Supply and Use and Input-Output Tables](https://psa.gov.ph/statistics/supply-and-use-input-output/tables) page. They are included here with PSA's file names (`data/DATA_INVENTORY.md` lists each file with its source and checksum). PSA's terms of use: cite PSA as the source.

| File | PSA table | Used by |
|---|---|---|
| `80-Industry20Table202018.xlsx` and its CSV copy `80-Industry20Table202018.csv` | B.1, 80-industry transactions | the I-O model (`paths.IO_2018`); checks I1-I4, S5 and R0's input-output results |
| `80-Industry20Matrix202018.xlsx` | B.3, 80-industry Leontief inverse | check I1 (the inverse computed from B.1 must equal PSA's, to about 1e-8) |
| `16-Industry20Table202018.xlsx` and its CSV copy `16-Industry_Table_2018.csv` | A.1, 16-industry transactions | the 16-industry I-O model (`paths.IO_2018_16`); checks I5, S5 and S6 |
| `16-Industry20Matrix202018.xlsx` | A.3, 16-industry Leontief inverse | check I5 |
| `240-Industry20Table202018.xlsx` | C.1, 240-industry transactions | the petroleum and rice splits of the SAM (checks S1, S3), the oil and fertilizer import shares |
| `2018 Supply and Use Tables.xlsx` | supply and use tables by 240 products | the oil import shares (`infinity_gem/oil.py`) |

The CSV files are cell-by-cell copies of PSA's Excel tables (nothing computed): `python data/raw/io/psa_io_to_csv.py` makes them again from the Excel files (the 16-industry copy is also made by `tools/build_io16_csv.py`).

Not included, because no code reads them: PSA's technical coefficient tables, the 240-industry Leontief inverse, the industry classification file and the press release. They can be downloaded from the same PSA page.
