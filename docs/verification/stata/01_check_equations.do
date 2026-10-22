* =============================================================================
* 01_check_equations.do  -  Infinity GEM verification in Stata (option a)
*
* WHAT IT DOES, IN ONE SENTENCE
*   It takes the numbers Infinity GEM's Python solver found (the "solution") and the
*   model's parameters, plugs them into the equations of the published IFPRI
*   standard CGE model (Lofgren, Harris and Robinson 2002), and shows that every
*   equation holds: left side minus right side is (about) zero.
*
* WHY THAT PROVES SOMETHING
*   Finding a CGE solution needs a solver; CHECKING one does not. If a set of
*   prices and quantities satisfies every equation of the published model, it IS
*   a solution of that model, whoever (or whatever) found it. Stata does the
*   checking here with ordinary arithmetic that any Stata user can read.
*   The parameters are not taken on trust either: Section C recomputes the main
*   ones from the SAM itself.
*
* WHAT IT DOES NOT PROVE (read 00_README_STATA_ROUTE.md, section 4)
*   It does not re-solve the model (that would be option c, Mata solvenl), and
*   it checks Infinity GEM's equations in the form Infinity GEM uses (the concordance,
*   ../01_EQUATION_CONCORDANCE_Lofgren2002_GAMS_Python.md, maps each one to the book).
*
* DATA (folder data/, written by tools/export_for_stata.py; checksums in data/MANIFEST.txt)
*   parameters.csv   the 639 numbers on the 'Parameters' sheet of the Excel workbook
*   solution.csv     the 497 solved values on its 'Solution' sheet, 5 scenarios:
*                    base (reproduces the SAM), t1 chemicals/petroleum import price +10%,
*                    t2 construction investment -10%, t3 remittances -10%,
*                    t4 farm productivity +5%
*   sets.csv         the names of the 9 commodities, 9 activities, 5 factors, 10 households
*   sam_base_long.csv, sam_T2_long.csv   the 9-sector 2023 SAM (IFPRI netting, as used in
*                    check V2) and the SAM rebuilt after shock T2, one cell per line
*
* NAMES: the same as in the Excel workbook. PM_cchem = import price of chemicals,
*   tm_cchem = its tariff rate, QH_cagri_hhd_r1 = farm goods bought by rural quintile 1,
*   W_flab_n_aagri = wage of labour with no schooling/primary in agriculture, etc.
*   Book symbols: see the workbook's 'Read me' sheet.
*
* HOW TO RUN: in Stata:
*     cd "<this folder>"
*     do 01_check_equations.do
*   Results: results/01_check_equations.log and results/01_equation_results.csv
*
* Written with an AI coding assistant, 8 Oct 2026. AI-written: the point is that a Stata user can
* read every line and check it. NOT YET RUN IN STATA when written: no Stata licence was available (see the README). The same arithmetic was run in
* Python (tools/mirror_stata_checks.py) and passed.
* =============================================================================

version 16                 // works in Stata 16, 17 and 18
clear all                  // start from an empty memory: no old data or scalars
set more off               // do not pause when the Results window fills
set varabbrev off          // never let Stata guess a variable name from an abbreviation

* --- 0. Folders ---------------------------------------------------------------
capture confirm file "data/parameters.csv"      // are we in the right folder?
if _rc {
    display as error "Run this do-file from its own folder (docs/verification/stata)."
    display as error "In Stata: cd ""<that folder>"", then: do 01_check_equations.do"
    exit 601
}
capture mkdir "results"                         // results go here (no error if it exists)
capture log close _all
log using "results/01_check_equations.log", replace text name(eqlog)

local TOL = 1e-6           // PASS if |left - right| < 0.000001 (pesos billions, or price units),
                           // the same threshold as the Excel workbook

* =============================================================================
* A. READ THE DATA
* =============================================================================

* --- A1. Sets: the lists of commodities (C), activities (A), factors (F), households (H)
import delimited using "data/sets.csv", varnames(1) stringcols(1 2) clear
sort setname order                              // keep the workbook's order
foreach s in C A F H {
    global `s' ""                               // start each list empty
    forvalues i = 1/`=_N' {
        if setname[`i'] == "`s'" global `s' "${`s'} `=member[`i']'"
    }
    display as text "Set `s': " as result "${`s'}"
}
global INST "$H ent"        // institutions that receive factor income: households + enterprises

* --- A2. Parameters: one Stata scalar per parameter, with the workbook's name
import delimited using "data/parameters.csv", varnames(1) stringcols(1) asdouble clear
                            // asdouble: keep all 16 digits (the default float would keep only 7)
forvalues i = 1/`=_N' {
    scalar `=name[`i']' = value[`i']            // e.g. scalar tm_cchem = 0.0123...
}
display as text "Parameters read: " as result _N

* --- A3. A small program that loads ONE scenario's solution into scalars
*         (called again for each scenario, so the equations below never change)
capture program drop load_solution
program define load_solution
    args scen                                    // base, t1, t2, t3 or t4
    quietly import delimited using "data/solution.csv", varnames(1) stringcols(1) asdouble clear
    forvalues i = 1/`=_N' {
        scalar `=name[`i']' = `scen'[`i']        // e.g. scalar PM_cchem = <value in column t1>
    }
    clear                                        // leave memory empty: names now mean scalars only
end

* --- A4. Which goods are imported, exported, sold at home? Read from the BASE solution,
*         exactly as Infinity GEM and the workbook decide it (a flow above 1e-12 exists).
*         Equations that need imports, say, are checked only for goods that have imports.
clear                                            // empty dataset: names below can only mean scalars
load_solution base
foreach g in CM CE CD CX CQ CED CDnoE CEnoD CMD CDnoM CMnoD {
    global `g' ""
}
foreach c of global C {
    local m = (QM_`c' > 1e-12)                   // has imports
    local e = (QE_`c' > 1e-12)                   // has exports
    local d = (QD_`c' > 1e-12)                   // has domestic sales
    if `m' global CM "$CM `c'"
    if `e' global CE "$CE `c'"
    if `d' global CD "$CD `c'"
    if QX_`c' > 1e-12 global CX "$CX `c'"        // is produced at home
    if QQ_`c' > 1e-12 global CQ "$CQ `c'"        // is used at home (composite good)
    if `e' & `d'  global CED   "$CED `c'"        // both exported and sold at home (CET applies)
    if `d' & !`e' global CDnoE "$CDnoE `c'"      // sold at home only
    if `e' & !`d' global CEnoD "$CEnoD `c'"      // exported only
    if `m' & `d'  global CMD   "$CMD `c'"        // both imported and home-made (Armington applies)
    if `d' & !`m' global CDnoM "$CDnoM `c'"      // home-made only
    if `m' & !`d' global CMnoD "$CMnoD `c'"      // imported only
}
foreach a of global A {
    foreach f of global F {
        scalar use_`f'_`a' = (QF_`f'_`a' > 0)   // 1 if activity a employs factor f in the SAM
    }
}
display as text "Imported: $CM" _n "Exported: $CE" _n "Sold at home only: $CDnoE" _n "Home-made only: $CDnoM"

* =============================================================================
* B. THE EQUATIONS
*    One block per equation of the book (numbers = Lofgren et al. 2002 appendix,
*    printed pp. 50-59). Each line posts:  scenario | order | book eq. | element | error,
*    where error = left side - right side. All errors must be ~0.
* =============================================================================
capture program drop check_equations
program define check_equations
    args P scen                                  // P = the results file handle; scen = scenario label

    * --- Eq. 1 (p. 50) import price: PM = pwm * EXR * (1 + tm)
    *     [Infinity GEM charges trade margins on the composite good instead (eq. 4); concordance row 1]
    foreach c of global CM {
        post `P' ("`scen'") (1) ("1") ("`c'") (PM_`c' - pwm_`c'*EXR*(1+tm_`c'))
    }

    * --- Eq. 2 (p. 50) export price: PE = pwe * EXR   [no export tax in the Philippine SAM]
    foreach c of global CE {
        post `P' ("`scen'") (2) ("2") ("`c'") (PE_`c' - pwe_`c'*EXR)
    }

    * --- Eq. 4 (p. 50) absorption: PQ*QQ = (1+tq) * (PM*QM + PDS*QD + margin cost)
    *     (Infinity GEM's sales tax rate is on the pre-tax value; the book's on the tax-inclusive value)
    foreach c of global CQ {
        post `P' ("`scen'") (3) ("4") ("`c'") ///
            (PQ_`c'*QQ_`c' - (1+tq_`c')*(PM_`c'*QM_`c' + PDS_`c'*QD_`c' + icq_`c'*PTRC*QQ_`c'))
    }

    * --- Eq. 5 (p. 50) value of marketed output: PX*QX = PDS*QD + PE*QE
    foreach c of global CX {
        post `P' ("`scen'") (4) ("5") ("`c'") (PX_`c'*QX_`c' - (PDS_`c'*QD_`c' + PE_`c'*QE_`c'))
    }

    * --- Eq. 6 (p. 51) activity price: PA = sum over c of theta * PX
    foreach a of global A {
        scalar _t = 0
        foreach c of global C {
            scalar _t = _t + theta_`a'_`c'*PX_`c'
        }
        post `P' ("`scen'") (5) ("6") ("`a'") (PA_`a' - _t)
    }

    * --- Eq. 7-8 (p. 51) zero profit: PA = sum over c of ica*PQ + iva*PVA
    *     (price of one unit of output = cost of its inputs; no activity tax in the 2023 SAM)
    foreach a of global A {
        scalar _t = iva_`a'*PVA_`a'
        foreach c of global C {
            scalar _t = _t + ica_`c'_`a'*PQ_`c'
        }
        post `P' ("`scen'") (6) ("7-8") ("`a'") (PA_`a' - _t)
    }

    * --- Eq. 9 (p. 51) consumer price index CPI = sum of cwts*PQ, and CPI = 1 (the numeraire)
    scalar _t = 0
    foreach c of global C {
        scalar _t = _t + cwts_`c'*PQ_`c'
    }
    post `P' ("`scen'") (7) ("9") ("CPI definition") (CPI - _t)
    post `P' ("`scen'") (7) ("9") ("numeraire")      (CPI - 1)

    * --- Eq. 13 (p. 52) Leontief demand for value added: QVA = iva*QA
    foreach a of global A {
        post `P' ("`scen'") (8) ("13") ("`a'") (QVA_`a' - iva_`a'*QA_`a')
    }

    * --- Eq. 15 (p. 52) CES value added, in its unit-cost ("dual") form:
    *     PVA = ( sum over f of delta * W^(1-sigma) )^(1/(1-sigma)) / productivity
    foreach a of global A {
        scalar _t = 0
        foreach f of global F {
            if use_`f'_`a' {
                scalar _t = _t + delta_`f'_`a'*W_`f'_`a'^(1-sigva_`a')
            }
        }
        post `P' ("`scen'") (9) ("15") ("`a'") (PVA_`a' - _t^(1/(1-sigva_`a'))/(tfp_`a'*tfps_`a'))
    }

    * --- Eq. 16 (p. 53) factor demand: QF = QVA/prod * delta * (PVA*prod/W)^sigma
    *     (the cost-minimising use of each factor; prod = tfp * scenario productivity scale)
    foreach a of global A {
        foreach f of global F {
            if use_`f'_`a' {
                scalar _p = tfp_`a'*tfps_`a'
                post `P' ("`scen'") (10) ("16") ("`f', `a'") ///
                    (QF_`f'_`a' - QVA_`a'/_p*delta_`f'_`a'*(PVA_`a'*_p/W_`f'_`a')^sigva_`a')
            }
        }
    }

    * --- Eq. 14 and 17 (p. 52-53) intermediate demand: QINT = sum over a of ica*QA
    foreach c of global C {
        scalar _t = 0
        foreach a of global A {
            scalar _t = _t + ica_`c'_`a'*QA_`a'
        }
        post `P' ("`scen'") (11) ("14, 17") ("`c'") (QINT_`c' - _t)
    }

    * --- Eq. 18-19 (p. 53) commodity output: QX = sum over a of theta*QA
    *     (one activity per commodity in this SAM; no home consumption: concordance rows 18-19)
    foreach c of global C {
        scalar _t = 0
        foreach a of global A {
            scalar _t = _t + theta_`a'_`c'*QA_`a'
        }
        post `P' ("`scen'") (12) ("18-19") ("`c'") (QX_`c' - _t)
    }

    * --- Eq. 21 (p. 54) CET: QX = at * ( gam*QE^rt + (1-gam)*QD^rt )^(1/rt)
    *     (output is split between exports and home sales along a transformation frontier)
    foreach c of global CED {
        post `P' ("`scen'") (13) ("21") ("`c'") ///
            (QX_`c' - at_`c'*(gam_`c'*QE_`c'^rt_`c' + (1-gam_`c')*QD_`c'^rt_`c')^(1/rt_`c'))
    }

    * --- Eq. 22 (p. 54) export/home-sales ratio: QE/QD = ( PE/PDS * (1-gam)/gam )^omega
    foreach c of global CED {
        post `P' ("`scen'") (14) ("22") ("`c'") ///
            (QE_`c'/QD_`c' - (PE_`c'/PDS_`c'*(1-gam_`c')/gam_`c')^omega_`c')
    }

    * --- Eq. 23 (p. 54) goods sold only at home (QX = QD) or only exported (QX = QE)
    foreach c of global CDnoE {
        post `P' ("`scen'") (15) ("23") ("`c' (no exports)") (QX_`c' - QD_`c')
    }
    foreach c of global CEnoD {
        post `P' ("`scen'") (15) ("23") ("`c' (only exports)") (QX_`c' - QE_`c')
    }

    * --- Eq. 24 (p. 54) Armington composite:
    *     QQ = aq * ( dq^(1/s)*QM^((s-1)/s) + (1-dq)^(1/s)*QD^((s-1)/s) )^(s/(s-1))
    *     (imports and home goods are imperfect substitutes; s = sigq)
    foreach c of global CMD {
        scalar _e = (sigq_`c'-1)/sigq_`c'
        post `P' ("`scen'") (16) ("24") ("`c'") ///
            (QQ_`c' - aq_`c'*(dq_`c'^(1/sigq_`c')*QM_`c'^_e + (1-dq_`c')^(1/sigq_`c')*QD_`c'^_e)^(1/_e))
    }

    * --- Eq. 25 (p. 55) import/home ratio: QM/QD = dq/(1-dq) * (PDS/PM)^sigq
    foreach c of global CMD {
        post `P' ("`scen'") (17) ("25") ("`c'") ///
            (QM_`c'/QD_`c' - dq_`c'/(1-dq_`c')*(PDS_`c'/PM_`c')^sigq_`c')
    }

    * --- Eq. 26 (p. 55) goods that are only home-made or only imported
    foreach c of global CDnoM {
        post `P' ("`scen'") (18) ("26") ("`c' (no imports)") (QD_`c' - QQ_`c'*k_d_`c')
    }
    foreach c of global CMnoD {
        post `P' ("`scen'") (18) ("26") ("`c' (only imports)") (QM_`c' - QQ_`c'*k_m_`c')
    }

    * --- Eq. 27 (p. 55) trade and transport margins: TMARG = sum of icq*QQ; PTRC = sum of sm*PQ
    *     [simplified: one margin per unit of composite good; concordance row 27]
    scalar _t = 0
    scalar _u = 0
    foreach c of global C {
        scalar _t = _t + icq_`c'*QQ_`c'
        scalar _u = _u + sm_`c'*PQ_`c'
    }
    post `P' ("`scen'") (19) ("27") ("margin quantity") (TMARG - _t)
    post `P' ("`scen'") (19) ("27") ("margin price")    (PTRC - _u)

    * --- Eq. 28 (p. 55) factor income: YF = sum over a of W*QF + factor income from abroad * EXR
    foreach f of global F {
        scalar _t = frow_in_`f'*EXR
        foreach a of global A {
            scalar _t = _t + W_`f'_`a'*QF_`f'_`a'
        }
        post `P' ("`scen'") (20) ("28") ("`f'") (YF_`f' - _t)
    }

    * --- Eq. 29 (p. 56) factor income of each institution: YIF = shif * ((1-tf)*YF - paid abroad*EXR)
    foreach i of global INST {
        foreach f of global F {
            post `P' ("`scen'") (21) ("29") ("`i', `f'") ///
                (YIF_`i'_`f' - shif_`i'_`f'*((1-tf_`f')*YF_`f' - frow_out_`f'*EXR))
        }
    }

    * --- Eq. 30 (p. 56) income of enterprises and households
    *     enterprises: YE = factor income + government transfers*CPI + income from abroad*EXR
    scalar _t = trg_ent*CPI + erow_in*EXR
    foreach f of global F {
        scalar _t = _t + YIF_ent_`f'
    }
    post `P' ("`scen'") (22) ("30") ("enterprises") (YE - _t)
    *     households: YH = factor income + share of enterprise income + gov. transfers*CPI + remittances*EXR
    foreach h of global H {
        scalar _t = she_`h'*YE + trg_h_`h'*CPI + hrow_in_`h'*remits_`h'*EXR
        foreach f of global F {
            scalar _t = _t + YIF_`h'_`f'
        }
        post `P' ("`scen'") (22) ("30") ("`h'") (YH_`h' - _t)
    }

    * --- Eq. 31-32 (p. 56) disposable income: DY = YH*(1 - tins - tgh) - payments abroad*EXR
    foreach h of global H {
        post `P' ("`scen'") (23) ("31-32") ("`h'") ///
            (DY_`h' - (YH_`h'*(1-tins_`h'-tgh_`h') - hrow_out_`h'*EXR))
    }

    * --- Eq. 32 and 44 (p. 56, 59) spending and saving: EH = DY*(1-MPS), HSAV = MPS*DY,
    *     with MPS = mps*(1+MPSADJ) (saving rates adjust in the investment-driven closure)
    foreach h of global H {
        post `P' ("`scen'") (24) ("32, 44") ("`h' spending") (EH_`h' - DY_`h'*(1-mps_`h'*(1+MPSADJ)))
        post `P' ("`scen'") (24) ("32, 44") ("`h' saving")   (HSAV_`h' - mps_`h'*(1+MPSADJ)*DY_`h')
    }

    * --- Eq. 33 (p. 57) household demand, Cobb-Douglas (the LES with no subsistence part):
    *     PQ*QH = beta*EH  (each household spends a fixed share of its budget on each good)
    foreach c of global C {
        foreach h of global H {
            post `P' ("`scen'") (25) ("33") ("`c', `h'") (PQ_`c'*QH_`c'_`h' - beta_`c'_`h'*EH_`h')
        }
    }

    * --- Eq. 35 (p. 57) investment demand: QINV = qinvbar * IADJ * scenario scale
    foreach c of global C {
        post `P' ("`scen'") (26) ("35") ("`c'") (QINV_`c' - qinvbar_`c'*IADJ*qinvs_`c')
    }

    * --- Eq. 36 (p. 57) government consumption, fixed in real terms: QG = qgbar
    foreach c of global C {
        post `P' ("`scen'") (27) ("36") ("`c'") (QG_`c' - qgbar_`c')
    }

    * --- Eq. 37 (p. 57) government revenue YG = direct taxes + factor taxes + tariffs
    *     + sales taxes + enterprise and household payments to government + receipts from abroad
    scalar _t = te*YE + sheg*YE + grow_in*EXR
    foreach h of global H {
        scalar _t = _t + tins_`h'*YH_`h' + tgh_`h'*YH_`h'
    }
    foreach f of global F {
        scalar _t = _t + tf_`f'*YF_`f'
    }
    foreach c of global C {
        scalar _t = _t + tm_`c'*pwm_`c'*EXR*QM_`c' + tq_`c'/(1+tq_`c')*PQ_`c'*QQ_`c'
    }
    post `P' ("`scen'") (28) ("37-38, 42") ("revenue YG") (YG - _t)
    * --- Eq. 38 (p. 58) government spending EG = consumption + transfers*CPI + payments abroad
    scalar _t = trg_ent*CPI + grow_out*EXR
    foreach c of global C {
        scalar _t = _t + PQ_`c'*QG_`c'
    }
    foreach h of global H {
        scalar _t = _t + trg_h_`h'*CPI
    }
    post `P' ("`scen'") (28) ("37-38, 42") ("spending EG") (GEXP - _t)
    * --- Eq. 42 (p. 58) government saving = revenue - spending
    post `P' ("`scen'") (28) ("37-38, 42") ("saving GSAV = YG - EG") (GSAV - (YG - GEXP))
    *     enterprise saving = what is left after taxes, transfers to households and government, payments abroad
    scalar _t = 0
    foreach h of global H {
        scalar _t = _t + she_`h'
    }
    post `P' ("`scen'") (28) ("37-38, 42") ("enterprise saving") (ESAV - (YE*(1-te-_t-sheg) - erow_out*EXR))

    * --- Eq. 39 (p. 58) factor markets clear: sum over a of QF = QFS (full employment)
    foreach f of global F {
        scalar _t = 0
        foreach a of global A {
            scalar _t = _t + QF_`f'_`a'
        }
        post `P' ("`scen'") (29) ("39") ("`f'") (_t - QFS_`f')
    }

    * --- Eq. 40 (p. 58) goods markets clear: QQ = QINT + sum of QH + QG + QINV + qdst + margin use
    foreach c of global C {
        scalar _t = QINT_`c' + QG_`c' + QINV_`c' + qdst_`c' + sm_`c'*TMARG
        foreach h of global H {
            scalar _t = _t + QH_`c'_`h'
        }
        post `P' ("`scen'") (30) ("40") ("`c'") (QQ_`c' - _t)
    }

    * --- Eq. 41 (p. 58) current account in foreign currency: payments abroad = receipts from abroad
    scalar _t = erow_out + grow_out              // payments abroad
    scalar _u = erow_in + grow_in + FSAV         // receipts from abroad (incl. foreign saving)
    foreach c of global C {
        scalar _t = _t + pwm_`c'*(QM_`c' + rex_`c')
        scalar _u = _u + pwe_`c'*(QE_`c' + rex_`c')
    }
    foreach f of global F {
        scalar _t = _t + frow_out_`f'
        scalar _u = _u + frow_in_`f'
    }
    foreach h of global H {
        scalar _t = _t + hrow_out_`h'
        scalar _u = _u + hrow_in_`h'*remits_`h'
    }
    post `P' ("`scen'") (31) ("41") ("balance") (_t - _u)

    * --- Eq. 45 (p. 59) savings = investment; WALRAS is the model's check variable (must be 0)
    scalar _t = ESAV + GSAV + FSAV*EXR
    foreach h of global H {
        scalar _t = _t + HSAV_`h'
    }
    scalar _u = 0
    foreach c of global C {
        scalar _u = _u + PQ_`c'*(QINV_`c' + qdst_`c')
    }
    post `P' ("`scen'") (32) ("45") ("savings - investment") (_t - _u)
    post `P' ("`scen'") (32) ("45") ("WALRAS")               (WALRAS)
end

* --- B1. Run the equations for the five scenarios, then the tamper test
tempname P
postfile `P' str8 scen int order str12 eq str48 element double err ///
    using "results/residuals.dta", replace
foreach s in base t1 t2 t3 t4 {
    clear
    load_solution `s'                            // the solution of scenario s, into scalars
    check_equations `P' `s'                      // every equation, at that solution
}

* --- B2. TAMPER TEST: does the check catch a wrong number?
*     Take the base solution, raise farm output QX_cagri by 1%, check again.
*     Equations that contain QX_cagri (5, 18-19, 21) MUST now fail; the rest still pass.
clear
load_solution base
scalar QX_cagri = QX_cagri*1.01
check_equations `P' TAMPER
postclose `P'

* =============================================================================
* C. CALIBRATION: recompute the main parameters from the SAM itself
*    (so that the parameters, too, are checked against the data, not taken on trust)
* =============================================================================
import delimited using "data/sam_base_long.csv", varnames(1) stringcols(1 2) asdouble clear
* --- C1. SAM balance: for every account, receipts (row total) = payments (column total)
tempfile cells rtot
save `cells'
collapse (sum) receipts = value, by(row)
rename row account
save `rtot'
use `cells', clear
collapse (sum) payments = value, by(col)
rename col account
merge 1:1 account using `rtot', nogenerate
generate double gap = receipts - payments
quietly summarize gap
local samgap = max(abs(r(min)), abs(r(max)))
display as text _n "Base SAM: largest |receipts - payments| = " as result %9.2e `samgap'
forvalues i = 1/`=_N' {
    scalar TOT_`=account[`i']' = receipts[`i']   // e.g. TOT_aagri = total of activity aagri
}
* --- C2. Every SAM cell as a scalar SAM_<row>_<column> (pesos billions)
use `cells', clear
forvalues i = 1/`=_N' {
    scalar SAM_`=row[`i']'_`=col[`i']' = value[`i']
}
* --- C3. Recompute and compare (Stata value - Infinity GEM value), same formulas as the workbook
tempname K
postfile `K' str10 param str32 name double stata own diff using "results/calibration.dta", replace
foreach a of global A {
    scalar _va = 0
    foreach f of global F {
        scalar _va = _va + SAM_`f'_`a'           // value added = sum of factor payments
    }
    foreach c of global C {
        * ica: input c per unit of activity a = SAM[c,a] / total of a
        post `K' ("ica") ("ica_`c'_`a'") (SAM_`c'_`a'/TOT_`a') (ica_`c'_`a') (SAM_`c'_`a'/TOT_`a' - ica_`c'_`a')
        * theta: yield of commodity c per unit of activity a = SAM[a,c] / total of a
        post `K' ("theta") ("theta_`a'_`c'") (SAM_`a'_`c'/TOT_`a') (theta_`a'_`c') (SAM_`a'_`c'/TOT_`a' - theta_`a'_`c')
    }
    * iva: value added per unit of activity
    post `K' ("iva") ("iva_`a'") (_va/TOT_`a') (iva_`a') (_va/TOT_`a' - iva_`a')
    foreach f of global F {
        * delta: factor f's share of value added in activity a
        post `K' ("delta") ("delta_`f'_`a'") (SAM_`f'_`a'/_va) (delta_`f'_`a') (SAM_`f'_`a'/_va - delta_`f'_`a')
    }
}
scalar _allcons = 0                              // all household consumption
foreach h of global H {
    scalar _ch = 0
    foreach c of global C {
        scalar _ch = _ch + SAM_`c'_`h'           // household h's total consumption
    }
    scalar _allcons = _allcons + _ch
    foreach c of global C {
        * beta: budget share of good c for household h
        post `K' ("beta") ("beta_`c'_`h'") (SAM_`c'_`h'/_ch) (beta_`c'_`h') (SAM_`c'_`h'/_ch - beta_`c'_`h')
    }
}
foreach c of global C {
    * tm: tariff rate = tariff paid / imports at world prices (0 if not imported)
    scalar _k = cond(SAM_row_`c' == 0, 0, SAM_mtax_`c'/SAM_row_`c')
    post `K' ("tm") ("tm_`c'") (_k) (tm_`c') (_k - tm_`c')
    * cwts: CPI weight = household consumption of c / all household consumption
    scalar _ch = 0
    foreach h of global H {
        scalar _ch = _ch + SAM_`c'_`h'
    }
    post `K' ("cwts") ("cwts_`c'") (_ch/_allcons) (cwts_`c') (_ch/_allcons - cwts_`c')
}
postclose `K'

* --- C4. The SAM rebuilt from the T2 solution (construction investment -10%) must also balance
import delimited using "data/sam_T2_long.csv", varnames(1) stringcols(1 2) asdouble clear
tempfile c2 r2
save `c2'
collapse (sum) receipts = value, by(row)
rename row account
save `r2'
use `c2', clear
collapse (sum) payments = value, by(col)
rename col account
merge 1:1 account using `r2', nogenerate
generate double gap = receipts - payments
quietly summarize gap
local t2gap = max(abs(r(min)), abs(r(max)))
display as text "SAM after T2: largest |receipts - payments| = " as result %9.2e `t2gap'

* =============================================================================
* D. RESULTS: one PASS/FAIL line per book equation and scenario
* =============================================================================
use "results/residuals.dta", clear
generate double abserr = abs(err)
collapse (count) rows = abserr (max) max_abs_error = abserr, by(scen order eq)
generate str4 result = cond(max_abs_error < `TOL', "PASS", "FAIL")
format max_abs_error %9.2e
sort scen order
display as text _n "{hline 70}" _n "EQUATION CHECKS (error = left side - right side; PASS if < `TOL')" _n "{hline 70}"
foreach s in base t1 t2 t3 t4 {
    display as text _n "Scenario `s'"
    list eq rows max_abs_error result if scen == "`s'", noobs sep(0) abbreviate(14)
}
export delimited using "results/01_equation_results.csv", replace

* --- D1. The verdicts, enforced: assert stops the do-file with an error if anything is wrong
quietly count if scen != "TAMPER"
local nchecks = r(N)
quietly count if scen != "TAMPER" & result == "FAIL"
local nfail = r(N)
display as text _n "Equation groups checked (5 scenarios): " as result `nchecks' as text "   failed: " as result `nfail'
assert result == "PASS" if scen != "TAMPER"      // every equation, every scenario

* the tamper test must fail exactly where QX_cagri appears, and nowhere else
display as text _n "Tamper test (QX_cagri + 1% in the base solution):"
list eq max_abs_error result if scen == "TAMPER" & result == "FAIL", noobs sep(0)
assert result == "FAIL" if scen == "TAMPER" & inlist(eq, "5", "18-19", "21")
assert result == "PASS" if scen == "TAMPER" & !inlist(eq, "5", "18-19", "21")

* --- D2. Calibration verdict
use "results/calibration.dta", clear
generate double absdiff = abs(diff)
quietly summarize absdiff
local caldiff = r(max)
display as text _n "Calibration: " as result _N as text " parameters recomputed from the SAM; largest |Stata - Infinity GEM| = " as result %9.2e `caldiff'
export delimited using "results/01_calibration_results.csv", replace
assert absdiff < 1e-9
assert `samgap' < 0.001
assert `t2gap' < 0.001

* --- D3. Optional: compare with the Python mirror of this file, if it has been run
capture confirm file "results/python_mirror_equation_results.csv"
if !_rc {
    import delimited using "results/python_mirror_equation_results.csv", varnames(1) stringcols(1 3) asdouble clear
    rename (max_abs_error rows) (py_max py_rows)
    keep scen eq py_rows py_max
    tempfile py
    save `py'
    import delimited using "results/01_equation_results.csv", varnames(1) stringcols(1 3) asdouble clear
    merge 1:1 scen eq using `py'
    assert _merge == 3                           // the same equation groups in both files
    assert rows == py_rows                       // the same number of rows in each group
    generate double gap_vs_python = abs(max_abs_error - py_max)
    quietly summarize gap_vs_python
    display as text "Stata vs Python mirror: " as result r(N) as text " groups matched; largest difference in max |error| = " as result %9.2e r(max)
}

display as result _n "ALL STATA CHECKS PASSED: every book equation holds at Infinity GEM's solution in all five scenarios;"
display as result "the parameters match the SAM; both SAMs balance; the tamper test was caught."
log close eqlog
