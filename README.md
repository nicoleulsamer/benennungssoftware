# Neue Benennungssoftware

Ein kleines Python-Projekt zur automatischen Benennung und Ablage von gescannten Dokumenten.

## Abgedeckte User Stories

- Administratoren konfigurieren ein einheitliches Namensschema.
- Administratoren verwalten Projekt-Keywords.
- Mitarbeiter verarbeiten Scan-Ordner automatisch.
- Dokumente werden in den passenden Projektordner verschoben.
- Nicht zuordenbare Dokumente landen sichtbar im Klärungsordner.
- Bestehende Dateien werden nicht überschrieben.
- PDF-Dateien werden per Text-Extraktion und optional per OCR durchsucht.

## Schnellstart

```powershell
python -m benennungssoftware.cli process --config examples/config.json --dry-run
```

Ohne `--dry-run` werden Dateien tatsächlich verschoben:

```powershell
python -m benennungssoftware.cli process --config examples/config.json
```

Ein CSV-Protokoll kann zusätzlich geschrieben werden:

```powershell
python -m benennungssoftware.cli process --config examples/config.json --dry-run --log examples/demo/process-log.csv
```

Das Protokoll enthält Zeitstempel, Dry-Run-Status, Quellpfad, Zielpfad, Projektcode und den Grund bei nicht zuordenbaren Dokumenten.

Konfigurierte Projekte anzeigen:

```powershell
python -m benennungssoftware.cli projects --config examples/config.json --keywords
```

Dateien im Klärungsordner anzeigen:

```powershell
python -m benennungssoftware.cli unassigned --config examples/config.json
```

Ein Dokument aus dem Klärungsordner kann manuell einem Projekt zugewiesen werden:

```powershell
python -m benennungssoftware.cli assign --config examples/config.json --source examples/demo/unassigned/scan003_unbekannt.txt --project PRJ001 --dry-run --log examples/demo/process-log.csv
```

Das nutzt dasselbe Namensschema und denselben Überschreibschutz wie die automatische Verarbeitung.

## Konfiguration

Siehe [examples/config.json](examples/config.json). Wichtige Felder:

- `scan_folder`: Eingang für neue Scans
- `projects_root`: Zielordner für Projektunterordner
- `unassigned_folder`: Ablage für nicht zuordenbare Dateien
- `name_schema`: Bausteine für den neuen Dateinamen
- `projects`: Projektcodes, Ordnernamen und Keywords
- `text_extraction`: Einstellungen für PDF-Text und OCR

Für Schritt 1 gibt es eine kurze Arbeitsnotiz mit Testordnern, Beispiel-Dateien und Keyword-Regeln:

```text
docs/testordner-und-keywords.md
```

Das Standard-Namensschema erzeugt Dateinamen wie:

```text
2026-06-14_PRJ001_Rechnung_scan001.pdf
```

## OCR für echte PDF-Scans

Die Software versucht bei PDFs zuerst eingebetteten Text zu lesen. Das ist schnell und reicht für digital erzeugte PDFs. Wenn dabei zu wenig Text gefunden wird, wird OCR versucht. OCR bedeutet: Die PDF-Seiten werden als Bilder gerendert und Tesseract erkennt daraus Buchstaben.

Python-Pakete installieren:

```powershell
python -m pip install -r requirements-ocr.txt
```

Zusätzlich muss Tesseract OCR mit deutscher Sprachdatei `deu` installiert und im `PATH` verfügbar sein.

Für das Rendern der PDF-Seiten nutzt die Software zuerst PyMuPDF. Poppler ist nur noch ein optionaler Fallback für `pdf2image`.

OCR-Voraussetzungen prüfen:

```powershell
python -m benennungssoftware.cli check-ocr
```

Wenn dort `FEHLT` steht, kann die Basisverarbeitung weiterlaufen, aber echte Scan-PDFs werden noch nicht per OCR gelesen.

Die ausführliche lokale Setup-Notiz liegt hier:

```text
docs/ocr-setup.md
```

Die OCR-Einstellungen stehen in [examples/config.json](examples/config.json):

```json
"text_extraction": {
  "ocr_enabled": true,
  "ocr_language": "deu",
  "ocr_max_pages": 3,
  "min_embedded_text_length": 20
}
```

`ocr_max_pages` begrenzt die Zahl der gelesenen Seiten. Das hält die Verarbeitung schnell und verhindert, dass ein langer Scan den ganzen Durchlauf blockiert.

## Tests

```powershell
python -m unittest discover -s tests
```
