from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import json

from .text_extraction import TextExtractionConfig


@dataclass(frozen=True)
class Project:
    code: str
    folder: str
    keywords: tuple[str, ...]


@dataclass(frozen=True)
class AppConfig:
    scan_folder: Path
    projects_root: Path
    unassigned_folder: Path
    name_schema: str
    default_document_type: str
    allowed_extensions: tuple[str, ...]
    projects: tuple[Project, ...]
    text_extraction: TextExtractionConfig = field(default_factory=TextExtractionConfig)


def load_config(path: str | Path) -> AppConfig:
    config_path = Path(path)
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    base_dir = config_path.parent

    return AppConfig(
        scan_folder=_resolve(base_dir, raw["scan_folder"]),
        projects_root=_resolve(base_dir, raw["projects_root"]),
        unassigned_folder=_resolve(base_dir, raw["unassigned_folder"]),
        name_schema=raw.get("name_schema", "{date}_{project_code}_{document_type}_{original_stem}{extension}"),
        default_document_type=raw.get("default_document_type", "Dokument"),
        allowed_extensions=tuple(ext.lower() for ext in raw.get("allowed_extensions", [".pdf"])),
        text_extraction=_load_text_extraction(raw.get("text_extraction", {})),
        projects=tuple(
            Project(
                code=item["code"],
                folder=item["folder"],
                keywords=tuple(keyword.casefold() for keyword in item.get("keywords", [])),
            )
            for item in raw.get("projects", [])
        ),
    )


def _load_text_extraction(raw: dict) -> TextExtractionConfig:
    return TextExtractionConfig(
        ocr_enabled=bool(raw.get("ocr_enabled", True)),
        ocr_language=raw.get("ocr_language", "deu"),
        ocr_max_pages=int(raw.get("ocr_max_pages", 3)),
        min_embedded_text_length=int(raw.get("min_embedded_text_length", 20)),
    )


def _resolve(base_dir: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return (base_dir / path).resolve()
