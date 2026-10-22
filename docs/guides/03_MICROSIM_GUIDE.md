# 3. Poverty microsimulation (FIES 2023)

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
