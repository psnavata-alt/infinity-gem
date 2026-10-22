# 1. The SAM and fixed-price multipliers

## What a SAM is

A Social Accounting Matrix records, for one year, every flow of money between the parts of the economy. Rows receive, columns pay: the cell in row *i*, column *j* is what account *j* pays account *i*. Because every payment is someone's receipt, each account's row total equals its column total. That balance is what makes a SAM the natural base for an economy-wide model.

IFPRI's 2023 Philippine SAM (in ₱ billions) has these blocks (run `SAM.load().block_summary()` to see them):

| Flow | Row ← column | ₱ bn | Meaning |
|---|---|---|---|
| Output | activities ← commodities | 45,299 | industries' sales of what they produce |
| Intermediate inputs | commodities ← activities | 21,418 | what industries buy from each other |
| Value added | labour, land, capital ← activities | 24,245 | wages, rents and profits |
| Household consumption | commodities ← households | 20,040 | plus ₱364 bn of home consumption |
| Government consumption | commodities ← government | 3,476 | |
| Investment | commodities ← savings-investment | 5,747 | |
| Exports / imports | commodities ← rest of world / rest of world ← commodities | 6,493 / 9,886 | |
| Taxes | tax accounts ← commodities, factors, households, enterprises | 3,536 | tariffs, sales taxes, factor and direct taxes |
| Remittances | households ← rest of world | 1,576 | |

Households are grouped into rural and urban quintiles (10 groups). Labour has three education levels: low (not finished primary), medium (finished primary but not secondary) and high (finished secondary or more).

## Practical rules

- Always load with `infinity_gem.sam.SAM.load()`. The IFPRI files write large cells with thousands separators; naive readers turn them into zeros without warning.
- Check balance first: `SAM.load().check()`. The 2023 SAM balances to 10⁻⁸; the 2018 SAM is published in whole billions and balances only to about ₱5 bn.
- To aggregate (for example, all crops into one), use `SAM.aggregate(mapping)`: it sums flows and preserves balance.

## The SAM multiplier

Treat some accounts as **exogenous** (government, taxes, savings-investment, stock change, rest of world) and the rest as **endogenous** (activities, commodities, factors, enterprises, households). Divide each endogenous column by its total to get the matrix of spending shares **A**. A change in injections **dx** (e.g. less government spending on construction) changes endogenous incomes by

**dy = (I − A)⁻¹ dx**

This counts every round of spending: a construction project pays wages; workers spend; shops buy from suppliers; and so on.

```python
from infinity_gem.sam import SAM
from infinity_gem.multiplier import SAMMultiplier
m = SAMMultiplier(SAM.load())
dy = m.shock({"ccons": -100})          # ₱100 bn less construction demand
print(dy[["flab-n", "flab-p", "flab-s", "fcap"]].sum())   # value added lost
```

## When the multiplier is wrong

It assumes (1) **prices never change**, (2) **supply is unlimited** (idle workers and machines everywhere) and (3) spending patterns are fixed. So it gives an **upper bound**. It is still valuable: it is transparent, it can be reproduced in Excel (an earlier run log), and it tells you which accounts a shock passes through. Always pair it with the CGE, which relaxes all three assumptions.

## Input-output (Leontief) models on the PSA 80-industry table

`infinity_gem/iomodel.py` (class `IOTable`) holds the methods used for earlier oil-price and policy work, written once so that every user gets the same numbers. The Simulator's *Input-output* page runs them.

| Model | What it does | Call |
|---|---|---|
| Demand (quantity) | A change in final demand for some industries → output, value added (GDP), compensation, imported inputs, through the supply chain (Type I: no household spending round) | `IOTable().quantity({"Construction": -238.3}, "domestic", gdp_other_year=28009.93)` |
| Price (cost push) | A price rise in some industries (e.g. refined petroleum) passed on in full to every buyer; CPI with household-consumption weights, producer prices with output weights | `IOTable().price_summary({"Coke and refined petroleum products": 0.10})` |
| Job-equivalents | Employment by LFS major industry group moves in proportion to output | `IOTable().jobs(q["industries"]["output (%)"])` |
| Multipliers | Output, GDP and compensation multipliers for all 80 industries | `IOTable().multipliers("domestic")` |

**Domestic or total inverse?** PSA's transactions table puts imported inputs inside the input coefficients. With PSA's published (total) inverse, every peso of final demand returns exactly one peso of value added, whatever the industry, because imports are never subtracted. The **domestic** inverse removes each product's import share first (the usual "import similarity" assumption) and is the one to use: for construction it gives ₱0.68 of GDP per peso.

### Reproducing a method is not the same as validating it

Getting someone's earlier numbers back (checks I1, I2) proves our code computes what their method computes. It does not prove the method is right. That needs separate evidence: an independent source (our inverse equals PSA's published Table B.3), textbook identities, and judgement about the assumptions. The assessment of the methods built into Infinity GEM, 27 September 2026:

| Piece | Verdict |
|---|---|
| **Price model** (cost push) | **Correct**: the standard Leontief price model (Miller and Blair, *Input-Output Analysis*). Limits: full pass-through, no substitution, no demand response, so it is a first-round upper bound. **Watch the input**: a 10% rise in *refined petroleum* prices is not a 10% rise in *crude*; crude is only part of refining costs, so a crude shock should enter smaller. That is a choice of input, not a formula error. |
| **Demand model**, domestic inverse (an earlier estimate) | **Correct and standard.** Proportional import removal is the usual assumption. Omits the household spending round (Type I), which earlier fixed-price estimates state. |
| **Job-equivalents** (jobs move one-for-one with output) | **Standard and correctly labelled** an upper bound. Pairs the 2018 structure with 2025 employment, as earlier fixed-price estimates flag. |
| **Prices → GDP shortcut** (CPI change × assumed elasticity × consumption share 0.75) | **Removed from Infinity GEM on 15 Oct 2026.** It was a rule of thumb, not a model: the elasticity was assumed, not estimated (an earlier workbook's −0.5 to −0.8 have no published source), and the error had no known direction. GDP and jobs from a price shock come from the CGE, which models the channels. |
| **Reference VAR** (geopolitical risk → peso, FDI) | **Sound as a description of the data**; small sample (N = 44) and borderline significance for some responses. |

Our earlier code also gets ₱0.68 per peso of construction. That is not independent confirmation: both apply the same formula. Independent evidence is the match with PSA's published inverse and the textbook method.
