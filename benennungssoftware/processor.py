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
            result = _move(source, target, dry_run=dry_run, status="unassigned", reason="no_project_match")
            if not dry_run:
                _append_to_excel_workbook(config, result)
            results.append(result)
            continue

        target_folder = config.projects_root / project.folder
        filename = build_filename(config, project, source, current_date)
        target = unique_path(target_folder / filename)
        result = _move(source, target, dry_run=dry_run, status="assigned", project_code=project.code)
        if not dry_run:
            _append_to_excel_workbook(config, result)
        results.append(result)

    return results


def process_single_file(
    config: AppConfig,
    source: Path,
    *,
    dry_run: bool = False,
    today: date | None = None,
) -> list[ProcessResult]:
    if not source.exists() or not source.is_file():
        raise FileNotFoundError(source)
    if source.suffix.lower() not in config.allowed_extensions:
        raise ValueError(f"Unsupported file extension: {source.suffix}")

    current_date = today or date.today()
    config.projects_root.mkdir(parents=True, exist_ok=True)
    config.unassigned_folder.mkdir(parents=True, exist_ok=True)

    project = match_project(source, config)
    if project is None:
        target = unique_path(config.unassigned_folder / source.name)
        result = _move(source, target, dry_run=dry_run, status="unassigned", reason="no_project_match")
        if not dry_run:
            _append_to_excel_workbook(config, result)
        return [result]

    target_folder = config.projects_root / project.folder
    filename = build_filename(config, project, source, current_date)
    target = unique_path(target_folder / filename)
    result = _move(source, target, dry_run=dry_run, status="assigned", project_code=project.code)
    if not dry_run:
        _append_to_excel_workbook(config, result)
    return [result]


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
    result = _move(source, target, dry_run=dry_run, status="manually_assigned", project_code=project.code)
    if not dry_run:
        _append_to_excel_workbook(config, result)
    return result


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
    normalized_haystack = re.sub(r"[^a-z0-9]+", " ", haystack.casefold()).strip()
    return [
        project
        for project in projects
        if any(
            keyword and re.sub(r"[^a-z0-9]+", " ", keyword.casefold()).strip() in normalized_haystack
            for keyword in project.keywords
        )
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
    transliterated = (
        value.strip()
        .replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ü", "ue")
        .replace("Ä", "Ae")
        .replace("Ö", "Oe")
        .replace("Ü", "Ue")
        .replace("ß", "ss")
    )
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", transliterated)
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


def _append_to_excel_workbook(config: AppConfig, result: ProcessResult) -> None:
    if not config.excel.enabled or config.excel.workbook_path is None:
        return

    try:
        from openpyxl import Workbook, load_workbook
    except ImportError:
        return

    workbook_path = config.excel.workbook_path
    workbook_path.parent.mkdir(parents=True, exist_ok=True)

    if workbook_path.exists():
        workbook = load_workbook(workbook_path)
    else:
        workbook = Workbook()

    if config.excel.sheet_name not in workbook.sheetnames:
        worksheet = workbook.active
        worksheet.title = config.excel.sheet_name
    else:
        worksheet = workbook[config.excel.sheet_name]

    if worksheet.max_row == 1 and worksheet["A1"].value is None:
        worksheet.delete_rows(1, 1)
        worksheet.append(list(config.excel.columns))
    elif worksheet.max_row == 0:
        worksheet.append(list(config.excel.columns))
    elif worksheet["A1"].value != config.excel.columns[0]:
        worksheet.insert_rows(1)
        worksheet["A1"] = config.excel.columns[0]
        for column_index, header in enumerate(config.excel.columns[1:], start=2):
            worksheet.cell(row=1, column=column_index, value=header)

    next_number = worksheet.max_row
    if worksheet.max_row == 1 and worksheet["A1"].value == config.excel.columns[0]:
        next_number = 1

    worksheet.append([
        next_number,
        result.source.name,
        result.target.name,
        result.status,
        result.reason or "",
    ])
    workbook.save(workbook_path)
