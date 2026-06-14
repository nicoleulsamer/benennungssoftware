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
    raw = load_raw_config(config_path)
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


def load_raw_config(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_raw_config(path: str | Path, raw: dict) -> None:
    Path(path).write_text(json.dumps(raw, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def add_project_to_config(path: str | Path, code: str, folder: str, keywords: list[str]) -> None:
    normalized_code = code.strip()
    normalized_folder = folder.strip()
    normalized_keywords = _normalize_keywords(keywords)
    if not normalized_code:
        raise ValueError("Project code must not be empty")
    if not normalized_folder:
        raise ValueError("Project folder must not be empty")
    if not normalized_keywords:
        raise ValueError("At least one keyword is required")

    raw = load_raw_config(path)
    projects = raw.setdefault("projects", [])
    if any(item.get("code", "").casefold() == normalized_code.casefold() for item in projects):
        raise ValueError(f"Project code already exists: {normalized_code}")
    if any(item.get("folder", "").casefold() == normalized_folder.casefold() for item in projects):
        raise ValueError(f"Project folder already exists: {normalized_folder}")

    projects.append(
        {
            "code": normalized_code,
            "folder": normalized_folder,
            "keywords": normalized_keywords,
        }
    )
    save_raw_config(path, raw)


def add_keyword_to_config(path: str | Path, project_code: str, keyword: str) -> None:
    normalized_keyword = keyword.strip().casefold()
    if not normalized_keyword:
        raise ValueError("Keyword must not be empty")

    raw = load_raw_config(path)
    for project in raw.get("projects", []):
        if project.get("code", "").casefold() == project_code.casefold():
            keywords = project.setdefault("keywords", [])
            existing = {item.casefold() for item in keywords}
            if normalized_keyword not in existing:
                keywords.append(normalized_keyword)
                save_raw_config(path, raw)
            return
    raise ValueError(f"Unknown project code: {project_code}")


def _load_text_extraction(raw: dict) -> TextExtractionConfig:
    return TextExtractionConfig(
        ocr_enabled=bool(raw.get("ocr_enabled", True)),
        ocr_language=raw.get("ocr_language", "deu"),
        ocr_max_pages=int(raw.get("ocr_max_pages", 3)),
        min_embedded_text_length=int(raw.get("min_embedded_text_length", 20)),
    )


def _normalize_keywords(keywords: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for keyword in keywords:
        value = keyword.strip().casefold()
        if value and value not in seen:
            normalized.append(value)
            seen.add(value)
    return normalized


def _resolve(base_dir: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return (base_dir / path).resolve()
