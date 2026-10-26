import contextlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
import json

ROOT = Path(__file__).resolve().parents[1]
AVAILABLE = importlib.util.find_spec("hwpx") is not None


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"kit/skills/hwpx-formatter/scripts/{name}.py")
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


@unittest.skipUnless(AVAILABLE, "optional python-hwpx not installed")
class HwpxTests(unittest.TestCase):
    def setUp(self):
        from hwpx import HwpxDocument
        self.document = HwpxDocument
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.form = self.base / "form.hwpx"
        doc = HwpxDocument.new()
        table = doc.add_table(1, 2)
        table.set_cell_text(0, 0, "과제명")
        doc.save_to_path(self.form)
        self.values = self.base / "values.json"
        self.values.write_text(json.dumps({"과제명 > right": "한글 과제"}, ensure_ascii=False), encoding="utf-8")
        self.fill = module("fill_hwpx_form").fill

    def tearDown(self):
        self.temp.cleanup()

    def test_markdown_table_and_korean_roundtrip(self):
        doc = module("md2hwpx").convert("# 한글 제목\n\n|항목|값|\n|---|---|\n|예산|500만 원|", self.base)
        dest = self.base / "report.hwpx"
        doc.save_to_path(dest)
        reopened = self.document.open(dest)
        self.assertTrue(reopened.validate().ok)
        self.assertIn("500만 원", reopened.text.plain())

    def test_fill_preserves_original_and_content(self):
        before = self.form.read_bytes()
        out = self.base / "filled.hwpx"
        with contextlib.redirect_stdout(io.StringIO()):
            self.fill(self.form, self.values, out)
        self.assertEqual(before, self.form.read_bytes())
        result = self.document.open(out)
        self.assertTrue(result.validate().ok)
        self.assertIn("한글 과제", result.text.plain())
        with self.assertRaises(SystemExit):
            self.fill(self.form, self.values, out)

    def test_missing_label_does_not_save_incomplete_form(self):
        self.values.write_text('{"unknown > right":"value"}', encoding="utf-8")
        out = self.base / "failed.hwpx"
        with self.assertRaises(SystemExit):
            self.fill(self.form, self.values, out)
        self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
