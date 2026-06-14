from __future__ import annotations

import argparse
from pathlib import Path

from .config import load_config
from .diagnostics import check_ocr_environment
from .processor import assign_unassigned_document, process_scan_folder
from .reporting import write_process_report


def main() -> int:
    parser = argparse.ArgumentParser(prog="benennungssoftware")
    subparsers = parser.add_subparsers(dest="command", required=True)

    process_parser = subparsers.add_parser("process", help="Scan-Ordner verarbeiten")
    process_parser.add_argument("--config", required=True, type=Path, help="Pfad zur JSON-Konfiguration")
    process_parser.add_argument("--dry-run", action="store_true", help="Nur anzeigen, nichts verschieben")
    process_parser.add_argument("--log", type=Path, help="CSV-Protokoll schreiben oder erweitern")

    assign_parser = subparsers.add_parser("assign", help="Nicht zuordenbares Dokument manuell einem Projekt zuweisen")
    assign_parser.add_argument("--config", required=True, type=Path, help="Pfad zur JSON-Konfiguration")
    assign_parser.add_argument("--source", required=True, type=Path, help="Datei aus dem Klaerungsordner")
    assign_parser.add_argument("--project", required=True, help="Projektcode, z. B. PRJ001")
    assign_parser.add_argument("--dry-run", action="store_true", help="Nur anzeigen, nichts verschieben")
    assign_parser.add_argument("--log", type=Path, help="CSV-Protokoll schreiben oder erweitern")

    projects_parser = subparsers.add_parser("projects", help="Konfigurierte Projekte anzeigen")
    projects_parser.add_argument("--config", required=True, type=Path, help="Pfad zur JSON-Konfiguration")
    projects_parser.add_argument("--keywords", action="store_true", help="Keywords je Projekt anzeigen")

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

    if args.command == "check-ocr":
        results = check_ocr_environment(language=args.language)
        for result in results:
            marker = "OK" if result.ok else "FEHLT"
            print(f"{marker}: {result.name} - {result.detail}")
        return 0 if all(result.ok for result in results) else 1

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
