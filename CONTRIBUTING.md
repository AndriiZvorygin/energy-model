# Contributing

Contributions that improve the research quality, source transparency, reproducibility, or educational presentation of the Energy Model are welcome.

## Research Contributions

Open an issue before beginning a substantial new model or dataset. Describe the research question, proposed variables, expected frequency, lag convention, and how the work fits the existing system hierarchy. New modules should remain clearly separated from the locked GM2-only lag-5 benchmark oil model unless the evidence and project scope explicitly support revisiting it.

Research contributions should:

- state a testable hypothesis and decision rule;
- distinguish descriptive association, forecasting evidence, and causal claims;
- use chronological or rolling validation where frequency permits;
- report negative and null results alongside positive findings;
- document shock-period and regime sensitivity;
- prefer interpretable specifications over unnecessary complexity.

## Data Source Documentation

Every new external series should document:

- the primary provider and exact series identifier;
- source URL or API endpoint pattern;
- units, frequency, seasonal adjustment, and revision behavior;
- retrieval date and raw-cache location;
- all resampling, currency conversion, deflation, and derived-field formulas;
- licensing or redistribution constraints.

Do not commit credentials, private datasets, or source material that cannot be redistributed. Public raw responses may be cached when this improves reproducibility and their terms permit it.

## Reproducibility Requirements

Before submitting a change, run:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m oil_model.pipeline --root .
.venv/bin/python -m oil_model.verify_release --root .

cd website
npm install
npm run build
```

Keep model outputs synchronized with pipeline changes. Website-only contributions should not alter analysis outputs. Avoid committing virtual environments, dependency directories, local caches, build directories, environment files, or editor metadata.

## Methodology Review

Methodology changes should explain:

- why the existing specification is insufficient;
- how future leakage is prevented;
- why the validation window and benchmark are appropriate;
- whether HAC/Newey-West or another autocorrelation treatment is used;
- how results change outside the defined shock regimes;
- what evidence would reject the proposed interpretation.

Pull requests should summarize the research conclusion, changed files, validation commands, and any remaining limitations. Reviewers should prioritize leakage, reproducibility, source provenance, regime dependence, and overfitting risk.
