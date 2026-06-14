# OCR-Setup

## Stand der Prüfung

Die Software kann die OCR-Voraussetzungen selbst prüfen:

```powershell
python -m benennungssoftware.cli check-ocr
```

Aktuell sind die Python-Pakete installiert:

- `pypdf`
- `pdf2image`
- `pytesseract`

Für OCR braucht die Software diese Systemkomponenten:

- `tesseract`
- deutsche Tesseract-Sprachdatei `deu`

Für das Rendern von PDF-Seiten nutzt die Software zuerst das Python-Paket `PyMuPDF`. Poppler beziehungsweise `pdftoppm` ist nur noch ein optionaler Fallback.

## Bedeutung

`pypdf` liest Text aus PDFs, die digital erzeugt wurden. Dafür ist keine OCR nötig.

`Tesseract` liest Text aus Bildscans. Das ist für echte Scan-PDFs nötig, bei denen im PDF kein Text gespeichert ist.

`PyMuPDF` wandelt PDF-Seiten in Bilder um. Diese Bilder bekommt anschließend Tesseract zur Texterkennung.

## Installation mit Chocolatey

Chocolatey ist auf diesem Rechner vorhanden, aber die Installation muss in einer PowerShell mit Administratorrechten laufen.

PowerShell als Administrator öffnen und ausführen, falls Poppler zusätzlich als Fallback installiert werden soll:

```powershell
choco install tesseract poppler -y
```

Danach eine neue normale PowerShell öffnen und prüfen:

```powershell
python -m benennungssoftware.cli check-ocr
```

Wenn die deutsche Sprache `deu` fehlt, muss die deutsche Tesseract-Sprachdatei nachinstalliert oder in den Tesseract-Datenordner gelegt werden.

## Erwartetes Ergebnis

Wenn alles bereit ist, sollte die Prüfung ungefähr so aussehen:

```text
OK: pypdf - Python-Paket installiert
OK: pdf2image - Python-Paket installiert
OK: pytesseract - Python-Paket installiert
OK: tesseract - ...
OK: pdf renderer - PyMuPDF verfügbar; Poppler nicht zwingend nötig
OK: tesseract language deu - Sprachdatei gefunden
```
