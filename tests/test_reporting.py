from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from benennungssoftware.processor import ProcessResult
from benennungssoftware.reporting import write_process_report


class ReportingTests(unittest.TestCase):
    def test_writes_csv_report_with_header(self) -> None:
        with TemporaryDirectory() as tmp:
            report_path = Path(tmp) / "logs" / "process.csv"
            results = [
                ProcessResult(
                    source=Path("scan001.txt"),
                    target=Path("PRJ001/2026-06-14_scan001.txt"),
                    status="assigned",
                    project_code="PRJ001",
                )
            ]

            write_process_report(report_path, results, dry_run=True, now=datetime(2026, 6, 14, 9, 30, 0))

            with report_path.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))

            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["timestamp"], "2026-06-14T09:30:00")
            self.assertEqual(rows[0]["dry_run"], "true")
            self.assertEqual(rows[0]["status"], "assigned")
            self.assertEqual(rows[0]["project_code"], "PRJ001")

    def test_appends_without_repeating_header(self) -> None:
        with TemporaryDirectory() as tmp:
            report_path = Path(tmp) / "process.csv"
            result = ProcessResult(source=Path("a.txt"), target=Path("b.txt"), status="unassigned", reason="no_project_match")

            write_process_report(report_path, [result], dry_run=True, now=datetime(2026, 6, 14, 9, 30, 0))
            write_process_report(report_path, [result], dry_run=False, now=datetime(2026, 6, 14, 9, 31, 0))

            lines = report_path.read_text(encoding="utf-8").splitlines()

            self.assertEqual(len(lines), 3)
            self.assertEqual(lines[0].count("timestamp"), 1)


if __name__ == "__main__":
    unittest.main()
