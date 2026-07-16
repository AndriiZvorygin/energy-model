# Canadian Data Audit

## Scope

Canadian energy-economic conditions with global oil-market and global-liquidity inputs.

This release adds a **provisional transparent Canadian classifier** without modifying the existing U.S. classifier or locked GM2 lag-5 oil model. Household stress remains insufficiently evaluated, and Ontario and Alberta contributions are preserved separately.

## Implemented Core

The Canadian namespace contains **25 core global/Canadian indicators** plus Ontario and Alberta context. Core date coverage spans `1976-01-01` to `2026-07-01`, but every card retains its own observation and source-release date.

Primary sources are Statistics Canada WDS vectors and the Bank of Canada Valet API. Physical crude balances distinguish production, exports, imports, refinery inputs and inventories. Monthly real GDP by industry is the main high-frequency output measure. Labour uses rates and employment relative to population rather than unemployment alone.

## Revision And Vintage Limitations

Statistics Canada release timestamps are retained per observation, but full historical vintages are not yet archived. Current results are therefore latest-vintage histories with source-date provenance, not a real-time backtest. Monthly GDP, labour, CPI, physical balances and quarterly debt-service data can be revised on different schedules. Bank of Canada observation dates are retained; Valet does not provide a publication-vintage archive in these responses.

## Geography And Comparability

Canada is the domestic default. Ontario inherits global oil/liquidity inputs but uses provincial CPI and labour histories. Alberta appears only as a producing-region comparison. No values from Canada, Ontario, Alberta and the United States are mixed into a regime score. Similar Canadian and U.S. values can have different meanings because energy production, trade, currencies, housing systems, population growth and industrial structure differ.

## Missing Or Proposed

The catalogue identifies unresolved WCS pricing, refined-product consumption, refinery utilization, natural-gas production, household energy expenditure, income/saving, insolvency, wage/hour and Ontario industry-employment series. They remain proposed rather than being filled with commercial data, copied U.S. measures or interpolated provincial observations.

## Provisional Classification

The versioned rules use global GM2 and benchmark oil; Canadian crude production, exports, imports, refinery inputs and inventories; real CAD oil and energy CPI; monthly total/manufacturing/resource GDP; employment, unemployment, prime-age employment and full-time share; and debt service. The next calibration step is real-time-vintage validation and the later addition of wages, hours, household income, expenditure burden and insolvency evidence.
