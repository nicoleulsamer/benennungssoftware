from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from benennungssoftware.diagnostics import _check_program, _check_tesseract_language


class DiagnosticsTests(unittest.TestCase):
    def test_check_program_reports_missing_path_entry(self) -> None:
        with patch("benennungssoftware.diagnostics.shutil.which", return_value=None):
            result = _check_program("tesseract")

        self.assertFalse(result.ok)
        self.assertEqual(result.detail, "Programm nicht im PATH gefunden")

    def test_tesseract_language_is_detected(self) -> None:
        completed = Mock(stdout="List of available languages in data path:\ndeu\neng\n")

        with patch("benennungssoftware.diagnostics.shutil.which", return_value="C:/Tools/tesseract.exe"):
            with patch("benennungssoftware.diagnostics.subprocess.run", return_value=completed):
                result = _check_tesseract_language("deu")

        self.assertTrue(result.ok)


if __name__ == "__main__":
    unittest.main()
