# Second-Stage Oil Liquidity Inventory Findings

## Data Status

- Latest complete G4 GM2 month: 2026-05
- Latest complete G4 GM2 USD: 1.02409e+14
- All lagged GM2 features use only values observed at or before `t - lag`; inventory state variables are same-month physical-market conditions.

## Selection Rule

- Rolling validation is primary. A combined model is treated as useful only if it improves rolling RMSE or MAE versus the same-lag GM2-only model by at least 5%, or materially improves directional accuracy.
- The chronological train/test split is retained as a secondary check.
- HAC/Newey-West standard errors are reported in the model summary CSVs.

## Best Rolling Models

- WTI_YoY best GM2-only: lag 5, RMSE 31.628, MAE 22.295, directional accuracy 0.498.
- WTI_YoY best combined: `interaction_zscore` lag 5, RMSE 31.903, MAE 21.994; it does not pass the 5% error-improvement rule versus same-lag GM2.
- Brent_YoY best GM2-only: lag 5, RMSE 32.358, MAE 23.990, directional accuracy 0.498.
- Brent_YoY best combined: `interaction_zscore` lag 5, RMSE 32.153, MAE 23.274; it does not pass the 5% error-improvement rule versus same-lag GM2.

## Inventory Residual Test

- WTI_YoY: the best residual specification by test RMSE uses GM2 lag 7 with residual-model R2 0.109. Coefficients and HAC p-values are in `analysis/residual_model_summary.csv`.
- Brent_YoY: the best residual specification by test RMSE uses GM2 lag 7 with residual-model R2 0.104. Coefficients and HAC p-values are in `analysis/residual_model_summary.csv`.

## Regime And Shock Checks

- Main shock periods flagged: financial_crisis_2008_2009, covid_2020_2021, war_spr_2022_2023, shale_regime_2014_2017. Shock-excluded rolling reruns are included in `analysis/rolling_validation_extended.csv` with `sample=excluding_shocks`.
- Non-shock sample months with usable rows: 367.
- Excluding shock target months, WTI_YoY best 60m rolling model is `gm2_only` lag 4, RMSE 18.628, MAE 16.199.
- Excluding shock target months, Brent_YoY best 60m rolling model is `gm2_only` lag 3, RMSE 18.528, MAE 15.244.
- Low split-error regime check: WTI_YoY `regime_gm2` / war_spr_2022_2023 lag 8, test RMSE 18.474.
- Low split-error regime check: WTI_YoY `regime_gm2` / war_spr_2022_2023 lag 9, test RMSE 18.730.
- Low split-error regime check: Brent_YoY `regime_gm2` / war_spr_2022_2023 lag 8, test RMSE 18.878.
- Low split-error regime check: Brent_YoY `regime_gm2` / war_spr_2022_2023 lag 9, test RMSE 19.157.
- Low split-error regime check: WTI_YoY `regime_gm2` / financial_crisis_2008_2009 lag 10, test RMSE 19.399.
- Low split-error regime check: WTI_YoY `regime_gm2` / financial_crisis_2008_2009 lag 9, test RMSE 19.708.

## Interpretation

- GM2 remains the cleaner leading oil-momentum signal in these interpretable linear tests.
- Comparative inventory should be read as a physical-market state variable: its direct additive coefficient is not enough by itself; the useful question is whether inventory amplifies, dampens, or explains deviations from the liquidity-implied path.
- Where combined models fail the 5% rolling-error rule, the result should be stated as a failure of CI as a direct predictor, not as proof that inventory is irrelevant to risk periods or residual deviations.
