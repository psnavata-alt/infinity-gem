"""Infinity GEM: open-source general equilibrium and econometric models of the Philippine economy.

Modules
-------
paths      Folder locations (data, outputs) resolved relative to this package.
sam        Load, check, aggregate and analyse IFPRI-style Social Accounting Matrices.
multiplier SAM and input-output multipliers (fixed-price models).
iomodel    Leontief quantity, price and job-equivalent models on PSA's 2018 input-output tables (data/raw/io).
cge        Static CGE model calibrated to the SAM (IFPRI standard-model tradition).
dynamic    Recursive-dynamic extension of the CGE (capital accumulation, labour growth, TFP, hybrid closures, short-run options).
settings   Named sets of model assumptions; the default is "0.4.1 recommended" (CHANGELOG.md).
microsim   Links model results to FIES households for poverty and distribution (FIES downloaded by the user from PSA).
fies_base  Which survey the poverty microsimulation starts from: FIES 2025 (the default) or FIES 2023.
var, svar  Time-series tools: OLS with Newey-West errors, VARs, structural VARs, local projections.

Start with README.md and docs/STATUS.md. Research results only: nothing here is an official statement.
"""
__version__ = "0.4.2"   # built from version 0.4.2 of 18 Nov 2026; see CHANGELOG.md
