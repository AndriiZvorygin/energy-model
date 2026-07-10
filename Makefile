PYTHON ?= python

.PHONY: release verify-release

release:
	$(PYTHON) -m pip install -e '.[dev]'
	$(PYTHON) -m pytest -q
	$(PYTHON) -m oil_model.pipeline --root .
	$(PYTHON) scripts/verify_release.py

verify-release:
	$(PYTHON) scripts/verify_release.py
