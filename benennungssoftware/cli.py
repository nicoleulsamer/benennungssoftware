from __future__ import annotations

import argparse
from pathlib import Path

from .config import load_config
from .diagnostics import check_ocr_environment
from .processor import process_scan_folder


def main() -> int:
    parser = argparse.ArgumentParser(prog="benennungssoftware")
    subparsers = parser.add_subparsers(dest="command", required=True)

    process_parser = subparsers.add_parser("process", help="Scan-Ordner verarbeiten")
    process_parser.add_argument("--config", required=True, type=Path, help="Pfad zur JSON-Konfiguration")
    process_parser.add_argument("--dry-run", action="store_true", help="Nur anzeigen, nichts verschieben")

    check_ocr_parser = subparsers.add_parser("check-ocr", help="OCR-Voraussetzungen pruefen")
    check_ocr_parser.add_argument("--language", default="deu", help="Tesseract-Sprachcode, z. B. deu oder eng")

    args = parser.parse_args()
    if args.command == "process":
        config = load_config(args.config)
        results = process_scan_folder(config, dry_run=args.dry_run)
        for result in results:
            detail = f" -> {result.target}"
            if result.project_code:
                detail += f" ({result.project_code})"
            if result.reason:
                detail += f" [{result.reason}]"
            print(f"{result.status}: {result.source}{detail}")
        print(f"{len(results)} Datei(en) verarbeitet")
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
