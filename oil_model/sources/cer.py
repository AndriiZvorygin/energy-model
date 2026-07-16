from __future__ import annotations

import csv
from datetime import UTC, datetime

from ..cache import RawCache
from .base import SourceObservation, SourceSeries


class CerAdapter:
    """Adapter for documented public CER CSV downloads.

    CER publication pages do not expose one stable API for every commodity table,
    so callers supply the documented public CSV URL and column contract.
    """

    def __init__(self, cache: RawCache) -> None:
        self.cache = cache

    def fetch_csv_series(self, url: str, *, source_id: str, label: str, date_column: str, value_column: str, unit: str, geography: str = "Canada", frequency: str = "monthly") -> SourceSeries:
        path = self.cache.fetch(url, f"cer/{source_id}.csv")
        observations = []
        with path.open(newline="", encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                raw = row.get(value_column)
                if raw in {None, "", "..", "x"}:
                    continue
                observations.append(SourceObservation(str(row[date_column])[:10], float(str(raw).replace(",", "")), None))
        if not observations:
            raise ValueError(f"CER series {source_id} contains no observations")
        return SourceSeries(source_id, label, unit, geography, frequency, "source-defined", "physical quantity", "Canada Energy Regulator", url, datetime.now(UTC).isoformat(timespec="seconds"), "CER commodity data can be revised; confidentiality suppressions may limit detail.", observations)
