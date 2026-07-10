# Model Card

## Purpose

Interpret monthly oil-price momentum through a global-liquidity signal, then use comparative inventory and regime context to diagnose residual deviations.

## Data Sources

- FRED: U.S. M2 `M2SL`, FX `DEXUSEU`/`DEXCHUS`/`DEXJPUS`, WTI `DCOILWTICO`, Brent `DCOILBRENTEU`, CPI `CPIAUCSL`.
- ECB Data Portal: euro area M2.
- Bank of Japan: Japan M2.
- ChinaData/PBoC proxy plus IMF/FRED history: China M2.
- EIA: U.S. crude stocks excluding SPR `WCESTUS1`.

## Core Formulas

- `GM2_USD = US_M2_USD + EA_M2_EUR*EURUSD + CN_M2_CNY/CNY_per_USD + JP_M2_JPY/JPY_per_USD`.
- `GM2_YoY = 100 * (GM2_USD / GM2_USD[t-12] - 1)`.
- `Oil_YoY = 100 * (monthly oil price / monthly oil price[t-12] - 1)`.
- `comparative_inventory = current inventory - prior five-year same-month average`.
- `CI_zscore = comparative_inventory / prior five-year same-month standard deviation`.

## Target Definitions

- Primary target: WTI YoY and Brent YoY.
- Diagnostic targets: GM2-implied residuals, nominal price levels, CPI-deflated price levels, trailing 12-month deviations, and forward 3-month/6-month returns.

## Lag Convention

`GM2_YoY_lag_5` means oil at month `t` is predicted using GM2 YoY from `t-5`. The final reporting model is locked at lag 5.

## Validation Method

Primary validation uses 60-month rolling one-step predictions. Supporting checks include 84-month and 120-month rolling windows, chronological train/test splits, directional accuracy, sign accuracy, paired error comparisons, HAC standard errors, high-leverage month flags, and shock-excluded reruns.

## Current Best Model

- WTI YoY: GM2-only lag 5, rolling RMSE 31.628, MAE 22.295.
- Brent YoY: GM2-only lag 5, rolling RMSE 32.358, MAE 23.990.

## Known Caveats

- G4 M2 is a proxy, not a harmonized monetary aggregate.
- USD conversion blends domestic money growth with FX moves.
- U.S. comparative inventory is not global oil inventory.
- Monthly averaging can hide intra-month shocks.
- Linear OLS models are descriptive and can miss nonlinear policy/geopolitical breaks.

## Shock Periods

- Financial crisis: 2008-2009.
- Shale regime: 2014-2017.
- Covid shock: 2020-2021.
- War/SPR period: 2022-2023.

## Suitable Uses

- Monthly macro/commodity research.
- Interpreting oil momentum relative to global liquidity.
- Diagnosing rich/cheap residuals using inventory and regime state.
- Scenario framing for human analysts.

## Unsuitable Uses

- Short-term trading signals.
- Standalone price forecasts without analyst review.
- Replacing physical oil-market analysis.
- Forecasting during acute geopolitical or policy shocks without overrides.
