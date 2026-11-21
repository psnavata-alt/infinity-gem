# Verification, Phase 1: Infinity GEM's CGE equations against the published IFPRI model

**What this is.** A line-by-line map of all 48 equations of the IFPRI standard CGE model, as published in a book, to:
- IFPRI's own computer code (GAMS);
- Infinity GEM's code (Python).

It lets anyone check, without knowing Python, that each equation in Infinity GEM is the published one, or see exactly where and why it differs.

**Prepared:** 7 October 2026, with an AI coding assistant. **This document is AI-written: verify it with the steps in Section 2, not on trust.**

**Line numbers refreshed on 13 November 2026, about 2:30-3:00 PM, for Infinity GEM 0.3.13 (live) and 0.4.0 (development copy, to be merged into live on 13 Nov).** Both use the same `infinity_gem/cge.py`: 1,435 lines, SHA-256 `812061F4E2A4F6850E47DE28E6A554AE9D377E60C3AA95FFFD4FA7C0AC66824E` (the live and development files compared byte for byte on 13 Nov 2026 at 2:27 PM). How they were checked:
- every Infinity GEM line was found again by reading the code (the code's comments name the book's equations in many places);
- a script then confirmed that every line number cited in Sections 2, 3 and 3a (each single line, and the first and last line of each range) holds the code text it is cited for: 156 of 156 lines (153 in `cge.py`, 1 in `sam.py`, 2 in `settings.py`);
- the code on those lines was compared with the lines the 8 Oct map gave for 0.3.1 (Section 9), in the 0.3.1 backup;
- IFPRI's GAMS lines were checked against `1DMODEL_PH.GMS` (1,857 lines, SHA-256 `731FACDF2165CC3433F234E3CA37D829B3F01BC4B7DCADB278B764CABE67B6E5`): all equation names are at the lines given since 7 Oct; none changed;
- the book's pages were checked against the text of the PDF: equations 1-5 are on printed p. 50, 6-10 on p. 51, 11-15 on p. 52, 16-20 on p. 53, 21-25 on p. 54, 26-30 on p. 55, 31-35 on p. 56, 36-39 on p. 57, 40-44 on p. 58 and 45-48 on p. 59.

The line numbers of the earlier versions (0.2 and 0.3.1) are kept in Section 9.

---

## 1. The three sources

| Source | Who wrote it | Where it is |
|---|---|---|
| **The book:** Lofgren, H., R. L. Harris and S. Robinson (2002), *A Standard Computable General Equilibrium (CGE) Model in GAMS*, Microcomputers in Policy Research 5, International Food Policy Research Institute (IFPRI), Washington, D.C. | IFPRI economists (published 2002) | IFPRI's website (Microcomputers in Policy Research 5; not redistributed here). All 48 equations are summarised in the book's appendix table, **printed pages 50–59** (PDF pages 59–68). They are derived one by one in the main text, printed pages 18–40. |
| **IFPRI's code:** *Extended Standard Recursive Dynamic CGE Model, Version 2.00* (July 2005; Thurlow's extension of the book's model), GAMS, GNU GPL v2 | IFPRI economists | [`../../validation/ifpri/gams_ph/1DMODEL_PH.GMS`](../../validation/ifpri/gams_ph/1DMODEL_PH.GMS). Our copy is marked as altered: only the data file name was changed and a results block appended at the end, so the equation lines are IFPRI's. The unaltered original is in the GitHub repository `uw-windc/IFPRI_model`. **Provenance caveat:** taken from a GitHub copy (`uw-windc/IFPRI_model`), not from IFPRI's own website; to be checked against IFPRI's official files. |
| **Infinity GEM's code:** `infinity_gem/cge.py` | An AI coding assistant, 26 Sept 2026, following the book; **not** translated from the GAMS code, which was obtained only on 2 Oct for testing | **Live version 0.3.13 and development version 0.4.0** (13 Nov 2026; the same file): [`../../infinity_gem/cge.py`](../../infinity_gem/cge.py) (1,435 lines). It has the activity tax and these options, all **off in the code's own defaults**: LES demand, IFPRI-style margins, home consumption as own produce, the Hosoe textbook options for government and investment demand, and the project-specific short-run options listed in Section 3a. Version 0.2, behind the results published up to 7 Oct 2026: an archived copy, not included (574 lines; the default settings reproduce its results exactly, check R0). |

**Code defaults and named settings.** The statuses below describe `cge.py` as it runs with no options. Infinity GEM's runs normally use a *named setting* (`infinity_gem/settings.py`), which switches some options on. The settings "0.3 recommended" and "0.4 recommended" (the default setting since 13 Nov 2026) both build the one-year CGE with the LES and IFPRI-style margins (`settings.py` line 190: `les=..., margins="split", wage="nominal"`). Under them, eq. 1, 3, 27 and 33 follow the book (see the Status column). "0.2 published" uses the code defaults.

**Why the formulas sometimes look different but are the same.** The book writes production as a *production function* (output from inputs) plus a *first-order condition* (how much of each input to hire). Infinity GEM writes the equivalent *unit-cost function* (the cost of one unit of output at given input prices) plus the *input demands* derived from it. Economists call this the "dual" form. Both give the same quantities and prices. Check V2 (Section 4) shows they do, numerically.

## 2. How to check any row yourself (no programming needed)

1. **Book:** open the book PDF and go to the printed page shown (PDF page = printed page + 9). In Edge or Chrome, type the PDF page number in the page box.
2. **IFPRI code:** right-click `1DMODEL_PH.GMS` → *Open with* → Notepad. Press **Ctrl+G** and type the line number. (If Ctrl+G does nothing: *Format* menu → untick *Word Wrap*.) The equation name is in capitals, e.g. `PMDEF`.
3. **Infinity GEM code:** open `cge.py` the same way (Notepad, Ctrl+G, line number). The comments next to each line say in English what it computes. **First check the file is the one mapped here:** press Ctrl+End; the status bar at the bottom of Notepad (*View* → *Status bar* if hidden) should show **Ln 1436**, an empty line just after the last line of code, line 1435, `return S`. If it shows another number, the code has changed since 13 Nov 2026 and the lines may have moved: find the line instead with **Ctrl+F** and the code text quoted in the table below (for the ten spot-check equations) or in the Note column.
4. Compare the three. The **Status** column says what to expect; the **Note** column explains any difference.

**The ten spot-check equations of `CHECK_LOG.md`, with the text to look for** (cge.py of 13 Nov 2026):

| Book eq. | Book page | IFPRI line | cge.py line | Text on that cge.py line (Ctrl+F) |
|---|---|---|---|---|
| 1 Import price | 50 | 1256 `PMDEF` | 666 (and 694) | `PM = pwm * EXR * (1 + tm)` (694: `PM = PM + self.icx * PTRC`) |
| 5 Marketed output value | 50 | 1265 `PXDEF` | 724 | `PX[m] = (PE[m] * QE[m] + PDS[m] * QDs[m])` |
| 8 Activity revenue and costs | 51 | 1271 `PVADEF` | 751 (with 744) | `ZP = PA * (1 - ta) - UCOST` (744: `UCOST = ica.T @ PQ + self.iva * PVA`) |
| 15 Value-added function | 52 | 1301 `CESVAPRD` | 733–740 | `PVA = terms.sum(axis=0) ** (1 / (1 - sig_))` (line 738) |
| 21 CET function | 54 | 1330 `CET` | 705–712 | `denom[both] = self.at[both] * (self.gam[both]` (line 710) |
| 24 Armington function | 54 | 1339 `ARMINGTON` | 875–876 (896–897) | `PARM[mix] = (self.dq[mix] * PM[mix]` |
| 29 Institutional factor incomes | 55 | 1364 `YIFDEF` | 817–818 | `YIF = self.shif * dist[None, :]` (line 818) |
| 33 Household consumption demand | 56 | 1377 `HMDEM` | 833 (LES: 836) | `QH = self.beta * EH[None, :]` (836: `QH = g_ + mb_ * (EH - PQ @ g_)`) |
| 37 Government revenue | 57 | 1391 `YGDEF` | 931–932 | `YG = (self.te * YE + (tins * YH).sum()` |
| 41 Current account balance | 58 | 1413 `CURACCBAL` | 970–974 | `res.append(np.array([(fcu_out - fcu_in)` (line 974) |

## 3. The concordance (all 48 equations)

Status key:
- **Same:** the book's equation, possibly in the equivalent dual form.
- **Same (cond.):** gives identical results under the settings Infinity GEM uses; differs only under options Infinity GEM does not use.
- **Not needed:** the book's term is zero in the Philippine SAM, so it would change nothing.
- **Simplified:** Infinity GEM treats this more simply than the book.
- **Option absent:** an alternative the book offers that Infinity GEM does not have.
- **Special case:** Infinity GEM uses a restricted version.
- **the project-specific (option):** an addition of Infinity GEM's own that replaces or changes the book's equation when it is switched on (Section 3a). It is not counted in the tally: each book equation keeps the status it has with the option off.

"cge.py line" = the line in `infinity_gem/cge.py` of Infinity GEM 0.3.13 / 0.4.0 (13 Nov 2026). Where a row gives several lines, the first is the default code and the others are options (e.g. "split margins", "LES") or the calibration (where the parameters are computed from the SAM). Lines in the 0.2 and 0.3.1 code: Section 9.

**Statuses re-confirmed on 13 Nov 2026 against the code as it is now.** No status changed. The code of the book's equations is as it was in 0.3.1 (compared line by line with the 0.3.1 backup, `Infinity GEM - Evolution\Backups before each merge\Infinity GEM 0.3.1 BACKUP 9Oct2026 (before 0.3.2 merge)\infinity_gem\cge.py`). The only differences are terms that are zero unless an option or a scenario key is used (lines 822, 934 and 972: `sav_add`, `grow_out_add`; 943: hoarded labour `QFH`; 927–929 and 970: the oil and peso pass-through keys; 696–697: `wage="nominal"`), and eq. 8, now written in two lines. Three things are new or are now stated more precisely:
- the code's own defaults are unchanged (Cobb-Douglas demand, margins on the composite good); the named settings "0.3 recommended" and "0.4 recommended" switch on the LES and IFPRI-style margins, so eq. 1, 3, 27 and 33 are as in the book under them (this was already true of "0.3 recommended" on 8 Oct, but the earlier text did not say so);
- options added since 0.3.1 (0.3.4 to 0.3.13) change some equations when switched on; "0.4 recommended" switches several of them on in the short-run years of its dynamic runs (Section 3a);
- eq. 8 is written in two lines now (unit cost on line 744, zero profit on line 751); the formula is the same.

### Price block (book appendix p. 50–51)

| # | Book equation | IFPRI GAMS (line) | Infinity GEM 0.3.13 / 0.4.0 (13 Nov 2026), infinity_gem/cge.py lines | Status | Note |
|---|---|---|---|---|---|
| 1 | Import price: PM = pwm·(1+tm)·EXR + Σ PQ·icm | PMDEF (1256) | 666; 693–694 with split margins | **Simplified** (code default); **Same** with `margins="split"` (on in "0.3/0.4 recommended") | Infinity GEM has the world price, tariff and exchange rate. With the default margins, trade and transport margins on imports (icm) are not added here: they are charged on the composite good (eq. 4, 27). This is the one structural difference; it explains the largest V2 gap (0.51 pp). The option `margins="split"` (7 Oct; released since 8 Oct) implements the book's version: gap falls to 0.11 pp (check V3). The project-specific options that change PM: incomplete peso pass-through (`erpt`, 664–665) and the within-year oil pass-through (`oil_pass`, 667–672); Section 3a. |
| 2 | Export price: PE = pwe·(1−te)·EXR − Σ PQ·ice | PEDEF (1258) | 673 | **Simplified** | No export tax (te) and no export margin. The Philippine SAM has no export tax, so te is *not needed*. The export margin is the simplification above; the split-margins option adds none either, because the SAM records no margins on exports (docstring, line 134). |
| 3 | Demand price of domestic goods: PDD = PDS + Σ PQ·icd | PDDDEF (1260) | 871 (PDD = PDS); 892 with split margins | **Simplified** (code default); **Same** with `margins="split"` | Same margin simplification as eq. 1. As in the book with `margins="split"`. |
| 4 | Absorption: PQ·(1−tq)·QQ = PDD·QD + PM·QM | PQDEF (1262) | 911 (residual: 941) | **Same** (different tax convention) | Infinity GEM writes PQ = (1+tq)·(Armington price + margin). Its sales-tax rate is defined on the pre-tax value, the book's on the tax-inclusive value. Both are calibrated to the same SAM tax payments. Margins enter here with the default margins (see eq. 1). |
| 5 | Marketed output value: PX·QX = PDS·QD + PE·QE | PXDEF (1265) | 724 | **Same** | |
| 6 | Activity price: PA = Σ PXAC·θ | PADEF (1267) | 725 | **Same** | Infinity GEM uses one producer price per commodity (PXAC = PX), exact here because each commodity has one producing activity (eq. 19). |
| 7 | Intermediate input price: PINTA = Σ PQ·ica | PINTADEF (1269) | 744 (inside the unit cost) | **Same** | Written inside eq. 8: `ica.T @ PQ` on line 744. |
| 8 | Activity revenue and costs: PA·(1−ta)·QA = PVA·QVA + PINTA·QINTA | PVADEF (1271) | 751 (unit cost: 744; activity tax: 741, calibrated on 338) | **Same** (code default) | Zero profit per unit of output, line 751: `ZP = PA * (1 - ta) - UCOST`. Activity tax (ta): *not needed* with the 2023 SAM (none recorded); included for the 2018 SAM. In the short-run (Keynesian) closure only, two the project-specific options replace zero profit for listed activities: downward-sticky prices (`pricing="sticky"`, 793–801) and markup pricing (`pricing="markup"`, 802–814 and 912–922), on in "0.4 recommended"'s short-run years; Section 3a. |
| 9 | Consumer price index: CPI = Σ PQ·cwts (fixed) | CPIDEF (1273) | 695 (numeraire: 979; weights: 531) | **Same** | The CPI is the numeraire (fixed), as in the book. In the short-run (Keynesian) closure the exchange rate is fixed instead (643–644), a closure the book also describes. |
| 10 | Producer price index for non-traded output: DPI = Σ PDS·dwts | DPIDEF (1275) | — | **Option absent** | Only needed if DPI is chosen as numeraire instead of the CPI. |

### Production and trade block (p. 52–55)

| # | Book equation | IFPRI GAMS (line) | Infinity GEM 0.3.13 / 0.4.0 (13 Nov 2026), infinity_gem/cge.py lines | Status | Note |
|---|---|---|---|---|---|
| 11 | CES activity production function (value added vs intermediates) | CESAGGPRD (1283) | — | **Option absent** | The book lets each activity use either a CES top nest (eq. 11–12) or fixed proportions (eq. 13–14). Infinity GEM uses fixed proportions (Leontief) for all; V2 ran IFPRI's model the same way. The option `energy_nest` (0.3.11; 353–367, 746–750) is a different nest, value added with energy (MANAGE-WB), not the book's eq. 11–12; it is off by default and in no named setting. |
| 12 | CES value-added/intermediate ratio | CESAGGFOC (1287) | — | **Option absent** | As eq. 11. |
| 13 | Leontief demand for value added: QVA = iva·QA | LEOAGGVA (1296) | 745 | **Same** | |
| 14 | Leontief demand for intermediates: QINTA = inta·QA | LEOAGGINT (1294) | 860 (with eq. 17) | **Same** | Combined with eq. 17 into one step (QINT = ica·QA). |
| 15 | CES value-added function: QVA = αva·(Σ δ·QF^−ρ)^−1/ρ | CESVAPRD (1301) | 733–740 | **Same** (dual) | Infinity GEM computes the value-added price from factor prices (unit-cost form, line 738). αva is the productivity term `tfp` (line 740). Elasticity exactly 1 uses the exact Cobb-Douglas form (lines 734, 739). |
| 16 | Factor demand: WF·WFDIST = PVA·(1−tva)·QVA·(…)·δ·QF^(−ρ−1) | CESVAFOC (1307) | 754 | **Same** (dual) | WFDIST (sector wage differentials) is 1 at the base, as in the book when factors are measured in value units. With capital fixed by sector, rents differ by sector (line 730), as in the book's "activity-specific factor" closure; land likewise with `land="fixed"` (line 732). Value-added tax (tva): *not needed* (none in the SAM). With markup pricing (Section 3a) labour per unit of output is fixed instead (756–765). |
| 17 | Disaggregated intermediate demand: QINT = ica·QINTA | INTDEM (1319) | 860 | **Same** | |
| 18 | Commodity production and allocation: QXAC + Σ QHA = θ·QA | COMPRDFN (1321) | 703; 837–847 with `home="separate"` | **Simplified** (code default and named settings) | No home consumption (QHA) by default: the SAM's own-consumption flows are moved into market purchases before calibration (`sam.py`, `move_home_consumption_to_market`, line 184). V2 used the same treatment for IFPRI's model. Option `home="separate"` (released since 0.3.1, 8 Oct 2026; off by default and in no named setting) applies the book's eq. 18 and 34 (QHA on line 841, marketed output on line 847): against IFPRI's own model run with home consumption kept, GDP and consumption agree within 0.0006 pp and home consumption within 0.001 pp (check V4, `validation/ifpri_home/`). Effect on September 2026 results: negligible. |
| 19 | Output aggregation (CES across activities) | OUTAGGFN (1324) | 703 (sum) | **Not needed** | Matters only if two or more activities produce the same commodity. In the 2023 SAM **none does** (checked 7 Oct), so the book's equation reduces to Infinity GEM's sum. |
| 20 | First-order condition for output aggregation | OUTAGGFOC (1327) | — | **Not needed** | As eq. 19. |
| 21 | CET between exports and domestic sales | CET (1330) | 705–712 (parameters: 422–437) | **Same** | With markup pricing (Section 3a), a markup activity's exports and home sales are found from the same CET in another order (717–721). |
| 22 | Export–domestic supply ratio | ESUPPLY (1333) | 707 (and 712) | **Same** | ω = 1/(ρ−1) in the book's notation. The share term is computed in a numerically safer way (the development history (not included)). |
| 23 | Output when a good is only exported or only sold at home: QX = QD + QE | CET2 (1336) | 713–716 | **Same** | |
| 24 | Armington composite supply | ARMINGTON (1339) | 875–876; 896–897 with split margins (parameters: 439–460) | **Same** (dual) | Composite price written as a unit-cost function. |
| 25 | Import–domestic demand ratio | COSTMIN (1342) | 877–879; 898–899 and 909–910 with split margins | **Same** | Import and domestic demands from the same CES. |
| 26 | Composite supply when a good is only imported or only domestic: QQ = QD + QM | ARMINGTON2 (1345) | 880–885; 900–905 with split margins | **Same** | |
| 27 | Demand for trade and transport services: QT = Σ (icm·QM + ice·QE + icd·QD) | QTDEM (1348) | 865–868; 906–908 with split margins | **Simplified** (code default); **Same** with `margins="split"` (on in "0.3/0.4 recommended"), except export margins (none in the SAM, eq. 2) | By default Infinity GEM charges margins per unit of the composite good, with one fixed mix of margin services. Same simplification as eq. 1–3. As in the book (domestic and import margins) with `margins="split"`. |

### Institution block (p. 55–57)

| # | Book equation | IFPRI GAMS (line) | Infinity GEM 0.3.13 / 0.4.0 (13 Nov 2026), infinity_gem/cge.py lines | Status | Note |
|---|---|---|---|---|---|
| 28 | Factor income: YF = Σ WF·WFDIST·QF | YFDEF (1362) | 788, 816 | **Same** | Infinity GEM also adds factor income received from abroad (a SAM cell, line 816) before distributing it. With paid labour hoarding (Section 3a), hoarded workers' wages are moved from capital to labour income (789–792); total factor income is unchanged. |
| 29 | Institutional factor incomes: YIF = shif·[(1−tf)·YF − trnsfr(row,f)·EXR] | YIFDEF (1364) | 817–818 | **Same** | |
| 30 | Income of households and enterprises: YI = Σ YIF + Σ TRII + trnsfr(gov)·CPI + trnsfr(row)·EXR | YIDEF (1367) | 821 (enterprises), 826 (households) | **Same** | Line 826 also adds the scenario key `trg_h_add` (extra real transfers, ₱ bn; default 0). |
| 31 | Transfers between institutions: TRII = shii·(1−MPS)·(1−TINS)·YI | TRIIDEF (1371) | 821–826 | **Same (cond.)** | Infinity GEM makes enterprise-to-household transfers proportional to enterprise income (`self.she * YE`, line 826). This equals the book whenever the enterprise tax and saving rates are fixed, as in all Infinity GEM closures. V2 fixed IFPRI's enterprise saving rate the same way. Enterprise saving (line 822) also takes the scenario key `sav_add` (default 0; see eq. 38). |
| 32 | Household consumption spending: EH = (1−Σ shii)·(1−MPS)·(1−TINS)·YH | EHDEF (1374) | 827–831 | **Same (cond.)** | Same SAM flows, ordered slightly differently: Infinity GEM deducts households' payments to government and abroad before saving. Identical at the base and under fixed rates. |
| 33 | Household demand, Linear Expenditure System (LES) | HMDEM (1377) | 832–833 (Cobb-Douglas); 834–836 (LES; parameters: 491–516) | **Special case** (code default); **Same** with `les=` (on in "0.3/0.4 recommended") | Code default: Cobb-Douglas, the LES with no subsistence quantities (book p. 32). The `les=` option (0.3) is the full LES for marketed goods (Briones et al. 2023 parameters); it is not combined with home consumption yet (line 286), so the book's home-good terms in eq. 33 do not apply. |
| 34 | Household demand for home-produced goods | HADEM (1381) | 837–841 with `home="separate"` | **Simplified** (code default and named settings) | No home consumption (see eq. 18). Option `home="separate"` (released since 0.3.1, off by default): as in the book (see eq. 18). |
| 35 | Investment demand: QINV = IADJ·qinv | INVDEM (1386) | 859 (IADJ: 648–657) | **Same** | Line 857 is the Hosoe option `inv="value_shares"` (check V5). With `closure="interest"` (0.3.11), IADJ moves with a real interest rate (652–655); Section 3a. |
| 36 | Government consumption: QG = GADJ·qg | GOVDEM (1389) | 855 | **Same** | GADJ is the scenario setting `qg_scale`. Line 853 is the Hosoe option `gov="cd"` (check V5). |
| 37 | Government revenue (direct, factor, activity, import, export, sales and value-added taxes; factor income; transfers from abroad) | YGDEF (1391) | 931–932 (the taxes: 925–930) | **Same** for every tax in the SAM | Direct taxes, factor tax, import tariffs, sales tax and activity tax: as the book. Export and value-added taxes: *not needed* (zero in the SAM). Infinity GEM also includes the SAM's transfers from enterprises and households to government. With the within-year oil pass-through (Section 3a), the tariff line is net of what the government absorbs at the border (927–929). |
| 38 | Government expenditure: EG = Σ PQ·QG + Σ trnsfr(i,gov)·CPI | EGDEF (1402) | 933–934 | **Same** | Plus the SAM's government payments abroad. Line 934 adds two scenario keys, diverted public money saved or sent abroad (`sav_add`, `grow_out_add`; 0.3.6; default 0). |

### System constraint block (p. 57–59)

| # | Book equation | IFPRI GAMS (line) | Infinity GEM 0.3.13 / 0.4.0 (13 Nov 2026), infinity_gem/cge.py lines | Status | Note |
|---|---|---|---|---|---|
| 39 | Factor markets: Σ QF = QFS | FACEQUIL (1408) | 943 | **Same** | Plus the book's alternative closures: unemployment at a fixed wage (696–697; indexed to the CPI by default, fixed in pesos with `wage="nominal"`), capital fixed by sector (945–950) and land fixed by activity (967–969). The project-specific options: capital vintages (951–966), paid labour hoarding (766–785; the hoarded workers `QFH` enter line 943) and a smooth employment cap (698–700, 982–985); Section 3a. |
| 40 | Composite commodity markets: QQ = Σ QINT + Σ QH + QG + QINV + qdst + QT | COMEQUIL (1410) | 860–868 (907–908 with split margins); 940 | **Same** | Demand D (line 864) plus margin services gives QQ (868 or 908); line 940 clears the market for domestic output. |
| 41 | Current account (foreign currency) | CURACCBAL (1413) | 970–974 | **Same** | Infinity GEM also handles re-exports (exports above domestic output, e.g. electronics) on both sides of the account, a Philippine-data feature (lines 389–397). Line 972 adds the scenario key `grow_out_add` (default 0; see eq. 38); line 970 the peso pass-through option (Section 3a). |
| 42 | Government balance: YG = EG + GSAV | GOVBAL (1416) | 935 | **Same** | Government saving adjusts (fixed tax rates), one of the book's closures. |
| 43 | Direct tax rates: TINS = tins·(1+TINSADJ·tins01) + DTINS·tins01 | TINSDEF (1418) | 827 (fixed, scalable; rates: 483) | **Option absent** (partial) | Tax rates can be changed as a scenario (`tins_scale`), but the closure where they adjust to hold government saving fixed is not built. |
| 44 | Saving rates: MPS = mps·(1+MPSADJ·mps01) + DMPS·mps01 | MPSDEF (1421) | 829 (rates: 487; MPSADJ: 648–657) | **Same** (partial) | MPSADJ (proportional change for households) is used in the investment-driven closure. The additive DMPS alternative is not built. |
| 45 | Savings–investment balance | SAVINVBAL (1427) | 975–977 | **Same** | Includes the WALRAS check variable, as in IFPRI's code; it is zero in every Infinity GEM solution. |
| 46 | Total absorption | TABSEQ (1431) | — | **Option absent** | Eq. 46–48 serve the book's "balanced" closure (investment and government shares of absorption fixed). Not built. |
| 47 | Investment/absorption ratio | INVABEQ (1435) | — | **Option absent** | As eq. 46. |
| 48 | Government consumption/absorption ratio | GDABEQ (1437) | — | **Option absent** | As eq. 46. |

### Tally (each of the 48 equations counted once; code defaults)

| Status | Equations | Count |
|---|---|---|
| Same: the published equation, including dual forms, the sales-tax convention (eq. 4) and every tax present in the SAM (eq. 37) | 4, 5, 6, 7, 8, 9, 13, 14, 15, 16, 17, 21, 22, 23, 24, 25, 26, 28, 29, 30, 35, 36, 37, 38, 39, 40, 41, 42, 45 | 29 |
| Same under Infinity GEM's settings | 31, 32 | 2 |
| Same, partial (one of the book's two adjustment forms) | 44 | 1 |
| Not needed with the Philippine SAM | 19, 20 | 2 |
| Simplified (trade margins; home consumption) | 1, 2, 3, 18, 27, 34 | 6 |
| Special case (Cobb-Douglas by default; full LES as an option) | 33 | 1 |
| Option absent (alternative technology, numeraire or closures) | 10, 11, 12, 43, 46, 47, 48 | 7 |
| **Total** | | **48** |

**Under the named settings "0.3 recommended" and "0.4 recommended"** (split margins and the LES on): eq. 1, 3, 27 and 33 move to "Same", so 36 are as published, 3 simplified (2, 18, 34), 2 not needed and 7 options absent (total 48).

## 3a. The project-specific options that change a book equation when switched on

These are additions of Infinity GEM's own, each opt-in; the "Check" column names the check-suite test where the code names one ("—": none named in `cge.py`). With them off, every equation above is as stated. They are not in the book or in IFPRI's code, so a checker comparing the book with `cge.py` should expect them to differ. "0.4 recommended" (the default setting since 13 Nov 2026) switches on the ones marked "yes" in the **short-run years of its dynamic runs only** (`settings.py`, `OPTION_C_04`); its one-year CGE is that of "0.3 recommended".

| Option (version) | What it does | Book eq. affected | cge.py lines | Check | On in "0.4 recommended"? |
|---|---|---|---|---|---|
| `wage="nominal"` (0.3.4) | Fixed-wage labour paid a fixed peso wage within the period, not one indexed to the CPI | 39 (closure) | 696–697 | — (`validation/labour_closures/`) | yes (also "0.3 recommended") |
| `land="fixed"` (0.3.7) | Each activity keeps its land within the period | 16, 39 | 731–732, 967–969 | — | no (drought runs only) |
| `pricing="sticky"` (0.3.8) | Prices of listed activities rigid downward | 8 | 793–801 | — | no ("sticky falls" are applied through markup pricing) |
| `pricing="markup"` (0.3.13) | Non-farm home prices set as a markup over unit variable cost; labour per unit of output fixed; capital earns the residual | 8, 16, 21 | 717–721, 756–765, 802–814, 912–922 | MK1, MG1, MF1 | yes |
| `hoarding=` (0.3.11) | Paid labour hoarding: part of a fall in labour demand stays employed and paid | 28, 39 | 766–785, 789–792, 943 | — | yes |
| `labour_cap=True` (0.3.13) | Employment of fixed-wage labour capped at its supply, by a smooth condition | 39 | 698–700, 982–985 | EC1 | yes ("smooth" cap) |
| `oil_pass` shock key (0.3.13) | Only a share of a move of the world oil price in pesos reaches domestic prices within the year; the government absorbs the rest at the border | 1, 37 | 667–672, 927–929 | OP1 | yes |
| `erpt` shock key (0.3.13) | Incomplete pass-through of the peso to import prices | 1, 41 | 664–665, 970 | ER1 | no |
| `capital="vintage"` (0.3.12) | Old capital by activity plus a mobile pool of new capital | 16, 39 | 951–966 | VN1 | no |
| `closure="interest"` (0.3.11) | A real interest rate clears savings and investment | 35, 44 | 652–655 | IR1 | no |
| `energy_nest` (0.3.11) | Value added and energy in one CES bundle | 7, 8, 13, 14 | 353–367, 746–750 | — | no |

Two further parts of "0.4 recommended" act through shock keys that the dynamic model (`infinity_gem/dynamic.py`) sets each short-run year, not through new equations in `cge.py`: the short-run consumption rule (`sr_consumption`, a hand-to-mouth share, which sets the saving-rate adjustment of eq. 44) and the BSP policy rule (`infinity_gem/monetary.py`, which moves investment, eq. 35). They are outside this map.

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
- **It does not test** the "Option absent" rows, because they are not in Infinity GEM, nor the full 41-sector model, because the free GAMS licence limits model size, nor the project-specific options of Section 3a, which have their own checks.

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
| **Special case** (Cobb-Douglas instead of LES by default; full LES as an option) | 33 | **1** |
| **Optional features not built** (CES top nest, alternative numeraire, alternative closures) | 10, 11, 12, 43, 46, 47, 48 | **7** |
| **Total** | | **48** |

In words:
- Of the book's 48 equations, **32 are in Infinity GEM as published**, some in an equivalent form. **2 are not needed** with Philippine data.
- **6 are simplified**, all about trade margins or home consumption. **1 is a special case** by default (complete as an option).
- **7 are optional features** of the book that Infinity GEM does not offer.
- These counts are for the code's own defaults. Under the settings Infinity GEM's runs normally use ("0.3 recommended", and "0.4 recommended" since 13 Nov 2026), the margins and LES options are on: **36 are as published** and 3 simplified (eq. 2 and the two home-consumption equations).
- The simplifications have a measured cost: at most 0.51 percentage points on one sector's output in the IFPRI test, and under 0.005 points on GDP and consumption. With the margins option (7 Oct), the largest gap falls to 0.11 points and GDP and consumption agree within 0.0006.

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
- Infinity GEM (0.2 line 330): `ZP = PA - (self.ica.T @ PQ + self.iva * PVA)`. The same equation, written as "price minus unit cost = 0". In 0.3.13 / 0.4.0 it is two lines, the same with the activity tax (zero in the 2023 SAM): line 744, `UCOST = ica.T @ PQ + self.iva * PVA`, and line 751, `ZP = PA * (1 - ta) - UCOST`.

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
- [ ] Have a human reader check ten rows (e.g. an outside reviewer, using Section 2; the ten of `CHECK_LOG.md` are listed in Section 2 with the text to look for). Record who checked what and when. Line numbers refreshed for this on 13 Nov 2026.
- [x] Produce a PDF and a website version (Phase 4), 7 Oct (not included).
- [x] Phase 3, home consumption (eq. 18, 34): option `home="separate"`, check V4: matches IFPRI's model run with home consumption kept (GDP and consumption within 0.0006 pp); released since 0.3.1.
- [x] Phase 3, trade margins: option `margins="split"` (book eq. 1, 3, 27), check V3: largest gap with IFPRI 0.51 → 0.11 pp; real GDP and consumption within 0.0006 pp. Opt-in; released since 0.3.0; on in the named settings "0.3 recommended" and "0.4 recommended".

## 9. History: Infinity GEM line numbers in earlier versions

Line numbers move whenever the code changes. Those below are kept only for checking older results; **do not use them with today's `cge.py`.**
- "0.2" = Infinity GEM 0.2 (574 lines), the version behind the results published up to 7 Oct 2026, kept in an archived copy.
- "0.3.1" = 0.3.1 (772 lines), re-checked on 8 Oct 2026, 8:50 PM. (The 7 Oct draft gave pre-margins development lines; the 0.3.1 options shifted them by 36 to 59 lines.)
- From 0.3.1 to 0.3.13 the options of Section 3a moved most lines by 200 to 400 (e.g. eq. 1's split-margins line from 419 to 694). The 0.3.2-0.3.12 lines were never published in this map.

| # | 0.2 line | 0.3.1 line | | # | 0.2 line | 0.3.1 line |
|---|---|---|---|---|---|---|
| 1 | 295 | 397 (+419 split margins) | | 25 | 374–375 | 525–526 (545–546) |
| 2 | 296 | 398 | | 26 | 376–381 | 527–532 (547–552) |
| 3 | 367 | 518; 539 split margins | | 27 | 363–364 | 513–515 (553–554) |
| 4 | 382 | 558 | | 28 | 337–339 | 464–466 |
| 5 | 319 | 441 | | 29 | 340–341 | 467–468 |
| 6 | 320 | 442 | | 30 | 344, 349 | 471, 476 |
| 7 | 330 | 457 | | 31 | 344–349 | 471–476 |
| 8 | 330 | 457 (activity tax 456) | | 32 | 351–354 | 478–481 |
| 9 | 298, 409 | 420, 586 | | 33 | 355 | 483 (CD), 486 (LES) |
| 13 | 331 | 458 | | 35 | 359 | 509 |
| 14 | 360 | 510 | | 36 | 358 | 505 |
| 15 | 329 | 452–455 | | 37 | 387–388 | 564–565 |
| 16 | 334 (rents 325) | 461 (rents 447) | | 38 | 389 | 566 |
| 17 | 360 | 510 | | 39 | 398 (closures 299–300, 401) | 575 (closures 421–422, 578) |
| 18 | 303 (`sam.py` —) | 425 (`sam.py` 174) | | 40 | 361–364, 395–396 | 511–515, 572–573 |
| 19 | 303 | 425 | | 41 | 402–404 (re-exports 127–135) | 579–581 (re-exports 184–192) |
| 21 | 305–312 | 427–434 | | 42 | 390 | 567 |
| 22 | 307 | 429 | | 43 | 350 | 477 |
| 23 | 313–316 | 435–438 | | 44 | 352 | 479 |
| 24 | 371–372 | 522–523 (543–544) | | 45 | 405–407 | 582–584 |
