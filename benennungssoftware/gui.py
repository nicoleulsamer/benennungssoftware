from __future__ import annotations

import argparse
import os
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

from .config import add_keyword_to_config, add_project_to_config, load_config
from .processor import (
    assign_unassigned_document,
    list_unassigned_documents,
    match_project,
    process_scan_folder,
    process_single_file,
    suggest_projects,
)


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[1] / "examples" / "config.json"


def process_selected_file(config_path: str | Path, source: str | Path, *, dry_run: bool = False):
    config = load_config(config_path)
    return process_single_file(config, Path(source), dry_run=dry_run)


class DocumentProcessorApp:
    def __init__(self, root: tk.Tk, config_path: str | Path | None = None) -> None:
        self.root = root
        self.root.title("Benennungssoftware")
        self.root.geometry("900x620")
        self.root.minsize(820, 500)

        default_config = config_path or DEFAULT_CONFIG_PATH
        self.config_path = Path(default_config)
        self.selected_file = tk.StringVar(value="")
        self.selected_project = tk.StringVar(value="-")
        self.status_text = tk.StringVar(value="Bereit")
        self.dry_run = tk.BooleanVar(value=False)
        self.project_code_var = tk.StringVar(value="")
        self.unassigned_var = tk.StringVar(value="")

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
        action_row.pack(fill="x", pady=(0, 6))
        ttk.Button(action_row, text="Verarbeiten", command=self.process_file).pack(side="left")
        ttk.Button(action_row, text="Scan-Ordner verarbeiten", command=self.process_scan_folder).pack(side="left", padx=(8, 0))
        ttk.Button(action_row, text="Neustart", command=self.reset_state).pack(side="left", padx=(8, 0))

        admin_row = ttk.Frame(main)
        admin_row.pack(fill="x", pady=(8, 8))
        ttk.Button(admin_row, text="Projekt hinzufügen", command=self.add_project).pack(side="left")
        ttk.Button(admin_row, text="Keyword hinzufügen", command=self.add_keyword).pack(side="left", padx=(8, 0))
        ttk.Button(admin_row, text="Klärungsordner laden", command=self.load_unassigned).pack(side="left", padx=(8, 0))

        unassigned_frame = ttk.LabelFrame(main, text="Klärungsordner")
        unassigned_frame.pack(fill="both", expand=True, pady=(0, 8))
        self.unassigned_listbox = tk.Listbox(unassigned_frame, height=8)
        self.unassigned_listbox.pack(side="left", fill="both", expand=True, padx=(8, 8), pady=(8, 8))
        self.unassigned_listbox.bind("<<ListboxSelect>>", self.on_unassigned_select)

        suggestion_frame = ttk.LabelFrame(main, text="Vorschläge")
        suggestion_frame.pack(fill="x", pady=(0, 8))
        self.suggestion_text = tk.Text(suggestion_frame, height=5, wrap="word", state="disabled")
        self.suggestion_text.pack(fill="x", padx=(8, 8), pady=(8, 8))

        assign_row = ttk.Frame(main)
        assign_row.pack(fill="x", pady=(0, 8))
        ttk.Label(assign_row, text="Projekt für Klärungsfall:").pack(side="left")
        self.project_combo = ttk.Combobox(assign_row, textvariable=self.project_code_var, state="readonly", width=24)
        self.project_combo.pack(side="left", padx=(8, 8))
        ttk.Button(assign_row, text="Zuweisen", command=self.assign_selected_unassigned).pack(side="left")

        ttk.Label(main, text="Status", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        ttk.Label(main, textvariable=self.status_text, foreground="#0b5131", wraplength=850, justify="left").pack(anchor="w", pady=(4, 0))

        self.refresh_project_codes()
        self.update_project_hint()

    def choose_config(self) -> None:
        path = filedialog.askopenfilename(title="Konfigurationsdatei wählen", filetypes=[("JSON", "*.json")])
        if not path:
            return
        self.config_path = Path(path)
        self.config_entry.delete(0, tk.END)
        self.config_entry.insert(0, str(self.config_path))
        self.refresh_project_codes()
        self.status_text.set(f"Konfiguration geladen: {self.config_path}")

    def refresh_project_codes(self) -> None:
        try:
            config = load_config(self.config_path)
            projects = [project.code for project in config.projects]
            self.project_combo["values"] = projects
            if projects:
                self.project_code_var.set(projects[0])
        except Exception:
            self.project_combo["values"] = []
            self.project_code_var.set("")

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
            self.load_unassigned()
        except Exception as exc:
            messagebox.showerror("Verarbeitung fehlgeschlagen", str(exc))
            self.status_text.set(f"Fehler: {exc}")

    def process_scan_folder(self) -> None:
        try:
            config = load_config(self.config_path)
            results = process_scan_folder(config, dry_run=self.dry_run.get())
            assigned = sum(1 for item in results if item.status == "assigned")
            unassigned = sum(1 for item in results if item.status == "unassigned")
            self.status_text.set(
                f"Scan-Ordner verarbeitet: {assigned} zugewiesen, {unassigned} ungeklärt"
            )
            self.load_unassigned()
        except Exception as exc:
            messagebox.showerror("Fehler beim Verarbeiten", str(exc))
            self.status_text.set(f"Fehler: {exc}")

    def add_project(self) -> None:
        code = simpledialog.askstring("Projekt hinzufügen", "Projektcode:")
        if not code:
            return
        folder = simpledialog.askstring("Projekt hinzufügen", "Ordnername:")
        if not folder:
            return
        keywords_text = simpledialog.askstring("Projekt hinzufügen", "Keywords (kommagetrennt):")
        keywords = [item.strip() for item in (keywords_text or "").split(",") if item.strip()]
        if not keywords:
            keywords = [code.lower()]
        try:
            add_project_to_config(self.config_path, code, folder, keywords)
            self.refresh_project_codes()
            self.status_text.set(f"Projekt hinzugefügt: {code}")
        except Exception as exc:
            messagebox.showerror("Projekt konnte nicht hinzugefügt werden", str(exc))

    def add_keyword(self) -> None:
        try:
            config = load_config(self.config_path)
        except Exception as exc:
            messagebox.showerror("Konfiguration konnte nicht geladen werden", str(exc))
            return
        project_codes = [project.code for project in config.projects]
        if not project_codes:
            messagebox.showwarning("Keine Projekte", "Bitte zuerst ein Projekt anlegen.")
            return
        project = simpledialog.askstring("Keyword hinzufügen", f"Projektcode ({', '.join(project_codes)}):")
        if not project:
            return
        keyword = simpledialog.askstring("Keyword hinzufügen", "Neues Keyword:")
        if not keyword:
            return
        try:
            add_keyword_to_config(self.config_path, project, keyword)
            self.status_text.set(f"Keyword hinzugefügt: {project} -> {keyword}")
        except Exception as exc:
            messagebox.showerror("Keyword konnte nicht hinzugefügt werden", str(exc))

    def load_unassigned(self) -> None:
        try:
            config = load_config(self.config_path)
            documents = list_unassigned_documents(config)
            self.unassigned_listbox.delete(0, tk.END)
            for document in documents:
                self.unassigned_listbox.insert(tk.END, str(document))
            if not documents:
                self.status_text.set("Klärungsordner ist leer.")
        except Exception as exc:
            messagebox.showerror("Klärungsordner konnte nicht geladen werden", str(exc))

    def on_unassigned_select(self, _event) -> None:
        selection = self.unassigned_listbox.curselection()
        if not selection:
            return
        file_path = self.unassigned_listbox.get(selection[0])
        self.selected_file.set(file_path)
        self.update_project_hint()
        try:
            config = load_config(self.config_path)
            suggestions = suggest_projects(Path(file_path), config, limit=5)
            if not suggestions:
                self.suggestion_text.configure(state="normal")
                self.suggestion_text.delete("1.0", tk.END)
                self.suggestion_text.insert(tk.END, "Keine Projektsuggestions gefunden.")
                self.suggestion_text.configure(state="disabled")
                return
            lines = [f"{project.code}: score={score} | {project.folder}" for project, score in suggestions]
            self.suggestion_text.configure(state="normal")
            self.suggestion_text.delete("1.0", tk.END)
            self.suggestion_text.insert(tk.END, "\n".join(lines))
            self.suggestion_text.configure(state="disabled")
        except Exception as exc:
            self.suggestion_text.configure(state="normal")
            self.suggestion_text.delete("1.0", tk.END)
            self.suggestion_text.insert(tk.END, f"Fehler: {exc}")
            self.suggestion_text.configure(state="disabled")

    def assign_selected_unassigned(self) -> None:
        selection = self.unassigned_listbox.curselection()
        if not selection:
            messagebox.showwarning("Keine Auswahl", "Bitte wählen Sie zuerst eine Datei aus dem Klärungsordner aus.")
            return
        project_code = self.project_code_var.get().strip()
        if not project_code:
            messagebox.showwarning("Kein Projekt", "Bitte wählen Sie ein Projekt aus.")
            return
        file_path = self.unassigned_listbox.get(selection[0])
        try:
            config = load_config(self.config_path)
            result = assign_unassigned_document(config, Path(file_path), project_code)
            self.status_text.set(f"Zugewiesen: {result.source} -> {result.target} ({result.project_code})")
            self.load_unassigned()
            self.selected_file.set("")
            self.selected_project.set("-")
        except Exception as exc:
            messagebox.showerror("Zuweisung fehlgeschlagen", str(exc))
            self.status_text.set(f"Fehler: {exc}")

    def reset_state(self) -> None:
        self.selected_file.set("")
        self.selected_project.set("-")
        self.unassigned_listbox.delete(0, tk.END)
        self.suggestion_text.configure(state="normal")
        self.suggestion_text.delete("1.0", tk.END)
        self.suggestion_text.insert(tk.END, "Keine Vorschläge")
        self.suggestion_text.configure(state="disabled")
        self.status_text.set("Bereit")


def run_gui(config_path: str | Path | None = None) -> None:
    if os.environ.get("DISPLAY", "") == "" and os.name != "nt":
        raise RuntimeError("GUI kann hier nicht gestartet werden, weil keine Desktop-Umgebung verfügbar ist.")

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
