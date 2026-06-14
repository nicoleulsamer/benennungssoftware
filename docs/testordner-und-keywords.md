# Testordner und Projekt-Keywords

## Testordner

Die Beispielkonfiguration verwendet diese Ordner:

- `examples/demo/scans`: Eingang für neue Testdokumente
- `examples/demo/projects`: Zielordner für erkannte Projekte
- `examples/demo/unassigned`: Klärungsordner für nicht zuordenbare Dokumente

Ein sicherer Testlauf verschiebt nichts:

```powershell
python -m benennungssoftware.cli process --config examples/config.json --dry-run
```

Ein echter Lauf verschiebt die Dateien:

```powershell
python -m benennungssoftware.cli process --config examples/config.json
```

## Aktuelle Beispiel-Projekte

| Projektcode | Zielordner | Keywords |
| --- | --- | --- |
| `PRJ001` | `PRJ001_Bauvorhaben-Mitte` | `bauvorhaben mitte`, `bv-mitte`, `kunde a`, `rechnung mitte` |
| `PRJ002` | `PRJ002_Sanierung-Nord` | `sanierung nord`, `snord`, `kunde b`, `abschlagszahlung nord` |

## Keyword-Regeln

- Keywords sollten so eindeutig sein, dass sie nur zu einem Projekt passen.
- Gute Keywords sind Projektname, Kurzcode, Kundennummer, Bauvorhaben-Nummer oder eindeutige Aktenzeichen.
- Zu allgemeine Wörter wie `rechnung`, `angebot` oder `protokoll` sind riskant, weil sie in vielen Dokumenten vorkommen.
- Wenn ein Dokument Keywords aus mehreren Projekten enthält, wird es nicht automatisch zugeordnet. Das ist Absicht, damit keine falsche Ablage passiert.

## Vorlage für echte Projekte

Für jedes echte Projekt solltest du mindestens diese Angaben sammeln:

```text
Projektcode:
Zielordner:
Projektname:
Kunde:
Kurzzeichen:
Weitere eindeutige Suchbegriffe:
```
