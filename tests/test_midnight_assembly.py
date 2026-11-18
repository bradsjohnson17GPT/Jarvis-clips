"""Guard against incomplete/stale art and the previously observed short AAC tail."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import unittest
import zlib

from scripts.assemble_midnight_story import assemble, digest, validate_inputs, validate_probe


def png(shade):
    def chunk(kind, data):
        return (struct.pack('>I', len(data)) + kind + data +
                struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff))
    pixels = (b'\0' + bytes([shade]) * (720 * 3)) * 1280
    return (b'\x89PNG\r\n\x1a\n' +
            chunk(b'IHDR', struct.pack('>IIBBBBB', 720, 1280, 8, 2, 0, 0, 0)) +
            chunk(b'IDAT', zlib.compress(pixels)) + chunk(b'IEND', b''))


class MidnightAssemblyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'frames').mkdir()
        (self.root / 'denoised').mkdir()
        (self.root / 'frozen-scene.py').write_text('# test scene\n')
        (self.root / 'frozen-scene.blend').write_bytes(b'fixture blend identity')
        self.audio = self.root / 'inspected.m4a'
        self.audio.write_bytes(b'fixture audio identity; no encoding claimed')
        self.captions = self.root / 'captions.ass'
        self.captions.write_text('[Script Info]\nScriptType: v4.00+\nPlayResX: 720\nPlayResY: 1280\n')
        self.plan = {'id': 'fixture', 'expected_frames': 8, 'fps': 24,
                     'dimensions': [720, 1280], 'duration_seconds': 8 / 24,
                     'source_sha256': digest(self.root / 'frozen-scene.py'),
                     'frozen_blend_sha256': digest(self.root / 'frozen-scene.blend'),
                     'audio_container_sha256': digest(self.audio),
                     'caption_sha256': digest(self.captions)}
        self.denoiser = {'archive_sha256': 'fixture-reviewed-runtime'}
        self.manifest = {'id': 'fixture', 'expected_frames': 8, 'fps': 24,
                         'width': 720, 'height': 1280, 'frame_numbers': list(range(1, 9)),
                         'source_sha256': self.plan['source_sha256'],
                         'blend_sha256': self.plan['frozen_blend_sha256']}
        (self.root / 'render-manifest.json').write_text(json.dumps(self.manifest))
        pictures = [png(40), png(60)]
        for number in range(1, 9):
            raw = self.root / 'frames' / f'{number:05d}.png'
            clean = self.root / 'denoised' / raw.name
            raw.write_bytes(pictures[number % 2])
            clean.write_bytes(pictures[number % 2])
            evidence = {'frame': number, 'frozen_scene_sha256': self.plan['source_sha256'],
                        'source_png_sha256': digest(raw), 'output_png_sha256': digest(clean),
                        'oidn_archive_sha256': self.denoiser['archive_sha256'],
                        'method': 'OIDN2.5.1 CPU RT LDR/sRGB high, beauty-only',
                        'dimensions': [720, 1280], 'resized': False}
            clean.with_suffix('.json').write_text(json.dumps(evidence))

    def verify(self):
        return validate_inputs(self.root, self.audio, self.captions, self.plan, self.denoiser)

    def test_complete_raw_frames_do_not_replace_missing_denoised_frame(self):
        (self.root / 'denoised/00006.png').unlink()
        with self.assertRaisesRegex(ValueError, 'frame 6 is incomplete'):
            self.verify()

    def test_scene_blend_substitution_invalidates_otherwise_complete_cache(self):
        (self.root / 'frozen-scene.blend').write_bytes(b'another scene')
        with self.assertRaisesRegex(ValueError, 'Frozen scene or blend changed'):
            self.verify()

    def test_changed_raw_frame_cannot_reuse_old_denoise_receipt(self):
        (self.root / 'frames/00004.png').write_bytes(png(90))
        with self.assertRaisesRegex(ValueError, 'frame 4 has stale or substituted'):
            self.verify()

    def test_superseded_audio_cannot_use_completed_picture(self):
        self.audio.write_bytes(b'superseded shorter audio container')
        with self.assertRaisesRegex(ValueError, 'inspected complete V2'):
            self.verify()

    def test_video_length_cannot_hide_the_previous_72ms_audio_shortfall(self):
        plan = copy.deepcopy(self.plan)
        plan.update(expected_frames=678, duration_seconds=28.25)
        probe = {'streams': [
            {'codec_type': 'video', 'codec_name': 'h264', 'pix_fmt': 'yuv420p',
             'nb_frames': '678', 'width': 720, 'height': 1280, 'r_frame_rate': '24/1',
             'avg_frame_rate': '24/1', 'duration': '28.250000'},
            {'codec_type': 'audio', 'codec_name': 'aac', 'channels': 2,
             'sample_rate': '48000', 'duration': '28.178000'}],
            'format': {'duration': '28.250000'}}
        with self.assertRaisesRegex(ValueError, 'duration differs'):
            validate_probe(probe, plan)

    @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'FFmpeg integration unavailable')
    def test_actual_mux_preserves_frame_count_and_inspected_aac_bytes(self):
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i',
                        'anullsrc=r=48000:cl=stereo', '-t', str(8 / 24), '-c:a', 'aac',
                        '-b:a', '128k', str(self.audio)], check=True, capture_output=True)
        essence = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(self.audio),
                                          '-c:a', 'copy', '-f', 'adts', 'pipe:1'])
        self.plan['audio_container_sha256'] = digest(self.audio)
        self.plan['audio_aac_essence_adts_sha256'] = hashlib.sha256(essence).hexdigest()
        output = self.root / 'private-fixture.mp4'
        report = assemble(self.verify(), self.audio, self.captions, output, self.plan)
        self.assertEqual(report['frames'], 8)
        self.assertTrue(report['full_decode_passed'])
        self.assertTrue(report['audio_essence_unchanged'])
        self.assertFalse(report['publishable'])
        self.assertFalse(report['publication_mutation'])


if __name__ == '__main__':
    unittest.main()
