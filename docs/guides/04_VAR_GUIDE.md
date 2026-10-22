# 4. Time-series econometrics: regressions, VARs, SVARs and local projections

## Why both a CGE and a VAR?

The CGE says what *should* happen given the economy's structure. Time-series models say what *has* happened in the data. They answer different questions and check each other: if the CGE says a 20% oil-price rise cuts GDP by 0.4% and the data never show anything close, one of them is wrong.

## The data

`infinity_gem.var.load_macro()` reads a compiled monthly panel: 46 quarters (2015Q1-2026Q2) of year-on-year growth rates: GDP, investment (GFCF), exports, imports, peso depreciation, remittances, the deficit-to-GDP ratio, the geopolitical risk index (Caldara-Iacoviello), Dubai crude and FDI.

**46 quarters is short.** Expect wide confidence bands and fragile results; say so whenever results are reported. Extending the database (PSA OpenSTAT, BSP) is Roadmap Phase 4.

## Tools

| Tool | What it estimates | Function |
|---|---|---|
| Regression with Newey-West errors | Effect of X on Y controlling for Z, with standard errors robust to autocorrelation | `newey_west(df, y, xs, lags=4, convention=...)` |
| VAR | How several variables move together over time | `fit_var(df[cols], lags=1)` |
| Cholesky SVAR | Responses to a shock under a timing assumption (earlier variables do not respond within the quarter to later ones) | `irf_table(res, impulse, steps, bootstrap)` |
| Local projections | The same responses, estimated horizon by horizon; more robust, noisier | `local_projection(df, y, shock, controls)` |

## Two p-value conventions: report both

`convention="large"` (statsmodels' default) uses the normal distribution; `convention="stata"` uses Stata's `newey` rules (t distribution with n−k degrees of freedom and an n/(n−k) scaling). With N = 46 they differ enough to matter: the same-quarter effect of geopolitical risk on the peso is p = 0.044 under one and p = 0.058 under the other. Significant at 5% or only at 10% depends on the convention, so state which you used.

## Reproducing the reference VAR

`py scenarios/var_task1.py` reproduces an earlier VAR exactly (b(gpr): peso +0.0078, FDI −0.0600, and the lagged models) and adds VAR impulse responses with 90% bootstrap bands and local projections. Check V1 guards the replication.

## Identification: the assumption you must defend

A Cholesky ordering (oil → geopolitical risk → peso → GDP) assumes oil does not respond within the quarter to geopolitical risk, and so on. Change the order and the "shocks" change. Always:
- justify the ordering in words (what can plausibly react within a quarter?);
- show that the main result survives a reasonable alternative ordering;
- prefer external instruments or sign restrictions (Roadmap) when the timing assumption is doubtful.

## Note on the software

statsmodels' built-in Monte Carlo IRF bands returned identical lower and upper bands in testing (26 September 2026), so `irf_table` uses its own residual bootstrap. If you upgrade statsmodels, re-test before switching back.

## Exercises

1. Add remittances to the VAR (`["oil", "gpr", "fx", "remit", "gdp"]`) and compare the GDP response.
2. Swap the order of `gpr` and `oil`; does anything important change?
3. Run `local_projection` for GDP; do the local projections and the VAR tell the same story?
4. Drop 2020Q2-2021Q2 (COVID) and re-estimate the Newey-West regressions; which results survive?
