# Oil, Liquidity, and Inventory Model

This project builds monthly datasets for global M2, oil prices, and U.S. crude inventories, then runs lag-correlation and regression checks.

## Quick Start

```bash
python3 -m oil_model.pipeline --refresh
```

Single-command regeneration:

```bash
python -m oil_model.pipeline --root .
```

Full v0.1 research release check:

```bash
make release
```

Use `make PYTHON=.venv/bin/python release` when working inside the project virtual environment.

To regenerate every cached source, processed dataset, SQLite table, analysis CSV/Markdown file, and chart from the project root:

```bash
python3 -m oil_model.pipeline --refresh --root .
```

Outputs:

- `data/raw/`: cached source responses.
- `data/processed/monthly_dataset.csv`: joined monthly dataset.
- `data/oil_model.sqlite`: SQLite copy of datasets and analysis tables.
- `analysis/lag_correlations.csv`: GM2 YoY leading oil YoY from 0 to 18 months.
- `analysis/regression_summary.csv`: train/test OLS summaries.
- `analysis/rolling_validation.csv`: rolling-window validation.
- `analysis/second_stage_findings.md`: second-stage interaction, residual, and regime findings.
- `analysis/interaction_model_summary.csv`: GM2/inventory interaction model summaries with HAC standard errors.
- `analysis/residual_model_summary.csv`: comparative-inventory tests on deviations from the GM2-implied oil path.
- `analysis/regime_model_summary.csv`: historical-regime model summaries.
- `analysis/rolling_validation_extended.csv`: 60-, 84-, and 120-month rolling validation with RMSE, MAE, R2, directional accuracy, sign accuracy, and paired error comparisons.
- `analysis/final_model_interpretation.md`: third-stage interpretation of forecast target design and residual diagnostics.
- `analysis/target_comparison_summary.csv`: alternative target tests across nominal price levels, CPI-deflated price levels, GM2 residuals, trailing-average deviations, and forward returns.
- `analysis/residual_diagnostic_summary.csv`: two-step GM2 residual diagnostics using inventory state and regime variables.
- `analysis/executive_summary.md`: final research summary for human readers.
- `analysis/model_card.md`: model documentation, validation method, caveats, and suitable uses.
- `analysis/final_findings_table.csv`: compact table of final locked-model findings.
- `analysis/current_signal_snapshot.md`: latest complete-month signal and residual interpretation.
- `analysis/oil_equity_lead_lag_summary.csv`: oil-equity correlations, lead-lag tests, forecast checks, reverse equity tests, and regime splits.
- `analysis/oil_equity_findings.md`: readable summary of oil-equity lead-lag results.
- `analysis/oil_equity_return_lag_summary.csv`: SP500-oil lead-lag robustness checks using monthly and quarterly returns.
- `analysis/oil_equity_robustness.md`: cautionary note on YoY lead-lag versus return-based timing evidence.
- `analysis/uso_findings.md`: readable findings for USO as a tradable oil-exposure proxy.
- `analysis/uso_lead_lag_summary.csv`: USO-WTI/Brent contemporaneous, lead-lag, and rolling-correlation results.
- `analysis/uso_tracking_residual_summary.csv`: USO benchmark return spreads and tracking residuals by regime.
- `analysis/uso_model_summary.csv`: GM2-only and combined USO YoY models plus the tracking-residual diagnostic.
- `analysis/energy_gdp_lead_lag.csv`: energy, oil, liquidity, GDP, and industrial-production lead-lag tests.
- `analysis/energy_gdp_model_summary.csv`: energy-GDP model summaries, HAC standard errors, and rolling validation metrics where available.
- `analysis/energy_gdp_findings.md`: readable summary of the physical-throughput GDP layer.
- `analysis/integrated_lead_lag_atlas.md`: integrated lead-lag synthesis across liquidity, oil, stocks, inventory, energy, and GDP.
- `analysis/system_signal_hierarchy.csv`: concise hierarchy of signals, targets, relationships, and interpretations.
- `analysis/final_system_interpretation.md`: final integrated macro-system interpretation.
- `charts/*.png`: generated time-series, lag-correlation, and scatter charts.

If `pandas` and `pyarrow` are installed, `data/processed/monthly_dataset.parquet` is also written.

## Sources

- U.S. M2: FRED `M2SL`, Board of Governors H.6 source, billions of USD.
- WTI: FRED `DCOILWTICO`, daily Cushing WTI spot price, averaged to monthly.
- Brent: FRED `DCOILBRENTEU`, daily Brent spot price, averaged to monthly.
- FX: FRED `DEXUSEU`, `DEXCHUS`, and `DEXJPUS`, daily exchange rates averaged to monthly.
- U.S. CPI: FRED `CPIAUCSL`, used to deflate nominal WTI and Brent price levels.
- S&P 500: FRED `SP500`, daily price index averaged to month for oil-equity lead-lag analysis.
- USO: Yahoo Finance chart API adjusted close, aggregated over completed months to monthly average and month-end observations for tradable-oil exposure analysis.
- U.S. real GDP: FRED `GDPC1`, quarterly chained-dollar real GDP.
- U.S. industrial production: FRED `INDPRO`, monthly real-activity proxy.
- U.S. total primary energy consumption: EIA Monthly Energy Review table `T01.03`, series `TETCBUS`.
- U.S. petroleum consumption excluding biofuels: EIA Monthly Energy Review table `T01.03`, series `PMTCBUS`.
- Euro area M2: ECB Data Portal SDMX CSV, `BSI.M.U2.Y.V.M20.X.1.U2.2300.Z01.E`, outstanding stocks, treated as EUR millions.
- Japan M2: Bank of Japan Time-Series Data Search API, database `MD02`, series `MAM1NAM2M2MO`, average amounts outstanding, unit `100 million yen`.
- China M2: IMF/FRED `MYAGM2CNM189N` historical data merged with the current ChinaData public API, which documents People's Bank of China as its primary source. ChinaData overlap is preferred because the FRED/IMF series currently stops in 2019.
- U.S. commercial crude inventory excluding SPR: EIA weekly history page `WCESTUS1`, averaged to monthly.

Optional BIS credit:

```bash
python3 -m oil_model.pipeline --bis-url "https://..."
```

or set `BIS_TOTAL_CREDIT_URL`. The pipeline caches the raw BIS response under `data/raw/bis/` and writes `data/processed/bis_total_credit_quarterly.csv`.

## Formulas

Currency conversion uses same-month average FX:

- U.S. M2 USD = `M2SL * 1e9`
- Euro area M2 USD = `EA_M2_EUR * EURUSD`
- China M2 USD = `CN_M2_CNY / CNY_per_USD`
- Japan M2 USD = `JP_M2_JPY / JPY_per_USD`
- `GM2_USD = US_M2_USD + EA_M2_USD + CN_M2_USD + JP_M2_USD`

Growth rates:

- `GM2_YoY = 100 * (GM2_USD / GM2_USD[t-12] - 1)`
- `Oil_YoY = 100 * (monthly oil price / monthly oil price[t-12] - 1)`
- `Real_Oil = nominal oil price / (CPIAUCSL / 100)`
- `Oil_deviation_12m_avg = 100 * (oil price / trailing prior 12-month average - 1)`
- `Oil_forward_3m_return` and `Oil_forward_6m_return` use future oil prices as targets only; contemporaneous predictors are not shifted forward.
- `SP500_YoY`, `SP500_log_return_1m`, `SP500_forward_3m_return`, and `SP500_forward_6m_return` are computed from monthly average FRED `SP500`.
- `USO_YoY`, `USO_log_return_1m`, `USO_forward_3m_return`, and `USO_forward_6m_return` are computed from monthly adjusted close observations.
- `USO_vs_WTI_return_spread = USO_log_return_1m - WTI_log_return_1m`; the Brent spread is defined analogously.
- `USO_tracking_residual = USO_YoY - WTI_YoY`; `USO_tracking_residual_vs_Brent` uses Brent YoY.

Inventory:

- Monthly crude inventory is the average of weekly EIA `WCESTUS1` observations inside each month.
- Comparative inventory = monthly inventory minus the prior five-year same-month average.
- `CI_zscore = comparative_inventory / prior five-year same-month standard deviation`
- `CI_monthly_change = inventory[t] - inventory[t-1]`

Models:

- `Oil_YoY ~ GM2_YoY_lag`
- `Oil_YoY ~ CI_zscore + CI_monthly_change`
- `Oil_YoY ~ GM2_YoY_lag + CI_zscore + CI_monthly_change`
- Interaction pass: `Oil_YoY ~ GM2_YoY_lag + CI_zscore + CI_monthly_change + GM2_YoY_lag*CI_zscore + GM2_YoY_lag*CI_monthly_change`
- Residual pass: first fit `Oil_YoY ~ GM2_YoY_lag`, then test whether `CI_zscore`, `CI_monthly_change`, inventory surplus, and inventory deficit explain the residual.
- Regime pass: test GM2, inventory, additive, and interaction terms across 2008-2009 financial crisis, 2014-2017 shale, 2020-2021 covid, 2022-2023 war/SPR, and normal periods.

Lag tests evaluate GM2 YoY leading oil YoY from 0 to 18 months. Regressions use a chronological train/test split and rolling 60-month one-step validation where enough observations exist.

## Working Hypothesis

GM2 appears to be a leading oil-momentum indicator: broad liquidity growth tends to line up best with later oil YoY momentum rather than same-month price moves. Comparative inventory may be a physical-market state variable rather than a simple direct predictor.

The core hypothesis is that liquidity drives broad oil-price momentum, while inventory determines whether the physical market amplifies or dampens that impulse. The second-stage tests therefore emphasize interactions, residual deviations from the liquidity-implied path, and explicit historical regimes. A combined model is considered useful only when it improves rolling RMSE or MAE versus GM2-only by at least 5 percent, or materially improves directional accuracy.

## Current Interpretation

The current best primary model is GM2-only for `Oil_YoY`, with the strongest lead-time range clustering around 5 to 6 months in rolling validation and a simple lag-correlation peak at 4 months. A single chronological train/test split previously selected WTI YoY GM2-only lag 9 as the best split-specific model, so the project treats rolling validation as the more stable selection guide.

Comparative inventory does not improve primary rolling RMSE or MAE versus GM2-only by the 5 percent rule. Its stronger role is diagnostic: inventory-state variables explain roughly 10 percent of the GM2-only residual variance for both WTI and Brent, which supports using comparative inventory to interpret deviations, regimes, and physical-market risk rather than as a direct `Oil_YoY` forecasting feature.

Regime caveat: the 2008-2009 financial crisis, 2014-2017 shale adjustment, 2020-2021 covid shock, and 2022-2023 war/SPR period behave differently from normal periods. Any operational reading should compare full-sample and shock-excluded validation.

## Final Interpretation

Global M2 provides the strongest leading signal for oil-price momentum. Comparative inventory adds less value as a direct `Oil_YoY` forecast variable, but it helps explain deviations from the liquidity-implied path. In practical terms, liquidity describes the impulse, while inventory describes the physical-market state through which that impulse is amplified, dampened, or contradicted.

## Integrated Lead-Lag Interpretation

Global M2 is the strongest leading financial signal for oil-price momentum. Stocks mostly reflect risk appetite and growth expectations, adding context rather than improving the locked oil model. Comparative inventory describes the physical oil-market state and helps explain deviations from the GM2-implied price path. Energy consumption anchors real activity, while GDP records the measured economic outcome. Rising GDP per unit of energy shows efficiency and structural change, while the continuing high correlation between energy use and GDP shows the economy remains physically grounded in energy throughput.

Concise hierarchy:

1. Liquidity impulse: GM2 leads oil momentum.
2. Market pricing layer: stocks and oil respond to growth/risk conditions.
3. Physical economy layer: energy use anchors industrial activity and GDP.

## Tradable oil exposure: USO

WTI and Brent are benchmark oil price series. USO is a tradable oil ETF exposure series. USO is analysed separately because its return path can diverge from spot or front-month benchmark oil through roll yield, fund expenses, tracking differences, and ETF structure. In this project, WTI and Brent remain the benchmark oil-price targets, while USO tests what the oil signal looks like for a market participant using a tradable ETF proxy.

The USO layer compares YoY and monthly returns with WTI and Brent over lags from -18 to +18 months, tests GM2-only and combined tradable-exposure models, and reports USO tracking residuals across the project regimes. A public futures-curve series is not currently part of the reproducible pipeline, so the return spread and tracking residual are treated as reduced-form diagnostics for roll and fund-structure effects rather than direct measurements of roll yield.

## Limitations

- M2 definitions vary across jurisdictions; this is a liquidity proxy, not a harmonized monetary aggregate.
- Same-month FX conversion makes USD GM2 sensitive to exchange-rate moves as well as domestic money growth.
- Euro area M2 is an ECB changing-composition aggregate.
- China M2 uses a public PBoC-sourced API for current values because the IMF/FRED no-key feed is stale; keep the cached raw file for auditability.
- EIA inventory is weekly; the monthly value here is a within-month average, not end-of-month stock.
- U.S. comparative inventory is only one physical-market proxy and may miss global inventory, spare capacity, refining margins, OPEC policy, sanctions, shipping disruptions, and curve structure.
- Forward oil returns are target variables that necessarily use future prices; they are included for target-design analysis, not for contemporaneous explanatory features.
- CPI-deflated price levels are descriptive real-price targets, not a complete cost-curve or purchasing-power model.
- Correlations and regressions are descriptive. The validation tables are included to make overfitting visible, not to establish causality.
