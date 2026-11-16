import importlib.util
import tempfile
import unittest
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("audio_tools", ROOT / "scripts/add_audio.py")
audio_tools = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audio_tools)


class AudioChecks(unittest.TestCase):
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
