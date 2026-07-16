# Energy Model Educational Website

## Purpose

This Node.js/TypeScript application explains a Canadian-centred Energy Model for human readers. Canada is the default domestic geography; Ontario provides regional context, global liquidity and benchmark oil remain upstream inputs, and the United States remains a separate comparison dataset.

The website is an educational research atlas, not a trading dashboard. It does not run models or fetch research data in the browser.

## Relationship to the Python Pipeline

The Python package under `../oil_model/` owns data acquisition, transformations, model estimation, validation, Markdown findings, CSV summaries, and PNG chart generation.

The Python pipeline writes chart-ready JSON under `public/generated/`. The website build also runs `scripts/generate-data.mjs`, which:

- reads selected CSV files from `../analysis/`;
- extracts relevant sections from generated Markdown reports;
- writes the typed presentation module `src/data/generated.ts`;
- copies selected generated charts from `../charts/` to `public/charts/`.

`public/generated/charts/` contains multi-series research views. `public/generated/indicators/` contains one complete historical series and interpretation contract per Current State indicator. `manifest.json` indexes both collections. The Vite build validates required metadata, units, chronological dates, duplicate dates, null handling, reference ranges, and interpretation metadata before compiling React.

`public/generated/canada/` is an independent namespace containing its own manifest, current-state evidence, country-comparison foundation, indicator histories, provisional symptoms, and regime scores. Geography, source-release dates, seasonal adjustment, nominal/real status, comparability limitations, availability, and freshness remain explicit. The classifier is calculated by Python from versioned root configuration files; React only presents the generated results.

Affordability evidence is split across `public/generated/global/`, `public/generated/canada/`, and `public/generated/us/`. The manifests index self-describing food commodity, consumer food, property purchase-price, and shelter-cost histories. `oil_model.affordability` also writes multi-series chart contracts and descriptive food-transmission results without invoking or modifying either classifier.

The Canadian namespace also publishes quarterly household disposable income, income per person, CPI-deflated real income, saving, monthly Canada/Ontario wages, and purchasing-power ratios. Monthly price indexes are averaged over completed quarters for household-income comparisons; quarterly income is never interpolated or forward-filled into monthly rows. Wage-based comparisons remain monthly and distinct from household-income measures.

The system-response routes consume the generated indicator catalogue, current-state table, energy-burden validation, physical-tightness summary, labour lead scan, historical episode library, symptom evaluations, and regime scores. The browser does not recalculate those results. Version-controlled rules live in `../config/symptom_rules.json` and `../config/regime_rules.json`; Python publishes separate monthly-nowcast and confirmed-quarterly results, including coverage, freshness, conflicts, persistence, sensitivity, and revised-data warnings.

## Research Sections

- `/canada`: Canadian evidence overview
- `/canada/current-state`: default Canadian Current State
- `/canada/energy`, `/canada/economy`, `/canada/labour`, `/canada/households`: Canadian evidence layers
- `/canada/ontario`: Ontario CPI and labour context with global inputs
- `/compare/canada-us`: native-source country comparisons
- `/current-state/us`: existing U.S. Current State and classifier evidence
- `/canada/regimes`: provisional Canadian regime candidates and regional split
- `/canada/symptoms`: Canadian symptom evidence and missing-data states
- `/system-response`: complete transmission framework
- `/current-state`: Canadian Current State alias
- `/regimes`: interpretable system-state sequence
- `/symptoms`: observable patterns, confirmations, and alternatives
- `/indicators`: searchable source and definition catalogue
- `/episodes`: interactive historical comparisons
- `/energy-burden`: affordability measures and benchmark validation
- `/labour`: hours, wages, flexible work, and employment structure
- `/output-quality`: headline output, net capacity, household prosperity, financialization, and energy comparisons
- `/affordability`, `/affordability/food`, `/affordability/housing`: global, Canadian, and U.S. food and housing evidence
- `/canada/food`, `/canada/housing`: Canadian and Ontario detail
- `/compare/food`, `/compare/housing`: cross-country transmission and housing comparisons
- `/methodology`: sources, lags, validation, and limitations
- `/roadmap`: implemented, experimental, and proposed work

Evidence labels are shown consistently. No page reduces the system to one red/green score, and social or institutional measures remain proposed research rather than implemented claims.

The website is therefore downstream of the research pipeline. It must not change the locked model or existing analysis outputs.

Interactive research charts load versioned JSON from `public/generated/`. These files are generated by `oil_model.website_data` and focused downstream modules such as `oil_model.affordability`, validated before each development or production build, and fetched lazily by route. Current State cards show 10-year sparklines, historical ranges, percentiles, freshness, and metadata-driven interpretations; each opens the full source history with event/recession overlays, episode comparison, CSV export, and an accessible table. See [the chart-data documentation](../docs/website_chart_data.md) for the schema and extension workflow.

## Local Development

Requirements:

- Node.js 20 or newer
- npm
- generated project files under `../analysis/` and `../charts/`

From `website/`:

```bash
npm install
npm run dev
```

The `predev` script refreshes the website data module and chart copies before starting Vite. The development server prints its local URL in the terminal.

## Build Process

Create a production build:

```bash
npm install
npm run build
```

The build performs these steps:

1. regenerate website data from the existing research artifacts;
2. validate the Python-generated chart manifest and datasets;
3. type-check the TypeScript application;
4. create an optimized static site under `website/dist/`.

Run component and data-transformation tests with:

```bash
npm test
```

Preview the production build locally:

```bash
npm run preview
```

For repeatable CI installations, use `npm ci` instead of `npm install`.

## Deployment

For the GitHub Pages project path `AndriiZvorygin/energy-model`, run:

```bash
npm ci
npm run build:pages
```

Deploy the contents of `website/dist/`. The `build:pages` script configures Vite and React Router for the `/energy-model/` base path.

For a root-domain deployment, use the standard `npm run build`. For a custom subpath such as `andrii.zvorygin.ca/energy-model`, use:

```bash
npm run build -- --base /energy-model/
```

The host should serve `index.html` as the fallback for client-side routes. See [../docs/deployment.md](../docs/deployment.md) for GitHub Pages workflow guidance and custom-domain details.

## Refreshing Research Content

When research outputs are intentionally updated, run from the repository root:

```bash
.venv/bin/python -m oil_model.pipeline --root .
.venv/bin/python -m oil_model.verify_release --root .
cd website
npm run build
```

Review changes to `src/data/generated.ts` and `public/charts/` before publication.

## Interactive Chart System

The reusable components under `src/components/charts/` provide series visibility and focus controls, valid transformations, time ranges, brush navigation, lag exploration, event and regime overlays, exact tooltips, tap-locked inspection, latest values, downloads, citations, URL state, accessible tables, indicator sparklines, historical-range bars, modal histories, and visual statistical explainers. `ChartDetails.tsx` renders the permanent plain-language summary and the shared expandable calculation, reading, pattern, limitation, source, observation-date, and relevant worked-graphic disclosure.

Z-scores use the fixed reference period published in each dataset. Zooming or selecting a shorter visible range never recalculates the baseline. Z-score tooltips retain the raw observation, transformed value, historical mean, standard deviation, and reference period; shifted-series tooltips retain the original and displayed dates and locked/exploratory lag status.

Raw series with different units use synchronized panels. They share a panel only after a valid unitless transformation such as indexing or z-scoring. No visual downsampling is currently applied; full-resolution values remain available for tooltips and downloads.

## Diagnostic Evidence Summaries

Current State, Regimes, Symptoms, Canada, Food, Housing, and Affordability pages place a compact interpretation and evidence matrix before the detailed charts. These matrices are generated by the Python pipeline in `public/generated/evidence-summary.json`; website components only render the published supporting, mixed, contradicting, and insufficient classifications. Selecting a count filters the matrix, and selecting a row reveals its values, source date, calculation, limitations, sparkline, historical range, and full interactive history when available.

## Theme And Chart Contrast

The default `Auto` theme is resolved entirely in the browser from the reader's local time: light from 07:00 through 18:59 and dark from 19:00 through 06:59. Readers can choose an explicit Light or Dark override from the navigation; that preference is stored locally. The theme is applied before React starts to avoid a light/dark flash during page loading.

Research charts use shared semantic CSS colors with separate high-contrast light and dark palettes. Series identity remains consistent across themes, while axes, grids, annotations, tooltips, and range controls adapt to the active surface.
