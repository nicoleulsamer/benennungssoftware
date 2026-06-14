from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from collections import Counter

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


@dataclass(frozen=True)
class ReportSummary:
    total: int
    by_status: dict[str, int]
    by_project: dict[str, int]
    unassigned_targets: list[str]


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


def summarize_process_report(path: Path) -> ReportSummary:
    status_counter: Counter[str] = Counter()
    project_counter: Counter[str] = Counter()
    unassigned_targets: list[str] = []

    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            status = row.get("status", "") or "unknown"
            project_code = row.get("project_code", "")
            target = row.get("target", "")
            status_counter[status] += 1
            if project_code:
                project_counter[project_code] += 1
            if status == "unassigned" and target:
                unassigned_targets.append(target)

    return ReportSummary(
        total=sum(status_counter.values()),
        by_status=dict(sorted(status_counter.items())),
        by_project=dict(sorted(project_counter.items())),
        unassigned_targets=unassigned_targets,
    )
