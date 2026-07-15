# Economic Output Quality

## Research question

This module asks whether energy throughput and energy affordability align differently with headline measured output, net productive capacity, realized household prosperity, and financialization or asset valuation. It does not label financial or service activity as valueless and does not create a single output-quality score.

## Four lenses

1. **Headline measured output:** real GDP, real GDP per capita, real gross domestic income, and real final private domestic sales.
2. **Net productive capacity:** official real net domestic product, net investment, capital consumption, industrial and manufacturing output, and freight activity.
3. **Realized household prosperity:** real median income and earnings, hours and employment structure, plus an experimental household-command measure.
4. **Financialization and asset valuation:** finance and insurance, real estate, household leverage and debt service, and equity valuation are kept separate.

## Household-command experiment

`HouseholdCommand = real median household income - real average shelter expenditure - real average food expenditure - real average utilities/fuels/public-services expenditure`.

All components are published in `economic_output_quality.csv`. This is an experimental proxy, not an official disposable-income measure: it combines a median income with mean consumer-unit expenditures, the utilities category is broader than household energy alone, and household composition differs across sources.

## Initial relationship tests

The largest available contemporaneous energy-growth correlation is 0.805 for Real NDP per capita. Each row in `energy_output_quality_correlations.csv` also reports lag correlation, rolling-window stability (20 quarters for quarterly measures or 10 years for annual measures), a distributed-lag coefficient sum, recession and expansion correlations, and expanding out-of-sample performance versus a one-period autoregressive benchmark.

## Interpretation limits

GDP measures current production, not total wealth. Real GDP adjusts for inflation; official real NDP accounts for capital consumption without manually subtracting non-additive chained-dollar components. Asset valuations can diverge from productive capacity, but that divergence is not evidence that finance, insurance, real estate, or services are intrinsically unproductive. Results use latest-vintage observations and are descriptive rather than causal.

Latest observation present in the module: 2026-06-01.

## Data gaps retained explicitly

This first release does not yet include a harmonized productive-capital-stock series, construction output, electricity consumption, a financial-sector profit share, a housing-price-to-income ratio, or an imputed-housing-services share. GDP-by-industry coverage is represented narrowly by separate finance/insurance and real-estate value-added shares rather than a complete industry panel. These are documented next steps, not silently proxied or folded into a composite.
