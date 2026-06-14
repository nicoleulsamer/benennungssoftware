from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
import re
import shutil

from .config import AppConfig, Project
from .text_extraction import extract_document_text


@dataclass(frozen=True)
class ProcessResult:
    source: Path
    target: Path
    status: str
    project_code: str | None = None
    reason: str | None = None


def process_scan_folder(config: AppConfig, *, dry_run: bool = False, today: date | None = None) -> list[ProcessResult]:
    current_date = today or date.today()
    config.scan_folder.mkdir(parents=True, exist_ok=True)
    config.projects_root.mkdir(parents=True, exist_ok=True)
    config.unassigned_folder.mkdir(parents=True, exist_ok=True)

    results: list[ProcessResult] = []
    for source in sorted(config.scan_folder.iterdir()):
        if not source.is_file() or source.suffix.lower() not in config.allowed_extensions:
            continue

        project = match_project(source, config)
        if project is None:
            target = unique_path(config.unassigned_folder / source.name)
            results.append(_move(source, target, dry_run=dry_run, status="unassigned", reason="no_project_match"))
            continue

        target_folder = config.projects_root / project.folder
        filename = build_filename(config, project, source, current_date)
        target = unique_path(target_folder / filename)
        results.append(_move(source, target, dry_run=dry_run, status="assigned", project_code=project.code))

    return results


def assign_unassigned_document(
    config: AppConfig,
    source: Path,
    project_code: str,
    *,
    dry_run: bool = False,
    today: date | None = None,
) -> ProcessResult:
    project = find_project_by_code(config, project_code)
    if project is None:
        raise ValueError(f"Unknown project code: {project_code}")
    if not source.exists() or not source.is_file():
        raise FileNotFoundError(source)
    if source.suffix.lower() not in config.allowed_extensions:
        raise ValueError(f"Unsupported file extension: {source.suffix}")

    current_date = today or date.today()
    target_folder = config.projects_root / project.folder
    filename = build_filename(config, project, source, current_date)
    target = unique_path(target_folder / filename)
    return _move(source, target, dry_run=dry_run, status="manually_assigned", project_code=project.code)


def list_unassigned_documents(config: AppConfig) -> list[Path]:
    if not config.unassigned_folder.exists():
        return []
    return [
        source
        for source in sorted(config.unassigned_folder.iterdir())
        if source.is_file() and source.suffix.lower() in config.allowed_extensions
    ]


def find_project_by_code(config: AppConfig, project_code: str) -> Project | None:
    normalized = project_code.casefold()
    for project in config.projects:
        if project.code.casefold() == normalized:
            return project
    return None


def match_project(source: Path, config: AppConfig) -> Project | None:
    filename_matches = _matching_projects(source.stem.casefold(), config.projects)
    if len(filename_matches) == 1:
        return filename_matches[0]

    text = extract_document_text(source, config.text_extraction)
    haystack = f"{source.stem} {text}".casefold()
    matches = _matching_projects(haystack, config.projects)
    if len(matches) == 1:
        return matches[0]
    return None


def _matching_projects(haystack: str, projects: tuple[Project, ...]) -> list[Project]:
    return [
        project
        for project in projects
        if any(keyword and keyword in haystack for keyword in project.keywords)
    ]


def build_filename(config: AppConfig, project: Project, source: Path, current_date: date) -> str:
    values = {
        "date": current_date.isoformat(),
        "project_code": sanitize(project.code),
        "document_type": sanitize(config.default_document_type),
        "original_stem": sanitize(source.stem),
        "extension": source.suffix.lower(),
    }
    return config.name_schema.format(**values)


def sanitize(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip())
    cleaned = re.sub(r"-{2,}", "-", cleaned).strip("-._")
    return cleaned or "unbenannt"


def unique_path(target: Path) -> Path:
    if not target.exists():
        return target

    stem = target.stem
    suffix = target.suffix
    parent = target.parent
    counter = 1
    while True:
        candidate = parent / f"{stem}_{counter:03d}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def _move(
    source: Path,
    target: Path,
    *,
    dry_run: bool,
    status: str,
    project_code: str | None = None,
    reason: str | None = None,
) -> ProcessResult:
    if not dry_run:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(target))
    return ProcessResult(source=source, target=target, status=status, project_code=project_code, reason=reason)
