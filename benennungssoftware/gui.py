from __future__ import annotations

import argparse
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .config import load_config
from .processor import match_project, process_single_file


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[1] / "examples" / "config.json"


def process_selected_file(config_path: str | Path, source: str | Path, *, dry_run: bool = False):
    config = load_config(config_path)
    return process_single_file(config, Path(source), dry_run=dry_run)


class DocumentProcessorApp:
    def __init__(self, root: tk.Tk, config_path: str | Path | None = None) -> None:
        self.root = root
        self.root.title("Benennungssoftware")
        self.root.geometry("760x520")
        self.root.minsize(700, 420)

        default_config = config_path or DEFAULT_CONFIG_PATH
        self.config_path = Path(default_config)
        self.selected_file = tk.StringVar(value="")
        self.selected_project = tk.StringVar(value="-")
        self.status_text = tk.StringVar(value="Bereit")
        self.dry_run = tk.BooleanVar(value=False)

        main = ttk.Frame(root, padding=18)
        main.pack(fill="both", expand=True)

        ttk.Label(main, text="Konfigurationsdatei", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        config_row = ttk.Frame(main)
        config_row.pack(fill="x", pady=(4, 8))
        self.config_entry = ttk.Entry(config_row, textvariable=tk.StringVar(value=str(self.config_path)))
        self.config_entry.pack(side="left", fill="x", expand=True)
        ttk.Button(config_row, text="Öffnen", command=self.choose_config).pack(side="left", padx=(8, 0))

        ttk.Label(main, text="Datei zum Verarbeiten", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        file_row = ttk.Frame(main)
        file_row.pack(fill="x", pady=(4, 8))
        self.file_entry = ttk.Entry(file_row, textvariable=self.selected_file)
        self.file_entry.pack(side="left", fill="x", expand=True)
        ttk.Button(file_row, text="Datei wählen", command=self.choose_file).pack(side="left", padx=(8, 0))

        ttk.Checkbutton(main, text="Nur Vorschau (dry-run)", variable=self.dry_run).pack(anchor="w", pady=(0, 12))

        ttk.Label(main, text="Erkanntes Projekt", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        ttk.Entry(main, textvariable=self.selected_project, state="readonly").pack(fill="x", pady=(4, 12))

        action_row = ttk.Frame(main)
        action_row.pack(fill="x", pady=(0, 12))
        ttk.Button(action_row, text="Verarbeiten", command=self.process_file).pack(side="left")
        ttk.Button(action_row, text="Neustart", command=self.reset_state).pack(side="left", padx=(8, 0))

        ttk.Label(main, text="Status", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        ttk.Label(main, textvariable=self.status_text, foreground="#0b5131", wraplength=650, justify="left").pack(anchor="w", pady=(4, 0))

        self.update_project_hint()

    def choose_config(self) -> None:
        path = filedialog.askopenfilename(title="Konfigurationsdatei wählen", filetypes=[("JSON", "*.json")])
        if not path:
            return
        self.config_path = Path(path)
        self.config_entry.delete(0, tk.END)
        self.config_entry.insert(0, str(self.config_path))
        self.status_text.set(f"Konfiguration geladen: {self.config_path}")

    def choose_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Datei wählen",
            filetypes=[("PDF und TXT", "*.pdf *.txt"), ("Alle Dateien", "*.*")],
        )
        if not path:
            return
        self.selected_file.set(path)
        self.update_project_hint()
        self.status_text.set(f"Datei ausgewählt: {Path(path).name}")

    def update_project_hint(self) -> None:
        file_path = self.selected_file.get().strip()
        if not file_path:
            self.selected_project.set("-")
            return
        try:
            config = load_config(self.config_path)
            project = match_project(Path(file_path), config)
            self.selected_project.set(
                "nicht zugeordnet" if project is None else f"{project.code} ({project.folder})"
            )
        except Exception:
            self.selected_project.set("-")

    def process_file(self) -> None:
        file_path = self.selected_file.get().strip()
        if not file_path:
            messagebox.showwarning("Keine Datei", "Bitte wählen Sie zuerst eine Datei aus.")
            return

        try:
            results = process_selected_file(self.config_path, file_path, dry_run=self.dry_run.get())
            result = results[0]
            detail = f"Datei: {result.source} -> {result.target}"
            if result.project_code:
                detail += f" ({result.project_code})"
            if result.reason:
                detail += f" [{result.reason}]"
            self.status_text.set(f"{result.status}: {detail}")
            if self.dry_run.get():
                self.status_text.set(f"Vorschau: {detail}")
        except Exception as exc:
            messagebox.showerror("Verarbeitung fehlgeschlagen", str(exc))
            self.status_text.set(f"Fehler: {exc}")

    def reset_state(self) -> None:
        self.selected_file.set("")
        self.selected_project.set("-")
        self.status_text.set("Bereit")


def run_gui(config_path: str | Path | None = None) -> None:
    root = tk.Tk()
    DocumentProcessorApp(root, config_path=config_path)
    root.mainloop()


def main() -> int:
    parser = argparse.ArgumentParser(prog="benennungssoftware-gui")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH, help="Pfad zur JSON-Konfiguration")
    args = parser.parse_args()
    run_gui(config_path=args.config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
