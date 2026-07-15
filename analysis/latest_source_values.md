# Latest Source Values

Retrieved at: `2026-07-10T16:24:24+00:00`

Latest complete GM2 month: **2026-05**
G4 GM2 USD: **1.02409e+14**

## G4 Components

| Component | Native value | Native unit | FX to USD | USD value | Source | Series |
|---|---:|---|---:|---:|---|---|
| US M2 | 23052.3 | USD_billion | 1 | 2.30523e+13 | FRED | `M2SL` |
| Euro area M2 | 1.63818e+07 | EUR_million | 1.1681 | 1.91357e+13 | ECB Data Portal | `BSI.M.U2.Y.V.M20.X.1.U2.2300.Z01.E` |
| China M2 | 353670 | CNY_billion | 0.147067 | 5.20131e+13 | ChinaData/PBoC proxy plus IMF/FRED history | `china-m2-money-supply; MYAGM2CNM189N` |
| Japan M2 | 1.29809e+06 | JPY_billion | 0.00632299 | 8.20783e+12 | Bank of Japan | `MD02:MAM1NAM2M2MO` |
| G4 total |  |  |  | 1.02409e+14 | Computed | `G4_GLOBAL_M2_USD` |

## Latest Raw Source Dates

| Source | Latest date | Latest native value | Unit | Adapter source |
|---|---|---:|---|---|
| US M2 | 2026-05 | 23052.3 | FRED native units | FRED:M2SL |
| Euro area M2 | 2026-05 | 1.63818e+13 | EUR | ECB BSI.M.U2.Y.V.M20.X.1.U2.2300.Z01.E |
| China M2 | 2026-05 | 3.5367e+14 | CNY | IMF/FRED MYAGM2CNM189N merged with ChinaData PBoC-sourced API |
| Japan M2 | 2026-05 | 1.29809e+15 | JPY | BOJ MD02:MAM1NAM2M2MO |
| EURUSD | 2026-07 | 1.1416 | FRED native units | FRED:DEXUSEU |
| CNY per USD | 2026-07 | 6.7914 | FRED native units | FRED:DEXCHUS |
| JPY per USD | 2026-07 | 161.655 | FRED native units | FRED:DEXJPUS |
| U.S. CPI | 2026-05 | 333.979 | FRED native units | FRED:CPIAUCSL |
| S&P 500 | 2026-07 | 7498.09 | FRED native units | FRED:SP500 |
| USO adjusted close monthly average | 2026-06 | 122.035 | USD | Yahoo Finance chart adjusted close:USO |
| USO adjusted close month-end | 2026-06 | 106.44 | USD | Yahoo Finance chart adjusted close:USO |
| Real GDP | 2026-01 | 24180.4 | FRED native units | FRED:GDPC1 |
| Industrial production | 2026-05 | 102.647 | FRED native units | FRED:INDPRO |
| WTI | 2026-06 | 85.5195 | FRED native units | FRED:DCOILWTICO |
| Brent | 2026-06 | 86.1105 | FRED native units | FRED:DCOILBRENTEU |
| Crude inventory excl SPR | 2026-06 | 416300 | thousand barrels | EIA WCESTUS1 |
| RAC composite | 2026-05 | 97.7 | dollars per barrel | EIA Petroleum Marketing Monthly:R0000____3 |
| RAC domestic | 2026-05 | 99.48 | dollars per barrel | EIA Petroleum Marketing Monthly:R1200____3 |
| RAC imported | 2026-05 | 94.88 | dollars per barrel | EIA Petroleum Marketing Monthly:R1300____3 |
| Domestic first purchase price | 2026-04 | 97.75 | dollars per barrel | EIA Petroleum Marketing Monthly:F000000__3 |
| Imported crude FOB cost | 2026-04 | 86.13 | dollars per barrel | EIA Petroleum Marketing Monthly:I000000004 |
| Imported crude landed cost | 2026-04 | 89.7 | dollars per barrel | EIA Petroleum Marketing Monthly:I000000008 |
| Total primary energy consumption | 2026-03 | 7.8865 | Quadrillion Btu | EIA MER T01.03:TETCBUS Total Primary Energy Consumption |
| Petroleum consumption | 2026-03 | 3.00206 | Quadrillion Btu | EIA MER T01.03:PMTCBUS Petroleum Consumption (Excluding Biofuels) |

## Oil And Inventory

- WTI latest monthly value: 2026-06 = 85.5195
- Brent latest monthly value: 2026-06 = 86.1105
- Crude inventory latest value: 2026-06 = 416,300 thousand barrels
- Comparative inventory latest value: 2026-06 = -27,263.6 thousand barrels

## Missing Or Stale Sources

- GM2 is complete only through 2026-05; later monthly rows exist through 2026-07 but are partial.
- Source(s) limiting latest complete G4 month: US M2, Euro area M2, China M2, Japan M2.
