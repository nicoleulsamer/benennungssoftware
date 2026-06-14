from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from benennungssoftware.text_extraction import TextExtractionConfig, extract_document_text, extract_ocr_pdf_text, extract_pdf_text, preview_text


class TextExtractionTests(unittest.TestCase):
    def test_reads_text_files(self) -> None:
        with TemporaryDirectory() as tmp:
            source = Path(tmp) / "scan.txt"
            source.write_text("Projekt Sanierung Nord", encoding="utf-8")

            text = extract_document_text(source, TextExtractionConfig())

            self.assertIn("Sanierung Nord", text)

    def test_preview_text_compacts_and_truncates_text(self) -> None:
        text = " Erste\n\nZeile   zweite Zeile mit mehr Text "

        self.assertEqual(preview_text(text, 18), "Erste Zeile zweite...")

    def test_pdf_uses_embedded_text_when_it_is_long_enough(self) -> None:
        config = TextExtractionConfig(min_embedded_text_length=10)

        with patch("benennungssoftware.text_extraction.extract_embedded_pdf_text", return_value="Genug eingebetteter PDF Text"):
            with patch("benennungssoftware.text_extraction.extract_ocr_pdf_text") as ocr:
                text = extract_pdf_text(Path("scan.pdf"), config)

        self.assertIn("eingebetteter", text)
        ocr.assert_not_called()

    def test_pdf_falls_back_to_ocr_for_scanned_documents(self) -> None:
        config = TextExtractionConfig(ocr_enabled=True, min_embedded_text_length=10)

        with patch("benennungssoftware.text_extraction.extract_embedded_pdf_text", return_value=""):
            with patch("benennungssoftware.text_extraction.extract_ocr_pdf_text", return_value="OCR Ergebnis Kunde A") as ocr:
                text = extract_pdf_text(Path("scan.pdf"), config)

        self.assertEqual(text, "OCR Ergebnis Kunde A")
        ocr.assert_called_once()

    def test_ocr_uses_pymupdf_before_pdf2image(self) -> None:
        config = TextExtractionConfig(ocr_enabled=True)

        with patch("benennungssoftware.text_extraction.extract_ocr_pdf_text_with_pymupdf", return_value="PyMuPDF OCR"):
            with patch("benennungssoftware.text_extraction.extract_ocr_pdf_text_with_pdf2image") as pdf2image:
                text = extract_ocr_pdf_text(Path("scan.pdf"), config)

        self.assertEqual(text, "PyMuPDF OCR")
        pdf2image.assert_not_called()

    def test_ocr_falls_back_to_pdf2image_when_pymupdf_is_unavailable(self) -> None:
        config = TextExtractionConfig(ocr_enabled=True)

        with patch("benennungssoftware.text_extraction.extract_ocr_pdf_text_with_pymupdf", return_value=""):
            with patch("benennungssoftware.text_extraction.extract_ocr_pdf_text_with_pdf2image", return_value="Poppler OCR"):
                text = extract_ocr_pdf_text(Path("scan.pdf"), config)

        self.assertEqual(text, "Poppler OCR")

    def test_pdf_skips_ocr_when_disabled(self) -> None:
        config = TextExtractionConfig(ocr_enabled=False, min_embedded_text_length=10)

        with patch("benennungssoftware.text_extraction.extract_embedded_pdf_text", return_value=""):
            with patch("benennungssoftware.text_extraction.extract_ocr_pdf_text") as ocr:
                text = extract_pdf_text(Path("scan.pdf"), config)

        self.assertEqual(text, "")
        ocr.assert_not_called()


if __name__ == "__main__":
    unittest.main()
