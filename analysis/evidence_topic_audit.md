# Evidence Topic Audit

Evidence summaries use canonical `geography:topic` keys and one `generate_evidence_summary(geography, topic)` interface.

Generated geography/topic combinations: 31.

## Remaining Manually Named Topics

The following analytical topic names and indicator groups remain explicitly configured because they express research semantics rather than route behavior:

- `affordability`: indicator groups and component IDs are declared in `config/evidence_topics.json`.
- `food`: indicator groups and component IDs are declared in `config/evidence_topics.json`.
- `housing`: indicator groups and component IDs are declared in `config/evidence_topics.json`.
- `symptom/<rule-id>`: names and required evidence come from the jurisdiction symptom-rule files.
- `overview`, `current-state`, `regimes`, and `symptoms`: canonical evaluator names shared across geographies.

## Geography-Specific Configuration

- `us`: source namespace, classifier field names, symptom source, or indicator-geography filters are configured without route-specific code.
- `canada`: source namespace, classifier field names, symptom source, or indicator-geography filters are configured without route-specific code.
- `ontario`: source namespace, classifier field names, symptom source, or indicator-geography filters are configured without route-specific code.
- `alberta`: source namespace, classifier field names, symptom source, or indicator-geography filters are configured without route-specific code.
- `global`: source namespace, classifier field names, symptom source, or indicator-geography filters are configured without route-specific code.

Adding a future geography requires configuration and generated source data, not a new Python or React route branch.
