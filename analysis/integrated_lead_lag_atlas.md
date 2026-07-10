# Integrated Lead-Lag Atlas

## Core Interpretation

Global M2 is the strongest leading financial signal for oil-price momentum. Stocks mostly reflect risk appetite and growth expectations, adding context rather than improving the locked oil model. Comparative inventory describes the physical oil-market state and helps explain deviations from the GM2-implied price path. Energy consumption anchors real activity, while GDP records the measured economic outcome. Rising GDP per unit of energy shows efficiency and structural change, while the continuing high correlation between energy use and GDP shows the economy remains physically grounded in energy throughput.

## Which Signals Lead Oil?

- G4 GM2 YoY is the primary leading signal. The final oil model is locked at GM2-only lag 5, with simple lag correlations peaking around 4 months.
- SP500 does not qualify as an independent oil forecast signal because SP500-augmented models do not clear the 5% rolling RMSE/MAE improvement rule versus locked GM2-only lag 5.

## Which Signals Move With Oil?

- Stocks and oil share a market-pricing layer: both respond to risk appetite, inflation/growth expectations, and macro-financial conditions.
- Oil and industrial activity have some contemporaneous or near-contemporaneous relationship, but this belongs more to the real-activity layer than the locked oil-price forecast.

## Which Signals Lag Or Record The Outcome?

- Real GDP records the measured economic outcome at quarterly frequency.
- Industrial production gives a higher-frequency real-activity read.
- Energy consumption and petroleum consumption move closely with GDP, showing the physical throughput base beneath measured output.

## Where Do Stocks Fit?

Stocks fit as a coincident risk/growth proxy. The full-sample SP500 YoY versus oil YoY test shows the strongest lag correlation at negative lag, meaning oil leads stocks under the project convention, but the sign is negative. Because YoY variables are overlapping and autocorrelated, this is best interpreted as a broad macro stress-pattern signal for equities, not as a precise equity timing rule.

YoY lead-lag is useful for macro cycle interpretation because it smooths short-term noise and emphasizes broad expansions or contractions. Monthly return lead-lag is more relevant for market timing because it uses non-overlapping one-month changes, but it is also noisier and more regime-dependent.

## Where Does Comparative Inventory Fit?

Comparative inventory is a physical oil-market state variable. It explains residuals around the GM2-implied oil path and helps diagnose rich/cheap oil pricing, but it is not the primary Oil YoY forecast variable.

## How Energy And GDP Fit

Energy use anchors real activity. Petroleum consumption growth and real GDP growth have the strongest current energy-GDP relationship, while GDP per energy rises over time. The synthesis is that GDP remains physically grounded in energy throughput, while efficiency and structural change allow more measured GDP per unit of energy.

## Signal Hierarchy

- Liquidity impulse: G4 GM2 YoY -> Oil YoY momentum (leads; WTI rolling RMSE / Brent rolling RMSE 31.628 / 32.358). Global M2 is the strongest leading financial signal for oil-price momentum.
- Oil momentum validation: GM2 lag correlation -> WTI / Brent YoY (leads; Pearson correlation 0.532 / 0.523). Correlation peaks slightly earlier than rolling forecast selection, but both point to a leading liquidity impulse.
- Physical oil-market state: Comparative inventory -> Oil residual vs GM2 path (diagnoses residual/state; Residual explained variance WTI / Brent 0.148 / 0.135). Inventory helps explain rich/cheap deviations but is not promoted to the primary forecast model.
- Market pricing layer: SP500 -> Oil YoY and equity risk (coincident risk/growth proxy; Peak correlation WTI / Brent -0.661 / -0.691). Stocks add context around risk appetite and growth expectations but do not improve the locked oil model by the 5% rule.
- Physical economy layer: Energy consumption -> Real GDP (moves with / anchors; Correlation 0.680). Energy use is the physical throughput base of GDP at quarterly scale.
- Physical economy layer: Petroleum consumption -> Real GDP (moves with / anchors; Correlation 0.738). Petroleum consumption growth has the strongest current real-economy relationship in the energy layer.
- Industrial activity: Energy consumption -> Industrial production (moves with; Correlation 0.642). Industrial production is the higher-frequency activity proxy tied to physical energy throughput.
- Measured outcome: GDP per energy -> Efficiency / structural change (trend over time; Direction rising). Rising GDP per unit of energy shows efficiency gains and structural change, not full physical decoupling.
