# Model Findings

Generated at: `2026-07-10T12:38:39+00:00`

## Lag Correlations

- Best GM2 lead time for WTI YoY: 4 months (correlation 0.532, n=263)
- Best GM2 lead time for Brent YoY: 4 months (correlation 0.523, n=263)

## Regression Selection

- Best single-signal model by test RMSE: WTI_YoY a_gm2 lag 9 test RMSE 20.985, test R2 0.370733
- Best combined model by test RMSE: WTI_YoY c_gm2_inventory lag 6 test RMSE 23.417, test R2 0.301729
- Best overall model by test RMSE: WTI_YoY a_gm2 lag 9 test RMSE 20.985, test R2 0.370733

## Combined Model Comparisons

- Brent_YoY lag 5: combined RMSE 24.948 does not beat GM2-only RMSE 21.658 by -15.19% vs GM2-only.
- Brent_YoY lag 5: combined RMSE 24.948 beats CI-only RMSE 45.779 by 45.50% vs CI-only.
- WTI_YoY lag 6: combined RMSE 23.417 does not beat GM2-only RMSE 20.985 by -11.59% vs GM2-only.
- WTI_YoY lag 6: combined RMSE 23.417 beats CI-only RMSE 46.218 by 49.33% vs CI-only.

## Rolling Validation

- WTI_YoY a_gm2 lag 5: rolling RMSE 31.628, rolling R2 0.36079, n=202.
- WTI_YoY a_gm2 lag 6: rolling RMSE 31.809, rolling R2 0.353214, n=201.
- WTI_YoY a_gm2 lag 4: rolling RMSE 32.292, rolling R2 0.334906, n=203.
- Brent_YoY a_gm2 lag 5: rolling RMSE 32.358, rolling R2 0.346382, n=202.
- WTI_YoY a_gm2 lag 7: rolling RMSE 32.475, rolling R2 0.329032, n=200.
- Brent_YoY a_gm2 lag 4: rolling RMSE 32.619, rolling R2 0.33656, n=203.

## Regime Caveats

- 2008: financial-crisis oil collapse can dominate liquidity relationships and produce high-leverage observations.
- 2014 to 2016: shale supply growth and OPEC strategy shifts can weaken a pure liquidity signal.
- 2020: pandemic demand shock and extreme oil-market dislocation are not normal monetary-transmission observations.
- 2022: sanctions, SPR releases, and war-driven energy risk premia can make inventory and price behavior regime-specific.

All findings above are computed from the generated CSV files. No assumed 5 to 10 month lead is used.
