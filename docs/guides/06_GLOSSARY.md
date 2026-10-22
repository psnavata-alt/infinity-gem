# 6. Glossary

**Armington elasticity (σq).** How easily buyers switch between imported and domestic versions of a good when relative prices change. Higher = more switching.

**Benchmark.** The base-year equilibrium the model reproduces exactly (the 2023 SAM).

**Calibration.** Choosing model parameters so the model reproduces the benchmark data.

**CES / CET.** Constant Elasticity of Substitution (combining inputs or goods) and Constant Elasticity of Transformation (splitting output between markets).

**Cholesky ordering.** In an SVAR, the assumed order in which variables can respond to each other within the same period.

**Closure.** The choice of which variables are fixed and which adjust so the model has a unique solution (e.g. full employment vs. unemployment; fixed investment vs. fixed saving rates). Results can change sign across closures.

**Composite good.** The mix of imported and domestic supply that domestic buyers use.

**Counterfactual.** What would have happened under different conditions; in Infinity GEM, always a model run with a documented shock.

**Elasticity.** The percentage change in one variable for a 1% change in another.

**Exogenous / endogenous.** Set outside the model (a shock or policy) / determined by the model.

**FIES.** PSA's Family Income and Expenditure Survey; Infinity GEM uses FIES 2023.

**Homogeneity.** Doubling every price and nominal value leaves every real quantity unchanged. A test of correct model code.

**Keynesian closure.** Output is set by demand because some labour is unemployed at a fixed wage; used for short-run questions.

**Leontief.** Fixed proportions (no substitution).

**Local projection.** Estimating the response of a variable h periods ahead by a separate regression for each h.

**Microsimulation.** Applying model results to individual survey households.

**Multiplier (SAM).** Total change in incomes per peso of injected spending, at fixed prices.

**Numeraire.** The price fixed to 1 so that all other prices are measured relative to it (the CPI, or the exchange rate in the Keynesian closure).

**Re-exports.** Imported goods exported again with no domestic value added (here, part of machinery and electronics).

**Recursive-dynamic.** A sequence of static equilibria linked by capital accumulation and growth; agents do not look ahead.

**SAM.** Social Accounting Matrix: one year's flows among all parts of the economy, row totals = column totals.

**SVAR.** Structural VAR: a VAR with assumptions that identify economic shocks.

**TFP.** Total factor productivity: output per unit of all inputs combined.

**VAR.** Vector autoregression: each variable regressed on past values of all variables.

**Walras' law.** If all markets but one clear and all budgets balance, the last market clears too. In Infinity GEM the savings-investment slack must be zero: the test that the accounts close.

## Terms added in version 0.3

**Capital by industry ("putty-clay").** Capital can be put anywhere when new ("putty") but stays in its industry once installed ("clay"); only new investment moves towards higher returns.

**Investment mobility (omega).** How strongly new investment chases industries with above-average returns. 0 = new capital follows existing shares; IFPRI uses 3; above about 5 the rule overshoots.

**Hybrid closure.** Short run (unemployment possible) in years with a shock, then the job gap closes gradually under the long-run closure.

**Documented baseline.** The dynamic model's no-shock path built from sourced numbers: DBCC growth targets, Philippine depreciation and capital stock (Penn World Table).

**Public capital channel.** Lost (or restored) public infrastructure changes productivity in every industry, with an output elasticity of 0.083-0.122 (Bom and Ligthart 2014).

**GTAP, ESUBD, ESUBVA.** GTAP is the Global Trade Analysis Project's world database and model; ESUBD is its Armington (import vs domestic) elasticity and ESUBVA its value-added substitution elasticity, the international standard values.

**Regression check (R0).** A check that the upgraded model still gives exactly the published results when its new features are switched off.

**Benchmarking vs validation.** Reproducing someone's earlier number shows the code computes what their method computes; agreement with an independent model built by others on the same data (e.g. IFPRI's own CGE, check V2) is stronger evidence.

**Penn World Table (PWT).** The University of Groningen's international database of output, capital and productivity; its Philippine capital accounts are built on PSA's national accounts.

**DBCC.** The Development Budget Coordination Committee, which sets the government's official macroeconomic assumptions (growth, inflation, exchange rate, oil prices).
