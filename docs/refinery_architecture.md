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

`config/presentation_rules.json` maps routes to generated evidence topics and defines presentation policy. `oil_model/evidence_summary.py` converts classifier and indicator outputs into consistent evidence states. `oil_model/presentation.py` resolves configured routes, dates, confidence, counts and provenance into the final website contract.

## Ownership Rules

The refinery owns:

- current values, changes, percentiles and dates
- interpretation direction and evidence status
- symptom and regime status
- current diagnostic narratives
- confidence, coverage and freshness
- route-to-evidence mapping
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

The website build validates all required fields and fails when a configured route references a missing evidence topic.

## Adding A Page

1. Generate the underlying indicators or analytical result in Python.
2. Add an evidence topic derived from those outputs.
3. Map the route to that topic in `config/presentation_rules.json`.
4. Render `GeneratedRouteEvidenceSummary` on the page.
5. Add schema and behavior tests.

Do not add a current analytical sentence directly to a React component.
