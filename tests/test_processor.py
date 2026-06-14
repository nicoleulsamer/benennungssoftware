from __future__ import annotations

from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from benennungssoftware.config import AppConfig, Project
from benennungssoftware.processor import process_scan_folder, sanitize


class ProcessorTests(unittest.TestCase):
    def test_assigns_matching_scan_to_project_folder(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            scan_folder = root / "scans"
            projects_root = root / "projects"
            unassigned_folder = root / "unassigned"
            scan_folder.mkdir()
            source = scan_folder / "rechnung-kunde-a.pdf"
            source.write_bytes(b"pdf")

            config = AppConfig(
                scan_folder=scan_folder,
                projects_root=projects_root,
                unassigned_folder=unassigned_folder,
                name_schema="{date}_{project_code}_{document_type}_{original_stem}{extension}",
                default_document_type="Rechnung",
                allowed_extensions=(".pdf",),
                projects=(Project(code="PRJ001", folder="PRJ001_Test", keywords=("kunde-a", "kunde a")),),
            )

            results = process_scan_folder(config, today=date(2026, 6, 14))

            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].status, "assigned")
            self.assertFalse(source.exists())
            self.assertTrue((projects_root / "PRJ001_Test" / "2026-06-14_PRJ001_Rechnung_rechnung-kunde-a.pdf").exists())

    def test_unassigned_scan_is_moved_to_unassigned_folder(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            scan_folder = root / "scans"
            scan_folder.mkdir()
            source = scan_folder / "scan-ohne-treffer.txt"
            source.write_text("Kein Projektbezug", encoding="utf-8")

            config = AppConfig(
                scan_folder=scan_folder,
                projects_root=root / "projects",
                unassigned_folder=root / "unassigned",
                name_schema="{date}_{project_code}_{document_type}_{original_stem}{extension}",
                default_document_type="Dokument",
                allowed_extensions=(".txt",),
                projects=(Project(code="PRJ001", folder="PRJ001_Test", keywords=("anderes",)),),
            )

            results = process_scan_folder(config)

            self.assertEqual(results[0].status, "unassigned")
            self.assertEqual(results[0].reason, "no_project_match")
            self.assertTrue((root / "unassigned" / "scan-ohne-treffer.txt").exists())

    def test_existing_target_is_not_overwritten(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            scan_folder = root / "scans"
            target_folder = root / "projects" / "PRJ001_Test"
            scan_folder.mkdir()
            target_folder.mkdir(parents=True)
            source = scan_folder / "kunde-a.pdf"
            source.write_bytes(b"new")
            existing = target_folder / "2026-06-14_PRJ001_Dokument_kunde-a.pdf"
            existing.write_bytes(b"existing")

            config = AppConfig(
                scan_folder=scan_folder,
                projects_root=root / "projects",
                unassigned_folder=root / "unassigned",
                name_schema="{date}_{project_code}_{document_type}_{original_stem}{extension}",
                default_document_type="Dokument",
                allowed_extensions=(".pdf",),
                projects=(Project(code="PRJ001", folder="PRJ001_Test", keywords=("kunde-a",)),),
            )

            process_scan_folder(config, today=date(2026, 6, 14))

            self.assertEqual(existing.read_bytes(), b"existing")
            self.assertTrue((target_folder / "2026-06-14_PRJ001_Dokument_kunde-a_001.pdf").exists())

    def test_assigns_pdf_by_extracted_text(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            scan_folder = root / "scans"
            scan_folder.mkdir()
            source = scan_folder / "scan001.pdf"
            source.write_bytes(b"pdf")

            config = AppConfig(
                scan_folder=scan_folder,
                projects_root=root / "projects",
                unassigned_folder=root / "unassigned",
                name_schema="{date}_{project_code}_{document_type}_{original_stem}{extension}",
                default_document_type="Dokument",
                allowed_extensions=(".pdf",),
                projects=(Project(code="PRJ001", folder="PRJ001_Test", keywords=("kunde a",)),),
            )

            with patch("benennungssoftware.processor.extract_document_text", return_value="Rechnung fuer Kunde A"):
                results = process_scan_folder(config, today=date(2026, 6, 14))

            self.assertEqual(results[0].status, "assigned")
            self.assertTrue((root / "projects" / "PRJ001_Test" / "2026-06-14_PRJ001_Dokument_scan001.pdf").exists())

    def test_sanitize_removes_unsafe_filename_characters(self) -> None:
        self.assertEqual(sanitize(" Rechnung: Kunde A / 2026 "), "Rechnung-Kunde-A-2026")


if __name__ == "__main__":
    unittest.main()
