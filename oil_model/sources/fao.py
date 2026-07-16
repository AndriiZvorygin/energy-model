from __future__ import annotations

import json
import html
import re
import zipfile
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from xml.etree import ElementTree

import requests

from ..cache import RawCache
from .base import SourceObservation, SourceSeries


class FaoFoodPriceAdapter:
    page_url = "https://www.fao.org/worldfoodsituation/foodpricesindex/en/"
    workbook_url = "https://www.fao.org/media/docs/worldfoodsituationlibraries/default-document-library/ffpi-data-2026-07.xlsx?sfvrsn=63809b16_123"
    csv_url = "https://www.fao.org/media/docs/worldfoodsituationlibraries/default-document-library/food_price_indices_data.csv?sfvrsn=523ebd2a_81&download=true"
    labels = {
        "food": "FAO Food Price Index",
        "meat": "FAO Meat Price Index",
        "dairy": "FAO Dairy Price Index",
        "cereals": "FAO Cereal Price Index",
        "oils": "FAO Vegetable Oil Price Index",
        "sugar": "FAO Sugar Price Index",
    }

    def __init__(self, cache: RawCache) -> None:
        self.cache = cache

    def fetch(self) -> dict[str, SourceSeries]:
        page = self.cache.fetch(self.page_url, "fao/food_price_index_page.html")
        page_text = page.read_text(encoding="utf-8")
        match = re.search(r'href="([^"]*ffpi-data-[^"]+\.xlsx[^"]*)"', page_text, re.IGNORECASE)
        workbook_url = html.unescape(match.group(1)) if match else self.workbook_url
        workbook = self.cache.fetch(workbook_url, "fao/ffpi_monthly.xlsx")
        release_date = self._release_date()
        retrieval = datetime.now(UTC).isoformat(timespec="seconds")
        nominal = self._sheet(workbook, "xl/worksheets/sheet1.xml", date_column="A", value_start="B")
        real = self._sheet(workbook, "xl/worksheets/sheet3.xml", date_column="B", value_start="C")
        output: dict[str, SourceSeries] = {}
        for kind, rows in (("nominal", nominal), ("real", real)):
            for key, label in self.labels.items():
                observations = [SourceObservation(date, values[key], release_date) for date, values in rows if key in values]
                if not observations:
                    raise ValueError(f"FAO workbook contains no {kind} {key} observations")
                output[f"fao_{key}_{kind}"] = SourceSeries(
                    f"FAO_FFPI_{key.upper()}_{kind.upper()}",
                    f"{label} ({kind})",
                    "index, 2014-2016=100",
                    "Global",
                    "monthly",
                    "not seasonally adjusted",
                    kind,
                    "Food and Agriculture Organization of the United Nations",
                    self.page_url,
                    retrieval,
                    "FAO may revise the full history. Recent meat-index observations combine projected and observed prices and may be revised materially.",
                    observations,
                )
        return output

    def _release_date(self) -> str:
        path = self.cache.root / "fao" / "ffpi_metadata.json"
        if path.exists() and not self.cache.refresh:
            return str(json.loads(path.read_text(encoding="utf-8"))["sourceReleaseDate"])
        response = requests.head(self.csv_url, allow_redirects=True, timeout=60)
        response.raise_for_status()
        modified = response.headers.get("Last-Modified")
        release = parsedate_to_datetime(modified).date().isoformat() if modified else datetime.now(UTC).date().isoformat()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"sourceReleaseDate": release, "retrievedAt": datetime.now(UTC).isoformat(timespec="seconds"), "url": self.csv_url}, indent=2) + "\n", encoding="utf-8")
        return release

    @classmethod
    def _sheet(cls, workbook: Path, member: str, *, date_column: str, value_start: str) -> list[tuple[str, dict[str, float]]]:
        with zipfile.ZipFile(workbook) as archive:
            shared_root = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
            shared = ["".join(node.text or "" for node in item.iter() if node.tag.endswith("}t")) for item in shared_root]
            root = ElementTree.fromstring(archive.read(member))
        columns = [chr(ord(value_start) + offset) for offset in range(6)]
        keys = ["food", "meat", "dairy", "cereals", "oils", "sugar"]
        output = []
        for row in root.iter():
            if not row.tag.endswith("}row") or int(row.attrib.get("r", "0")) < 5:
                continue
            cells: dict[str, str] = {}
            for cell in row:
                if not cell.tag.endswith("}c"):
                    continue
                reference = str(cell.attrib.get("r", ""))
                column = re.match(r"[A-Z]+", reference)
                value = next((node.text for node in cell if node.tag.endswith("}v")), None)
                if not column or value is None:
                    continue
                cells[column.group()] = shared[int(value)] if cell.attrib.get("t") == "s" else value
            if date_column not in cells:
                continue
            date = (datetime(1899, 12, 30) + timedelta(days=float(cells[date_column]))).strftime("%Y-%m-01")
            values = {key: float(cells[column]) for key, column in zip(keys, columns) if column in cells}
            if values:
                output.append((date, values))
        return output
