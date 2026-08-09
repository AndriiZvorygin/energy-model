PYTHON ?= python3

.PHONY: release verify-release export-living-region-contract

release:
	$(PYTHON) -m pip install -e '.[dev]'
	$(PYTHON) -m pytest -q
	$(PYTHON) -m oil_model.pipeline --root .
	$(PYTHON) scripts/verify_release.py

verify-release:
	$(PYTHON) scripts/verify_release.py

export-living-region-contract:
	$(PYTHON) scripts/export_living_region_contract.py
