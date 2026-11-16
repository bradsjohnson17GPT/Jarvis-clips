import importlib.util
import hashlib
import json
import sys
import tempfile
import unittest
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("audio_tools", ROOT / "scripts/add_audio.py")
audio_tools = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audio_tools)


class AudioChecks(unittest.TestCase):
    def licensed_spec(self, track):
        spec = json.loads((ROOT / "clips/spreadsheet.json").read_text())
        spec["duration"] = 1
        spec["description"] = "Test track by Test composer. https://creativecommons.org/licenses/by/4.0/ Excerpt mixed with narration."
        spec["audio"] = {"licensed_music": {
            "rights_verified": True, "commercial_use": True,
            "title": "Test track", "artist": "Test composer",
            "page": "https://example.com/track", "download": "https://example.com/track.wav",
            "license": "https://creativecommons.org/licenses/by/4.0/",
            "sha256": hashlib.sha256(track.read_bytes()).hexdigest(),
            "reviewed_by": "Test reviewer", "reviewed_on": "2026-11-16",
            "rights_note": "Generated test signal, no third party recording.",
            "attribution": "Test track by Test composer.",
            "changes": "Excerpt mixed with narration.", "start": 0.1
        }}
        return spec

    def test_licensed_excerpt_decodes_stereo_and_rejects_swapped_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "track.wav"
            signal = np.sin(np.arange(72000) * 2 * np.pi * 440 / 48000).astype(np.float32) * 0.2
            audio_tools.write_wav(path, np.column_stack([signal, signal]))
            spec = self.licensed_spec(path)
            samples = audio_tools.licensed_music(spec, Path(temp), path)
            self.assertEqual(samples.shape, (48000, 2))
            self.assertGreater(float(np.max(np.abs(samples))), 0.01)
            self.assertLessEqual(float(np.max(np.abs(samples))), 0.35)
            spec["audio"]["licensed_music"]["sha256"] = "0" * 64
            with self.assertRaisesRegex(ValueError, "reviewed hash"):
                audio_tools.licensed_music(spec, Path(temp), path)

    def test_licensed_music_refuses_missing_credit_or_commercial_rights(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "track.wav"
            audio_tools.write_wav(path, np.zeros((72000, 2), dtype=np.float32))
            for defect in ("credit", "rights"):
                spec = self.licensed_spec(path)
                if defect == "credit":
                    spec["description"] = "Missing the required credit"
                else:
                    spec["audio"]["licensed_music"]["commercial_use"] = False
                with self.subTest(defect=defect), self.assertRaises(ValueError):
                    audio_tools.licensed_music(spec, Path(temp), path)

    def test_original_music_is_deterministic_stereo_and_audible(self):
        a = audio_tools.original_music(1, 123, "animal_pov")
        b = audio_tools.original_music(1, 123, "animal_pov")
        self.assertEqual(a.shape, (48000, 2))
        np.testing.assert_array_equal(a, b)
        self.assertGreater(float(np.max(np.abs(a))), 0.001)
        self.assertLess(float(np.max(np.abs(a))), 0.1)

    def test_writer_refuses_clipping_and_nonfinite_audio(self):
        with tempfile.TemporaryDirectory() as temp:
            for values in (np.array([1.1]), np.array([float("nan")])):
                with self.subTest(values=values), self.assertRaises(ValueError):
                    audio_tools.write_wav(Path(temp) / "bad.wav", values)

    def test_writer_preserves_stereo_frame_count(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "test.wav"
            audio_tools.write_wav(path, np.zeros((480, 2), dtype=np.float32))
            with wave.open(str(path), "rb") as stream:
                self.assertEqual(stream.getnframes(), 480)
                self.assertEqual(stream.getnchannels(), 2)
                self.assertEqual(stream.getframerate(), 48000)


if __name__ == "__main__":
    unittest.main()
