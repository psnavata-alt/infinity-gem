# 08. Parameters and their sources (Infinity GEM 0.3)

**Purpose.** Every number the models assume, where it comes from, how good the source is, and what other leading models use. Update this file whenever a parameter or source changes, and record the change in CHANGELOG.md.

**Grades.** **Gold** = official Philippine data, or a Philippine estimate in a peer-reviewed source. **Silver** = the standard value in an authoritative model or international dataset, not estimated for the Philippines. **Placeholder** = an assumption still to be replaced. Every source listed was opened before use (date given).

Last updated: 2 October 2026, about 4:30 AM.

---

## 1. Dynamic model: capital

| Parameter | Value used / proposed | Grade | Source (opened) | Other models, for comparison |
|---|---|---|---|---|
| Depreciation rate of capital (`depreciation`) | **5.02%** (2023); 5.0-5.4% over 2010-2023. Used by `documented_baseline()` (built 2 Oct); the plain default stays the 5% placeholder so published results do not change | **Gold** (built on PSA national accounts) | Penn World Table 11.0, capital detail (`data/raw/macro/pwt110_capital_detail.xlsx`): capital consumption ÷ previous-year net capital stock, current national prices. PWT's investment equals PSA's gross fixed capital formation exactly, 2010-2023 (checked 2 Oct) | PWT main file `delta`: 4.64% (2023), a stock-weighted average. IMF ICSD 2021 Manual, Table 1: 5.40% (private, middle income, 2016; assumption by income group). MANAGE-WB default: 4% (`depr0`). By asset (PWT, 2023): structures 2.3%, machinery 14.5%, transport equipment 21.7%, other 15.0% |
| Capital stock / GDP | **2.42** (2023, current prices; 2.19 in 2019); **about 1.96 excluding public capital** (rent-earning capital, for capital by industry) | **Gold** | PWT 11.0 capital detail: current-cost net capital stock ÷ PSA nominal GDP (`data/raw/macro/PSA_OpenSTAT_GDP_by_expenditure_quarterly_2000-2026.csv`). Public share about 19% from IMF ICSD 2019 | IMF ICSD: total 2.08 (2019, current pesos); private + PPP 1.69. PWT at constant 2021 prices: 3.94 (2023) — a price-base artefact, not used. MANAGE-WB template defaults: 5 (GTAP templates) or 2.62 (POW template); its GTAP route sets K = depreciation value ÷ 0.04 |
| Check | Rent-earning capital 1.96 × GDP and 5.02% depreciation, with the 2023 SAM's investment (22% of GDP), imply capital growth of about 6.2% a year | — | Calculation, 2 Oct | PWT: capital stock growth 5.44% (2023); ICSD private + PPP 8.2-8.4% (2017-2019) |
| Investment mobility ω (how strongly new capital chases above-average returns) | **3.0** central; 1 and 5 as sensitivity (tested: stable for 0-5, overshoots at 10 or more) | **Silver** (IFPRI's standard setting; no Philippine estimate found) | IFPRI Extended Standard Recursive Dynamic CGE v2.00 (July 2005), `external/IFPRI_model-main/src/gams/algebraic/1dmodel.gms`, lines 497-498: `beta1` and `beta2` = 3.00. Rule: Diao and Thurlow (book chapter, eqs 22′ and 23, pp. 16-17); Thurlow (2004), TIPS WP 1-2004, pp. 53-54 (eqs P-U) | MANAGE-WB: a different, vintage-based rule; "disinvestment elasticity for declining sectors" `invElas0` = 0.7 (`dat/BridgeFile_GTAP_9_template.xlsx`, sheet defPar; used in `inc/model.inc` line 2973). Lemelin and Decaluwé (2007) PEP survey reviews the alternatives |
| Public capital: depreciation | **3.52%** | Silver | IMF ICSD 2021 Manual & FAQ, Table 1 (middle income, 2016; a reference copy (not distributed)) | — |
| Public capital: share of spending that becomes usable capital `e` | **0.77** | **Gold** (Philippine-specific, IMF) | IMF Country Report 19/137, Philippines PIMA (Dec 2018), pp. 8, 25: efficiency gap "about 23 percent" | MANAGE-WB `PhiPcInv0` = 0.75: 75% of government investment adds to the capital stock (`inc/model.inc` line 2015 uses it this way; note: the Excel template's label says "share … that is *not* added", which contradicts the code). IMF (2015): average gap 27% |
| Public capital stock / GDP `kg_gdp` | 0.296 (constant 2017 PPP) to 0.397 (current pesos), 2019, run as a range | **Gold** (IMF's estimate for the Philippines) | IMF Investment and Capital Stock Dataset, published 1 July 2025 (the IMF ICSD download (not distributed: IMF terms)) | — |
| Output elasticity of public capital φ | **0.083** (short run) to **0.122** (long run) | Silver (meta-analysis, mostly OECD) | Bom and Ligthart (2014), *Journal of Economic Surveys* 28(5): 889-916, doi:10.1111/joes.12037 (abstract via University of Vienna portal, 1 Oct) | — |

## 2. Dynamic model: growth path and labour

| Parameter | Value | Grade | Source | Notes |
|---|---|---|---|---|
| Real GDP growth, 2024-2025 | 5.7%, 4.4% | Gold | PSA (in `infinity_gem/dynamic.py`) | |
| Real GDP growth, 2026-2030 (baseline) | **DBCC: 2026 3.5-4.5%; 2027-2030 5.0-6.0%** → midpoints 4.0% and 5.5%, bounds as sensitivity. Built 2 Oct as `DBCC_GROWTH` / `documented_baseline()`; the plain default keeps the old placeholders so published results do not change | **Gold** | **193rd DBCC Statement, 8 July 2026**, Review of the Medium-Term Macroeconomic Assumptions and Fiscal Program for FY 2026-2030 (dbm.gov.ph; opened 2 Oct). No later review found | Same statement: inflation 2026 6.0-7.0%, 2027 4.0-5.0%, 2028-30 2.0-4.0%; Dubai crude $80-100, $70-90, $60-80; ₱60-62/US$; deficit −5.4% (2026) to −3.5% (2030) of GDP |
| Labour force growth by skill | **2024: low −7.65%, medium −4.08%, high +4.92%; 2025: −4.65%, −2.21%, +1.97%; 2026 (Jan-Jul vs Jan-Jul): −4.19%, −4.50%, +3.58%; 2027-2030: total with population 15+ (1.78% → 1.64%), skill shares continuing their 2023-2025 trend** (`psa_labour_growth()`; in `documented_baseline()` since 2 Oct; the 1.5% placeholder kept as `labour="placeholder"`) | **Gold** (2024-2026); **Sourced projection with a trend assumption** (2027-2030; sensitivity: shares constant) | PSA OpenSTAT 0141B3FEMP7 (LFS, employed by highest grade completed, 2017 PSCED) and 0021A3BPOP1 (2020 CPH-based projections), pulled 2 Oct 2026 through the PXWeb API (`data/OPENSTAT_PULL_METHOD.md`). Mapping to the SAM's types: low = no grade + elementary undergraduate; medium = elementary graduate + junior high undergraduate; high = junior high completed and above | Employment, not the labour force: in the full-employment closure supply = employment. Employment grew more slowly than the population 15+ (0.35% in 2025). Check L1 |
| Industry baseline | Each PSA industry's real GVA growth 2024-2025 reproduced exactly; real GDP then 5.69% and 4.49% (PSA 5.71%, 4.40%) | **Gold** (targets) | PSA OpenSTAT 0052B5BPRA1, GVA by industry at constant 2018 prices (pulled 2 Oct 2026) | Levers: construction investment, government consumption of public administration, input intensity (twist) of trade and financial services, TFP for the other 12 industries (changes −4.5% to +9.0%). From 2026 the industries grow together. Contains the actual 2025 construction slump: do not add the 2025 freeze on top. Check Y5 |
| Job-gap persistence (hybrid closure) | 0.5 a year | **Placeholder** | To come: the labour-market evidence (labour-market evidence: LFS unemployment and underemployment, wage rigidity, Okun's law) | |

## 3. Static CGE: elasticities (built 2 Oct 2026)

### Summary in plain language (2 Oct 2026)

**What the search found.**
- **Philippine econometric estimates exist for only one kind of elasticity.** Kapuscinski and Warr (1999) estimated import-vs-domestic (Armington) elasticities for 33 Philippine products. Their recommended column was transcribed from the page images and is used where it is significant, positive and covers most of a product group's imports: 13 product groups (corn, poultry, food, textiles, machinery and others). The data are from the 1970s-80s, so the estimates are dated, but they are the only Philippine ones.
- **The other Philippine CGE models did not estimate anything themselves.** APEX and PCGEM reuse Kapuscinski and Warr (rounded); MIMAP's values are assumed; Briones set his "arbitrarily" to 2 (2015) or used uniform values (2023); PHILGEM does not publish its values.
- **For everything else, GTAP's standard values** (taken from the World Bank model's files and weighted by Philippine trade and value added): value-added substitution for every sector, and Armington where no Philippine estimate qualified.
- **No CET (export transformation) estimate exists** for the Philippines anywhere; those values remain assumptions, graded as such.

**Does it change the September 2026 numbers? Not by much.**

| Short-run results | Published (default elasticities) | With sourced elasticities |
|---|---|---|
| Infrastructure freeze, GDP | -0.279% | -0.237% to -0.261% |
| Freeze, new poor | 497,000 | 442,000 - 465,000 |
| Oil +20%, GDP | -0.215% | -0.249% to -0.258% |
| Oil +20%, new poor | 601,000 | 687,000 - 688,000 |

Signs and orders of magnitude hold. With sourced elasticities, the freeze costs slightly less and the oil shock 15-20% more. Long-run results barely move.

**Fixed along the way.** Very low export elasticities made the export calculation fail (it hit cattle, whose exports are tiny next to its domestic sales). It is now computed in a numerically stable way; the maths is identical, so no result changed (check R0).

### Technical detail

**Four sets** (`infinity_gem/elasticities.py`; table `data/processed/elasticities_ph_v1.csv`, built by `tools/build_elasticities.py`; check E1). The default stays as before (check R0); a set is chosen by name: `CGE.from_sam(elasticities=elasticity_set("ph"))`.

| Set | Value added (sigma_va, by activity) | Armington (sigma_q, by commodity) | CET (omega_t, by commodity) |
|---|---|---|---|
| `default` (all published results) | 0.8 everywhere | 2.0 everywhere | 2.0 everywhere |
| `gtap` | GTAP 9 ESUBVA: crops and livestock 0.26; forestry, fishing, mining 0.20; food and beverages 1.12; other manufacturing, utilities, most services 1.26; construction 1.40; trade, transport, hotels 1.68 | GTAP 9 ESUBD, Philippine import-weighted: 1.15 (beverages) to 5.05 (paddy rice); manufactures 2.9-4.1; services 1.9 | equal to ESUBD (MANAGE-WB's convention) |
| `ph` | as `gtap` | **Kapuscinski and Warr (1999) where valid** (13 commodities): corn 3.72, fruit 1.03, poultry 1.39, other livestock 1.32, forestry 0.83, mining 0.68, food 1.03, textiles 0.65, cement and non-metallic 0.59, metals 0.24, machinery 1.05, other manufacturing 1.04; GTAP elsewhere | as `gtap` |
| `ph_pcgem_cet` | as `gtap` | as `ph` | PCGEM (Cororaton 2000, Table 3), assumed values 0.3-3.0 |

**Grades.** Armington from Kapuscinski and Warr: **gold** (the only econometric Philippine estimates; peer-reviewed), but old (mid-1970s to late-1980s data) and from annual time series, which typically give lower values than the trade-model literature. GTAP ESUBD and ESUBVA: **silver** (international standard; via the World Bank MANAGE-WB template, MIT licence; ESUBVA = MANAGE-WB "va New" / 2, which reproduces GTAP's published values). CET: **no estimate exists for the Philippines**; both the GTAP-convention and PCGEM values are assumptions.

**GTAP version (17 Oct 2026).** The ESUBD values above were taken from GTAP 9's parameter file (through MANAGE-WB). A licensed GTAP 10A package (the GTAP 10A archive (licensed; not distributed), read by `tools/gtap10_philippines.py`, GTAP's parameter file) gives the **same** values for the sectors checked: petroleum and coal products (p_c) 2.1, processed rice (pcr) 2.6, paddy (pdr) 5.05 (the GTAP 10 parameter extract (not distributed: GTAP licence), column ESBD).
- These are behavioural parameters distributed with GTAP, not numbers from GTAP's database of flows. The SAM, not GTAP, supplies the Philippine flows.
- ESUBD comes from Hertel, Hummels, Ivanic and Keeney (2007, Economic Modelling 24(4)): import-import elasticities (ESUBM) estimated from cross-country trade data, with domestic-import ESUBD set at half of ESUBM (GTAP's "rule of two").
- Armington sensitivity (17 Oct 2026) tested Infinity GEM's own data against them: `ITEM72a_armington_fuel_rice_scoping_17Oct2026.md`.

**Rule for `ph`:** Kapuscinski and Warr's basic ECM (Table 4, column 7, the authors' preferred specification) where the estimate is significant at 10%, positive, and the significant estimates cover at least half of the group's imports (their Table 1 shares); otherwise GTAP. Chemicals and petroleum fall back to GTAP (no significant positive estimate). Transcription: `data/raw/elasticities/Kapuscinski_Warr_1999_Table4_ECM.csv` (from page images; the text layer is unusable).

**What the Philippine CGE literature uses (nothing estimated except via Kapuscinski-Warr):** APEX (Clarete and Warr 1992, as printed in Cororaton 2000, Table 2): Kapuscinski-Warr rounded, 0 where insignificant; PCGEM (Cororaton 2000): APEX averaged, floor 0.2, Cobb-Douglas value added, CET 0.3-3.0; MIMAP (Cororaton 1994): Armington 0.33-1.5 and export demand 1-4, assumed; Briones (2015): all elasticities "arbitrarily" 2; Briones et al. (2023): value added 2.0, Armington 4.0, CET 2.0, uniform; PHILGEM (Corong and Horridge 2012): values in its GEMPACK database, not published in the paper (typical export demand elasticity -5). MANAGE-WB defaults: Armington 5 and CET 3 where no GTAP value.

**Sensitivity of the main September 2026 results** (`scenarios/elasticity_sensitivity.py`; `outputs/elasticity_sensitivity_20261002.md`; not for citation): short-run CGE real GDP: infrastructure freeze -0.279% (default) vs -0.237% to -0.261% (sourced sets); oil +20% -0.215% vs -0.249% to -0.258%; remittances -10% -0.072% vs -0.049% to -0.067%. New poor: freeze 497k vs 442k-465k; oil 601k vs 687k-688k. Long-run results barely move. **Conclusion:** signs and orders of magnitude are robust; with sourced elasticities the freeze costs slightly less and the oil shock 15-20% more than the published default figures.

**Household demand: LES (built 2 Oct 2026; option `CGE(les=les_briones2023())`; `infinity_gem/demand.py`; check H1).**
- **Income elasticities:** Briones et al. (2023), PIDS DP 2023-23, Table 5 (the LES of AMPLE-CGE, a Philippine CGE; food values from the QAIDS estimates of Briones et al. 2022, non-food imputed by the authors), with Table 4 for other cereals; transcribed in `data/raw/elasticities/Briones_et_al_2023_Table5_LES_elasticities.csv`. Processed foods (0.65) and beverages & tobacco (1.58) are weighted from Briones's sub-groups with PSA's 2018-based CPI weights. Scaled per household group to satisfy Engel aggregation (unscaled sums 0.96-1.12).
- **Frisch parameter:** not published by any Philippine source on file (Briones 2015 and PHILGEM do not print it; Canlas 1985 is a 1965 food-and-leisure system). Fitted per household group so the LES own-price elasticities best match Briones's (budget-share-weighted least squares): **−1.28 (poorest rural) to −1.15 (richest urban)**; subsistence spending 13-22% of the total. Sensitivity: fitted to the food (econometric) elasticities only: −1.04 to −0.89. An LES cannot match every own-price elasticity (fit error about 0.25; processed food −0.6 against Briones's −0.88).
- **Effect on the September 2026 results** (`scenarios/demand_sensitivity.py`, `outputs/demand_sensitivity_20261002.md`; short run): freeze GDP −0.279% (Cobb-Douglas) → −0.269%, new poor 497,479 → 504,894; oil +20% GDP −0.215% → −0.210%, new poor 600,661 → 593,411. The mix changes: processed food consumption falls less (freeze −0.80% → −0.55%; oil −0.15% → +0.01%), as a necessity should. Long-run results barely move.
- **Benchmark (filed 2 Oct 2026, night): USDA ERS**, Muhammad, Seale, Meade and Regmi (2011), *International Evidence on Food Consumption Patterns: An Update Using 2005 ICP Data*, TB-1929 (144 countries; report in a reference copy (not distributed), Philippines rows in `data/raw/elasticities/USDA_ERS_2005ICP_Philippines_elasticities.csv`, originals in `USDA_ERS_2005ICP/`).
  - **Frisch:** USDA's own-price elasticities at constant marginal utility divided by its income elasticities give **−1.363 for every one of the nine broad groups**: the Frisch parameter implied for the Philippines. Our fitted −1.15 to −1.28 is close.
  - **Income elasticities (Philippines):** food, beverages & tobacco 0.756; clothing 0.967; housing 1.071; furnishings 1.053; medical 1.47; transport & communication 1.186; recreation 1.733; education 0.927; other 1.478. Food subgroups: cereals 0.43, meats 0.75, fish 0.62, dairy 0.77, oils 0.46, fruits & vegetables 0.57, other food 1.09, beverages & tobacco 1.01.
  - **Comparison:** the food-and-beverage aggregate comes out at 0.74-0.78 with Briones and 0.62-0.74 with USDA (by household group, after Engel scaling), against USDA's 0.756. Briones is higher for fish, dairy, oils and beverages and lower for cereals (0.10 imputed against 0.43).
  - **Variant `les_usda2011()`:** a benchmark LES with USDA elasticities (composites by PSA CPI weights: chemicals & petroleum = household fuels, transport fuels, medicines, personal care; machinery = appliances, vehicles) and Frisch −1.363. Short run: freeze GDP −0.265% (Briones −0.269%, Cobb-Douglas −0.279%), new poor 506,613 (504,894; 497,479); oil +20% GDP −0.210% (−0.210%; −0.215%), new poor 602,837 (593,411; 600,661). **The LES results do not depend on which of the two Philippine sources is used.**
  - GTAP's Philippine demand parameters: see the GTAP 10 benchmark below.
- **Second benchmark (3 Oct 2026, just after midnight): GTAP 10** (2014, region `phl`). Source: Aguiar, Chepeliev, Corong, McDougall and van der Mensbrugghe (2019), "The GTAP Data Base: Version 10", *JGEA* 4(1). Archived release, free with citation; package the GTAP 10A archive (licensed; not distributed), downloaded under the GTAP licence.
  - Extraction: `tools/gtap10_philippines.py` reads the package with the open-source `harpy3` (no GTAP software run). GTAP's demand system is CDE; the elasticities use the formulas of the GTAP model code (`gtapv7.tab`) with GTAP's 2014 Philippine household budget shares. Output: the GTAP 10 parameter extract (not distributed: GTAP licence) (Engel aggregation holds exactly).
  - Income elasticities: food and beverages 0.60 (USDA 0.756; Briones-based LES 0.74-0.78); rice and grains 0.42; meat, fish and dairy 0.71; services 1.0-1.35.
  - Own-price elasticities are much smaller in magnitude: food −0.13 to −0.26, services −0.33 to −0.49. GTAP's CDE parameters are calibrated from cross-country estimates, not estimated for the Philippines.
  - LES variant `les_gtap10()`: the Frisch fitted to GTAP's own-price elasticities is −3.3 to −4.1 (Briones −1.15 to −1.28; USDA −1.36), i.e. much less price-responsive households.
  - September 2026 results with all four demand settings (short run; `outputs/demand_sensitivity_20261003.md`):
    - freeze GDP −0.256% to −0.269% (Cobb-Douglas −0.279%), new poor 500,000-520,000 (497,000);
    - oil +20% GDP −0.203% to −0.210% (−0.215%), new poor 593,000-619,000 (601,000).
    - **The household-demand upgrade is robust to the source.** The GTAP variant shows a smaller CPI rise for oil (+0.43% on the combined SAM), because households keep buying fuel and chemicals and cut other goods, which lowers other prices.
  - GTAP 10's Philippine production structure dates from the 2000 I-O table (Cororaton, `12059.pdf`), so only its parameters are used, not its flows.
  - GTAP 10's Armington elasticities (ESBD) are in the same CSV for comparison with the `gtap` elasticity set (GTAP 9, via MANAGE-WB).

## 3b. Oil and the petroleum-split SAM (built 2 Oct 2026, night)

**Why.** The IFPRI Nexus SAM puts ISIC 19-22 (refined petroleum; chemicals incl. fertilisers; pharmaceuticals; rubber and plastics) in one account, "chemicals and petroleum" (IFPRI 2023 data paper, Table A1). Crude oil (ISIC 06) is in mining. The published CGE oil shock therefore raised the import price of the whole group by the oil change x 0.6 (assumed), and did not shock crude at all.

**The split SAM** (`data/processed/IFPRI_SAM_PHL_2023_SAM_petroleum_split.csv`, built by `tools/build_sam_petroleum_split.py`; report `outputs/sam_petroleum_split_20261002.md`; check S1).
- New accounts `apetr`/`cpetr` (refined petroleum, PSA 2018 sectors 107-108); `achem`/`cchem` keep chemicals, pharmaceuticals, rubber and plastics (109-118). Mapping as in Cororaton's GTAP chapter (Table 8.87).
- Every other account of the IFPRI 2023 SAM is unchanged, cell for cell.
- Shares from PSA's 2018 240-industry table (the base of the 2023 SAM itself):
  - purchases by each buyer, imports and exports;
  - the refinery's cost structure at basic prices: crude 27%, own use of petroleum products 26%, trade 10%, capital 15.5%, wages 6.6%.
- Taxes and margins:
  - import duties in proportion to imports (assumption);
  - sales taxes: the fuel excise (₱139.7 bn, 2023, BIR + BOC; **ATTRIBUTED** from CPBRD FF2025-42 as quoted in a search result: the PDF is behind a bot check, to be saved by hand) plus the rest in proportion to domestic use;
  - margins in proportion to domestic use.
- Households: all ten groups get PSA's average petroleum share of their purchases (33.5%); the FIES public file has no fuel detail.
- Result:
  - refinery output ₱655 bn (28% of the group; PSA 2018: 41%);
  - petroleum imports ₱1,092 bn;
  - households buy ₱979 bn of fuel (4.8% of their spending) and ₱1,942 bn of other chemical products.

**Sourced shares replacing assumptions** (`infinity_gem/oil.py`; PSA 2018 imports column and 80-industry table):

| Parameter | Was | Now | Source |
|---|---|---|---|
| Petroleum share of "chemicals and petroleum" imports (combined-SAM shock) | 0.6 (assumed) | 0.512 | PSA 2018, 240-industry imports, sectors 107-108 / 107-118 |
| Crude share of mining imports (split-SAM shock) | crude not shocked | 0.677 | PSA 2018, sector 40 / 39-45 |
| Fertiliser share of chemical imports (Cororaton benchmark) | — | 0.026 | PSA 2018, sector 110 / 109-118 |
| I-O pass-through, world oil → refined-petroleum price | 0.6 (assumed) | **0.634** = (s_m + (1-s_m) c) / (1 - (1-s_m) o) | import share s_m 0.354 (2018 Supply table, sector 107); crude c 0.269 and own use o 0.260 per peso of refinery output (80-industry table) |

Assumption kept: product prices of imported refined petroleum move one-for-one with crude.

**Results** (`scenarios/oil_petroleum_split.py`; `outputs/oil_petroleum_split_20261002.md`; not for citation). Short run, oil +20%:

| | Published (combined, 0.6) | Combined, PSA share 0.512 | Split SAM |
|---|---|---|---|
| Real GDP | −0.215% | −0.183% | −0.238% |
| CPI | +1.11% | +0.95% | **+0.29%** |
| Real household consumption | −1.24% | −1.08% | −1.23% |
| New poor | 600,661 | 510,189 | 602,955 |

- The split changes GDP and poverty little but **cuts the CGE's inflation effect by about three-quarters**.
  - The published method raised the price of every chemical product (medicines, soap, fertiliser, plastics: 14.3% of household spending) as if it were oil.
  - In the split SAM fuel rises 15.2% (4.8% of spending, +0.73 pp on the CPI), while weaker demand lowers other prices (food −0.47%).
  - The I-O price model's upper bound is +0.87% with the sourced pass-through (+0.82% with 0.6).
- **Benchmark 2 (Cororaton, Sim1, real GDP −4.49%):** with oil +65% and fertiliser +50% applied where they belong, Infinity GEM gives −0.81% (short run) and −0.63% (long run), against −1.17% and −1.47% with the 30 Sept combined shock (cchem x1.64).
  - The gap widens: the earlier, closer figure came partly from raising the price of non-oil chemicals by 64%.
  - The remaining gap is most likely Cororaton's 20% cut in import volumes of oil and fertiliser, which Infinity GEM does not impose (a quantity ration), and model differences. His SAM year and closures are not stated.

### 3c. Questions answered on the petroleum split (2 Oct 2026)

- **Why does IFPRI bundle petroleum with chemicals?** IFPRI's Nexus SAMs use one standard set of 42 accounts across many countries, for comparability. Their focus is agriculture and food: 17 farm activities and fine food detail, but coarse industry groups. It suits their purpose, not an oil shock.
- **Does the I-O side need splitting too?** No. PSA's 80-industry table (the I-O model) already separates crude petroleum and natural gas (21), coke and refined petroleum (35), chemicals (36), pharmaceuticals (37), and rubber and plastics (38). The I-O oil shock already hits refined petroleum alone. The petroleum split brings the CGE and the SAM multiplier model to the same detail, so the CGE and I-O columns of the September 2026 tables are like-for-like.
- **Two different "0.6"s.**
  - In the CGE (combined SAM), 0.6 was the assumed petroleum share of "chemicals and petroleum" imports. PSA says 0.512; with the split SAM the share is no longer needed.
  - In the I-O model, 0.6 was the assumed pass-through from world oil to the refined-petroleum price. It is now sourced: 0.634.
- **What the pass-through is.** The share of a world oil-price change that appears in the price of refined petroleum products in the Philippines (imported and locally refined together):
  - p = (s_m + (1 − s_m) c) / (1 − (1 − s_m) o) = (0.354 + 0.646 × 0.269) / (1 − 0.646 × 0.260) = **0.634**;
  - s_m = imported share of refined-petroleum supply (2018 Supply table, sector 107); c = crude per peso of refinery output; o = refined petroleum used per peso of refinery output (blending and own use), both from the 80-industry table (`infinity_gem.oil.io_refined_passthrough()`).
- **Is it recomputed for each shock, from the VAR?**
  - No. It is a structural feature of the economy (input-output coefficients and the import share), the same for +20%, +40% or +60%.
  - What changes with each shock is the oil-price change itself, taken from the data: Dubai crude in the quarterly macro panel; the September 2026 shock is +40%, the actual rise.
  - The reference VAR estimates how geopolitical risk and oil prices move the peso, FDI and other aggregates; it does not estimate the pass-through.
  - Where the VAR enters is the peso: with the reference VAR's depreciation of 1.87%, the peso price of imported oil rises by (1 + oil)(1 + depreciation) − 1 (40% → 42.6%), and the pass-through applies to that. This is the right way to build the "upper end with the peso" case.
  - Possible empirical check (not done): DOE weekly pump prices regressed on Dubai crude in pesos. That measures pass-through to pump prices, which is lower because the excise is fixed per litre.
- **Will the split improve the benchmark scores?**
  - IFPRI validation (V2): unaffected (same SAM on both sides).
  - Cororaton benchmark: not necessarily, and in fact it did not (above). The comparison is now fair: the old closer figure came from an over-broad shock.
  - Internal checks: unaffected (opt-in).
- **The GTAP archive (gtap.agecon.purdue.edu/databases/archives.asp, seen 2 Oct 2026):**
  - GTAP 10 (reference years 2004, 2007, 2011, 2014; 141 regions; 65 sectors) and GTAP 9 are free to use with citation.
  - Use for Infinity GEM: GTAP's Philippine household-demand parameters (CDE), a third benchmark for 7b beside Briones and USDA ERS, and its Philippine trade and production elasticities.
  - Limit: before GTAP 12 the Philippine input-output structure in GTAP came from the 2000 table (Cororaton, `12059.pdf`), so GTAP 10 is a parameter benchmark, not a replacement for the 2023 SAM.
  - Access: the "Data Package (All Reference Years)" plus GTAPAgg2, after accepting GTAP's licence (to be downloaded under the licence). The HAR files can be read in Python with the open-source `harpy` reader, without running GTAP's software.

## 4. Data sources unavailable or not usable

- **PSA consumption of fixed capital:** not on OpenSTAT. Consolidated Accounts I-III (tables 0012B5BCA01, 0022B5BCA02, 0032B5BCA03; updated 5 Aug 2026) are gross only. An eFOI request "Consumption of Fixed Capital, Net Operating Surplus (2000-2022)" exists; the portal was under maintenance on 2 Oct. PWT (above) is built on PSA data and fills the gap.
- **IFPRI 2018 SAM:** households' purchases of chemicals and petroleum and of fish are blank in IFPRI's published file (verified identical to Dataverse doi:10.7910/DVN/XSEXEP v1, MD5 match). Not usable for oil-price work.

## 5. External model code on file (for validation and design; not part of Infinity GEM)

| Folder (`external/`, not included) | What it is | Licence | Use |
|---|---|---|---|
| `IFPRI_model-main/` (GitHub uw-windc/IFPRI_model, ZIP 15 Jul 2025) | `src/gams/algebraic/1dmodel.gms`: IFPRI Extended Standard Recursive Dynamic CGE, v2.00 (July 2005; Thurlow's extension of Lofgren et al. 2002), with Thurlow's 2003 South Africa data workbook (`1model.xls`); `src/model.jl`: Julia/MPSGE port of Rutherford's (2006) MPSGE version of the standard model (Peru 2004 SAM) | IFPRI code: GNU GPL v2 (changed versions must be marked). Julia port: no licence file | Route A (GAMS demo, condensed SAM) and route B (Julia); ω = 3.0 |
| `MANAGE-WB-main/` (GitHub worldbank/MANAGE-WB, ZIP 2 Oct 2026; JRE, GUI jars and the 24 MB GTAP data file not extracted) | The World Bank's recursive dynamic CGE (GAMS ≥ 39; GUI via `manage.bat`; GTAP-based SAMs). Model in `inc/model.inc`; defaults in `dat/BridgeFile_*_template.xlsx` (sheet defPar). Documentation: Beyene, Britz, Christensen, Dudu and Galindev (2025), MANAGE-WB Model Documentation (worldbank.org/en/programs/economicpolicy-macro-modeling/cge) | MIT (World Bank, 2026) | Second benchmark (benchmark 3 already borrowed its consistency tests); design comparison for the dynamic options (vintage capital, activity-specific depreciation, unemployment equation, public investment share) |

## 6. References

The works cited in this guide are named where they are used. Copies of the papers are not redistributed (copyright); each can be found from its citation.

## 7. Still to source (gold standard)

1. Labour force growth by skill: PSA LFS by highest grade completed; PSA population projections.
2. Job-gap persistence: the labour-market evidence.
3. Philippine elasticities (start with Kapuscinski and Warr 1999).
4. ω for the Philippines (optional): ask IFPRI whether its Philippine work uses another value.
