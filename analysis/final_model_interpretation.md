# Final Model Interpretation

## Current Forecasting Core

- GM2-only remains the preferred primary Oil_YoY forecasting specification under the 60-month rolling validation rule.
- Comparative inventory is not promoted to a direct forecasting feature because it does not improve rolling RMSE or MAE versus GM2-only by at least 5%.

## Target Design

- WTI_YoY: best model `gm2_only` lag 5 with rolling RMSE 31.628 and MAE 22.295.
- Brent_YoY: best model `gm2_only` lag 5 with rolling RMSE 32.358 and MAE 23.990.
- WTI: best model `ci_diagnostic` lag 0 with rolling RMSE 17.338 and MAE 11.856.
- Brent: best model `ci_diagnostic` lag 0 with rolling RMSE 19.850 and MAE 13.379.
- real_WTI: best model `gm2_plus_ci` lag 18 with rolling RMSE 7.207 and MAE 5.470.
- real_Brent: best model `ci_diagnostic` lag 0 with rolling RMSE 8.421 and MAE 5.682.
- WTI_deviation_12m_avg: best model `gm2_only` lag 3 with rolling RMSE 16.315 and MAE 12.333.
- Brent_deviation_12m_avg: best model `gm2_only` lag 3 with rolling RMSE 17.148 and MAE 12.848.
- WTI_GM2_path_residual: best model `gm2_plus_ci` lag 17 with rolling RMSE 33.301 and MAE 22.458.
- Brent_GM2_path_residual: best model `gm2_plus_ci` lag 18 with rolling RMSE 34.377 and MAE 24.221.
- WTI_forward_3m_return: best model `ci_diagnostic` lag 0 with rolling RMSE 19.675 and MAE 14.069.
- Brent_forward_3m_return: best model `gm2_only` lag 0 with rolling RMSE 19.889 and MAE 13.053.
- WTI_forward_6m_return: best model `gm2_only` lag 0 with rolling RMSE 23.791 and MAE 17.728.
- Brent_forward_6m_return: best model `gm2_only` lag 0 with rolling RMSE 24.270 and MAE 18.625.

## Two-Step Residual Framework

- WTI_YoY: Step A GM2 lag 5; Step B residual explained variance 0.148, residual directional accuracy 0.518.
- Brent_YoY: Step A GM2 lag 5; Step B residual explained variance 0.135, residual directional accuracy 0.504.

## Interpretation

- The practical interpretation is two-layered: GM2 describes broad oil-price momentum; comparative inventory describes physical-market state and residual risk around that path.
- CI can be useful for diagnosing whether oil is rich or cheap relative to liquidity-implied momentum, especially across regimes, without being a robust direct Oil_YoY forecast improver.
- Regime caveat: 2008-2009, 2014-2017, 2020-2021, and 2022-2023 are high-shock periods. Results should be checked both with and without those windows before using the model operationally.

## Regeneration

Run `python3 -m oil_model.pipeline --refresh --root .` to rebuild raw data, processed data, analysis tables, SQLite tables, and charts.
