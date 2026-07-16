# Refinery-Driven Presentation Architecture

The observatory has one analytical authority: the Python refinery invoked by:

```bash
python -m oil_model.pipeline --root . --refresh
```

The website is a renderer. It must not classify evidence, choose a regime, calculate a current value, or compose a data-dependent conclusion.

## Data Flow

```text
Official source adapters and cached observations
                |
                v
Transforms, indicators, models and classifiers
                |
                v
Self-describing indicator and chart JSON
                |
                v
evidence-summary.json
                |
                v
presentation-manifest.json
                |
                v
React renderers
```

`config/evidence_topics.json` defines geography namespaces and shared topic evaluators. Every summary is produced through `generate_evidence_summary(geography, topic)` and receives a canonical key such as `canada:current-state`. `config/presentation_rules.json` maps routes to structured `{ geography, topic }` pairs and defines presentation policy. `oil_model/presentation.py` resolves those pairs, dates, confidence, counts and provenance into the final website contract.

## Ownership Rules

The refinery owns:

- current values, changes, percentiles and dates
- interpretation direction and evidence status
- symptom and regime status
- current diagnostic narratives
- confidence, coverage and freshness
- geography/topic-to-evidence mapping
- provenance and input hashes

React owns:

- layout, typography and responsive behavior
- expansion, filtering and chart interaction
- accessible labels for controls and symbols
- loading and contract-error states

Stable educational definitions may remain in page or chart metadata, but any sentence containing a current condition, count, date, score, direction, comparison or model conclusion must come from generated data.

## Generated Contracts

- `manifest.json`: chart and indicator discovery
- `evidence-summary.json`: normalized supporting, mixed, contradicting and detailed insufficient evidence
- `presentation-manifest.json`: route-level interpretation, confidence, coverage, observation range and provenance
- jurisdiction classifier files: source symptom, regime and clock results

The website build validates all required fields and fails when a configured route references a missing canonical evidence key.

## Adding A Page

1. Generate the underlying indicators or analytical result in Python.
2. Select or add a shared topic evaluator in `config/evidence_topics.json`.
3. Map the route to `{ geography, topic }` in `config/presentation_rules.json`.
4. Render `GeneratedRouteEvidenceSummary` on the page.
5. Add schema and behavior tests.

Do not add a current analytical sentence directly to a React component.

Adding a future geography requires source metadata plus a geography entry in `config/evidence_topics.json`. Route-specific Python and React branches are not part of the extension path.
