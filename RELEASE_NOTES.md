# v0.1 Research Release

## Final Model Conclusion

The locked v0.1 research model keeps GM2-only lag 5 as the primary Oil YoY momentum signal. Rolling validation shows the strongest stable lead-time range for G4 GM2 is roughly 5 to 6 months, while simple lag correlations peak at 4 months for both WTI and Brent.

Comparative inventory is not promoted to a direct Oil YoY forecasting feature. It does not improve primary rolling RMSE or MAE versus GM2-only by the 5% rule. Its role is diagnostic: comparative inventory and regime variables help explain whether oil is rich or cheap versus the liquidity-implied path.

## Current Signal Snapshot

Latest complete signal month: 2026-05.

- G4 GM2 USD: $102.41 trillion.
- GM2 YoY: 9.588%.
- WTI YoY: 64.288%.
- Brent YoY: 66.229%.
- Comparative inventory: -6,283.900 thousand barrels.
- CI z-score: -0.294, near normal.
- Locked lag-5 GM2-implied WTI YoY: 38.180%.
- WTI residual versus the GM2-implied path: +26.108 percentage points.

Interpretation: current WTI is materially richer than the lagged GM2-implied path, while comparative inventory is near normal and does not send a strong surplus or deficit signal.

## Validation Results

- WTI YoY, GM2-only lag 5: rolling RMSE 31.628, MAE 22.295, directional accuracy 49.8%.
- Brent YoY, GM2-only lag 5: rolling RMSE 32.358, MAE 23.990, directional accuracy 49.8%.
- CI/regime residual explained variance: 0.148 for WTI and 0.135 for Brent.
- Tests pass with `pytest`: 9 tests.
- Release verification checks required analysis files, charts, and data artifacts.

## Caveats

- This is a descriptive monthly research model, not a trading system.
- G4 M2 is a proxy and is sensitive to FX conversion.
- U.S. comparative inventory is not global inventory.
- The model is weakest around crisis, pandemic, war, OPEC/policy, shale-cycle, sanctions, and shipping shocks.
- The model does not directly include spare capacity, refining margins, curve structure, physical differentials, or geopolitical event data.

## Reproduction

Run the full release pipeline:

```bash
make release
```

or, with an explicit interpreter:

```bash
make PYTHON=.venv/bin/python release
```
