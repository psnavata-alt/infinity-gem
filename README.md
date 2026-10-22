# Infinity GEM

**Open-source general equilibrium models of the Philippine economy:** SAM and input-output multipliers; a computable general equilibrium (CGE) model in the tradition of IFPRI's standard model, validated against IFPRI's own GAMS code; a recursive-dynamic CGE to 2030; a poverty microsimulation; time-series tools (VARs, structural VARs, local projections); and research code for a small open-economy DSGE model and a forward-looking CGE. An automated validation suite of 75 checks holds them together.

Author and maintainer: Paolo Navata, independent researcher (ORCID [0009-0001-9476-1868](https://orcid.org/0009-0001-9476-1868)). Infinity GEM grows out of [pystdcge](https://github.com/psnavata-alt/pystdcge), the separately published Python port of the core of IFPRI's standard CGE model (release 0.3.3, 10 October 2026), and extends it: dynamics, the opt-in upgrades, the microsimulation link, the time-series and research models, and the validation suite.

> **Status: research code, version 0.3.13.dev1 (23 October 2026), published for outside review.** Model results are research results for discussion: they are not forecasts, not official statistics, and not the position of any institution. The models are under active development and every upgrade since version 0.2 is opt-in. Data that may not be redistributed are not included, so some checks report NOT RUN until you add those files yourself: see [`docs/STATUS.md`](docs/STATUS.md) for what is included, what is not and why. Comments and corrections are welcome (issues and pull requests).

Licences: code MIT (`LICENSE`); documentation CC BY 4.0; IFPRI's GAMS model files GNU GPL v2 (`LICENSES/GPL-2.0-only.txt`); data files their own licences and credits (`NOTICE.md`, `data/DATA_INVENTORY.md`).

## What is in it

| Part | What it does |
|---|---|
| `infinity_gem/sam.py`, `multiplier.py` | Load, check, balance and aggregate IFPRI-style social accounting matrices; SAM and fixed-price multipliers |
| `infinity_gem/cge.py` | The static CGE: CES value added, Leontief intermediates, Armington imports, CET exports, trade margins, taxes, ten household groups; long-run, savings-driven, short-run Keynesian and interest-rate closures; opt-in sticky prices, labour hoarding, a value added-energy bundle and within-year capital vintages |
| `infinity_gem/dynamic.py` | The recursive-dynamic CGE: capital accumulation, capital by industry, labour growth by skill, industry baselines from PSA national accounts, a short-run/long-run hybrid closure, a wage curve, an opt-in short-run consumption rule, public capital, and a central-bank rule solved inside the model |
| `infinity_gem/demand.py`, `elasticities.py`, `stickiness.py` | LES household demand from published elasticities; sourced elasticity sets; price stickiness by sector from published price-change durations |
| `infinity_gem/oil.py`, `iomodel.py` | World oil-price shocks on a SAM with refined petroleum split from chemicals; Leontief quantity, price and job-equivalent models on PSA's input-output tables |
| `infinity_gem/microsim.py`, `household.py`, `microlink.py`, `psa_cpi.py` | Poverty and distribution from the FIES 2023 microdata (which you download from PSA); the macro-micro link file; consumer prices on PSA's CPI weights |
| `infinity_gem/var.py`, `svar.py`, `macrolink.py`, `stochastic.py`, `decompose.py` | Newey-West regressions, VARs, structural VARs (block exogeneity, sign restrictions, bootstrap, historical decompositions, a Minnesota BVAR), local projections; the VAR-to-CGE link; a stochastic dynamic CGE; Shapley decompositions |
| `infinity_gem/settings.py` | Named settings: `"0.2 published"` (the original model) and `"0.3 recommended"` (every sourced upgrade that combines with the others) |
| `checks/` | The validation suite (75 checks) and the frozen reference results of version 0.2 |
| `validation/` | Comparisons with IFPRI's own GAMS model (condensed and full SAM, with and without home consumption), with pycge (a human-written port of Hosoe et al.'s model) and with a Julia/MPSGE version; labour-closure and backtest studies |
| `scenarios/`, `preshock/` | Scenario scripts, including the 2026 shock scenarios (world oil and fertilizer prices, the fall in public construction, El Nino, and their combination with a costed response), and the "pre-shock" models that size each shock from data |
| `research/` | A small open-economy DSGE model with Bayesian estimation; a forward-looking CGE |
| `app/` | The Simulator, a point-and-click front end (Streamlit) |
| `tools/` | The SAM builders (petroleum and rice splits, a PSA-consistent SAM, an own 2023 SAM from PSA sources, SAM updating by cross-entropy) and other tools |
| `docs/` | Guides, the equation-by-equation concordance with the published model and IFPRI's GAMS code, a "verify it yourself" guide, the audit for rigging, and a Stata route |

## Install

Python 3.12 or later.

```
git clone https://github.com/psnavata-alt/infinity-gem.git
cd infinity-gem
python -m pip install -r requirements.txt
```

## Run the checks

```
python checks/run_all_checks.py
```

Each check prints PASS, FAIL or NOT RUN, and the report is saved in `outputs/`. A check that needs a file that is not distributed (the FIES microdata, two compiled macro panels, two earlier reference tables) reports NOT RUN with the file it needs and where to get it; NOT RUN is never counted as a pass. The whole suite takes about half an hour on one processor core. `docs/STATUS.md` lists the checks that need undistributed files and the result on a clean clone.

The most important checks for a reviewer:

| Check | What it shows |
|---|---|
| C1-C8 | Every equation holds at the SAM; the model reproduces the SAM; homogeneity; Walras' law; the GDP identity; signs and bounds; the same on the 2018 SAM |
| **V2, V3, V4** | **Reproduces IFPRI's own GAMS model** on a condensed Philippine SAM (results saved from GAMS in `validation/ifpri*/gams_ph/`): real GDP and consumption within 0.01 pp, and within 0.001 pp with IFPRI-style trade margins; the remaining gaps are explained in `validation/ifpri/README.md` |
| **V5** | **Reproduces pycge**, a human-written Python port of Hosoe, Gasawa and Hashimoto's standard CGE model, to 1e-9 |
| V7, LP1 | The VAR code equals statsmodels; local projections recover a known impulse response |
| X2, X3 | The forward-looking CGE and the DSGE code against closed-form solutions |
| D1, D2, D3 | Data checksums; SAM balance; an edited SAM is refused, not balanced away |
| R0 | With default settings, the results equal those frozen from version 0.2 (`checks/reference_live.json`) |

`docs/verification/04_RIGGING_AUDIT_9Oct2026.md` describes an audit that looks for typed-in results, plugs, hidden failures and tests that pass without testing; `docs/verification/rigging_audit/rigging_audit.py` reruns it.

## Run a scenario

```python
from infinity_gem.settings import cge_model, short_run_closure

m = cge_model("0.3 recommended", **short_run_closure())        # IFPRI 2023 SAM with the 0.3 upgrades, short run
base = m.solve()
sim = m.solve({"pwm_scale": {"cpetr": 1.2}})                     # world price of refined petroleum +20%
print((m.gdp(sim)["real"] / m.gdp(base)["real"] - 1) * 100)      # real GDP, % change: about -0.33
```

The scripts in `scenarios/` write their reports to `outputs/`, for example `python scenarios/oil_price_shock.py`. The 2026 scenarios (`scenarios/combined_revised.py` and the scripts it calls in `preshock/`) count the poor with the FIES microdata, so they run once you have added the FIES files (`data/raw/fies/README.md`).

## The Simulator

```
python -m pip install streamlit
python -m streamlit run app/simulator.py
```

Its poverty results need the FIES files (`data/raw/fies/README.md`).

## Data

`data/DATA_INVENTORY.md` lists every data file with its source, licence and checksum: IFPRI's 2023 and 2018 Philippine SAMs (CC BY 4.0) and the SAMs built from them, PSA's 2018 input-output and supply-use tables and OpenSTAT series (PSA's terms: cite PSA as the source), published elasticities, the World Bank Pink Sheet and World Development Indicators, BIS, the OECD's quarterly national accounts, Penn World Table, EIA and climate series. **Not included**, because their terms do not allow redistribution or because they are not public: PSA's FIES and FIES-LFS microdata, GTAP data, the IMF's capital stock dataset, FRED series, the World Uncertainty Index and two compiled macro panels. The README files in `data/raw/*/` explain how to obtain each one.

*This data was provided by the International Food Policy Research Institute (IFPRI). IFPRI bears no responsibility for the analyses or interpretations of the data presented here.*

## Use of AI

The code, checks and documentation were written with AI coding assistants under the author's direction. The author specified the models and the checks, reviewed the results and is responsible for the content. Because AI-written code needs checks that do not rely on the AI, the models are validated against implementations written by people (IFPRI's GAMS code, pycge, statsmodels), against the published equations, and against official statistics.

## Citation

See `CITATION.cff`. Cite the version and the settings you used; results change between versions. Please also cite Lofgren, Harris and Robinson (2002) for the model and IFPRI for the SAMs.

## Contributing

Issues and pull requests are welcome (`CONTRIBUTING.md`). Every change must keep the checks passing, and new features must be opt-in, so check R0 is unchanged. This project follows the [Contributor Covenant code of conduct](CODE_OF_CONDUCT.md).

## References

- Lofgren, H., Harris, R. L. and Robinson, S. (2002). *A Standard Computable General Equilibrium (CGE) Model in GAMS*. Microcomputers in Policy Research 5. International Food Policy Research Institute.
- IFPRI (2025). *2023 Social Accounting Matrix for Philippines*. Harvard Dataverse, doi:10.7910/DVN/WQXUQW.
- International Food Policy Research Institute (2025). *2023 Social Accounting Matrix for Philippines: A Nexus Project SAM*. Data Paper. Washington, DC: IFPRI. https://hdl.handle.net/10568/176224.
- IFPRI (2021). *2018 Social Accounting Matrix for the Philippines*. Harvard Dataverse, doi:10.7910/DVN/XSEXEP.
- Hosoe, N., Gasawa, K. and Hashimoto, H. (2010). *Textbook of Computable General Equilibrium Modelling: Programming and Simulations*. Palgrave Macmillan.
- Thurlow, J. (2004). A dynamic computable general equilibrium (CGE) model for South Africa. TIPS Working Paper 1-2004.
