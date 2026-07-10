# Energy-GDP Lead-Lag Findings

## Physical-Economy Hypothesis

This layer tests whether energy use behaves like the physical throughput base of measured real activity, while GDP per unit of energy captures efficiency, technology, and partial decoupling.

## Lead-Lag Evidence

- Energy_consumption_growth vs Real_GDP_growth: strongest correlation 0.680 at lag 0 (quarterly).
- Energy_consumption_growth vs Industrial_production_YoY: strongest correlation 0.642 at lag 0 (monthly).
- Oil_consumption_growth vs Real_GDP_growth: strongest correlation 0.738 at lag 0 (quarterly).
- WTI_YoY vs Real_GDP_growth: strongest correlation 0.419 at lag 0 (quarterly).
- WTI_YoY vs Industrial_production_YoY: strongest correlation 0.410 at lag 1 (monthly).
- GM2_YoY vs Industrial_production_YoY: strongest correlation -0.271 at lag -8 (monthly).
- GM2_YoY vs Real_GDP_growth: strongest correlation -0.372 at lag -2 (quarterly).

## Energy Intensity

- GDP per energy is higher at the latest usable quarter (2026Q1) than at the beginning of the sample, consistent with efficiency gains, structural change, or partial decoupling.

## Model Evidence

- Real_GDP_growth: best rolling model `regime_real_activity_model` (quarterly) RMSE 0.801, MAE 0.629.
- Industrial_production_YoY: best rolling model `regime_real_activity_model` (monthly) RMSE 1.447, MAE 1.070.
- Energy_consumption_growth: best rolling model `energy_demand_model` (quarterly) RMSE 2.714, MAE 2.179.
- Forward_Real_GDP_growth: best rolling model `oil_stress_model` (quarterly) RMSE 2.834, MAE 1.634.

## Interpretation

- If energy consumption and GDP are tightly linked at quarterly scale, energy should be described as the physical throughput base of GDP.
- Rising GDP per energy means efficiency and structural change allow more GDP per unit of energy.
- If oil prices predict weaker future activity mainly during high-burden or shock regimes, oil should be described as a stress signal rather than a universal GDP predictor.

## Model Hierarchy

GM2 leads oil momentum. CI explains oil residual/state. SP500 reflects risk appetite. Energy anchors real activity. GDP records the measured economic outcome.
