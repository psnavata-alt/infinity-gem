# Checking the CGE's equations in Stata

`01_check_equations.do` plugs the model's solution into the equations of the published IFPRI standard model (Lofgren, Harris and Robinson 2002) that apply to it, 32 equation groups and 393 rows per scenario, and shows that each holds; it also recomputes the parameters from the SAM. It needs only Stata 16 or later and the CSV files in `data/`:

| File | What it holds |
|---|---|
| `data/sets.csv` | the account sets (activities, commodities, factors, households) |
| `data/parameters.csv` | the calibrated parameters |
| `data/sam_base_long.csv`, `data/sam_T2_long.csv` | the condensed 2023 SAM (nine sectors) and the SAM after a test shock, in long format |
| `data/solution.csv` | the model's solution for the base and four test scenarios |

The CSV files were written from the condensed SAM used in check V2 and the model's solutions on it, copying values (nothing computed). `results/` holds the Python mirror of the same checks (the do-file's logic run in Python on the same data, as a cross-check).

Run in Stata, from this folder: `do 01_check_equations.do`. The equation concordance between the published model, IFPRI's GAMS code and the Python code is `docs/verification/01_EQUATION_CONCORDANCE_Lofgren2002_GAMS_Python.md`.
