from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceObservation:
    date: str
    value: float
    release_date: str | None = None


@dataclass(frozen=True)
class SourceSeries:
    source_id: str
    label: str
    unit: str
    geography: str
    frequency: str
    seasonal_adjustment: str
    nominal_real: str
    source: str
    source_url: str
    retrieval_date: str
    revision_notes: str
    observations: list[SourceObservation]
