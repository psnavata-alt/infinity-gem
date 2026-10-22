# Verification, Phase 1: Infinity GEM's CGE equations against the published IFPRI model

**What this is.** A line-by-line map of all 48 equations of the IFPRI standard CGE model, as published in a book, to:
- IFPRI's own computer code (GAMS);
- Infinity GEM's code (Python).

It lets anyone check, without knowing Python, that each equation in Infinity GEM is the published one, or see exactly where and why it differs.

**Prepared:** 7 October 2026, with an AI coding assistant. **This document is AI-written: verify it with the steps in Section 2, not on trust.**

---

## 1. The three sources

| Source | Who wrote it | Where it is |
|---|---|---|
| **The book:** Lofgren, H., R. L. Harris and S. Robinson (2002), *A Standard Computable General Equilibrium (CGE) Model in GAMS*, Microcomputers in Policy Research 5, International Food Policy Research Institute (IFPRI), Washington, D.C. | IFPRI economists (published 2002) | IFPRI's website (Microcomputers in Policy Research 5; not redistributed here). All 48 equations are summarised in the book's appendix table, **printed pages 50–59** (PDF pages 59–68). They are derived one by one in the main text, printed pages 18–40. |
| **IFPRI's code:** *Extended Standard Recursive Dynamic CGE Model, Version 2.00* (July 2005; Thurlow's extension of the book's model), GAMS, GNU GPL v2 | IFPRI economists | [`../../validation/ifpri/gams_ph/1DMODEL_PH.GMS`](../../validation/ifpri/gams_ph/1DMODEL_PH.GMS). Our copy is marked as altered: only the data file name was changed and a results block appended at the end, so the equation lines are IFPRI's. The unaltered original is in the GitHub repository `uw-windc/IFPRI_model`. **Provenance caveat:** taken from a GitHub copy (`uw-windc/IFPRI_model`), not from IFPRI's own website; to be checked against IFPRI's official files. |
| **Infinity GEM's code:** `infinity_gem/cge.py` | An AI coding assistant, 26 Sept 2026, following the book; **not** translated from the GAMS code, which was obtained only on 2 Oct for testing | **Live version 0.3.1** (since 8 Oct 2026, evening): [`../../infinity_gem/cge.py`](../../infinity_gem/cge.py) (772 lines; adds the activity tax and these options, all off by default: LES demand, IFPRI-style margins, home consumption as own produce, and the Hosoe textbook options for government and investment demand). Version 0.2, behind the results published up to 7 Oct 2026: an archived copy, not included (574 lines; the default settings reproduce its results exactly, check R0). |

**Why the formulas sometimes look different but are the same.** The book writes production as a *production function* (output from inputs) plus a *first-order condition* (how much of each input to hire). Infinity GEM writes the equivalent *unit-cost function* (the cost of one unit of output at given input prices) plus the *input demands* derived from it. Economists call this the "dual" form. Both give the same quantities and prices. Check V2 (Section 4) shows they do, numerically.

## 2. How to check any row yourself (no programming needed)

1. **Book:** open the book PDF and go to the printed page shown (PDF page = printed page + 9). In Edge or Chrome, type the PDF page number in the page box.
2. **IFPRI code:** right-click `1DMODEL_PH.GMS` → *Open with* → Notepad. Press **Ctrl+G** and type the line number. (If Ctrl+G does nothing: *Format* menu → untick *Word Wrap*.) The equation name is in capitals, e.g. `PMDEF`.
3. **Infinity GEM code:** open `cge.py` the same way (Notepad, Ctrl+G, line number). The comments next to each line say in English what it computes.
4. Compare the three. The **Status** column says what to expect; the **Note** column explains any difference.

## 3. The concordance (all 48 equations)

Status key:
- **Same:** the book's equation, possibly in the equivalent dual form.
- **Same (cond.):** gives identical results under the settings Infinity GEM uses; differs only under options Infinity GEM does not use.
- **Not needed:** the book's term is zero in the Philippine SAM, so it would change nothing.
- **Simplified:** Infinity GEM treats this more simply than the book.
- **Option absent:** an alternative the book offers that Infinity GEM does not have.
- **Special case:** Infinity GEM uses a restricted version.

"0.2" = Infinity GEM 0.2 line (the version behind results published up to 7 Oct 2026, kept in an archived copy); "0.3" = line in Infinity GEM since 8 Oct 2026. **0.3 line numbers re-checked against the released 0.3.1 code on 8 Oct 2026, 8:50 PM.** They move whenever the code changes: the 7 Oct draft gave the line numbers before the margins change, and the 0.3.1 options shifted them again (by 36 to 59 lines). Each was re-found by its exact text in the code; eq. 15 was rewritten in 0.3.1 (an exact Cobb-Douglas case) and was mapped by reading the code.

### Price block (book appendix p. 50–51)

| # | Book equation | IFPRI GAMS (line) | 0.2 / 0.3 line | Status | Note |
|---|---|---|---|---|---|
| 1 | Import price: PM = pwm·(1+tm)·EXR + Σ PQ·icm | PMDEF (1256) | 295 / 397 (+419 with split margins) | **Simplified** | Infinity GEM has the world price, tariff and exchange rate. Trade and transport margins on imports (icm) are not added here: they are charged on the composite good (eq. 4, 27). This is the one structural difference; it explains the largest V2 gap (0.51 pp). **0.3 option `margins="split"` (7 Oct; released since 8 Oct) implements the book's version: gap falls to 0.11 pp (check V3).** |
| 2 | Export price: PE = pwe·(1−te)·EXR − Σ PQ·ice | PEDEF (1258) | 296 / 398 | **Simplified** | No export tax (te) and no export margin. The Philippine SAM has no export tax, so te is *not needed*; the export margin is the simplification above. |
| 3 | Demand price of domestic goods: PDD = PDS + Σ PQ·icd | PDDDEF (1260) | 367 / 518 (PDD = PDS); 539 with split margins | **Simplified** | Same margin simplification. As in the book with the 0.3 option `margins="split"`. |
| 4 | Absorption: PQ·(1−tq)·QQ = PDD·QD + PM·QM | PQDEF (1262) | 382 / 558 | **Same** (different tax convention) | Infinity GEM writes PQ = (1+tq)·(Armington price + margin). Its sales-tax rate is defined on the pre-tax value, the book's on the tax-inclusive value. Both are calibrated to the same SAM tax payments. Margins enter here (see eq. 1). |
| 5 | Marketed output value: PX·QX = PDS·QD + PE·QE | PXDEF (1265) | 319 / 441 | **Same** | |
| 6 | Activity price: PA = Σ PXAC·θ | PADEF (1267) | 320 / 442 | **Same** | Infinity GEM uses one producer price per commodity (PXAC = PX), exact here because each commodity has one producing activity (eq. 19). |
| 7 | Intermediate input price: PINTA = Σ PQ·ica | PINTADEF (1269) | 330 / 457 (inside zero profit) | **Same** | Written inside eq. 8. |
| 8 | Activity revenue and costs: PA·(1−ta)·QA = PVA·QVA + PINTA·QINTA | PVADEF (1271) | 330 / 457 | **Same** | Zero profit per unit of output. Activity tax (ta): version 0.2, *not needed* (none in the 2023 SAM); 0.3 includes it for the 2018 SAM (line 456). |
| 9 | Consumer price index: CPI = Σ PQ·cwts (fixed) | CPIDEF (1273) | 298, 409 / 420, 586 | **Same** | The CPI is the numeraire (fixed), as in the book. In the short-run (Keynesian) closure the exchange rate is fixed instead, a closure the book also describes. |
| 10 | Producer price index for non-traded output: DPI = Σ PDS·dwts | DPIDEF (1275) | — | **Option absent** | Only needed if DPI is chosen as numeraire instead of the CPI. |

### Production and trade block (p. 52–55)

| # | Book equation | IFPRI GAMS (line) | 0.2 / 0.3 line | Status | Note |
|---|---|---|---|---|---|
| 11 | CES activity production function (value added vs intermediates) | CESAGGPRD (1283) | — | **Option absent** | The book lets each activity use either a CES top nest (eq. 11–12) or fixed proportions (eq. 13–14). Infinity GEM uses fixed proportions (Leontief) for all; V2 ran IFPRI's model the same way. |
| 12 | CES value-added/intermediate ratio | CESAGGFOC (1287) | — | **Option absent** | As eq. 11. |
| 13 | Leontief demand for value added: QVA = iva·QA | LEOAGGVA (1296) | 331 / 458 | **Same** | |
| 14 | Leontief demand for intermediates: QINTA = inta·QA | LEOAGGINT (1294) | 360 / 510 (with eq. 17) | **Same** | Combined with eq. 17 into one step (QINT = ica·QA). |
| 15 | CES value-added function: QVA = αva·(Σ δ·QF^−ρ)^−1/ρ | CESVAPRD (1301) | 329 / 452–455 | **Same** (dual) | Infinity GEM computes the value-added price from factor prices (unit-cost form). αva is the productivity term `tfp`. |
| 16 | Factor demand: WF·WFDIST = PVA·(1−tva)·QVA·(…)·δ·QF^(−ρ−1) | CESVAFOC (1307) | 334 / 461 | **Same** (dual) | WFDIST (sector wage differentials) is 1 at the base, as in the book when factors are measured in value units. With capital fixed by sector, rents differ by sector (lines 325 / 447), as in the book's "activity-specific factor" closure. Value-added tax (tva): *not needed* (none in the SAM). |
| 17 | Disaggregated intermediate demand: QINT = ica·QINTA | INTDEM (1319) | 360 / 510 | **Same** | |
| 18 | Commodity production and allocation: QXAC + Σ QHA = θ·QA | COMPRDFN (1321) | 303 / 425 | **Simplified** | No home consumption (QHA): the SAM's own-consumption flows are moved into market purchases before calibration (`sam.py`, `move_home_consumption_to_market`, 0.3 line 174). V2 used the same treatment for IFPRI's model. **Released since 0.3.1 (8 Oct 2026), as an option, off by default: `home="separate"` applies the book's eq. 18 and 34; against IFPRI's own model run with home consumption kept, GDP and consumption agree within 0.0006 pp and home consumption within 0.001 pp (check V4, `validation/ifpri_home/`). Effect on September 2026 results: negligible.** |
| 19 | Output aggregation (CES across activities) | OUTAGGFN (1324) | 303 / 425 (sum) | **Not needed** | Matters only if two or more activities produce the same commodity. In the 2023 SAM **none does** (checked 7 Oct), so the book's equation reduces to Infinity GEM's sum. |
| 20 | First-order condition for output aggregation | OUTAGGFOC (1327) | — | **Not needed** | As eq. 19. |
| 21 | CET between exports and domestic sales | CET (1330) | 305–312 / 427–434 | **Same** | |
| 22 | Export–domestic supply ratio | ESUPPLY (1333) | 307 / 429 | **Same** | ω = 1/(ρ−1) in the book's notation. 0.3 computes the share term in a numerically safer way (the development history (not included)). |
| 23 | Output when a good is only exported or only sold at home: QX = QD + QE | CET2 (1336) | 313–316 / 435–438 | **Same** | |
| 24 | Armington composite supply | ARMINGTON (1339) | 371–372 / 522–523 (543–544 with split margins) | **Same** (dual) | Composite price written as a unit-cost function. |
| 25 | Import–domestic demand ratio | COSTMIN (1342) | 374–375 / 525–526 (545–546) | **Same** | Import and domestic demands from the same CES. |
| 26 | Composite supply when a good is only imported or only domestic: QQ = QD + QM | ARMINGTON2 (1345) | 376–381 / 527–532 (547–552) | **Same** | |
| 27 | Demand for trade and transport services: QT = Σ (icm·QM + ice·QE + icd·QD) | QTDEM (1348) | 363–364 / 513–515 (553–554) | **Simplified** | Infinity GEM charges margins per unit of the composite good, with one fixed mix of margin services. Same simplification as eq. 1–3. As in the book (domestic and import margins) with the 0.3 option `margins="split"`. |

### Institution block (p. 55–57)

| # | Book equation | IFPRI GAMS (line) | 0.2 / 0.3 line | Status | Note |
|---|---|---|---|---|---|
| 28 | Factor income: YF = Σ WF·WFDIST·QF | YFDEF (1362) | 337–339 / 464–466 | **Same** | Infinity GEM also adds factor income received from abroad (a SAM cell) before distributing it. |
| 29 | Institutional factor incomes: YIF = shif·[(1−tf)·YF − trnsfr(row,f)·EXR] | YIFDEF (1364) | 340–341 / 467–468 | **Same** | |
| 30 | Income of households and enterprises: YI = Σ YIF + Σ TRII + trnsfr(gov)·CPI + trnsfr(row)·EXR | YIDEF (1367) | 344, 349 / 471, 476 | **Same** | |
| 31 | Transfers between institutions: TRII = shii·(1−MPS)·(1−TINS)·YI | TRIIDEF (1371) | 344–349 / 471–476 | **Same (cond.)** | Infinity GEM makes enterprise-to-household transfers proportional to enterprise income. This equals the book whenever the enterprise tax and saving rates are fixed, as in all Infinity GEM closures. V2 fixed IFPRI's enterprise saving rate the same way. |
| 32 | Household consumption spending: EH = (1−Σ shii)·(1−MPS)·(1−TINS)·YH | EHDEF (1374) | 351–354 / 478–481 | **Same (cond.)** | Same SAM flows, ordered slightly differently: Infinity GEM deducts households' payments to government and abroad before saving. Identical at the base and under fixed rates. |
| 33 | Household demand, Linear Expenditure System (LES) | HMDEM (1377) | 355 / 483 (Cobb-Douglas), 486 (LES) | **Special case** (default); **Same** (0.3 LES option) | Live: Cobb-Douglas, the LES with no subsistence quantities (book p. 32). 0.3 adds the full LES (`les=` option; Briones et al. 2023 parameters). |
| 34 | Household demand for home-produced goods | HADEM (1381) | — | **Simplified** | No home consumption (see eq. 18). **Option `home="separate"` (released since 0.3.1, off by default): as in the book (see eq. 18).** |
| 35 | Investment demand: QINV = IADJ·qinv | INVDEM (1386) | 359 / 509 | **Same** | |
| 36 | Government consumption: QG = GADJ·qg | GOVDEM (1389) | 358 / 505 | **Same** | GADJ is the scenario setting `qg_scale`. |
| 37 | Government revenue (direct, factor, activity, import, export, sales and value-added taxes; factor income; transfers from abroad) | YGDEF (1391) | 387–388 / 564–565 | **Same** for every tax in the SAM | Direct taxes, factor tax, import tariffs, sales tax (+ activity tax in 0.3): as the book. Export and value-added taxes: *not needed* (zero in the SAM). Infinity GEM also includes the SAM's transfers from enterprises and households to government. |
| 38 | Government expenditure: EG = Σ PQ·QG + Σ trnsfr(i,gov)·CPI | EGDEF (1402) | 389 / 566 | **Same** | Plus the SAM's government payments abroad. |

### System constraint block (p. 57–59)

| # | Book equation | IFPRI GAMS (line) | 0.2 / 0.3 line | Status | Note |
|---|---|---|---|---|---|
| 39 | Factor markets: Σ QF = QFS | FACEQUIL (1408) | 398 / 575 | **Same** | Plus the book's alternative closures: unemployment at a fixed real wage (lines 299–300 / 421–422) and capital fixed by sector (401 / 578). |
| 40 | Composite commodity markets: QQ = Σ QINT + Σ QH + QG + QINV + qdst + QT | COMEQUIL (1410) | 361–364, 395–396 / 511–515, 572–573 | **Same** | |
| 41 | Current account (foreign currency) | CURACCBAL (1413) | 402–404 / 579–581 | **Same** | Infinity GEM also handles re-exports (exports above domestic output, e.g. electronics) on both sides of the account, a Philippine-data feature (0.2 lines 127–135; 0.3 lines 184–192). |
| 42 | Government balance: YG = EG + GSAV | GOVBAL (1416) | 390 / 567 | **Same** | Government saving adjusts (fixed tax rates), one of the book's closures. |
| 43 | Direct tax rates: TINS = tins·(1+TINSADJ·tins01) + DTINS·tins01 | TINSDEF (1418) | 350 / 477 (fixed, scalable) | **Option absent** (partial) | Tax rates can be changed as a scenario, but the closure where they adjust to hold government saving fixed is not built. |
| 44 | Saving rates: MPS = mps·(1+MPSADJ·mps01) + DMPS·mps01 | MPSDEF (1421) | 352 / 479 | **Same** (partial) | MPSADJ (proportional change for households) is used in the investment-driven closure. The additive DMPS alternative is not built. |
| 45 | Savings–investment balance | SAVINVBAL (1427) | 405–407 / 582–584 | **Same** | Includes the WALRAS check variable, as in IFPRI's code; it is zero in every Infinity GEM solution. |
| 46 | Total absorption | TABSEQ (1431) | — | **Option absent** | Eq. 46–48 serve the book's "balanced" closure (investment and government shares of absorption fixed). Not built. |
| 47 | Investment/absorption ratio | INVABEQ (1435) | — | **Option absent** | As eq. 46. |
| 48 | Government consumption/absorption ratio | GDABEQ (1437) | — | **Option absent** | As eq. 46. |

### Tally (each of the 48 equations counted once)

| Status | Equations | Count |
|---|---|---|
| Same: the published equation, including dual forms, the sales-tax convention (eq. 4) and every tax present in the SAM (eq. 37) | 4, 5, 6, 7, 8, 9, 13, 14, 15, 16, 17, 21, 22, 23, 24, 25, 26, 28, 29, 30, 35, 36, 37, 38, 39, 40, 41, 42, 45 | 29 |
| Same under Infinity GEM's settings | 31, 32 | 2 |
| Same, partial (one of the book's two adjustment forms) | 44 | 1 |
| Not needed with the Philippine SAM | 19, 20 | 2 |
| Simplified (trade margins; home consumption) | 1, 2, 3, 18, 27, 34 | 6 |
| Special case (Cobb-Douglas by default; full LES as a 0.3 option) | 33 | 1 |
| Option absent (alternative technology, numeraire or closures) | 10, 11, 12, 43, 46, 47, 48 | 7 |
| **Total** | | **48** |

## 4. The numerical test that backs this up (check V2)

On 2 October 2026, IFPRI's GAMS model and Infinity GEM were both solved on the **same** condensed Philippine SAM (9 sectors, 10 household groups), for four test shocks under two closures.
- **IFPRI side:** set to Infinity GEM's choices (eq. 11–14 Leontief; eq. 33 with Cobb-Douglas parameters; home consumption moved to market). No IFPRI equation was changed.
- **Results:**
  - real GDP and real consumption agree within 0.005 percentage points;
  - 96% of 232 compared results agree within 0.1 pp;
  - the largest gaps (up to 0.51 pp, chemicals output under an import-price shock) are where the margins treatment differs (eq. 1–3, 27).
- Details: [`../../validation/ifpri/README.md`](../../validation/ifpri/README.md); comparison table: `../../validation/ifpri/out/comparison_infinity_gem_vs_ifpri.csv`.

**What V2 proves, and what it does not.**
- **It proves** that Infinity GEM's equations in the "Same" rows are the published ones in practice: an independent program, written by IFPRI, gives the same answers.
- **It does not test** the "Option absent" rows, because they are not in Infinity GEM, nor the full 41-sector model, because the free GAMS licence limits model size.

## 5. Features of IFPRI's Version 2.00 code that are not in the 2002 book

The GAMS code is Thurlow's 2005 extension, so it declares equations the book does not have. None is in the book's 48, and none is used in V2. Infinity GEM has its own, separately tested, dynamic module.
- several trading regions (`R`);
- nested factors (`CESVAPRD2`, `CESVAFOC2`);
- a growth-adjustment equation (`QVADEF`);
- labour-supply and wage equations (`LBRSUPPLY`, `WFREALEQ`, `WFDEF`, `RELWAGEQ`);
- sales-tax adjustment (`TQDEF`);
- a second government-share equation (`GDABEQ2`);
- the solver objective (`OBJEQ`).

## 6. Summary

| | Equations | Count |
|---|---|---|
| **As published** (same formula, or a mathematically equivalent form) | 4–9, 13–17, 21–26, 28–32, 35–42, 44, 45 | **32** |
| **Not needed** (the term is zero in the Philippine data) | 19, 20 | **2** |
| **Simplified** (trade margins charged on the composite good; no separate home consumption) | 1, 2, 3, 18, 27, 34 | **6** |
| **Special case** (Cobb-Douglas instead of LES by default; full LES as a 0.3 option) | 33 | **1** |
| **Optional features not built** (CES top nest, alternative numeraire, alternative closures) | 10, 11, 12, 43, 46, 47, 48 | **7** |
| **Total** | | **48** |

In words:
- Of the book's 48 equations, **32 are in Infinity GEM as published**, some in an equivalent form. **2 are not needed** with Philippine data.
- **6 are simplified**, all about trade margins or home consumption. **1 is a special case** by default (complete as a 0.3 option).
- **7 are optional features** of the book that Infinity GEM does not offer.
- The simplifications have a measured cost: at most 0.51 percentage points on one sector's output in the IFPRI test, and under 0.005 points on GDP and consumption. With the 0.3 margins option (7 Oct), the largest gap falls to 0.11 points and GDP and consumption agree within 0.0006.

## 7. Would a human Python programmer write it the same way?

**Infinity GEM's own Python lines have no non-AI documentation.** The explanation of how they follow the book (this concordance, the code comments, the guides) is AI-written. The non-AI evidence that they are right is numerical: IFPRI's own program gives the same answers (Section 4).

**Human programmers do write CGE models in Python, and they do it in the same way.** Three open-source, human-written Python CGE codes were saved on 5 Oct (reference copies, not distributed):

| Package | Author | What it is | Style |
|---|---|---|---|
| `pycge-master.zip` | Juan Fung (U.S. National Institute of Standards and Technology) and Charles Burtwistle | Its model file says: "Pyomo port of stdcge.gms from GAMS Model Library", created **10 July 2017**. This is a human translating a GAMS CGE into Python, years before AI coding assistants. It contains **both** of Hosoe et al.'s models: the simple CGE (`splcge`) and the **standard CGE** (`stdcge`, 24 equations), with their data (checked 8 Oct 2026). | Equations declared one by one, as in GAMS (Pyomo) |
| `CGE-master.zip` | PSLmodels (Policy Simulation Library, an open-source catalogue of policy models) | Its README says it is "based off of the simplest CGE model" of Hosoe, Gasawa and Hashimoto (2010), *Textbook of Computable General Equilibrium Modeling*. Its code (`open_cge`, 35 equations) also has imports and exports (Armington, CET), taxes, a balance of payments and foreign capital, i.e. the structure of Hosoe's standard model plus extensions, on its own 4-sector SAM (corrected 8 Oct 2026) | **Same as Infinity GEM:** each equation is a NumPy function returning its error; the whole system is solved with SciPy's `optimize.root` |
| `cge_modeling-0.0.6.tar.gz` | Jesse Grabowski | A general CGE toolkit using automatic differentiation (PyTensor) | Symbolic equations, compiled |

**Example: the same equation (book eq. 8, zero profit with fixed input coefficients) written three ways:**
- Book (p. 51): PA·(1−ta)·QA = PVA·QVA + PINTA·QINTA, with QVA = iva·QA and PINTA = Σ PQ·ica.
- PSLmodels, human-written (`open_cge/firms.py`, function `eqpz`): `pz = ay * py + (ax * pq).sum(axis=0)`, i.e. output price = value-added share × value-added price + Σ input coefficients × input prices.
- Infinity GEM (0.2 line 330): `ZP = PA - (self.ica.T @ PQ + self.iva * PVA)`. The same equation, written as "price minus unit cost = 0". (0.3, line 457: `ZP = PA * (1 - ta) - (ica.T @ PQ + self.iva * PVA)`, the same with the activity tax, which is zero in the 2023 SAM.)

The lines are not character-for-character identical, and no two programmers write identical code. The mathematics is the same, and the method is the same: NumPy arrays, residual equations, SciPy's root-finder.

**What this shows, and what it does not.**
- Python CGE models are established, human practice, including direct translations of GAMS models.
- Infinity GEM's architecture is one that human modellers use.
- The human Python ports found so far are of the **Hosoe et al.** textbook model, not of the IFPRI/Lofgren model. My search found no human-written Python port of the IFPRI standard model; the model is distributed in GAMS. Not finding one is not proof that none exists.

**Where to look for more evidence:**
- **GitHub:** search "computable general equilibrium python", "stdcge", "IFPRI standard CGE", "Lofgren CGE".
- **PSLmodels.org** (catalogue) and **PyPI** (Python packages).
- The **GAMS Model Library** (`stdcge`, `splcge`: Hosoe et al.'s models, which these ports translate).
- **AGRODEP** (agrodep.org, IFPRI's African Growth and Development Policy modelling consortium), which distributes IFPRI's standard model files.
- **Julia/MPSGE** work by the WiNDC group (University of Wisconsin), which hosts the copy of IFPRI's code we used.


**Done since (8 Oct 2026):** the stronger test below was run against pycge's port of Hosoe's *standard* model. Infinity GEM agrees to machine precision (largest gap 7e-13) on the textbook's tariff-abolition experiment: [`../../validation/hosoe/README.md`](../../validation/hosoe/README.md); benchmark 7. The two options the textbook model needs (government and investment spending as fixed value shares, `gov="cd"`, `inv="value_shares"`) and the exact Cobb-Douglas case are **in Infinity GEM's engine since 0.3.1** (off by default; check V5). Rerun on the released 0.3.1 engine on 8 Oct 2026, 8:45 PM: the same agreement (largest gap 6.8e-13). Note: Hosoe's "standard CGE" and IFPRI's "standard CGE" (this map) are different models that share a name.

**The test, as first proposed (now done; see above).** Run Infinity GEM's engine on Hosoe et al.'s textbook SAM. Compare with the GAMS file (`stdcge.gms`; the GAMS Model Library publishes the code, not results) and with the human-written Python ports. Agreement would add two more independent, human-written implementations to the evidence. (Downloaded code would be run read-only, in a separate folder.)

## 8. Still to do in Phase 1

- [ ] Get IFPRI's **official** standard-model files from AGRODEP (agrodep.org, "IFPRI Standard Model", node 108; the book's page is node 616) and confirm by checksum that our GitHub copy matches. If the site needs a login or blocks scripts, save them by hand.
- [ ] Add the main-text page (pp. 18–40) for each equation, next to the appendix page.
- [ ] Have a human reader check ten random rows (using Section 2). Record who checked what and when.
- [x] Produce a PDF and a website version (Phase 4), 7 Oct (not included).
- [x] Phase 3, home consumption (eq. 18, 34): option `home="separate"`, check V4: matches IFPRI's model run with home consumption kept (GDP and consumption within 0.0006 pp); released since 0.3.1.
- [x] Phase 3, trade margins: 0.3 option `margins="split"` (book eq. 1, 3, 27), check V3: largest gap with IFPRI 0.51 → 0.11 pp; real GDP and consumption within 0.0006 pp. Opt-in; released since 0.3.0.
