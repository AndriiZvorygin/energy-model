# Physical Realised Crude Price Findings

## Interpretation

No single barrel price exists. WTI and Brent are traded benchmarks, USO is an investor-accessible futures-fund exposure, refiner acquisition cost measures what refiners paid for crude, first purchase price measures the first arm's-length physical sale from the lease, and landed import cost includes the delivered cost of imported crude at the port of discharge.

The locked benchmark model remains unchanged: WTI and Brent Oil_YoY use G4 GM2 YoY lagged five months. This layer compares physical price realization and benchmark basis; it does not reopen model selection.

## Tracking Results

- Strongest absolute contemporaneous relationship with comparative inventory is USO tradable exposure (USO_YoY) at correlation -0.456, n=231.
- Strongest absolute GM2-price relationship in the descriptive 0-18 month scan is RAC composite at lag 4, correlation 0.541, n=262.
- `RAC_vs_WTI_spread` explained by CI z-score and monthly inventory change: full-sample HAC OLS R2 0.001, test RMSE 2.694.
- `RAC_vs_Brent_spread` explained by CI z-score and monthly inventory change: full-sample HAC OLS R2 0.038, test RMSE 3.901.
- `first_purchase_vs_WTI_spread` explained by CI z-score and monthly inventory change: full-sample HAC OLS R2 0.014, test RMSE 2.431.
- `landed_import_vs_Brent_spread` explained by CI z-score and monthly inventory change: full-sample HAC OLS R2 0.032, test RMSE 7.273.

## Latest Physical-Price Snapshot

- WTI benchmark: 2026-06 level $85.520/bbl, YoY 25.452%.
- Brent benchmark: 2026-06 level $86.110/bbl, YoY 20.527%.
- USO tradable exposure: 2026-06 level $106.440/share, YoY 45.589%.
- RAC composite: 2026-05 level $97.700/bbl, YoY 54.442%.
- domestic first purchase: 2026-04 level $97.750/bbl, YoY 57.636%.
- imported landed cost: 2026-04 level $89.700/bbl, YoY 44.421%.
- RAC domestic: 2026-05 level $99.480/bbl, YoY 55.389%.
- RAC imported: 2026-05 level $94.880/bbl, YoY 53.478%.
- imported FOB cost: 2026-04 level $86.130/bbl, YoY 48.602%.

## Scope Note

The release includes aggregate imported FOB and landed costs in the processed dataset. API-gravity and sulphur cross-sections are deferred: they are optional, frequently withheld or sparse, and would add many narrow series without changing the aggregate physical-price question in this pass.

Sources: EIA Petroleum Marketing Monthly history series R0000____3, R1200____3, R1300____3, F000000__3, I000000004, and I000000008; FRED WTI/Brent; Yahoo Finance USO adjusted close. Formulas: YoY = 100*(price/price[t-12]-1); physical spread = physical realised price minus its named monthly benchmark.
