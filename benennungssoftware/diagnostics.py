from __future__ import annotations

from dataclasses import dataclass
import importlib.util
import shutil
import subprocess


@dataclass(frozen=True)
class CheckResult:
    name: str
    ok: bool
    detail: str


def check_ocr_environment(language: str = "deu") -> list[CheckResult]:
    return [
        _check_python_package("pypdf"),
        _check_python_package("pdf2image"),
        _check_python_package("pytesseract"),
        _check_program("tesseract"),
        _check_program("pdftoppm", label="poppler/pdftoppm"),
        _check_tesseract_language(language),
    ]


def _check_python_package(package: str) -> CheckResult:
    if importlib.util.find_spec(package) is None:
        return CheckResult(package, False, "Python-Paket fehlt")
    return CheckResult(package, True, "Python-Paket installiert")


def _check_program(program: str, *, label: str | None = None) -> CheckResult:
    path = shutil.which(program)
    name = label or program
    if path is None:
        return CheckResult(name, False, "Programm nicht im PATH gefunden")
    return CheckResult(name, True, path)


def _check_tesseract_language(language: str) -> CheckResult:
    if shutil.which("tesseract") is None:
        return CheckResult(f"tesseract language {language}", False, "Tesseract nicht im PATH gefunden")

    try:
        completed = subprocess.run(
            ["tesseract", "--list-langs"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except Exception as exc:
        return CheckResult(f"tesseract language {language}", False, f"Sprachliste konnte nicht gelesen werden: {exc}")

    languages = {
        line.strip()
        for line in completed.stdout.splitlines()
        if line.strip() and not line.lower().startswith("list of")
    }
    if language in languages:
        return CheckResult(f"tesseract language {language}", True, "Sprachdatei gefunden")
    return CheckResult(f"tesseract language {language}", False, f"Sprachdatei fehlt; gefunden: {', '.join(sorted(languages)) or 'keine'}")
