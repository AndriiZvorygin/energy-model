from __future__ import annotations

import csv
import html
import io
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path

from .cache import RawCache


Observation = tuple[str, float]


class SourceDataError(RuntimeError):
    """Raised when a source adapter cannot produce real observations."""


@dataclass(frozen=True)
class Series:
    name: str
    unit: str
    source: str
    observations: list[Observation]


def month_key(value: str) -> str:
    if len(value) == 6 and value.isdigit():
        return f"{value[:4]}-{value[4:6]}"
    return value[:7]


def monthly_average(observations: list[Observation]) -> list[Observation]:
    buckets: dict[str, list[float]] = defaultdict(list)
    for obs_date, value in observations:
        buckets[month_key(obs_date)].append(value)
    return sorted((month, sum(values) / len(values)) for month, values in buckets.items())


class FredAdapter:
    base_url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"

    def __init__(self, cache: RawCache) -> None:
        self.cache = cache

    def fetch(self, series_id: str, *, monthly: bool = False) -> Series:
        url = self.base_url.format(series_id=series_id)
        path = self.cache.fetch(url, f"fred/{series_id}.csv")
        observations: list[Observation] = []
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                raw = row.get(series_id, ".")
                if not raw or raw == ".":
                    continue
                observations.append((row["observation_date"], float(raw)))
        if monthly:
            observations = monthly_average(observations)
        else:
            observations = [(month_key(d), v) for d, v in observations]
        require_observations(series_id, observations)
        return Series(series_id, "FRED native units", f"FRED:{series_id}", observations)


class YahooChartAdapter:
    base_url = (
        "https://query2.finance.yahoo.com/v8/finance/chart/{symbol}"
        "?period1=0&period2=4102444800&interval=1d&events=history&includeAdjustedClose=true"
    )

    def __init__(self, cache: RawCache) -> None:
        self.cache = cache

    def fetch_adjusted_monthly(self, symbol: str) -> tuple[Series, Series]:
        url = self.base_url.format(symbol=symbol)
        path = self.cache.fetch(url, f"yahoo/{symbol}_chart.json", headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
        payload = json.loads(path.read_text(encoding="utf-8"))
        result = (payload.get("chart", {}).get("result") or [None])[0]
        if not result:
            raise SourceDataError(f"Yahoo chart returned no result for {symbol}")
        timestamps = result.get("timestamp") or []
        adj = ((result.get("indicators") or {}).get("adjclose") or [{}])[0].get("adjclose") or []
        daily: list[Observation] = []
        for ts, value in zip(timestamps, adj):
            if value is None:
                continue
            day = datetime.fromtimestamp(int(ts), UTC).date().isoformat()
            daily.append((day, float(value)))
        require_observations(symbol, daily)
        buckets: dict[str, list[Observation]] = defaultdict(list)
        for day, value in daily:
            buckets[month_key(day)].append((day, value))
        current_month = datetime.now(UTC).strftime("%Y-%m")
        complete_buckets = {month: obs for month, obs in buckets.items() if month < current_month}
        monthly_avg = sorted((month, sum(v for _, v in obs) / len(obs)) for month, obs in complete_buckets.items())
        month_end = sorted((month, sorted(obs)[-1][1]) for month, obs in complete_buckets.items())
        source = f"Yahoo Finance chart adjusted close:{symbol}"
        return (
            Series(f"{symbol}_MONTHLY_AVG_ADJ_CLOSE", "USD", source, monthly_avg),
            Series(f"{symbol}_MONTH_END_ADJ_CLOSE", "USD", source, month_end),
        )


class EcbAdapter:
    m2_url = (
        "https://data-api.ecb.europa.eu/service/data/BSI/"
        "M.U2.Y.V.M20.X.1.U2.2300.Z01.E?startPeriod=1980-01&format=csvdata"
    )

    def __init__(self, cache: RawCache) -> None:
        self.cache = cache

    def fetch_euro_area_m2(self) -> Series:
        path = self.cache.fetch(self.m2_url, "ecb/euro_area_m2_bsi.csv", headers={"Accept": "text/csv"})
        observations: list[Observation] = []
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                if row.get("OBS_VALUE"):
                    observations.append((row["TIME_PERIOD"], float(row["OBS_VALUE"]) * 1_000_000))
        require_observations("EA_M2", observations)
        return Series("EA_M2", "EUR", "ECB BSI.M.U2.Y.V.M20.X.1.U2.2300.Z01.E", observations)


class BojAdapter:
    url = (
        "https://www.stat-search.boj.or.jp/api/v1/getDataCode?"
        "format=csv&lang=en&db=MD02&startDate=199801&code=MAM1NAM2M2MO"
    )

    def __init__(self, cache: RawCache) -> None:
        self.cache = cache

    def fetch_japan_m2(self) -> Series:
        path = self.cache.fetch(self.url, "boj/japan_m2_md02.csv")
        lines = path.read_text(encoding="utf-8").splitlines()
        header = "SERIES_CODE,NAME_OF_TIME_SERIES,UNIT,FREQUENCY,CATEGORY,LAST_UPDATE,SURVEY_DATES,VALUES"
        if header not in lines:
            raise SourceDataError("BOJ MD02 response did not contain the expected data table header")
        start = lines.index(header)
        observations: list[Observation] = []
        for row in csv.DictReader(io.StringIO("\n".join(lines[start:]))):
            raw = row.get("VALUES")
            if raw and raw != "null":
                observations.append((month_key(row["SURVEY_DATES"]), float(raw) * 100_000_000))
        require_observations("JP_M2", observations)
        return Series("JP_M2", "JPY", "BOJ MD02:MAM1NAM2M2MO", observations)


class ChinaM2Adapter:
    china_data_url = "https://chinadata.live/api/v2/data/china-m2-money-supply"

    def __init__(self, cache: RawCache, fred: FredAdapter) -> None:
        self.cache = cache
        self.fred = fred

    def fetch_china_m2(self) -> Series:
        merged: dict[str, float] = {}
        for obs_date, value in self.fred.fetch("MYAGM2CNM189N").observations:
            merged[obs_date] = value

        path = self.cache.fetch(self.china_data_url, "chinadata/china_m2_money_supply.json")
        payload = json.loads(path.read_text(encoding="utf-8"))
        rows = payload.get("data") or payload.get("records") or payload.get("values") or []
        if isinstance(rows, dict):
            rows = rows.get("data") or rows.get("records") or rows.get("values") or []
        for row in rows:
            if not isinstance(row, dict):
                continue
            period = row.get("date") or row.get("period") or row.get("month") or row.get("time")
            raw = row.get("value") or row.get("m2") or row.get("M2")
            if period and raw is not None:
                merged[month_key(str(period))] = float(raw) * 100_000_000

        require_observations("CN_M2", sorted(merged.items()))
        return Series(
            "CN_M2",
            "CNY",
            "IMF/FRED MYAGM2CNM189N merged with ChinaData PBoC-sourced API",
            sorted(merged.items()),
        )


class EiaInventoryAdapter:
    url = "https://www.eia.gov/dnav/pet/hist/LeafHandler.ashx?f=W&n=PET&s=WCESTUS1"
    history_url = "https://www.eia.gov/dnav/pet/hist/LeafHandler.ashx?f=W&n=PET&s={series_id}"

    def __init__(self, cache: RawCache) -> None:
        self.cache = cache

    def fetch_crude_stocks_ex_spr(self) -> Series:
        path = self.cache.fetch(self.url, "eia/WCESTUS1_weekly.html")
        text = path.read_text(encoding="utf-8", errors="replace")
        observations: list[Observation] = []
        for row_html in re.findall(r"<tr>(.*?)</tr>", text, flags=re.S | re.I):
            cells = [
                html.unescape(re.sub(r"<.*?>", "", cell)).replace("\xa0", " ").strip()
                for cell in re.findall(r"<td[^>]*>(.*?)</td>", row_html, flags=re.S | re.I)
            ]
            if len(cells) < 3 or not re.match(r"^\d{4}-[A-Za-z]{3}$", cells[0]):
                continue
            year = int(cells[0][:4])
            for i in range(1, len(cells) - 1, 2):
                mmdd = cells[i]
                value = cells[i + 1].replace(",", "")
                if re.match(r"^\d{2}/\d{2}$", mmdd) and value.isdigit():
                    month, day = map(int, mmdd.split("/"))
                    observations.append((date(year, month, day).isoformat(), float(value)))
        monthly = monthly_average(observations)
        require_observations("US_CRUDE_STOCKS_EX_SPR", monthly)
        return Series("US_CRUDE_STOCKS_EX_SPR", "thousand barrels", "EIA WCESTUS1", monthly)

    def fetch_weekly_series(self, series_id: str, name: str, unit: str) -> Series:
        url = self.history_url.format(series_id=series_id)
        path = self.cache.fetch(url, f"eia/{series_id}_weekly.html")
        text = path.read_text(encoding="utf-8", errors="replace")
        observations: list[Observation] = []
        for row_html in re.findall(r"<tr[^>]*>(.*?)</tr>", text, flags=re.S | re.I):
            cells = [
                html.unescape(re.sub(r"<.*?>", "", cell)).replace("\xa0", " ").strip()
                for cell in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row_html, flags=re.S | re.I)
            ]
            if len(cells) < 3 or not re.match(r"^\d{4}-[A-Za-z]{3}$", cells[0]):
                continue
            year = int(cells[0][:4])
            for i in range(1, len(cells) - 1, 2):
                mmdd = cells[i]
                raw = cells[i + 1].replace(",", "")
                try:
                    value = float(raw)
                except ValueError:
                    continue
                if re.match(r"^\d{2}/\d{2}$", mmdd):
                    month, day = map(int, mmdd.split("/"))
                    observations.append((date(year, month, day).isoformat(), value))
        monthly = monthly_average(observations)
        require_observations(series_id, monthly)
        return Series(name, unit, f"EIA weekly history:{series_id}; monthly average", monthly)


class EiaMerAdapter:
    table_url = "https://www.eia.gov/totalenergy/data/browser/csv.php?tbl={table_id}"

    def __init__(self, cache: RawCache) -> None:
        self.cache = cache

    def fetch_monthly_series(self, table_id: str, msn: str, name: str) -> Series:
        url = self.table_url.format(table_id=table_id)
        path = self.cache.fetch(url, f"eia_mer/{table_id}.csv")
        observations: list[Observation] = []
        unit = "EIA MER native units"
        description = name
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                period = row.get("YYYYMM", "")
                if row.get("MSN") != msn or len(period) != 6 or period.endswith("13"):
                    continue
                raw = row.get("Value")
                if raw in (None, "", "Not Available"):
                    continue
                observations.append((f"{period[:4]}-{period[4:6]}", float(raw)))
                unit = row.get("Unit") or unit
                description = row.get("Description") or description
        require_observations(msn, observations)
        return Series(name, unit, f"EIA MER {table_id}:{msn} {description}", observations)


class EiaPetroleumPriceAdapter:
    base_url = "https://www.eia.gov/dnav/pet/hist/LeafHandler.ashx?f=M&n=PET&s={series_id}"

    def __init__(self, cache: RawCache) -> None:
        self.cache = cache

    def fetch_monthly_series(self, series_id: str, name: str) -> Series:
        url = self.base_url.format(series_id=series_id)
        path = self.cache.fetch(url, f"eia_prices/{series_id}_monthly.html")
        text = path.read_text(encoding="utf-8", errors="replace")
        observations: list[Observation] = []
        for row_html in re.findall(r"<tr[^>]*>(.*?)</tr>", text, flags=re.S | re.I):
            cells = [
                html.unescape(re.sub(r"<.*?>", "", cell)).replace("\xa0", " ").strip()
                for cell in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row_html, flags=re.S | re.I)
            ]
            if len(cells) != 13 or not re.fullmatch(r"\d{4}", cells[0]):
                continue
            year = int(cells[0])
            for month, raw in enumerate(cells[1:], start=1):
                try:
                    value = float(raw.replace(",", ""))
                except ValueError:
                    continue
                observations.append((f"{year}-{month:02d}", value))
        require_observations(series_id, observations)
        return Series(name, "dollars per barrel", f"EIA Petroleum Marketing Monthly:{series_id}", observations)


class BisAdapter:
    def __init__(self, cache: RawCache) -> None:
        self.cache = cache

    def fetch_csv_url(self, url: str) -> list[dict[str, str]]:
        path = self.cache.fetch(url, "bis/total_credit.csv", headers={"Accept": "text/csv"})
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        if not rows:
            raise SourceDataError("BIS URL returned no CSV rows")
        return rows


def require_observations(name: str, observations: list[Observation]) -> None:
    if not observations:
        raise SourceDataError(f"{name} source returned no observations")
