from __future__ import annotations

from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from benennungssoftware.config import AppConfig, Project
from benennungssoftware.processor import assign_unassigned_document, list_unassigned_documents, process_scan_folder, sanitize


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

    def test_manually_assigns_unassigned_document(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            unassigned_folder = root / "unassigned"
            unassigned_folder.mkdir()
            source = unassigned_folder / "scan003_unbekannt.txt"
            source.write_text("Kein Treffer", encoding="utf-8")

            config = AppConfig(
                scan_folder=root / "scans",
                projects_root=root / "projects",
                unassigned_folder=unassigned_folder,
                name_schema="{date}_{project_code}_{document_type}_{original_stem}{extension}",
                default_document_type="Dokument",
                allowed_extensions=(".txt",),
                projects=(Project(code="PRJ002", folder="PRJ002_Test", keywords=("kunde b",)),),
            )

            result = assign_unassigned_document(config, source, "PRJ002", today=date(2026, 6, 14))

            self.assertEqual(result.status, "manually_assigned")
            self.assertFalse(source.exists())
            self.assertTrue((root / "projects" / "PRJ002_Test" / "2026-06-14_PRJ002_Dokument_scan003_unbekannt.txt").exists())

    def test_manual_assignment_rejects_unknown_project_code(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "scan.txt"
            source.write_text("Text", encoding="utf-8")
            config = AppConfig(
                scan_folder=root / "scans",
                projects_root=root / "projects",
                unassigned_folder=root / "unassigned",
                name_schema="{date}_{project_code}_{document_type}_{original_stem}{extension}",
                default_document_type="Dokument",
                allowed_extensions=(".txt",),
                projects=(),
            )

            with self.assertRaises(ValueError):
                assign_unassigned_document(config, source, "PRJ999")

    def test_lists_unassigned_documents_with_allowed_extensions(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            unassigned_folder = root / "unassigned"
            unassigned_folder.mkdir()
            first = unassigned_folder / "a.txt"
            second = unassigned_folder / "b.pdf"
            ignored = unassigned_folder / "ignore.tmp"
            first.write_text("A", encoding="utf-8")
            second.write_bytes(b"pdf")
            ignored.write_text("tmp", encoding="utf-8")

            config = AppConfig(
                scan_folder=root / "scans",
                projects_root=root / "projects",
                unassigned_folder=unassigned_folder,
                name_schema="{date}_{project_code}_{document_type}_{original_stem}{extension}",
                default_document_type="Dokument",
                allowed_extensions=(".pdf", ".txt"),
                projects=(),
            )

            self.assertEqual(list_unassigned_documents(config), [first, second])

    def test_lists_no_unassigned_documents_when_folder_is_missing(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = AppConfig(
                scan_folder=root / "scans",
                projects_root=root / "projects",
                unassigned_folder=root / "unassigned",
                name_schema="{date}_{project_code}_{document_type}_{original_stem}{extension}",
                default_document_type="Dokument",
                allowed_extensions=(".pdf", ".txt"),
                projects=(),
            )

            self.assertEqual(list_unassigned_documents(config), [])

    def test_sanitize_removes_unsafe_filename_characters(self) -> None:
        self.assertEqual(sanitize(" Rechnung: Kunde A / 2026 "), "Rechnung-Kunde-A-2026")

    def test_sanitize_transliterates_german_characters(self) -> None:
        self.assertEqual(
            sanitize("Präsentation zur Studie Sexuelle Belästigung"),
            "Praesentation-zur-Studie-Sexuelle-Belaestigung",
        )
        self.assertEqual(sanitize("Grüße aus Österreich"), "Gruesse-aus-Oesterreich")


if __name__ == "__main__":
    unittest.main()
