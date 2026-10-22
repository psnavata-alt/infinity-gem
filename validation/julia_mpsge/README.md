# Comparison with the Julia/MPSGE IFPRI model, at full size (9 October 2026)

A third, human-written implementation (no GAMS licence or size limit), run with an AI coding assistant.

## Result in brief

- **The human-written Julia model replicates the Philippine SAM exactly at 40 sectors** (zero iterations, residual 1.6e-10). This is the first comparison at (nearly) full size; the GAMS comparison (V2-V4) was limited to 9 sectors by the free GAMS licence.
- **It is a different formulation of the IFPRI model**, so it does not agree with Infinity GEM to machine precision as IFPRI's GAMS code does. Every difference found so far is traced, by test, to a named modelling choice:
  1. **Export supply.** As written, both Rutherford's GAMS file (`$prod:X(g)  eta(g)`, elasticity unlabelled) and the Julia port (`[t=0, s=eta[g]]`) put the export-transformation elasticity in the input-substitution slot, so exports and domestic sales move in **fixed proportions**. The IFPRI standard model (and Infinity GEM) uses a CET with elasticity 2. Tests: (a) as Infinity GEM's CET elasticity falls toward zero, the largest gaps close (land rents: 28.6 pp gap at 2.0, 0.53 pp at 0.05); (b) in a marked test copy of the Julia model with the elasticity moved to the transformation slot (one line, `julia/test_copy_change.diff`), the real exchange rate agrees within **0.009 pp** and factor prices within **0.63 pp**.
  2. **Saving and direct taxes.** Rutherford's closure (flexible exchange rate, fixed real government consumption, `eqyield=0`, `fixedGS=1`) holds each household's and the enterprises' saving and direct tax fixed in REAL terms; Infinity GEM's savings-driven closure holds the RATES fixed. The household gaps grow with income (0.3 pp poorest urban, 2.3 pp richest urban), as this predicts. Test: holding Infinity GEM's total real household saving and direct taxes at the benchmark (common rate adjusters) roughly **halves every remaining gap** (investment 4.8 → 2.6 pp; household consumption 2.3 → 1.1 pp; factor prices 0.63 → 0.34 pp; real exchange rate 0.005 pp).
  3. **Not yet tested** (the remainder): the match in 2 is in aggregate, not household by household; enterprise saving and taxes remain rate-based in Infinity GEM; Rutherford values all net transfers in foreign exchange (Infinity GEM: government transfers in CPI terms).
- **Tobacco** is extreme in both models (+6,815% and +6,611% output when tariffs go): a ₱7 bn industry behind a 53% tariff. Not a model error, but a warning about percentage changes in very small sectors.

## Experiment

All tariffs abolished (Rutherford's own experiment), savings-driven closure, flexible exchange rate, fixed real government consumption. Same SAM in both models: the IFPRI 2023 SAM with two exact aggregations that Rutherford's formulation requires (one margin commodity: trade + transport; one activity per commodity: other cereals into rice), home consumption at market, re-exports netted (`build_mpsge_inputs.py`). Elasticities: value added 0.8, Armington 2, CET 2.

| Comparison | Original Julia model | Test copy (CET slot) | Test copy + matched saving/tax closure |
|---|---|---|---|
| Real exchange rate, gap | 0.50 pp | 0.009 pp | 0.005 pp |
| Factor prices, largest gap | 28.6 pp (land) | 0.63 pp | 0.34 pp |
| Real investment, gap | 5.0 pp | 4.8 pp | 2.6 pp |
| Household utility, largest gap | 2.9 pp | 2.3 pp | 1.1 pp |
| Outputs, median gap | 1.7 pp | 0.9 pp | (see CSV) |

Files: `out/comparison_no_tariffs_savings_omega2.csv` (test copy vs Infinity GEM), `out/comparison_no_tariffs_savings_omega2_matched.csv`, Julia results `out/mpsge_results_original.csv` and `out/mpsge_results_cet_slot_test_copy.csv`.

## Data mapping notes (Rutherford's data step on the Philippine SAM)

- **Negative foreign factor ownership.** The Philippines receives more factor income from abroad than it pays (net ₱293 bn, mainly labour). Rutherford's formulation treats the rest of the world as an owner of factor services, which cannot be negative in MPSGE (its income was set to zero and the benchmark failed by exactly ₱293 bn). Mapping used: the rest of the world owns the factor services it is paid for; income from abroad reaches domestic owners as a foreign-currency transfer (as Infinity GEM values it).
- **Government factor income** (the capital tax) is passed in `fe0_govt.csv` and filled after loading, because the Julia loader adds an empty government row itself; the Julia package is otherwise unchanged.

## Software and licences

- Julia 1.13.1 (MIT), installed with the official `juliaup` (winget `Julialang.Juliaup`); MPSGE.jl 0.7.2 (MIT), JuMP 1.32.1 (MPL-2.0), PATHSolver.jl 1.7.9 (MIT); exact versions in `julia/Manifest.toml`.
- The Julia IFPRI model: M. Phillipson (WiNDC), GitHub `uw-windc/IFPRI_model` (no licence file: not redistributed). Rutherford's GAMS file is in the same repository.
- **PATH solver licence:** the solver author's published evaluation licence for Julia users (pages.cs.wisc.edu/~ferris/path/julia/LICENSE, valid to 31 Dec 2035, no purpose restriction stated), read at run time by `julia/run_phl.jl` and not stored. Without it PATH is limited to 300 variables.

## Rerun

1. Install Julia; copy `external/IFPRI_model-main/` to a folder outside a cloud-synced folder; put `julia/setup_env.jl` and `julia/run_phl.jl` in it; `julia setup_env.jl`.
2. `py validation/julia_mpsge/build_mpsge_inputs.py <julia folder>/data/phl40`
3. `julia run_phl.jl data/phl40 out_phl40` (the CET test ran on a changed copy of the Julia model, described above; the copy is not included).
4. `py validation/julia_mpsge/compare_mpsge.py <julia folder>/out_phl40/mpsge_results.csv savings 2.0 [matched]`

## Next

- Test the remainder (point 3): household-by-household saving and tax, enterprise closure, transfer valuation.
- Ask the authors (Phillipson; the WiNDC group) whether the export-transformation slot is intended; if not, it is a finding for them.
- More shocks: sales taxes (`ta`), value-added taxes (`tva`); world prices and quantities need small, marked additions to the Julia code.
