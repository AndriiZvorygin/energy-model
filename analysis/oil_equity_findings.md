# Oil-Equity Lead-Lag Findings

## Scope

This layer tests whether oil leads stocks, stocks lead oil, or both mostly behave as coincident risk/growth assets responding to common macro and liquidity factors.

## Lead-Lag Convention

- Positive lag means the stock market leads oil.
- Negative lag means oil leads the stock market.
- Zero means contemporaneous.

## Correlation Evidence

- SP500 YoY vs WTI_YoY: strongest full-sample correlation is -0.661 at lag -13 (oil leads stocks).
- SP500 YoY vs Brent_YoY: strongest full-sample correlation is -0.691 at lag -13 (oil leads stocks).
- Caution: YoY variables are overlapping and autocorrelated, so the lag result is a macro stress-pattern signal rather than a precise equity timing rule. Monthly and quarterly return robustness checks are in `analysis/oil_equity_robustness.md`.

## Forecast Evidence

- WTI_YoY: best SP500-augmented model is `gm2_plus_sp500_plus_ci` at SP500 lag 12; it does not pass the 5% improvement rule versus locked GM2-only lag 5.
- Brent_YoY: best SP500-augmented model is `gm2_plus_sp500` at SP500 lag 4; it does not pass the 5% improvement rule versus locked GM2-only lag 5.

## Reverse Direction

- Best forward-equity-return oil specification is `WTI_oil_shock_regime` for SP500_forward_3m_return, RMSE 6.716.

## Interpretation

If SP500-augmented oil models fail the 5% rolling RMSE/MAE rule, stocks should be treated as a coincident risk/growth proxy rather than an independent oil forecast signal.
If oil helps predict forward equity returns mainly inside shock regimes, oil should be treated as a regime-risk signal for stocks rather than a general equity timing tool.
