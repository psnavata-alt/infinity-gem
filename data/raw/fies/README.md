# PSA Family Income and Expenditure Survey 2023 (download it yourself)

The poverty microsimulation (`infinity_gem.microsim`), the household detail (`infinity_gem.household`), the macro-micro link (`infinity_gem.microlink`) and the Simulator's poverty results use PSA's FIES 2023 public-use file. PSA licenses it to the person who downloads it, so it is not included and must never be added to a public repository.

1. Register at the PSA Data Archive (psada.psa.gov.ph) and accept PSA's terms of use.
2. Download the FIES 2023 public-use file (the FIES-LFS 2023 collection includes a household summary file and a household-member file).
3. Save into this folder:
   - `FIES-LFS PUF 2023 Household Sum.csv` (household summary, 163,268 households);
   - `FIES2023_official_poverty_lines_extract.csv`, a CSV with one row per household and the columns `w_regn, w_prov, fsize, toinc, rfact, mem_rfact, urb, npcinc, pline_2023, fline_2023`, extracted from PSA's FIES 2023 Stata file (which carries the official 2023 poverty and food thresholds).
4. Optional, for the LFS link (check H3) and the own SAM's rebuild (check S6): the household-member file `FIES-LFS PUF 2023 Household Members.CSV`, in the folder `fies_lfs_2023/` here, or anywhere you name in the environment variable `INFINITY_GEM_FIES_LFS`.
5. Run `python checks/run_all_checks.py`: check P1 then shows that the baseline reproduces PSA's official count of 17.54 million poor people in 2023, and the checks that were NOT RUN for want of these files run.

Included here because it contains no household data: `fies_w_prov_to_psa_province.csv` (a map of province codes to names). PSA's published table of 2023 provincial poverty lines is not included (PSA's terms for its publications); no code reads it.

Cite PSA as the source and do not attempt to identify households.
