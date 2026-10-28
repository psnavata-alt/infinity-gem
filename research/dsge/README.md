# Research code: a small open-economy DSGE model for the Philippines

Research code, not used by any default result of the CGE models. The guide is `docs/guides/11_DSGE_GUIDE.md` and the estimation report `docs/guides/11b_DSGE_ESTIMATION_REPORT.md`.

- `klein.py`: the QZ (generalised Schur) solver for linear rational-expectations models, checked against closed forms.
- `soe_*.py`: the models, from a Gali-Monacelli small open economy (`soe_nk.py`) to versions with rule-of-thumb price setters, hand-to-mouth households, oil as an imported good and input, flexible energy-intensive prices, capital with investment adjustment costs, (milestone 25) the capital model with a flexible-price energy share of the CPI (`soe_htmkf.py`) and with sticky wages (`soe_htmkw.py`), and (milestone 26) the sticky-wage capital model with the oil block (`soe_htmkwo.py`: oil as an imported good and input, oil supply apart from world oil demand), on which the central bank's response to an oil supply shock is computed with the Calvo parameter estimated (`oil_policy_htmkwo.py`; `scenarios/bsp_oil_response_netting_htmkwo.py` feeds it to the CGE link).
- `estimate*.py`, `smc.py`, `chain_logpost.py`, `rhat.py`: Bayesian estimation (random-walk Metropolis chains and a sequential Monte Carlo sampler) on Philippine data (`ph_data.py` reads PSA, BIS, World Bank and OECD series from `data/raw/`).
- `qpm.py`, `link_cge.py`, `oil_policy.py`: a quarterly projection model calibrated to published central-bank parameters, and the links to the CGE.
- `test_milestone*.py`, `test_smc.py`: the tests that check X3 of the validation suite runs (`test_milestone25b.py`, for the sticky-wage model, and `test_milestone26.py`, for the sticky-wage model with oil, are run by hand: `python test_milestone25b.py` and `python test_milestone26.py` in this folder).

Long estimation runs write their chains to `outputs/` (not part of the repository); the tests run without them.

**The link's investment response (23 October 2026).** The money block (`DynamicCGE.monetary_scenario`) and the link scripts move real investment by theta percent per point of the real-interest-rate gap. The default is 1.5, with 0.7 and 2 as the low and high cases: the capital model with sticky wages (`soe_htmkw.py`, milestone 25), the best-fitting version, puts the year-1 response at 1.43 (90% band 0.72-2.23). The value used before, 2, came from matching the CGE to the quarterly projection model (1.9) and to an earlier DSGE (3.3).
