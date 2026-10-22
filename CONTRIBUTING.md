# Contributing

Thank you for helping. Issues (bugs, questions, results that look wrong) and pull requests are welcome.

## Rules for changes

1. **Every check must pass:** `python checks/run_all_checks.py`. Checks that need data you have not added report NOT RUN; they are never counted as passed.
2. **New features are opt-in.** With default settings the model must give exactly the results frozen in `checks/reference_live.json` (check R0). If a deliberate correction changes a default result, explain it in the pull request and in `CHANGELOG.md`.
3. **Every parameter needs a source** you have opened, cited in the code or in `docs/guides/08_PARAMETERS_AND_SOURCES.md` with page or table number.
4. **Data:** add only files whose licence allows redistribution, with their source, licence and checksum in `data/DATA_INVENTORY.md`; otherwise add download instructions.
5. **Equations:** if you change one, update `docs/verification/01_EQUATION_CONCORDANCE_Lofgren2002_GAMS_Python.md`.

## Reporting a result that looks wrong

Please include the shock, the closure, the settings, the version (`infinity_gem.__version__`) and the numbers you expected, with their source. Comparisons with other models (GAMS, MPSGE, GEMPACK, Dynare) are especially useful.

This project follows the [Contributor Covenant code of conduct](CODE_OF_CONDUCT.md).
