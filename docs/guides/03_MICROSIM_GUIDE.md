# 3. Poverty microsimulation (FIES 2023)

> **The base since 18 Nov 2026 (development version 0.4.2; the decision, about 6:15 AM): FIES 2025.** The steps below are the same on both bases. By default the model now uses PSA's FIES 2025 households (170,916 families) and PSA's 2025 poverty lines by province and urban or rural (11.08 million poor, 9.7%; check FB1), so new new-poor figures are **"on the FIES 2025 base"**. Every figure published before 18 Nov 2026 used the FIES 2023 households and 2023 lines described below (17.54 million poor; check P1) and keeps **"on the FIES 2023 base"**; reproduce it with `INFINITY_GEM_FIES_BASE=fies2023` or `base="fies2023"` (`infinity_gem/fies_base.py`). The LFS earnings link and the Simulator stay on FIES 2023.

## What it does

Economy-wide models speak about ten household groups; policy-makers ask about poor Filipinos. The microsimulation connects the two: it takes each group's change in real consumption from the CGE (or in income from the SAM multiplier) and applies it to every one of the 163,268 FIES 2023 households in that group, then counts how many people fall below PSA's official poverty line.

## The steps (`infinity_gem/microsim.py`)

1. **Assign households to SAM groups:** urban or rural (PSA's `URB`) × national per-capita income quintile (PSA's decile `NPCINC`, paired).
2. **Group change from the model:** real consumption change = (nominal spending, simulated ÷ base) ÷ (group price index, simulated ÷ base). The group price index uses that group's own budget shares, so a rise in food prices hurts poor groups more than rich ones.
3. **Apply and count:** each household's per-capita income is scaled by its group's change and compared with its own official threshold (`pline_2023`), weighted by `mem_rfact`.

**Baseline check (P1):** 17.539 million poor (15.54%) against PSA's official 17.54 million; food poor 4.838 million against 4.84 million.

```python
from infinity_gem.microsim import Microsim
ms = Microsim()
r = ms.from_cge(model, base, sim)
r["new_poor"], r["simulated"]["rate_pct"], r["bottom30_share_of_loss"]
```

## Reading the results

- **New poor** is a count of people, not households.
- Results depend on how many households sit just above the line: a 1% income fall moves far more people across the line when the distribution is dense near it, which is the case in the Philippines.
- Compare with the price-only FIES simulations in the September 2026 analysis (income held fixed): the CGE-based numbers include income effects (wages, employment, transfers), so they can be larger or smaller.

## Limits (state them)

- Households within a group all move by the same percentage: no change in inequality within groups.
- No re-ranking of households between groups; no movement between jobs or sectors.
- Income is the welfare measure, as in PSA's official statistics.
- The baseline is 2023. If PSA publishes newer poverty statistics (PSA has estimated that 6.5 million rose out of poverty between 2023 and 2025), label results "2023 baseline" or rebase.

## Next steps (Roadmap)

- A behavioural layer: link LFS employment changes by industry to FIES workers (who loses jobs, not just how much income falls).
- Poverty gap and severity by region and province.
- Bottom-30% price indices from PSA's CPI for the bottom 30% instead of SAM budget shares.
