from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from io import BytesIO
from typing import Any


@dataclass(frozen=True)
class TextExtractionConfig:
    ocr_enabled: bool = True
    ocr_language: str = "deu"
    ocr_max_pages: int = 3
    min_embedded_text_length: int = 20


def extract_document_text(source: Path, config: TextExtractionConfig) -> str:
    suffix = source.suffix.lower()
    if suffix in {".txt", ".csv"}:
        return source.read_text(encoding="utf-8", errors="ignore")
    if suffix == ".pdf":
        return extract_pdf_text(source, config)
    return ""


def extract_pdf_text(source: Path, config: TextExtractionConfig) -> str:
    embedded_text = extract_embedded_pdf_text(source)
    if len(embedded_text.strip()) >= config.min_embedded_text_length:
        return embedded_text
    if not config.ocr_enabled:
        return embedded_text
    ocr_text = extract_ocr_pdf_text(source, config)
    return f"{embedded_text}\n{ocr_text}".strip()


def extract_embedded_pdf_text(source: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        return ""

    try:
        reader = PdfReader(str(source))
        page_texts = [page.extract_text() or "" for page in reader.pages]
    except Exception:
        return ""
    return "\n".join(page_texts).strip()


def extract_ocr_pdf_text(source: Path, config: TextExtractionConfig) -> str:
    pymupdf_text = extract_ocr_pdf_text_with_pymupdf(source, config)
    if pymupdf_text:
        return pymupdf_text
    return extract_ocr_pdf_text_with_pdf2image(source, config)


def extract_ocr_pdf_text_with_pymupdf(source: Path, config: TextExtractionConfig) -> str:
    try:
        import fitz
        from PIL import Image
        import pytesseract
    except ImportError:
        return ""

    try:
        document = fitz.open(str(source))
        texts = []
        page_count = min(len(document), max(1, config.ocr_max_pages))
        for page_index in range(page_count):
            page = document.load_page(page_index)
            pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            image = Image.open(BytesIO(pixmap.tobytes("png")))
            texts.append(pytesseract.image_to_string(image, lang=config.ocr_language))
    except Exception:
        return ""
    return "\n".join(texts).strip()


def extract_ocr_pdf_text_with_pdf2image(source: Path, config: TextExtractionConfig) -> str:
    try:
        from pdf2image import convert_from_path
        import pytesseract
    except ImportError:
        return ""

    try:
        pages: list[Any] = convert_from_path(
            str(source),
            first_page=1,
            last_page=max(1, config.ocr_max_pages),
        )
        texts = [
            pytesseract.image_to_string(page, lang=config.ocr_language)
            for page in pages
        ]
    except Exception:
        return ""
    return "\n".join(texts).strip()
