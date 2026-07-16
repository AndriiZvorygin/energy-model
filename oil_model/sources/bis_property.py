from __future__ import annotations

import csv
from datetime import UTC, datetime

from ..cache import RawCache
from .base import SourceObservation, SourceSeries


class BisPropertyPriceAdapter:
    url = "https://stats.bis.org/api/v1/data/WS_SPP?format=csvfile"
    areas = {
        "XW": "World",
        "5R": "Advanced economies",
        "4T": "Emerging market economies",
        "CA": "Canada",
        "US": "United States",
        "GB": "United Kingdom",
        "DE": "Germany",
        "CN": "China",
        "IN": "India",
        "BR": "Brazil",
    }

    def __init__(self, cache: RawCache) -> None:
        self.cache = cache

    def fetch(self) -> dict[str, SourceSeries]:
        path = self.cache.fetch(self.url, "bis/selected_residential_property_prices.csv", headers={"Accept": "text/csv"})
        rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
        retrieval = datetime.now(UTC).isoformat(timespec="seconds")
        output = {}
        for code, geography in self.areas.items():
            for value_code, nominal_real in (("N", "nominal"), ("R", "real")):
                selected = [row for row in rows if row.get("REF_AREA") == code and row.get("VALUE") == value_code and row.get("UNIT_MEASURE") == "628" and row.get("OBS_VALUE")]
                observations = [SourceObservation(self._quarter_date(str(row["TIME_PERIOD"])), float(row["OBS_VALUE"]), None) for row in selected]
                if not observations:
                    continue
                key = f"bis_{code.lower()}_{nominal_real}_house_prices"
                output[key] = SourceSeries(
                    f"BIS_WS_SPP_{code}_{value_code}_628",
                    f"BIS {geography} residential property prices ({nominal_real})",
                    "index, 2010=100",
                    geography,
                    "quarterly",
                    "source-defined",
                    nominal_real,
                    "Bank for International Settlements",
                    "https://data.bis.org/topics/RPP",
                    retrieval,
                    "BIS selected residential property prices are revised when national sources or representative-series selections change. Aggregates cover participating economies and are not a census of every dwelling.",
                    observations,
                )
        return output

    @staticmethod
    def _quarter_date(period: str) -> str:
        year, quarter = period.split("-Q")
        return f"{year}-{int(quarter) * 3:02d}-01"
