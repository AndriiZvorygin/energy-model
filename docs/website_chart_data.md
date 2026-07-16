# Website Chart Data

## Ownership

The Python pipeline owns research data and writes versioned chart datasets to `website/public/generated/`. React loads those files on demand by route. The browser may apply documented visual transformations, but it does not refit research models or replace generated findings.

Run the complete chain from the repository root:

```bash
.venv/bin/python -m oil_model.pipeline --root .
cd website
npm run validate:chart-data
npm run build
```

`oil_model.website_data.write_website_chart_data` generates:

- `manifest.json`
- `charts/`, containing versioned multi-series research datasets (legacy root copies remain for compatibility)
- `indicators/`, containing one schema-version-1 history file for every Current State indicator
- `oil-price-layers.json`
- `gm2-oil-lead.json`
- `oil-residual-ci.json`
- `energy-gdp.json`
- `oil-equities.json`
- `uso-tracking.json`
- `output-quality-headline.json`, `output-quality-net-output.json`, `output-quality-capacity.json`, `output-quality-household.json`, and `output-quality-financial.json`
- `output-quality-correlations.json`
- shared lag, rolling-performance, recession, event, cross-layer, live symptom-evaluation, current-classification, regime-score, and regime-history files

The live diagnostic contract consists of `current-classification.json`, `symptom-evaluations.json`, `regime-scores.json`, and `regime-history.json`. These files are generated from the same 27 indicator histories used by Current State. The website only renders the published evidence; it never embeds or recalculates symptom and regime rules.

## Canadian Namespace

`website/public/generated/canada/` contains `manifest.json`, `current-state.json`, `canada-us-comparison.json`, classifier outputs, and `indicators/`. Canada is the domestic website default. Each Canadian or provincial indicator adds geography, national/provincial level, domestic/external input status, cross-country comparability, seasonal adjustment, nominal/real status, source identifier, per-observation source date and revision limitations.

Food and housing data use three namespaces: `global/` for FAO and BIS evidence, `canada/` for Statistics Canada and Canadian BIS histories, and `us/` for BLS, FHFA, and U.S. BIS histories. Their manifests preserve native geography and frequency. International food commodities are not relabelled as retail groceries; property purchase prices are not combined with shelter-service costs. `futureClassifierMetadata.status` is `metadata_only_not_scored`, so these fields can support later rule design without changing current symptom or regime scores.

New Canadian purchasing-power indicators use `futureClassifierMetadata.status: "Not yet evaluated"`. This is presentation and rule-preparation metadata only. Household-income ratios are quarterly and include only completed-quarter CPI or housing averages; wage ratios are monthly. Components, formulas, reference periods, source dates, and latest-vintage revision warnings are embedded in every indicator payload.

Statistics Canada WDS release timestamps are preserved. Bank of Canada Valet observations retain their native observation dates and the pipeline retrieval timestamp. These are latest-vintage histories; they do not yet constitute a complete real-time vintage archive.

The website build fails when a manifest dataset is missing required metadata, units, sources, final observation dates, ordered ISO dates, or unique dates.

Each indicator file includes latest and previous values, 3- and 12-month context, full-history and post-2000 percentiles, momentum, a seven-point historical range, interpretation direction and label, source URL, confirming/conflicting indicators, calculation details, and full observations with explicit `null` values. The Current State page loads this manifest lazily and does not duplicate readings in React source.

```json
{
  "schemaVersion": 1,
  "id": "ci-zscore",
  "label": "Comparative inventory z-score",
  "unit": "standard deviations",
  "interpretationDirection": "context-dependent",
  "latest": { "date": "2026-06-01", "value": -1.38, "historicalPercentile": 14.2 },
  "referenceRanges": { "p10": -1.63, "historicalMedian": 0.14, "p90": 2.45 },
  "observations": [{ "date": "1987-08-01", "value": -1.18 }]
}
```

## Schema

Every time-series file contains:

```json
{
  "schemaVersion": "1.1.0",
  "id": "oil-price-layers",
  "title": "Oil price layers",
  "description": "...",
  "plainLanguageSummary": "...",
  "howToRead": "...",
  "calculation": { "formula": "...", "explanation": "...", "example": "..." },
  "patternsToWatch": ["..."],
  "limitations": ["..."],
  "sourceNotes": ["..."],
  "transformation": {
    "type": "raw",
    "referenceStart": "2007-01-01",
    "referenceEnd": "2019-12-01",
    "mean": null,
    "standardDeviation": null,
    "statistics": { "WTI": { "mean": 75.0, "standardDeviation": 22.0, "n": 156 } }
  },
  "frequency": "monthly",
  "dateRange": { "start": "1986-01-01", "end": "2026-06-01" },
  "series": [
    {
      "key": "WTI",
      "label": "WTI",
      "unit": "USD per barrel",
      "source": "FRED DCOILWTICO",
      "status": "measured",
      "defaultVisible": true,
      "finalObservationDate": "2026-06-01",
      "transformations": ["raw", "indexed", "yoy", "zscore", "pct_change"]
    }
  ],
  "observations": [{ "date": "1986-01-01", "WTI": 22.93 }],
  "annotations": [],
  "availableTransformations": ["raw", "indexed", "yoy", "zscore", "pct_change"],
  "evidenceLabel": "Contextual indicator",
  "methodology": {},
  "staticFigure": "final_oil_price_layers_time_series.png",
  "generatedAt": "..."
}
```

Missing observations are JSON `null`, never fabricated zeros. Dates are ISO `YYYY-MM-DD`. Each series documents units, provenance, measured/derived/modelled/experimental status, valid transformations, and its own final observation date.

## Transformations

Transformations are implemented in `chartUtils.ts` and memoized by the chart shell:

- `raw`: generated observation
- `indexed`: first non-missing value in the selected display range equals 100
- `yoy`: current value relative to 12 months earlier, four quarters earlier, or one annual observation earlier
- `pct_change`: change from the prior observation
- `zscore`: `z = (observation - historical mean) / historical standard deviation` using the dataset's fixed published reference period

Changing the visible range does not change a z-score baseline. The transformed row retains hidden raw-value metadata for the tooltip. A visually shifted lag series also retains its original source month, displayed comparison month, selected lag, and locked/exploratory status.

Controls expose only the intersection of transformations valid for all visible series. Raw series with unrelated units are placed in synchronized panels. The interface does not use a dual axis to force visual agreement.

The current datasets are small enough to render at full resolution, so no visual downsampling is applied. Downloads and tooltips always use full-resolution observations.

## Adding An Indicator

Canadian indicator histories and diagnostics are namespaced below `website/public/generated/canada/`. The provisional classifier publishes `current-classification.json`, `symptom-evaluations.json`, and `regime-scores.json` there. These files retain separate global, national, Ontario, and Alberta contributions, expose availability and freshness-adjusted coverage, and mark household stress as insufficient data.

1. Add or derive the field in the Python pipeline without forward-filling unavailable future observations.
2. Add the indicator to the system-response catalogue/current-state generation. `oil_model/website_data.py` maps those rows to the indicator contract; add explicit interpretation-direction metadata there when the indicator is not context-dependent.
3. Assign valid transformations, unit, source, status, evidence label, fixed transformation reference period, plain-language summary, calculation example, patterns, limitations, and final-observation behavior.
4. Run the Python and website test suites.
5. Regenerate the pipeline and run `npm run validate:chart-data`.

## Adding An Event

Add the event to `_events()` in `oil_model/website_data.py`, including an ID, date range, category, neutral explanation, and affected transmission layers. Add its ID to relevant datasets. Event annotations organize historical context and must not be worded as causal proof.

## Connecting A Publication Figure

Set `staticFigure` in the dataset metadata and ensure the PNG remains in `charts/`. `website/scripts/generate-data.mjs` copies publication PNGs to `website/public/charts/`. The interactive chart’s download menu and expandable `PublicationFigure` component then link to that asset.

## GitHub Pages

Vite uses `base: '/energy-model/'`. Dataset, chart, and route URLs use `import.meta.env.BASE_URL`, so development works at `http://localhost:5173/energy-model/` and production works at `https://andriizvorygin.github.io/energy-model/`. The post-build step creates a static entry point for every known route and retains `404.html` as a fallback, preserving direct React Router navigation and refreshes under GitHub Pages.
