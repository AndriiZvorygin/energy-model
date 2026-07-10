from __future__ import annotations

import csv
import sqlite3
from pathlib import Path


Row = dict[str, float | int | str | None]


class Store:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.con = sqlite3.connect(db_path)

    def close(self) -> None:
        self.con.close()

    def write_rows(self, table: str, rows: list[Row]) -> None:
        if not rows:
            return
        cols = union_columns(rows)
        quoted = ", ".join(f'"{c}"' for c in cols)
        self.con.execute(f'DROP TABLE IF EXISTS "{table}"')
        self.con.execute(f'CREATE TABLE "{table}" ({", ".join(f"{q} TEXT" for q in [f"""\"{c}\"""" for c in cols])})')
        placeholders = ", ".join("?" for _ in cols)
        self.con.executemany(
            f'INSERT INTO "{table}" ({quoted}) VALUES ({placeholders})',
            [[row.get(col) for col in cols] for row in rows],
        )
        self.con.commit()


def write_csv(path: Path, rows: list[Row]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=union_columns(rows))
        writer.writeheader()
        writer.writerows(rows)


def union_columns(rows: list[Row]) -> list[str]:
    cols: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for col in row:
            if col not in seen:
                cols.append(col)
                seen.add(col)
    return cols


def maybe_write_parquet(path: Path, rows: list[Row]) -> bool:
    try:
        import pandas as pd
    except ImportError:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_parquet(path, index=False)
    return True
