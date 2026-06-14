from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from benennungssoftware.config import add_keyword_to_config, add_project_to_config, load_config


class ConfigManagementTests(unittest.TestCase):
    def test_adds_project_to_config(self) -> None:
        with TemporaryDirectory() as tmp:
            config_path = _write_config(Path(tmp))

            add_project_to_config(
                config_path,
                "PRJ003",
                "PRJ003_Neues-Projekt",
                [" Kunde C ", "kunde c", "Aktenzeichen 42"],
            )

            raw = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertEqual(raw["projects"][0]["code"], "PRJ003")
            self.assertEqual(raw["projects"][0]["keywords"], ["kunde c", "aktenzeichen 42"])
            loaded = load_config(config_path)
            self.assertEqual(loaded.projects[0].code, "PRJ003")

    def test_add_project_rejects_duplicate_code(self) -> None:
        with TemporaryDirectory() as tmp:
            config_path = _write_config(
                Path(tmp),
                projects=[{"code": "PRJ001", "folder": "PRJ001_Test", "keywords": ["test"]}],
            )

            with self.assertRaises(ValueError):
                add_project_to_config(config_path, "prj001", "PRJ001_Andere", ["anders"])

    def test_adds_keyword_to_existing_project(self) -> None:
        with TemporaryDirectory() as tmp:
            config_path = _write_config(
                Path(tmp),
                projects=[{"code": "PRJ001", "folder": "PRJ001_Test", "keywords": ["kunde a"]}],
            )

            add_keyword_to_config(config_path, "PRJ001", " Bauakte A ")
            add_keyword_to_config(config_path, "PRJ001", "bauakte a")

            raw = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertEqual(raw["projects"][0]["keywords"], ["kunde a", "bauakte a"])

    def test_add_keyword_rejects_unknown_project(self) -> None:
        with TemporaryDirectory() as tmp:
            config_path = _write_config(Path(tmp))

            with self.assertRaises(ValueError):
                add_keyword_to_config(config_path, "PRJ999", "keyword")


def _write_config(path: Path, *, projects: list[dict] | None = None) -> Path:
    config_path = path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "scan_folder": "scans",
                "projects_root": "projects",
                "unassigned_folder": "unassigned",
                "allowed_extensions": [".pdf", ".txt"],
                "projects": projects or [],
            }
        ),
        encoding="utf-8",
    )
    return config_path


if __name__ == "__main__":
    unittest.main()
