import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
module = importlib.util.spec_from_file_location("renderer", ROOT / "scripts/render.py")
renderer = importlib.util.module_from_spec(module)
module.loader.exec_module(renderer)


class ManifestChecks(unittest.TestCase):
    def setUp(self):
        self.spec = json.loads((ROOT / "clips/spreadsheet.json").read_text())

    def test_rejects_unreviewed_rights(self):
        self.spec["source"]["rights_verified"] = False
        with self.assertRaisesRegex(ValueError, "rights"):
            renderer.validate(self.spec)

    def test_rejects_missing_audience(self):
        del self.spec["audience"]
        with self.assertRaisesRegex(ValueError, "audience"):
            renderer.validate(self.spec)

    def test_rejects_overlapping_captions(self):
        self.spec["captions"][1]["start"] = 1
        with self.assertRaisesRegex(ValueError, "nonoverlapping"):
            renderer.validate(self.spec)

    def test_rejects_path_traversal(self):
        self.spec["id"] = "../escape"
        with self.assertRaisesRegex(ValueError, "id"):
            renderer.validate(self.spec)

    def test_rejects_nonfinite_times(self):
        for value in (float("nan"), float("inf"), True):
            with self.subTest(value=value):
                spec = copy.deepcopy(self.spec)
                spec["duration"] = value
                with self.assertRaises(ValueError):
                    renderer.validate(spec)

    def test_caption_text_cannot_inject_ass_commands(self):
        self.assertEqual(renderer.ass_text("{\\pos(1,1)}hello\\Nworld\nnext"), "｛＼pos(1,1)｝hello＼Nworld\\Nnext")

    def test_rounds_ass_timestamp_across_minute(self):
        self.assertEqual(renderer.ass_time(59.999), "0:01:00.00")


if __name__ == "__main__":
    unittest.main()

