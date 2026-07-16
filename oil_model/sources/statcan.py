from __future__ import annotations

import hashlib
import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import requests

from ..cache import RawCache
from .base import SourceObservation, SourceSeries


class StatCanAdapter:
    base_url = "https://www150.statcan.gc.ca/t1/wds/rest"

    def __init__(self, cache: RawCache) -> None:
        self.cache = cache

    def fetch_vector(
        self,
        vector_id: int,
        *,
        label: str,
        unit: str,
        geography: str,
        frequency: str = "monthly",
        seasonal_adjustment: str = "not seasonally adjusted",
        nominal_real: str = "index or physical quantity",
        start: str = "1976-01-01",
        end: str = "2027-12-31",
        revision_notes: str = "Statistics Canada may revise recent and historical observations.",
    ) -> SourceSeries:
        url = f"{self.base_url}/getDataFromVectorByReferencePeriodRange?vectorIds={vector_id}&startRefPeriod={start}&endReferencePeriod={end}"
        path = self.cache.fetch(url, f"statcan/vector-{vector_id}.json")
        payload = json.loads(path.read_text(encoding="utf-8"))
        item = payload[0] if isinstance(payload, list) and payload else payload
        if item.get("status") != "SUCCESS":
            raise ValueError(f"Statistics Canada vector {vector_id} failed: {item}")
        points = item["object"].get("vectorDataPoint", [])
        observations = [
            SourceObservation(str(point["refPer"])[:10], float(point["value"]), str(point.get("releaseTime") or "")[:10] or None)
            for point in points
            if point.get("value") is not None and int(point.get("securityLevelCode", 0)) == 0
        ]
        if not observations:
            raise ValueError(f"Statistics Canada vector {vector_id} contains no public observations")
        return SourceSeries(
            f"StatCan vector v{vector_id}", label, unit, geography, frequency, seasonal_adjustment, nominal_real,
            "Statistics Canada", f"https://www150.statcan.gc.ca/t1/wds/rest/getSeriesInfoFromVector", datetime.now(UTC).isoformat(timespec="seconds"), revision_notes, observations,
        )

    def fetch_table_download(self, product_id: int, language: str = "en") -> Path:
        request_url = f"{self.base_url}/getFullTableDownloadCSV/{product_id}/{language}"
        descriptor = self.cache.fetch(request_url, f"statcan/table-{product_id}-{language}.json")
        payload = json.loads(descriptor.read_text(encoding="utf-8"))
        if payload.get("status") != "SUCCESS" or not payload.get("object"):
            raise ValueError(f"Statistics Canada table {product_id} download lookup failed")
        return self.cache.fetch(str(payload["object"]), f"statcan/table-{product_id}-{language}.zip")

    def table_members(self, product_id: int) -> list[str]:
        path = self.fetch_table_download(product_id)
        with zipfile.ZipFile(path) as archive:
            return archive.namelist()

    def vector_metadata(self, vector_id: int) -> dict[str, object]:
        body = json.dumps([{"vectorId": vector_id}], separators=(",", ":"))
        digest = hashlib.sha256(body.encode()).hexdigest()[:12]
        path = self.cache.root / f"statcan/vector-{vector_id}-metadata-{digest}.json"
        if not path.exists() or self.cache.refresh:
            path.parent.mkdir(parents=True, exist_ok=True)
            response = requests.post(f"{self.base_url}/getSeriesInfoFromVector", data=body, headers={"Content-Type": "application/json"}, timeout=60)
            response.raise_for_status()
            path.write_bytes(response.content)
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload[0]["object"]
