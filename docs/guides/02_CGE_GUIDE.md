# 2. The Infinity GEM computable general equilibrium (CGE) model

## 2.1 The idea in one paragraph

A CGE model is the SAM brought to life. The SAM shows one year's flows; the model adds **behaviour**: industries choose inputs to minimise cost, households spend their income, buyers choose between imported and local goods, producers choose between exporting and selling at home. When something changes (a price abroad, a tax, spending), every price and quantity adjusts until all markets clear again and every peso paid is a peso received. Unlike the multiplier, the CGE lets prices move and respects limits on labour and capital, so it captures **crowding out, substitution and trade responses**.

## 2.2 Structure

The model follows the IFPRI Standard CGE model (Lofgren, Harris and Robinson, 2002), simplified to fit the Philippine SAM. Code: `infinity_gem/cge.py`.

| Block | Assumption | Parameter |
|---|---|---|
| Production | Each activity uses value added and intermediate inputs in fixed proportions; intermediate inputs in fixed proportions (Leontief) | `ica`, `iva` |
| Value added | CES combination of low-, medium- and high-skill labour, land and capital | elasticity `sigma_va` (default 0.8) |
| Outputs | Activities produce commodities in fixed shares (the SAM's make matrix) | `theta` |
| Exports | Output is split between exports and domestic sales (CET); world prices given | elasticity `omega_t` (default 2.0) |
| Imports | Buyers use a composite of imported and domestic goods (Armington CES) | elasticity `sigma_q` (default 2.0) |
| Re-exports | Where exports exceed domestic output (electronics, `cmach`: ₱345 bn), the excess passes through: imported and exported at world prices | `rex` |
| Margins | Each unit of composite supply needs trade and transport services | `icq`, `sm` |
| Taxes | Tariffs, sales taxes, capital tax, direct taxes on households and enterprises, all at fixed rates | `tm`, `tq`, `tf`, `tins`, `te` |
| Households (10) | Income from factors, enterprises, government and remittances; fixed tax and saving rates; spending in fixed budget shares (Cobb-Douglas) | `mps`, `beta` |
| Government | Fixed real consumption and transfers; savings adjust | `qg`, `trg_h` |
| Rest of world | Foreign savings fixed in foreign currency (except in the Keynesian closure) | `fsav` |

Home consumption (₱364 bn in the SAM) is treated as marketed consumption.

## 2.3 Key equations (in words and symbols)

For activity *a*, commodity *c*, factor *f*, household *h*:

1. **Zero profit:** price of output = cost of intermediates + cost of value added:
   PA_a = Σ_c ica_ca · PQ_c + iva_a · PVA_a
2. **Value-added unit cost (CES):** PVA_a = (1/TFP_a) · [Σ_f δ_fa · W_fa^(1−σ)]^(1/(1−σ))
3. **Factor demand:** QF_fa = (QVA_a / TFP_a) · δ_fa · (TFP_a · PVA_a / W_fa)^σ
4. **Output split (CET):** QE_c/QD_c = [(PE_c/PDS_c) · (1−γ_c)/γ_c]^ω
5. **Import demand (Armington):** QM_c/QD_c = [δq_c/(1−δq_c)] · (PDS_c/PM_c)^σq
6. **Composite price:** PQ_c = (1 + tq_c) · (PARM_c + icq_c · PTRC), where PARM is the Armington unit cost
7. **World prices:** PM_c = pwm_c · EXR · (1 + tm_c);  PE_c = pwe_c · EXR
8. **Household spending:** QH_ch = β_ch · EH_h / PQ_c, with EH_h = (1 − mps_h) × disposable income
9. **Market clearing:** domestic supply = domestic demand (each commodity); factor demand = supply (each factor, unless unemployed); foreign-exchange inflows = outflows
10. **Savings = investment**, with a slack variable (WALRAS) that must equal zero: the check that the accounts close.

## 2.4 Calibration

All parameters come from the SAM, with benchmark prices set to 1 (except composite prices, which carry taxes and margins). Shares and tax rates are read directly (e.g. `tm = tariff revenue / imports`); CES and CET shift and share parameters are solved so that, at benchmark prices, the model reproduces every SAM flow. Check C2 rebuilds the SAM from the benchmark solution: the largest cell gap is 10⁻⁷ (₱ bn).

The only numbers not from the SAM are the **elasticities**. The defaults (σ_va = 0.8, σ_q = 2.0, ω = 2.0) are common in the literature but not estimated for the Philippines. Replacing them is Phase 1 of the roadmap in `00_START_HERE.md`. Until then, report how results change when each elasticity is varied (see the exercises in section 2.8 of this guide).

## 2.5 Closures: the choices that drive the answers

A closure says which variables adjust to keep the model consistent. This is the most important modelling choice, and results can change sign across closures. Three are built in:

| Closure | Setting in code | What adjusts | Use it for |
|---|---|---|---|
| **Long run** | `CGE.from_sam()` | Wages and rents (full employment); saving rates keep savings = investment; exchange rate | Structural questions, multi-year horizons, tax reforms |
| **Savings-driven** | `closure="savings"` | Investment adjusts to available savings | Questions about national saving; not for investment shocks |
| **Short run (Keynesian)** | `closure="keynesian", unemployed=("flab-n","flab-p"), capital="fixed"` | Employment of low/medium-skill labour (real wages fixed); capital stuck in each industry; exchange rate fixed (numeraire); foreign savings (the current account) adjust | Spending freezes, stimulus, one-year shocks |

**Example (from `scenarios/infrastructure_freeze.py`, 2025 fall of ₱222.6 bn in SAM units):**

| Model | Real GDP | Why |
|---|---|---|
| SAM multiplier | −₱350 bn (−1.34%) | Fixed prices, unlimited supply: every round of spending is lost |
| CGE short run | −₱73 bn (−0.28%) | Employment falls, but lower prices raise exports and cut imports |
| CGE long run | +₱12 bn (+0.05%) | Full employment: the freed savings are spent on other goods |

None is "the" answer. Present the range and explain it. The short-run CGE is the usual central case for a one-year shock; the dynamic model (2.7) shows what persists.

**The wage rule in the short run** (added 16 Oct 2026). The table shows the default, `wage="real"`: real wages fixed, so peso wages rise with the CPI. The option `wage="nominal"` fixes wages in pesos instead (sticky pay, as Philippine minimum wages are set; check W2; evidence in `validation/labour_closures/` in the development copy). The named setting "0.3 recommended" (`infinity_gem/settings.py`) uses `wage="nominal"` and, since 0.3.6, lets workers of all skill levels lose work in the short run (`unemployed=("flab-n", "flab-p", "flab-s")`). The development copy 0.3.7 adds a wage curve whose slope is set from Okun's law on PSA data (check WC1), so pay also falls a little when jobs are lost. Most Philippine CGE studies assume full employment; PHILGEM's short run indexes wages to the CPI (survey in `validation/labour_closures/README.md`, section 6, development copy).

Two traps learned while building the model:
- An investment-driven closure with full employment makes household saving rates fall when investment falls, which props up consumption. That is why the long-run closure shows almost no loss from an investment cut.
- A Keynesian closure with the nominal wage as the only price anchor let every other price fall 40%: mathematically consistent, economically absurd. The built-in version anchors the exchange rate instead. **Always ask whether results are plausible, not just whether the solver converged.**

## 2.6 Running the model

```python
from infinity_gem.cge import CGE
m = CGE.from_sam(closure="keynesian", unemployed=("flab-n", "flab-p"), capital="fixed")
base = m.solve()
sim = m.solve({"qinv_scale": {"ccons": 0.9}})       # construction investment -10%
print(m.compare(base, sim))                          # GDP, consumption, trade, wages, employment, households
print(m.gdp(sim))                                    # nominal GDP by expenditure and income, real GDP
assert abs(sim["WALRAS"]) < 1e-6                     # the accounts must close
```

Shock keys (see `CGE.make_shocks`): `qinv_scale`, `qg_scale`, `pwm_scale`, `pwe_scale`, `tm_scale`, `tq_scale`, `tfp_scale`, `qfs_scale`, `remit_scale`, `trg_scale`, `trg_h_scale`, `trg_h_add` (₱ bn transfers), `tins_scale`, `fsav_scale`, `kscale`, `wbar`.

Note: the 2023 SAM records only **₱103.7 bn** of government transfers to households, far below the ₱325 bn in cash-transfer programs (most such spending is booked elsewhere in the national accounts). Model Ayuda changes with `trg_h_add` in pesos, not by scaling the SAM cell.

## 2.7 The recursive-dynamic model

`infinity_gem/dynamic.py` solves the static model for each year from 2023 to 2030:
- **Capital:** K(t) = (1 − dep)·K(t−1) + κ·I(t−1). Lower investment today means less capital tomorrow.
- **Labour:** grows at `labour_growth` (default 1.5% a year, all types).
- **Productivity (TFP):** calibrated each year so that baseline GDP follows `DEFAULT_GROWTH` (2024-2025 PSA actual; 2026 onward assumptions near current forecasts).
- **Exogenous demand** (government consumption, investment level, transfers, foreign savings, remittances) grows with baseline GDP.
- **Scenarios** keep the baseline TFP path and add shocks by year: `d.scenario({2025: {...}, 2026: {...}})`.

**Calibrating the dynamic baseline (assumptions to replace):** depreciation 5%; initial net capital growth 5% (sets κ); labour growth 1.5%; growth path in `DEFAULT_GROWTH`. Better values: depreciation and capital stock from PSA's capital stock estimates or a perpetual-inventory calculation from GFCF; labour growth by education from LFS projections; the growth path from DBCC assumptions. Record the source of each in the scenario report.

The dynamic model uses one closure throughout (default: long run), so it misses the short-run demand loss; a hybrid (short run in shock years, long run after) is Roadmap Phase 2.

**What kind of dynamic model this is.** *Recursive-dynamic*: a sequence of static equilibria linked by capital accumulation, with households and firms that do not look ahead. This is the standard for policy CGE work (IFPRI's dynamic standard model, the World Bank's MAMS, PEP-1-t). *Intertemporal* (forward-looking) models, in which agents plan over time, are a different family (e.g. DSGE models such as BSP's); Infinity GEM does not aim to be one.

**Example (infrastructure freeze, `scenarios/infrastructure_freeze.py`, 26 Sept 2026).** Capital ends about 1% below baseline; GDP is 0.64% below baseline in 2027 and still 0.47% below in 2030; the cumulative loss over 2025-2030 is about ₱776 bn in 2023 SAM pesos. In 2025 the path shows +0.05%, because the long-run closure keeps everyone employed: the shock-year loss is in the short-run static results, not here.

**What it does not do yet (27 September 2026)**

1. **Short run in the shock years.** Full employment every year, so the job and demand loss in the year of the cut is missing.
2. **Capital by industry.** One economy-wide capital stock; new investment is not directed to where returns are highest.
3. **Public capital.** Lost roads and bridges are treated like lost private machines; they do not lower other industries' productivity. This matters most for infrastructure questions.
4. **A documented baseline.** The growth path from 2026, depreciation (5%) and labour growth (1.5%) are placeholders; some come from forecasts of September 2026, not DBCC.
5. **In the Simulator.** The dynamic path runs from the scenario script only.

**How we go fully dynamic (order of work)**

1. **Hybrid closure**: short-run (Keynesian) closure in shock years, with unemployment closing over two or three years to the long-run closure, so one run shows both the first-year loss and its persistence.
2. **A "years" page in the Simulator** charting baseline and scenario, 2023-2030.
3. **Public capital**: government investment builds a public capital stock that raises productivity in all industries, with the strength of the link taken as a range from published estimates.
4. **Capital by industry**, with new investment allocated by relative returns (as in IFPRI's dynamic model).
5. **A documented baseline**: PSA actuals, DBCC growth assumptions, PSA population projections for labour, capital stock by industry from PSA or a perpetual inventory of GFCF.
6. **Checks for each new part** (steady state, zero shock, sensitivity to depreciation and to the public-capital elasticity).

### 2.7a New in version 0.3 (options, off by default; merged 8 Oct 2026)

Both options are **off by default**, so results are unchanged unless you switch them on (check R0).

```python
from infinity_gem.dynamic import DynamicCGE
d = DynamicCGE(hybrid=True, gap_persistence=0.5)        # short run in shock years; the job gap halves each year
base = d.baseline()
sim = d.scenario({2025: {"qinv_scale": {"ccons": 0.9}}})
print(d.compare(base, sim)); print(sim.table[["closure", "employment_gap_low_skill_pct"]])

d2 = DynamicCGE(hybrid=True, public_capital={"phi": 0.083, "kg_gdp": ...})   # kg_gdp from the IMF ICSD: required
```

- **Hybrid closure**: years with a shock use the short-run model, anchored to that year's baseline, so a zero shock reproduces the baseline (check Y2). Afterwards the low/medium-skill employment gap shrinks by `gap_persistence` a year (an assumption until the labour-market evidence). A positive shock (a catch-up) opens a positive gap that fades the same way.
- **Public capital**: changes in construction investment build or erode a public capital stock that scales productivity in every industry by (1 + dKG/KG)^φ. φ from Bom and Ligthart (2014): 0.083 short run, 0.122 long run; depreciation 3.52% (IMF ICSD 2021, middle income); 77% of spending becomes usable capital (IMF PIMA, Philippines). The Philippine public capital stock relative to GDP (`kg_gdp`) must come from the IMF ICSD; there is no default (check Y3).
- **2018 SAM:** `CGE.from_sam(paths.SAM_2018)` now works (balanced by `SAM.balance`; activity tax `atax`; check C8). Warning: households buy no chemicals and petroleum in that SAM, so do not use it for oil-price work.
- **Simulator:** page "Over time (dynamic)".
- **Capital by industry**: `DynamicCGE(capital_allocation="putty-clay", omega=3.0)`. Installed capital stays in its industry; new capital is shared out by IFPRI's rule (Thurlow 2004, eq. Q). Use omega 1-5 for sensitivity (10 or more overshoots). Check Y4.
- **Documented baseline**: `DynamicCGE(**documented_baseline())` = DBCC growth path (193rd DBCC, 8 July 2026), depreciation 5.02% and capital stock 1.96 x GDP (Penn World Table 11.0). Labour growth is still the 1.5% placeholder.
- **The full model:** `DynamicCGE(capital_allocation="putty-clay", hybrid=True, public_capital={...}, **documented_baseline())`; worked example `scenarios/infrastructure_full_dynamic.py`.
- **Elasticity sets**: `CGE.from_sam(elasticities=elasticity_set("ph"))`; sets `default`, `gtap`, `ph`, `ph_pcgem_cet` (`infinity_gem/elasticities.py`). Elasticities may now be one number or one per sector. Check E1.
- **Validated against IFPRI's own standard CGE** on a condensed Philippine SAM (`validation/ifpri/README.md`; check V2).
- **Home consumption as own produce** (0.3.1, 8 Oct 2026; not yet released): `CGE.from_sam(home="separate")`.
    - It applies the book's eq. 18 and 34: households' own rice, fish and food (₱363.7 bn in the 2023 SAM; 5.9% of the poorest rural quintile's consumption) are valued at producer prices, with no margins, sales tax or import competition.
    - The CPI then covers market purchases only, as in IFPRI's model.
    - Matches IFPRI's own model run with home consumption kept (check V4; `validation/ifpri_home/README.md`).
    - Effect on the September 2026 results: negligible (`scenarios/home_consumption_sensitivity.py`).
    - Not yet combined with `les=`.
- **Sources of every parameter:** `08_PARAMETERS_AND_SOURCES.md` (gold / silver / placeholder grades). Plain-language overview: `09_WHATS_NEW_IN_0.3.md`.

## 2.8 Exercises (do them; they build judgment)

1. **Closure comparison.** Run `scenarios/oil_price_shock.py`. Why is the CPI unchanged in the long-run closure? (Hint: what is the numeraire?)
2. **Armington elasticity.** Re-run the oil shock with `CGE.from_sam(elasticities={"sigma_q": 0.5})` and `{"sigma_q": 4.0}`. Which results move most, and why?
3. **Value-added elasticity.** Try `sigma_va` of 0.3 and 1.5 in the short-run infrastructure case. What happens to low-skill employment?
4. **Remove the unemployment.** Run the construction shock with `closure="keynesian", unemployed=()`. The model still solves, but real GDP barely moves (+0.01%) while foreign savings fall by about ₱390 bn. Why? (With full employment, output is set by supply, not demand; the current account absorbs the fall in investment.) What does this tell you about which assumption makes a model "Keynesian"?
5. **Homogeneity.** Solve with `{"cpi": 2.0}` (long run) and compare quantities with the base. Why must they be identical?
6. **Walras.** Deliberately remove a flow from the government budget in a copy of the code and watch check C4 fail. Put it back.

## 2.9 Limits to state in every report

- One representative producer per industry; no firm-level detail; no informal/formal split.
- Cobb-Douglas household demand (income elasticities of one); LES is Roadmap Phase 1.
- Petroleum is combined with chemicals in the SAM (`cchem`).
- No financial sector, interest rates or expectations: monetary policy questions belong to the BSP-style VAR/DSGE tools.
- Elasticities are defaults, not Philippine estimates.
- The 2023 SAM's structure (from the 2018 I-O table) may not reflect 2026 conditions.
