"""DSGE research, milestone 7 targets (19 Oct 2026, about 2:55 AM): the BSP's own monetary-policy impulse responses.

Source: Alarcon, S. J., P. R. Alhambra, R. Amodia and D. Bautista (2020). "Policy Analysis Model for the Philippines (PAMPh)."
BSP Working Paper Series No. 2020-12, Annex 1.A "Monetary policy shock" (BSP Working Paper Series/WPS202012.pdf, p. 22). PAMPh is the BSP's semi-structural quarterly projection model (IMF FPAS / QPM);
its parameters are calibrated.

The values below were READ OFF THE PUBLISHED CHARTS by eye (19 Oct 2026; rendered at 90 dpi), so each is
approximate (about +/- 0.02 for the inflation and growth panels, +/- 0.05 for the policy rate and the exchange rate). Use them as
soft targets for impulse-response matching, not as data. Quarter 0 = the quarter before the shock (all zero); the shock hits in
quarter 1.
"""
QUARTERS = [1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 16, 20]
POLICY_RATE_PA = {1: 0.80, 2: 0.35, 3: 0.05, 4: -0.12, 5: -0.20, 6: -0.18, 7: -0.14, 8: -0.08, 10: 0.0, 12: 0.04, 14: 0.05, 16: 0.03, 20: 0.0}
GDP_GROWTH_YOY = {1: -0.12, 2: -0.20, 3: -0.21, 4: -0.19, 5: 0.0, 6: 0.12, 7: 0.21, 8: 0.22, 10: 0.15, 12: 0.0, 14: -0.06, 16: -0.06, 20: -0.02}
CPI_INFLATION_YOY = {1: -0.03, 2: -0.10, 3: -0.17, 4: -0.23, 5: -0.24, 6: -0.23, 7: -0.20, 8: -0.15, 10: -0.05, 12: 0.0, 14: 0.03, 16: 0.02, 20: 0.0}
NOMINAL_EXCHANGE_RATE_100LOG = {1: -0.40, 2: -0.38, 3: -0.28, 4: -0.20, 5: -0.16, 6: -0.16, 7: -0.19, 8: -0.25, 10: -0.34, 12: -0.42, 14: -0.43, 16: -0.42, 20: -0.40}
# Per 100 bp of policy rate on impact (scale = 1 / 0.80): GDP growth trough about -0.26 pp y/y, CPI inflation trough about
# -0.30 pp y/y, peso appreciation about 0.5% on impact. The estimated soe_med (19 Oct, 2:43 AM) gives about 10x (output) and
# 15-20x (inflation) more per basis point: milestone 7 matches these responses (minimum distance with the posterior as prior).
