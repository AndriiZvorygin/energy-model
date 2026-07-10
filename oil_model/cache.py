from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.parse import urlparse

import requests


class RawCache:
    def __init__(self, root: Path, refresh: bool = False) -> None:
        self.root = root
        self.refresh = refresh
        self.root.mkdir(parents=True, exist_ok=True)

    def fetch(self, url: str, name: str | None = None, *, headers: dict[str, str] | None = None) -> Path:
        path = self.root / (name or self._name_for(url))
        if path.exists() and not self.refresh:
            return path
        path.parent.mkdir(parents=True, exist_ok=True)
        response = requests.get(url, timeout=60, headers=headers or {})
        response.raise_for_status()
        path.write_bytes(response.content)
        return path

    @staticmethod
    def _name_for(url: str) -> str:
        parsed = urlparse(url)
        suffix = Path(parsed.path).suffix or ".raw"
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
        stem = Path(parsed.path).stem or parsed.netloc.replace(".", "_")
        return f"{stem}-{digest}{suffix}"
