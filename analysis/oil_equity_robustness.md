# Oil-Equity Robustness

## Purpose

This robustness pass checks the SP500-oil lead-lag result using return horizons that are less overlapping than YoY growth rates.

## Main Caution

The SP500 YoY versus oil YoY result peaks at lag -13 with a negative sign, meaning oil leads stocks by about 13 months under the project convention. Because YoY variables are overlapping and autocorrelated, this should be interpreted as a broad macro stress-pattern signal, not as a precise equity timing rule.

## YoY Versus Return Lead-Lag

- YoY lead-lag: The YoY lag result is useful for macro-cycle interpretation because YoY variables smooth monthly noise, but the same overlap also creates autocorrelation.
- Monthly return lead-lag: more relevant for tradable market timing, but usually noisier and less stable.
- Quarterly return lead-lag: a middle ground between noisy monthly returns and overlapping YoY cycles.

## Return-Based Results

- monthly_log_return, WTI_log_return_1m: strongest full-sample correlation 0.324 at lag 0 (contemporaneous).
- monthly_log_return, Brent_log_return_1m: strongest full-sample correlation 0.298 at lag 0 (contemporaneous).
- quarterly_return, WTI_quarterly_return: strongest full-sample correlation -0.457 at lag 1 (stocks lead oil).
- quarterly_return, Brent_quarterly_return: strongest full-sample correlation -0.406 at lag 1 (stocks lead oil).

## Normal Versus Shock Periods

- WTI_log_return_1m: full best lag 0 corr 0.324; normal-period best lag 11 corr -0.356; shock-period best lag 1 corr 0.387. Oil-leading-stocks does not clearly survive outside shock regimes.
- Brent_log_return_1m: full best lag 0 corr 0.298; normal-period best lag 12 corr -0.433; shock-period best lag 0 corr 0.369. Oil-leading-stocks does not clearly survive outside shock regimes.

## Interpretation

The YoY oil-leading-stocks pattern is best treated as an oil-shock stress signal for equities. Monthly and quarterly return checks are the better evidence for market timing, and they should be expected to be noisier and more regime-dependent.
