# Living Region systemic-energy contract

`systemic-energy-v1.json` is a generated, versioned handoff from Energy Model
to Living Region. Regenerate it with:

```sh
python scripts/export_living_region_contract.py
```

The contract preserves source dates, retrieval dates, URLs, evidence labels and
limitations. Contextual indicators are not silently converted into Living
Region scenario coefficients. Living Region consumes a checked-in copy of this
file and does not import the Energy Model source tree at runtime.
