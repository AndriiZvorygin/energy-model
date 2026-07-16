from __future__ import annotations

import json
from collections import defaultdict
from datetime import UTC, datetime

from ..cache import RawCache
from .base import SourceObservation, SourceSeries


class BankOfCanadaAdapter:
    base_url = "https://www.bankofcanada.ca/valet/observations"

    def __init__(self, cache: RawCache) -> None:
        self.cache = cache

    def fetch_series(
        self,
        series_id: str,
        *,
        label: str,
        unit: str,
        frequency: str,
        seasonal_adjustment: str,
        nominal_real: str,
        start: str = "1976-01-01",
        monthly_aggregation: str | None = None,
        revision_notes: str = "Bank of Canada observations may be revised according to the source series methodology.",
    ) -> SourceSeries:
        url = f"{self.base_url}/{series_id}/json?start_date={start}"
        path = self.cache.fetch(url, f"bank_of_canada/{series_id}.json")
        payload = json.loads(path.read_text(encoding="utf-8"))
        raw = [(str(row["d"]), float(row[series_id]["v"])) for row in payload.get("observations", []) if row.get(series_id, {}).get("v") not in {None, ""}]
        if monthly_aggregation:
            buckets: dict[str, list[tuple[str, float]]] = defaultdict(list)
            for date, value in raw:
                buckets[date[:7]].append((date, value))
            raw = [
                (f"{month}-01", sum(value for _, value in values) / len(values) if monthly_aggregation == "average" else values[-1][1])
                for month, values in sorted(buckets.items())
            ]
            frequency = "monthly"
        observations = [SourceObservation(date, value, None) for date, value in raw]
        if not observations:
            raise ValueError(f"Bank of Canada series {series_id} contains no observations")
        detail = payload.get("seriesDetail", {}).get(series_id, {})
        return SourceSeries(
            f"Bank of Canada Valet {series_id}", label, unit, "Canada", frequency, seasonal_adjustment, nominal_real,
            "Bank of Canada", url, datetime.now(UTC).isoformat(timespec="seconds"), f"{revision_notes} {detail.get('description', '')}".strip(), observations,
        )
