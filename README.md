# Energy Model: Oil, Liquidity, Inventory, and the Real Economy

This project explores how financial conditions, energy markets, physical resource constraints, and economic activity interact over time.

It began as an oil-market model linking global liquidity to oil-price momentum and is expanding toward broader energy-system modelling. The repository combines a reproducible Python research pipeline with a Node.js educational website that explains the evidence for non-technical readers.

> This is an interpretive research project, not a trading system or investment recommendation.

## Overview

The current model separates the energy-macro system into distinct analytical layers:

```text
Global liquidity
        ↓
Oil price momentum
        ↓
Physical market state
        ↓
Tradable exposure
        ↓
Energy throughput
        ↓
Economic activity
```

The locked oil model uses year-over-year growth in G4 global M2, lagged five months, to describe WTI and Brent price momentum. Comparative inventory, equities, tradable oil exposure, realised crude prices, energy consumption, industrial production, and GDP are analysed as related but conceptually separate layers.

## Research Framework

1. **Liquidity impulse:** G4 GM2 is tested as a leading financial signal for oil-price momentum.
2. **Physical oil-market state:** Comparative inventory helps diagnose whether oil is rich or cheap relative to the liquidity-implied path.
3. **Market pricing:** WTI and Brent are benchmarks, USO represents investor-accessible exposure, and the S&P 500 provides risk and growth context.
4. **Physical economy:** Energy and petroleum consumption anchor real activity, while industrial production and real GDP record economic outcomes at different frequencies.
5. **Efficiency and structural change:** GDP per unit of energy tracks how much measured output is produced from physical energy throughput.

The project prioritizes interpretable specifications, chronological validation, explicit lag conventions, HAC/Newey-West standard errors, shock-period checks, and reproducible source caching.

## Current Validated Findings

- The strongest simple G4 GM2 correlation with WTI and Brent YoY occurs at a four-month lead: `0.532` for WTI and `0.523` for Brent.
- Rolling validation supports a nearby five-to-six-month lead range. The final benchmark oil model is locked at **GM2-only lag 5**.
- The locked 60-month rolling validation RMSE is `31.628` for WTI YoY and `32.358` for Brent YoY.
- Comparative inventory does not improve the primary rolling RMSE or MAE by the project's five-percent decision rule. Its validated role is a residual, state, and regime diagnostic.
- Inventory and regime variables explain approximately `14.8%` of WTI and `13.5%` of Brent residual variance around the GM2-implied path.
- S&P 500 monthly returns are primarily contemporaneous with oil returns. Stocks add growth and risk context but do not improve the locked oil model by the five-percent rule.
- U.S. energy consumption growth and real GDP growth have a contemporaneous quarterly correlation of `0.680`; petroleum consumption growth and real GDP growth correlate at `0.738`.
- GDP per unit of energy rises over time, consistent with efficiency gains and structural change while economic activity remains physically grounded in energy throughput.

See [the executive summary](analysis/executive_summary.md), [model card](analysis/model_card.md), and [integrated lead-lag atlas](analysis/integrated_lead_lag_atlas.md) for the complete interpretation.

![Integrated lead-lag network](charts/final_lead_lag_network.png)

## System Architecture

```text
energy-model/
├── oil_model/              # Python research pipeline
├── website/                # Vite/React educational website
├── analysis/               # generated research findings and tables
├── charts/                 # generated research charts
├── data/                   # cached sources, seeds, and processed datasets
├── docs/                   # research and deployment documentation
├── scripts/                # release verification entry points
├── tests/                  # pipeline and reproducibility tests
├── README.md
├── LICENSE
├── CITATION.cff
├── CONTRIBUTING.md
└── pyproject.toml
```

The Python pipeline owns data acquisition, transformations, models, validation, written findings, and chart generation. The website is a static presentation layer: its build reads existing files from `analysis/` and `charts/`; it does not run or alter the research model.

## Website

The educational website uses Node.js, TypeScript, Vite, React, Tailwind CSS, Recharts, and React Router. It presents the model as an explanatory research atlas rather than a trading dashboard.

```bash
cd website
npm install
npm run dev
```

Create a production build with `npm run build`. See [website/README.md](website/README.md) for local development and [docs/deployment.md](docs/deployment.md) for GitHub Pages and custom-domain deployment.

## Data Sources

Primary public sources include:

- **Federal Reserve Economic Data (FRED):** U.S. M2, WTI, Brent, exchange rates, CPI, S&P 500, U.S. real GDP, and industrial production.
- **European Central Bank:** euro-area M2.
- **Bank of Japan:** Japan M2.
- **People's Bank of China-sourced public data and IMF/FRED history:** China M2.
- **U.S. Energy Information Administration:** crude inventories, total and petroleum energy consumption, refiner acquisition costs, first purchase prices, and imported crude costs.
- **Yahoo Finance-compatible public chart data:** USO adjusted close.

Raw source responses are cached under `data/raw/` for auditability. Detailed series identifiers, units, transformations, and formulas are documented in [analysis/model_card.md](analysis/model_card.md) and [analysis/latest_source_values.md](analysis/latest_source_values.md).

## Reproducibility

Python 3.10 or newer is required. From the repository root:

```bash
python -m venv .venv
.venv/bin/python -m pip install -e '.[dev,parquet]'
.venv/bin/python -m pytest -q
.venv/bin/python -m oil_model.pipeline --root .
.venv/bin/python -m oil_model.verify_release --root .
```

The complete release workflow is also available through:

```bash
make PYTHON=.venv/bin/python release
```

Build the website after the research artifacts exist:

```bash
cd website
npm install
npm run build
```

The pipeline can use the committed raw-data cache. Use `--refresh` only when intentionally retrieving current source data and regenerating the research release.

## Limitations

- The G4 M2 aggregate is a USD-converted liquidity proxy, not a harmonized global monetary statistic.
- Same-month foreign-exchange conversion mixes domestic money growth with currency movements.
- U.S. comparative inventory does not represent the full global physical oil balance.
- Monthly averages can conceal intra-month market disruptions.
- Linear models can miss nonlinear policy, geopolitical, production, refining, shipping, and futures-curve effects.
- YoY variables overlap and are autocorrelated; their lead-lag relationships are more useful for macro-cycle interpretation than precise market timing.
- Historical correlations and rolling forecasts are descriptive and do not establish causality.
- Shock regimes such as 2008-2009, 2014-2017, 2020-2021, and 2022-2023 can behave differently from normal periods.

## Future Research Directions

This repository is intended to grow from an oil-market model into a broader energy-system research framework. Future modules may explore:

- energy supply adequacy
- energy surplus and EROI
- inflation transmission
- employment quality
- economic stress indicators
- social-system responses

These modules are research directions only and are **not currently implemented**.

## License and Citation

The code is released under the [MIT License](LICENSE). Please use [CITATION.cff](CITATION.cff) when citing the software or research framework. Contributions are welcome under the standards in [CONTRIBUTING.md](CONTRIBUTING.md).
