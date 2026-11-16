import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("experiments", ROOT / "scripts/experiments.py")
experiments = importlib.util.module_from_spec(spec)
spec.loader.exec_module(experiments)


class ExperimentChecks(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((ROOT / "config/strategy.json").read_text())

    def observations(self):
        return [
            {"clip_id": f"{kind}-{i}", "content_type": kind, "age_hours": 48,
             "views": (len(self.config["content_types"]) - rank) * 100,
             "duration_seconds": 10, "average_view_duration_seconds": 8, "shares": 2}
            for rank, kind in enumerate(self.config["content_types"]) for i in range(3)
        ]

    def test_no_data_stays_balanced(self):
        p = experiments.plan(self.config, [])
        self.assertEqual(p["mode"], "balanced")
        self.assertEqual(list(p["daily_slots"].values()), [4, 4, 2, 4, 4, 2])

    def test_incomplete_initial_allocation_is_rejected(self):
        del self.config["initial_slot_allocation"]["motivational"]
        with self.assertRaisesRegex(ValueError, "each active content type"):
            experiments.plan(self.config, [])

    def test_too_young_or_old_does_not_determine_winners(self):
        rows = self.observations()
        for i, row in enumerate(rows):
            row["age_hours"] = 12 if i % 2 else 100
        self.assertEqual(experiments.plan(self.config, rows)["mode"], "balanced")

    def test_repeat_snapshots_cannot_inflate_sample_size(self):
        rows = self.observations()[::3]
        self.assertEqual(experiments.plan(self.config, rows * 10)["mode"], "balanced")

    def test_supported_winners_keep_eight_exploration_slots(self):
        result = experiments.plan(self.config, self.observations())
        self.assertEqual(result["mode"], "adaptive")
        self.assertEqual(list(result["daily_slots"].values()), [8, 4, 2, 2, 2, 2])
        self.assertEqual(sum(result["daily_slots"].values()), 20)

    def test_zero_views_is_not_a_supported_winner(self):
        rows = self.observations()
        for row in rows:
            row["views"] = 0
        self.assertEqual(experiments.plan(self.config, rows)["mode"], "balanced")

    def test_single_viral_clip_does_not_beat_consistent_median(self):
        rows = self.observations()
        rows[-1]["views"] = 10000000
        result = experiments.plan(self.config, rows)
        self.assertEqual(result["ranking"][0]["content_type"], "animal_pov")

    def test_invalid_metrics_do_not_become_zero_view_evidence(self):
        rows = self.observations()
        rows[0]["views"] = None
        rows[1]["views"] = float("nan")
        rows[2]["views"] = True
        self.assertEqual(experiments.plan(self.config, rows)["mode"], "balanced")


if __name__ == "__main__":
    unittest.main()

