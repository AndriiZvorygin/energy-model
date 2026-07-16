# Historical Absolute-Affordability Series

## Scope

This release builds annual nominal budget comparisons from matched after-tax income and basic-needs thresholds. It does not alter the live affordability headline, symptom rules, regime classifiers, or oil models.

The status thresholds are project diagnostics: `severe-shortfall` below 75% of the matched threshold, `unaffordable` below 100%, `pressured` from 100% to below 125%, and `affordable` at or above 125%. They are not official Statistics Canada classifications.

## Canada

- **Years available:** 2002–2024. National income-decile/MBM matching is available from 2015; matched regional family histories begin in 2002.
- **Household types:** Couple with one child, Couple with two children, Couple without children, One parent with one child, One parent with two children, One person.
- **National distribution:** Statistics Canada Table 11-10-0103-01 supplies average after-tax income and each decile’s applicable MBM basket cost. This is the preferred Canada-wide absolute comparison because family size and region are matched inside the official microdata calculation.
- **Regional family histories:** tax-file median after-tax family income is matched to the corresponding MBM urban region and exact family size. MBM base vintages remain separate because methodological revisions change the basket.
- **Trend:** the lowest decile remained below its matched basket cost throughout 2015–2024. The second decile moved from 0.93 baskets in 2015 to 1.14 in 2020 and 1.01 in 2024; the fifth decile moved from 1.72 to 1.93 and then 1.85. Pandemic transfers temporarily improved lower-decile ratios in 2020, and much of that gain subsequently receded.

## Owen Sound

- **Annual regional history:** 2002–2023 for the Owen Sound census agglomeration, matched to the Ontario population 30,000–99,999 MBM region.
- **City-CSD anchors:** 2015, 2020. These observations use Owen Sound city household incomes and are not spliced to the census-agglomeration series.
- **Household types:** Couple with one child, Couple with two children, Couple without children, One parent with one child, One parent with two children, One person.
- **Trend:** The household-count-weighted share of evaluated median cases below the project’s `affordable` buffer was 2.7% in 2015 and 0.0% in 2023 under the 2018-base MBM. One-person and one-parent median cases generally have the smallest buffers; couple-family medians are materially stronger. The 2023 annual census-agglomeration medians all exceed 1.25 times their matched 2018-base thresholds, but this does not override local food-insecurity, renter-burden, or core-housing-need rates: medians describe central cases, not the lower tail. Base revisions and the 2020 pandemic-income shock must be read explicitly.

## Validation Evidence

CMHC rents and Grey Bruce food baskets are retained as validation observations rather than substituted for MBM components. The local validation file currently contains 6 observations: CMHC one-bedroom rent for 2002–2003 and Grey Bruce nutritious-food-basket costs for 2023–2024.

## Major Gaps

- No annual Owen Sound **city-CSD** income history exists between Census/NHS observations. Annual tax-file data uses the wider census agglomeration.
- A stable automated export for the complete CMHC Owen Sound rent history has not yet been integrated. Published HMIP coverage exists, but only verified archived observations are included here.
- Grey Bruce nutritious-food-basket reports were verified for 2023 and 2024. Earlier annual local baskets were not located in a reproducible official archive.
- Income by tenure is available nationally through CMHC/Statistics Canada for 2006–2024, but its downloadable workbook is not yet integrated into the clean-cache pipeline. Census-year Owen Sound owner/renter hardship rates remain validation evidence rather than invented annual income series.
- MBM Table 11-10-0066-01 publishes costs for a four-person reference family. Components for other sizes are transparently scaled by the official square-root family-size equivalence; they are derived, not separately observed food or rent budgets.
- Median household cases do not represent the within-type income distribution. National deciles and hardship rates should validate, rather than be replaced by, these budget comparisons.

## Sources

- Statistics Canada Tables 11-10-0017-01, 11-10-0066-01, 11-10-0103-01, and 98-10-0057-01.
- CMHC Rental Market Survey and archived Owen Sound Rental Market Report.
- Grey Bruce Public Health nutritious-food-basket reports.
