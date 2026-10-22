# Elasticities

The published elasticities in this folder are included with their sources (`data/DATA_INVENTORY.md`). The two MANAGE-WB parameter extracts are the World Bank's, under the MIT licence in `LICENSE-MANAGE-WB.txt`.

**Not included: the GTAP 10 household-demand parameters.** The third benchmark of check H1 (and `infinity_gem.demand.les_gtap10`) uses the Philippine household-demand parameters of the GTAP 10A Data Base (2014; Aguiar, Chepeliev, Corong, McDougall and van der Mensbrugghe 2019, *Journal of Global Economic Analysis* 4(1)). The GTAP licence does not allow us to redistribute them. If you have the GTAP 10A package, `tools/gtap10_philippines.py` extracts them into `GTAP10_2014_Philippines_household_demand.csv` in this folder (it reads the package with the open-source `harpy3` reader, which is GPL v3 and is not a requirement of Infinity GEM); without that file, check H1 runs its other parts and says that the GTAP benchmark was not run.

The original USDA ERS tables behind `USDA_ERS_2005ICP_Philippines_elasticities.csv` can be downloaded from the USDA Economic Research Service (International Food Consumption Patterns, 2005 ICP).
