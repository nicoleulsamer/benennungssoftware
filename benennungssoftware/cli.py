from __future__ import annotations

import argparse
from pathlib import Path

from .config import add_keyword_to_config, add_project_to_config, load_config, validate_config_file
from .diagnostics import check_ocr_environment
from .processor import assign_unassigned_document, list_unassigned_documents, process_scan_folder
from .reporting import summarize_process_report, write_process_report
from .text_extraction import extract_document_text, preview_text


def main() -> int:
    parser = argparse.ArgumentParser(prog="benennungssoftware")
    subparsers = parser.add_subparsers(dest="command", required=True)

    process_parser = subparsers.add_parser("process", help="Scan-Ordner verarbeiten")
    process_parser.add_argument("--config", required=True, type=Path, help="Pfad zur JSON-Konfiguration")
    process_parser.add_argument("--dry-run", action="store_true", help="Nur anzeigen, nichts verschieben")
    process_parser.add_argument("--log", type=Path, help="CSV-Protokoll schreiben oder erweitern")

    report_parser = subparsers.add_parser("report", help="CSV-Protokoll zusammenfassen")
    report_parser.add_argument("--log", required=True, type=Path, help="Pfad zum CSV-Protokoll")
    report_parser.add_argument("--show-unassigned", action="store_true", help="Nicht zugeordnete Zielpfade anzeigen")

    assign_parser = subparsers.add_parser("assign", help="Nicht zuordenbares Dokument manuell einem Projekt zuweisen")
    assign_parser.add_argument("--config", required=True, type=Path, help="Pfad zur JSON-Konfiguration")
    assign_parser.add_argument("--source", required=True, type=Path, help="Datei aus dem Klaerungsordner")
    assign_parser.add_argument("--project", required=True, help="Projektcode, z. B. PRJ001")
    assign_parser.add_argument("--dry-run", action="store_true", help="Nur anzeigen, nichts verschieben")
    assign_parser.add_argument("--log", type=Path, help="CSV-Protokoll schreiben oder erweitern")

    projects_parser = subparsers.add_parser("projects", help="Konfigurierte Projekte anzeigen")
    projects_parser.add_argument("--config", required=True, type=Path, help="Pfad zur JSON-Konfiguration")
    projects_parser.add_argument("--keywords", action="store_true", help="Keywords je Projekt anzeigen")

    add_project_parser = subparsers.add_parser("add-project", help="Projekt zur Konfiguration hinzufuegen")
    add_project_parser.add_argument("--config", required=True, type=Path, help="Pfad zur JSON-Konfiguration")
    add_project_parser.add_argument("--code", required=True, help="Projektcode, z. B. PRJ003")
    add_project_parser.add_argument("--folder", required=True, help="Zielordner fuer das Projekt")
    add_project_parser.add_argument("--keyword", required=True, action="append", help="Keyword; mehrfach verwendbar")

    add_keyword_parser = subparsers.add_parser("add-keyword", help="Keyword zu einem Projekt hinzufuegen")
    add_keyword_parser.add_argument("--config", required=True, type=Path, help="Pfad zur JSON-Konfiguration")
    add_keyword_parser.add_argument("--project", required=True, help="Projektcode, z. B. PRJ001")
    add_keyword_parser.add_argument("--keyword", required=True, help="Neues Keyword")

    validate_parser = subparsers.add_parser("validate-config", help="Konfiguration pruefen")
    validate_parser.add_argument("--config", required=True, type=Path, help="Pfad zur JSON-Konfiguration")

    unassigned_parser = subparsers.add_parser("unassigned", help="Dateien im Klaerungsordner anzeigen")
    unassigned_parser.add_argument("--config", required=True, type=Path, help="Pfad zur JSON-Konfiguration")

    inspect_parser = subparsers.add_parser("inspect", help="Extrahierten Text einer Datei anzeigen")
    inspect_parser.add_argument("--config", required=True, type=Path, help="Pfad zur JSON-Konfiguration")
    inspect_parser.add_argument("--source", required=True, type=Path, help="Zu pruefende Datei")
    inspect_parser.add_argument("--chars", type=int, default=2000, help="Maximale Zeichen im Textausschnitt")

    check_ocr_parser = subparsers.add_parser("check-ocr", help="OCR-Voraussetzungen pruefen")
    check_ocr_parser.add_argument("--language", default="deu", help="Tesseract-Sprachcode, z. B. deu oder eng")

    args = parser.parse_args()
    if args.command == "process":
        config = load_config(args.config)
        results = process_scan_folder(config, dry_run=args.dry_run)
        if args.log:
            write_process_report(args.log, results, dry_run=args.dry_run)
        for result in results:
            detail = f" -> {result.target}"
            if result.project_code:
                detail += f" ({result.project_code})"
            if result.reason:
                detail += f" [{result.reason}]"
            print(f"{result.status}: {result.source}{detail}")
        print(f"{len(results)} Datei(en) verarbeitet")
        if args.log:
            print(f"Protokoll geschrieben: {args.log}")
        return 0

    if args.command == "report":
        summary = summarize_process_report(args.log)
        print(f"Gesamt: {summary.total}")
        print("Status:")
        for status, count in summary.by_status.items():
            print(f"  {status}: {count}")
        print("Projekte:")
        if summary.by_project:
            for project_code, count in summary.by_project.items():
                print(f"  {project_code}: {count}")
        else:
            print("  -")
        print(f"Klärungsfälle: {len(summary.unassigned_targets)}")
        if args.show_unassigned:
            for target in summary.unassigned_targets:
                print(f"  {target}")
        return 0

    if args.command == "assign":
        config = load_config(args.config)
        result = assign_unassigned_document(config, args.source, args.project, dry_run=args.dry_run)
        if args.log:
            write_process_report(args.log, [result], dry_run=args.dry_run)
        print(f"{result.status}: {result.source} -> {result.target} ({result.project_code})")
        if args.log:
            print(f"Protokoll geschrieben: {args.log}")
        return 0

    if args.command == "projects":
        config = load_config(args.config)
        for project in config.projects:
            print(f"{project.code}: {project.folder}")
            if args.keywords:
                print(f"  keywords: {', '.join(project.keywords) or '-'}")
        print(f"{len(config.projects)} Projekt(e) konfiguriert")
        return 0

    if args.command == "add-project":
        add_project_to_config(args.config, args.code, args.folder, args.keyword)
        print(f"Projekt hinzugefügt: {args.code} -> {args.folder}")
        return 0

    if args.command == "add-keyword":
        add_keyword_to_config(args.config, args.project, args.keyword)
        print(f"Keyword hinzugefügt: {args.project} -> {args.keyword.strip().casefold()}")
        return 0

    if args.command == "validate-config":
        issues = validate_config_file(args.config)
        if not issues:
            print("OK: Konfiguration ist plausibel")
            return 0
        for issue in issues:
            print(f"{issue.severity.upper()}: {issue.message}")
        return 1 if any(issue.severity == "error" for issue in issues) else 0

    if args.command == "unassigned":
        config = load_config(args.config)
        documents = list_unassigned_documents(config)
        for index, document in enumerate(documents, start=1):
            print(f"{index}: {document}")
        print(f"{len(documents)} Datei(en) im Klärungsordner")
        return 0

    if args.command == "inspect":
        config = load_config(args.config)
        text = extract_document_text(args.source, config.text_extraction)
        print(f"Datei: {args.source}")
        print(f"Extrahierte Zeichen: {len(text)}")
        if not text.strip():
            print("Kein Text erkannt")
            return 1
        print(preview_text(text, max(1, args.chars)))
        return 0

    if args.command == "check-ocr":
        results = check_ocr_environment(language=args.language)
        for result in results:
            marker = "OK" if result.ok else "FEHLT"
            print(f"{marker}: {result.name} - {result.detail}")
        return 0 if all(result.ok for result in results) else 1

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
