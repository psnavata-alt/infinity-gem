"""Infinity GEM: open-source general equilibrium and econometric models of the Philippine economy.

Modules
-------
paths      Folder locations (data, outputs) resolved relative to this package.
sam        Load, check, aggregate and analyse IFPRI-style Social Accounting Matrices.
multiplier SAM and input-output multipliers (fixed-price models).
iomodel    Leontief quantity, price and job-equivalent models on PSA's 2018 input-output tables (data/raw/io).
cge        Static CGE model calibrated to the SAM (IFPRI standard-model tradition).
dynamic    Recursive-dynamic extension of the CGE (capital accumulation, labour growth, TFP, hybrid closures).
microsim   Links model results to FIES 2023 households for poverty and distribution (FIES downloaded by the user).
var, svar  Time-series tools: OLS with Newey-West errors, VARs, structural VARs, local projections.

Start with README.md and docs/STATUS.md. Research results only: nothing here is an official statement.
"""
__version__ = "0.3.13.dev3"   # built from the development copy (24 Oct 2026); see CHANGELOG.md
