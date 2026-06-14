from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .processor import ProcessResult


@dataclass(frozen=True)
class ProcessReportRow:
    timestamp: str
    dry_run: bool
    status: str
    source: str
    target: str
    project_code: str
    reason: str


def write_process_report(path: Path, results: list[ProcessResult], *, dry_run: bool, now: datetime | None = None) -> None:
    timestamp = (now or datetime.now()).isoformat(timespec="seconds")
    path.parent.mkdir(parents=True, exist_ok=True)
    file_exists = path.exists()

    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(ProcessReportRow.__annotations__.keys()))
        if not file_exists:
            writer.writeheader()
        for result in results:
            writer.writerow(
                {
                    "timestamp": timestamp,
                    "dry_run": str(dry_run).lower(),
                    "status": result.status,
                    "source": str(result.source),
                    "target": str(result.target),
                    "project_code": result.project_code or "",
                    "reason": result.reason or "",
                }
            )
