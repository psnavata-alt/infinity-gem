# Research code: a small open-economy DSGE model for the Philippines

Research code, not used by any default result of the CGE models. The guide is `docs/guides/11_DSGE_GUIDE.md` and the estimation report `docs/guides/11b_DSGE_ESTIMATION_REPORT.md`.

- `klein.py`: the QZ (generalised Schur) solver for linear rational-expectations models, checked against closed forms.
- `soe_*.py`: the models, from a Gali-Monacelli small open economy (`soe_nk.py`) to versions with rule-of-thumb price setters, hand-to-mouth households, oil as an imported good and input, flexible energy-intensive prices, and capital with investment adjustment costs.
- `estimate*.py`, `smc.py`, `chain_logpost.py`, `rhat.py`: Bayesian estimation (random-walk Metropolis chains and a sequential Monte Carlo sampler) on Philippine data (`ph_data.py` reads PSA, BIS, World Bank and OECD series from `data/raw/`).
- `qpm.py`, `link_cge.py`, `oil_policy.py`: a quarterly projection model calibrated to published central-bank parameters, and the links to the CGE.
- `test_milestone*.py`, `test_smc.py`: the tests that check X3 of the validation suite runs.

Long estimation runs write their chains to `outputs/` (not part of the repository); the tests run without them.
