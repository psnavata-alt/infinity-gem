# Labour Force Survey tables

The PSA OpenSTAT tables in this folder are included (see `data/DATA_INVENTORY.md`; PSA's terms of use: cite PSA as the source).

`LFS_2025_employed_by_major_industry.csv` (columns `group,employed_thousand`) gives the job-equivalents of the input-output model (`IOTable.jobs`; checks I2, I5 and R0's job result): employed persons by major industry group in 2025, from the 2025 annual row of PSA OpenSTAT table 0101B3FEMP2 (`PSA_OpenSTAT_0101B3FEMP2_LFS_employed_by_major_industry_2012-2026.csv` in this folder), compiled into 19 groups. Two pairs of PSA's sections are combined: professional, scientific and technical activities with administrative and support service activities; and activities of households as employers and of extraterritorial organizations with other service activities. Every group equals the OpenSTAT table.

The maps `io80_to_lfs_group_map.csv` and `io16_to_lfs_group_map.csv` (included) assign each input-output industry to one group.
