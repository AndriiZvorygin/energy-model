# USO Tradable Oil Exposure Findings

## Scope

WTI and Brent remain the benchmark oil-price targets. USO is added as a tradable ETF exposure proxy because its investor return path can diverge from benchmark oil through futures roll yield, contango/backwardation, fund expenses, tracking differences, and ETF structure.

## Lead-Lag Evidence

- USO_YoY vs WTI_YoY: strongest correlation is 0.863 at lag 0 (contemporaneous), n=231.
- USO_YoY vs Brent_YoY: strongest correlation is 0.859 at lag 0 (contemporaneous), n=231.
- USO_log_return_1m vs WTI_log_return_1m: strongest correlation is 0.800 at lag 0 (contemporaneous), n=242.
- USO_log_return_1m vs Brent_log_return_1m: strongest correlation is 0.773 at lag 0 (contemporaneous), n=242.

## Model Comparison

- Best rolling USO tradable-exposure specification is `uso_gm2_ci_sp500` at GM2 lag 10, RMSE 27.315, MAE 21.086.
- Best combined USO model is lag 10; it passes a 5% improvement rule versus the same-lag USO GM2-only baseline.
- The locked benchmark oil model is unchanged: WTI_YoY ~ GM2_YoY lag 5. USO is interpreted as a separate market-pricing layer, not a replacement target.

## Tracking Residuals By Regime

- all: mean USO minus WTI YoY residual -7.067; mean monthly USO-WTI return spread -0.770.
- financial_crisis_2008_2009: mean USO minus WTI YoY residual -11.888; mean monthly USO-WTI return spread -1.870.
- shale_regime_2014_2017: mean USO minus WTI YoY residual -11.599; mean monthly USO-WTI return spread -1.158.
- covid_2020_2021: mean USO minus WTI YoY residual -32.799; mean monthly USO-WTI return spread -3.398.
- war_spr_2022_2023: mean USO minus WTI YoY residual 14.117; mean monthly USO-WTI return spread 0.838.
- normal_period: mean USO minus WTI YoY residual -3.082; mean monthly USO-WTI return spread -0.200.

## Residual Model

- CI and regime variables explain USO tracking residual variance with full-sample R2 0.283. This is a reduced-form diagnostic for ETF/market-structure divergence, not a direct benchmark-oil forecast.

## Latest Snapshot

- Latest USO tracking month in the processed dataset is 2026-06: USO YoY 45.589, WTI YoY 25.452, USO minus WTI residual 20.137.

## Roll/Structure Note

A clean public WTI futures-curve source is not yet wired into the release pipeline. Until a documented curve source is added, USO tracking residuals and USO-WTI return spreads serve as reduced-form evidence of roll yield, contango/backwardation exposure, expenses, tracking error, and ETF structure.
