# 10 The dynamic-stochastic and forward-looking CGE: a guide

Written 18 Oct 2026, about 2:30 AM, to close a documentation gap. **Not for citation:** Stage 2 is research code. This chapter says what each piece answers, how it is built and tested, what it has shown, and its limits.

Planned 9 Oct 2026. The plan and Stage 2's design are design notes (not included).

## 1. Three stages

| Stage | What it answers | Where | State |
|---|---|---|---|
| 1. Stochastic recursive-dynamic CGE | How uncertain is the outlook? Ranges and probabilities for GDP, consumption and poverty when oil, remittances, FDI and geopolitical risk are uncertain | `infinity_gem/stochastic.py`, `scenarios/stochastic_outlook.py` | Released since 0.3.4; check X1 |
| 2. Forward-looking (perfect-foresight) CGE | What changes when households and firms look ahead? Announced vs surprise policies; saving and investment that plan for the future; foreign borrowing that must be repaid | `research/intertemporal/` (`pf_cge9.py` and its tests) | Research code; check X2; not in the Simulator |
| 3. New Keynesian DSGE | Monetary policy, sticky prices, expectations of inflation; estimated on Philippine data | `research/dsge/` | **Built and estimated 19 Oct 2026 (milestones 1-14): see guide 11, `11_DSGE_GUIDE.md`**; research code; check X3 |

## 2. Stage 1 in plain words

**The recursive-dynamic CGE** (`dynamic.py`) answers: what if this path of world events happens? Stage 1 asks how likely the different paths are:
1. **Estimate** a Bayesian VAR on monthly data for oil prices, geopolitical risk, remittances (relative to their trend) and FDI (Minnesota prior; Bańbura, Giannone and Reichlin 2010).
2. **Draw** many possible futures from it. Each draw has its own coefficients and its own future surprises.
3. **Turn each draw into yearly CGE shocks** (oil and remittances in % of the expected path, FDI in pesos) and run the dynamic CGE.
4. **Report the spread:** the 5th to 95th percentiles of GDP, consumption and the poor.

It does not forecast the level of growth (the baseline stays the documented one), and it has no expectations: that is Stage 2. **Checks (X1):** with no uncertainty it gives the baseline exactly; a fixed path gives the deterministic scenario; it is reproducible with a seed.

## 3. Stage 2 in plain words

### Why

In the recursive model, people react only when something happens. In reality, a public-works programme announced for 2027 changes plans in 2026: firms invest earlier and households save or spend differently. Foreign borrowing must also be repaid, so it cannot be treated as a gift. Stage 2 lets the economy look ahead.

### The model (`research/intertemporal/pf_cge9.py`)

- **Within each year** it is Infinity GEM's static CGE (Lofgren, Harris and Robinson 2002) on the condensed 2023 SAM, with nine sectors and the ten household groups.
  - Activities produce with labour (three skill levels), land, capital and, in the data calibration, a fixed factor.
  - Commodities mix domestic and imported goods (Armington) and split output between home and export (CET).
  - **Proved:** for the same shock and closure, this block gives the same answer as `cge.py` to within 2e-9 percentage points (`check_static_vs_cge.py`, with a test that a deliberate break is caught).
- **Across years** it adds three forward-looking choices:
  - **Households** choose total consumption over time to make lifetime welfare as high as possible: the Euler equation (Ramsey). The ten groups share it as in the static model.
  - **Firms** invest when the value of new capital (Tobin's q) exceeds its cost, with adjustment costs that make investment gradual (Hayashi 1982).
  - **The country** borrows or lends abroad at a world rate plus a premium that rises with its debt (Schmitt-Grohé and Uribe 2003). Without the premium, a small open economy's debt would drift forever; the same device closes BSP's own DSGE (WPS 2009-01).
- **Calibration** (`calib="pwt"`), all from the Penn World Table 11.0:
  - balanced growth g = 6.2%;
  - the return on capital r = 17.9%;
  - depreciation 5.0%;
  - capital 1.96 × GDP.
  - Capital income beyond what that capital earns is a fixed factor of each activity: the mixed income of the self-employed (Gollin 2002; Caselli and Feyrer 2007) and, in mining, the resource rent (World Bank).
- **Solving.** Every year to a 200-year horizon is solved at once by Newton's method on the stacked system, Dynare's method (Juillard 1996; `pf_solver.py`). The solver is checked against two textbook answers that share no code with it: the Brock-Mirman closed form (to 7e-16) and the Blanchard-Kahn linear solution (`benchmark_solver.py`).

### Options

| Option | Default | Other values |
|---|---|---|
| `calib` | `"sam"` (no growth; for tests) | `"pwt"`: balanced growth calibrated to data |
| `households` | `"one"` | `"groups"`: the SAM's ten groups |
| `public_capital` | off | Infinity GEM's low or high pair (output elasticity and stock) |
| `labour` | `"full"` (full employment) | `"wage_curve"` (Build 2, 18 Oct): in the years flagged `sr`, peso wages follow a wage curve and workers can be idle, as in Infinity GEM's short run |
| `rot` | 0 | Share of household spending that follows current income (rule-of-thumb households; 18 Oct); needs `households="groups"` |
| `bridge_baseline()` | (not used) | Build 1, 18 Oct: a base path in which the SAM's excess foreign saving is borrowed and repaid (the foreign-saving bridge) |

### What it has shown (not for citation)

**Measure C (₱208.7 bn of public works in 2027)**, output gained 2026-2035 per peso:

| Setting | Low public capital | High public capital |
|---|---|---|
| Full employment, announced in 2026 | ₱0.46 | ₱1.44 |
| Keynesian short run with idle workers in 2026-27, announced | ₱0.65 | ₱1.82 |
| Same, as a surprise in 2027 | ₱0.59 | ₱1.74 |

- **The ₱0.8 per peso of the 2026 scenarios** (Infinity GEM's recursive model, range ₱0.4-1.4) sits inside this range.
- **Caution (Build 2b):** these returns come mostly from the supply side, public capital's productivity in later years. The model's short-run demand effect is still too weak (section 3, Limits), so it is not yet a test of the 2026 scenarios' Keynesian years.
- **Announcing the programme a year early** adds about ₱0.06-0.08 per peso: firms invest earlier.
- Sources: `outputs/dscge_build2_keynesian_short_run_20261018_0153.md`, `outputs/dscge_step4c_announced_infrastructure_20261017_2240.md`.

**The foreign-saving bridge** (`outputs/dscge_build1_item74_bridge_20261018_0211.md`):
- Of the SAM's ₱1,458 bn of foreign saving, ₱778 bn is a statistical difference between the national accounts and the balance of payments, and ₱164 bn is sustainable borrowing.
- The remaining ₱516 bn is borrowed in 2023 and repaid.
- The base path's balance-of-payments deficit is 2.6% of GDP in 2023 (IMF: 2.8%). Foreign debt then rises to 11% of GDP before it is slowly repaid.

**Figures** (`outputs/figures_item37_20261018_0241/`; made by `research/intertemporal/figures_item37.py`):
- `fig1_measure_C_announced_vs_surprise.png`: measure C's real GDP effect, 2026-2035, announced vs surprise, low and high public capital.
- `fig2_item74_bridge_base_path.png`: the bridge base path. The current-account deficit is shown against the IMF's path, and foreign assets over 50 years.

### Limits

1. **The Keynesian short run is too weak so far.** The model's first-year public-works multiplier is 0.05-0.39 across wage rigidity, rule-of-thumb spending (option `rot`, added 18 Oct) and investment adjustment costs. PSA's data say about 1.1, and Infinity GEM's recursive short run 0.94 (`outputs/dscge_build2b_rule_of_thumb_multiplier_grid_20261018_0231.md`).
   - The binding difference: private investment rises when public works are cut, whereas in the data private and public construction move together.
   - The next step is a channel for that (short-run public-capital productivity, an accelerator term, or credit limits), then calibration to the data's multiplier.
   - Rule-of-thumb consumers (Galí, López-Salido and Vallés 2007) help only a little: the Euler households, who expect the lower taxes, raise their consumption more.
   - **Build 2c (18 Oct, about noon) tested two investment channels; neither reverses the private-investment response** (`outputs/dscge_build2c_cash_flow_investment_20261018_1135.md`, `…_output_accelerator_*.md`):
     - **Cash-flow investors** (option `rit`): a share of investment follows the real return on capital. Multiplier 0.053 → 0.063 at a 95% share; private investment still +1.3%.
     - **An output accelerator** (`rit_basis="output"`): multiplier 0.078-0.086 at 5-25%; private investment still +1.4-1.7%. A first attempt at 25% did not converge, a rerun did, so the solver is fragile there.
     - **The binding channel:** a public-works cut frees construction capacity, so construction (the investment good) gets cheaper. The real return on capital then rises, and both kinds of investor invest more.
     - **What is left to test:** construction prices that do not fall (sticky prices in the forward-looking model); a short-run complementarity between public and private capital. Also whether the data's 1.1 is causal: budget and election cycles move public and private construction together.
     - Both options default to off; check X2 passes unchanged.
2. **One Euler equation** for the whole economy; the ten groups share one saving decision.
3. **The interest rate puzzle.** The model has one return on capital, 17.9%, well above what the Philippines pays on its external debt (about 9.5%). Existing investment income is kept at the SAM's actual flows; only new borrowing pays the model rate. This is the allocation puzzle (Gourinchas and Jeanne 2013).
4. **Nine sectors**, against Infinity GEM's 43 activities: enough for macro questions, not for sector detail.
5. **Research code:** not in the Simulator, not merged into the engine, not for citation.

## 4. Stage 3 (not started)

- A multi-sector New Keynesian DSGE: Calvo price setting, a Taylor rule for BSP's policy rate, and Bayesian estimation on Philippine data.
- It would answer monetary-policy and inflation-expectation questions the CGE cannot.
- About 3-6 months of work. 
## 5. How to run it (for someone with Python)

From the `Infinity GEM 0.3` folder:
- `py research/intertemporal/pf_cge9.py`: the step 3b tests (7 tests).
- `py research/intertemporal/check_static_vs_cge.py`: the within-year block against `cge.py`, including the Keynesian year.
- `py research/intertemporal/benchmark_solver.py`: the solver benchmarks.
- `py research/intertemporal/step4_announced_infrastructure.py`: measure C, announced vs surprise, at full employment.
- `py research/intertemporal/build2_keynesian_short_run.py`: the Keynesian short run and measure C with idle workers (about 10 minutes).
- `py research/intertemporal/build1_item74_bridge.py`: the base path with the foreign-saving bridge.
- `py checks/run_all_checks.py`: the whole suite (X1 and X2 cover Stages 1 and 2).

## 6. Key references (PDFs in `Infinity GEM/a reference copy (not distributed))

- Juillard (1996), CEPREMAP 9602: the stacked Newton method (`dynamic_cge_dsge/`).
- Schmitt-Grohé and Uribe (2003), *JIE*: closing small open economy models (NBER w9270, `dynamic_cge_dsge/`).
- Caselli and Feyrer (2007), *QJE*: the marginal product of capital (NBER w11551, `dynamic_cge_dsge/`).
- Gourinchas and Jeanne (2013), *REStud*: the allocation puzzle (NBER w13602, `dynamic_cge_dsge/`).
- Galí, López-Salido and Vallés (2007), *JEEA*: rule-of-thumb consumers (NBER w11578, `dynamic_cge_dsge/`).
- **Cited, not saved (journals):** Hayashi (1982), *Econometrica* (Tobin's q); Brock and Mirman (1972), *JET*; Blanchard and Kahn (1980), *Econometrica*; Lau, Pahlke and Rutherford (2002), *JEDC*; Gollin (2002), *JPE*.
- Lofgren, Harris and Robinson (2002), IFPRI: the static model (`cge_models/`).
