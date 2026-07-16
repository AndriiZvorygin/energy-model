# Canadian Income, Wage, And Property-Price Source Audit

## Implemented Sources

- **Table 36-10-0112-01:** household disposable income (`v62305981`), household final consumption expenditure (`v62305982`), and household saving rate (`v62305984`), quarterly from 1961. Income and consumption are seasonally adjusted annual rates in millions of current Canadian dollars.
- **Table 17-10-0009-01:** Canada quarterly population (`v1`) from 1971. It is matched to the same quarter as income; no monthly population or income values are created.
- **Table 14-10-0063-01:** Canada and Ontario average hourly wage rates for all employees (`v2132579`, `v2153099`) and goods/services confirmation series, monthly from 1997, unadjusted for seasonality.
- **Table 14-10-0223-01:** Canada and Ontario average weekly earnings (`v79311153`, `v79311309`), monthly from 2001, seasonally adjusted. These SEPH estimates confirm rather than replace LFS hourly wages.
- **Table 18-10-0169-01:** archived broad residential property price indexes for a six-CMA composite, Ottawa, Toronto, and Calgary from 2017 Q1 through 2021 Q4. The source includes new and resale transactions but is inactive and has no Canada or Ontario aggregate.
- **Table 18-10-0273-01:** active new condominium apartment price indexes for Ottawa, Toronto, Calgary, and Edmonton from 2017 Q1. These cover new condominium apartments only.

## Definitions And Alignment

Disposable income per person divides the annual-rate household-income flow by the matching quarterly population. The result is therefore annualized CAD per person; it is not divided by four. Real disposable income per person is a transparent CPI-deflated derivative because no directly published national quarterly real-per-person series with the required history was identified.

Monthly CPI and housing indexes are averaged from all three months of each completed quarter before comparison with income. Missing or partial quarters are omitted. Quarterly income is never forward-filled or interpolated to monthly frequency. Wage-based affordability remains monthly and is analytically separate because average wages describe employed workers, while household disposable income includes broader income and transfers.

## Property-Price Finding

No active official broad Canada- or Ontario-wide transaction-price index was identified in the audited Statistics Canada tables. NHPI remains the current national new-housing measure. The inactive six-CMA RPPI and active metro new-condominium indexes are published separately and are not spliced into one history.

## Remaining Gaps

No directly published national quarterly real disposable-income-per-person series with the required history was identified. Ontario quarterly household income is available only through newer distributional household-account products with shorter coverage and a different analytical construction, so it is not mixed with the national accounts denominator in this release. A consistent monthly permanent-employee wage history was not added; the LFS all-employee hourly wage remains the primary wage measure and SEPH weekly earnings are a separate confirmation series.

## Later Classifier Candidates

The generated metadata marks, but does not evaluate, candidate evidence for food prices outgrowing disposable income or wages; rent, shelter, and mortgage-interest costs outgrowing income; residential property prices diverging from income; declining real disposable income per person; and a falling saving rate alongside rising essential costs. Calibration and historical validation belong to a later classifier task.

## Revisions And Vintages

All histories are latest-vintage Statistics Canada observations retrieved at pipeline generation. Per-observation release dates are retained where supplied, but the project does not yet hold complete real-time vintages for national accounts, population, or LFS wages. National accounts and population can undergo historical revisions; current LFS wage estimates can also be revised and are composition-sensitive.
