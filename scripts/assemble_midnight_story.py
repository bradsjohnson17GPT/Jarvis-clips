#!/usr/bin/env python3
"""Assemble Midnight Bell only from its complete pinned native picture and audio.

This creates a private review candidate, never a posting or ready-queue entry.
"""
import argparse
import fcntl
import hashlib
import json
import subprocess
from pathlib import Path

try:
    from scripts.denoise_original_frames import complete_png
except ModuleNotFoundError:
    from denoise_original_frames import complete_png


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(command):
    return subprocess.run(list(map(str, command)), capture_output=True, check=True)


def validate_inputs(root, audio, captions, plan, denoiser):
    root = Path(root).resolve()
    manifest = json.loads((root / 'render-manifest.json').read_text())
    expected = list(range(1, plan['expected_frames'] + 1))
    if (manifest['id'] != plan['id'] or manifest['source_sha256'] != plan['source_sha256'] or
            manifest['blend_sha256'] != plan['frozen_blend_sha256'] or
            manifest['frame_numbers'] != expected or manifest['expected_frames'] != len(expected) or
            manifest['fps'] != plan['fps'] or
            [manifest['width'], manifest['height']] != plan['dimensions']):
        raise ValueError('Native cache does not match the pinned complete scene plan.')
    if (digest(root / 'frozen-scene.py') != plan['source_sha256'] or
            digest(root / 'frozen-scene.blend') != plan['frozen_blend_sha256']):
        raise ValueError('Frozen scene or blend changed after rendering started.')
    if digest(audio) != plan['audio_container_sha256']:
        raise ValueError('Audio is not the inspected complete V2 container.')
    if digest(captions) != plan['caption_sha256']:
        raise ValueError('Captions differ from the inspected speech-timed version.')
    pictures = []
    for number in expected:
        raw = root / 'frames' / f'{number:05d}.png'
        clean = root / 'denoised' / raw.name
        receipt = clean.with_suffix('.json')
        if not (complete_png(raw, plan['dimensions']) and
                complete_png(clean, plan['dimensions']) and receipt.is_file()):
            raise ValueError(f'Native frame {number} is incomplete or not denoised; no fallback.')
        evidence = json.loads(receipt.read_text())
        if (evidence['frame'] != number or evidence['frozen_scene_sha256'] != plan['source_sha256'] or
                evidence['source_png_sha256'] != digest(raw) or
                evidence['output_png_sha256'] != digest(clean) or
                evidence['oidn_archive_sha256'] != denoiser['archive_sha256'] or
                evidence['method'] != 'OIDN2.5.1 CPU RT LDR/sRGB high, beauty-only' or
                evidence['dimensions'] != plan['dimensions'] or evidence['resized']):
            raise ValueError(f'Native frame {number} has stale or substituted denoise evidence.')
        pictures.append((clean, evidence['output_png_sha256']))
    return pictures


def validate_probe(probe, plan):
    video = [s for s in probe['streams'] if s['codec_type'] == 'video']
    audio = [s for s in probe['streams'] if s['codec_type'] == 'audio']
    if len(video) != 1 or len(audio) != 1:
        raise ValueError('The candidate must contain one video and one audio stream.')
    v, a = video[0], audio[0]
    if (int(v['nb_frames']) != plan['expected_frames'] or
            [v['width'], v['height']] != plan['dimensions'] or
            v['codec_name'] != 'h264' or v['pix_fmt'] != 'yuv420p' or
            v['r_frame_rate'] != f"{plan['fps']}/1" or
            v['avg_frame_rate'] != f"{plan['fps']}/1" or
            a['codec_name'] != 'aac' or a['channels'] != 2 or int(a['sample_rate']) != 48000):
        raise ValueError('Encoded frame count, portrait timing or stereo AAC format changed.')
    # A correct overall container duration can hide a shorter audio stream.
    for stream in (v, a, probe['format']):
        if abs(float(stream['duration']) - plan['duration_seconds']) > .04:
            raise ValueError('A video, audio or container duration differs from the full timeline.')


def assemble(pictures, audio, captions, output, plan):
    output = Path(output).resolve()
    if output.exists():
        raise ValueError('Choose a new private candidate path; never overwrite an existing movie.')
    subtitle = Path(captions).resolve()
    if any(c in str(subtitle) for c in "'[];,\n\\:"):
        raise ValueError('Use a simple task-owned subtitle path.')
    output.parent.mkdir(parents=True, exist_ok=True)
    log = output.with_suffix('.assembly.log')
    with log.open('wb') as error:
        process = subprocess.Popen([
            'ffmpeg', '-v', 'error', '-n', '-f', 'image2pipe', '-framerate', str(plan['fps']),
            '-vcodec', 'png', '-i', 'pipe:0', '-i', str(audio),
            '-map', '0:v:0', '-map', '1:a:0', '-vf', f"ass=filename='{subtitle}'",
            '-r', str(plan['fps']), '-fps_mode', 'cfr', '-c:v', 'libx264', '-threads', '2',
            '-crf', '18', '-pix_fmt', 'yuv420p', '-c:a', 'copy', '-movflags', '+faststart',
            str(output)], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=error)
        try:
            for path, expected_hash in pictures:
                data = path.read_bytes()
                if hashlib.sha256(data).hexdigest() != expected_hash:
                    raise ValueError('A denoised frame changed during assembly.')
                process.stdin.write(data)
        finally:
            process.stdin.close()
            code = process.wait()
    if code:
        raise RuntimeError(f'Assembly failed; inspect {log.name}.')
    run(['ffmpeg', '-v', 'error', '-xerror', '-err_detect', 'explode',
         '-i', output, '-f', 'null', '-'])
    probe = json.loads(run(['ffprobe', '-v', 'error', '-show_streams', '-show_format',
                            '-of', 'json', output]).stdout)
    validate_probe(probe, plan)
    essence = run(['ffmpeg', '-v', 'error', '-i', output, '-map', '0:a:0',
                   '-c:a', 'copy', '-f', 'adts', 'pipe:1']).stdout
    if hashlib.sha256(essence).hexdigest() != plan['audio_aac_essence_adts_sha256']:
        raise ValueError('Final AAC differs from the inspected soundtrack; preserve for investigation.')
    if (digest(audio) != plan['audio_container_sha256'] or
            digest(captions) != plan['caption_sha256']):
        raise ValueError('Pinned audio or captions changed during assembly.')
    report = {'id': plan['id'], 'status': 'private_candidate_pending_actual_finished_review',
              'publishable': False, 'frames': len(pictures), 'full_decode_passed': True,
              'audio_essence_unchanged': True, 'caption_sha256': digest(captions),
              'source_sha256': plan['source_sha256'], 'output_sha256': digest(output),
              'subjective_listening_claimed': False, 'publication_mutation': False}
    output.with_suffix('.operation.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--render-root', required=True, type=Path)
    parser.add_argument('--audio', required=True, type=Path)
    parser.add_argument('--captions', required=True, type=Path)
    parser.add_argument('--assemble', action='store_true', help='Default is read-only input verification.')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    project = Path(__file__).resolve().parents[1]
    plan = json.loads((project / 'assets/stories/midnight-bell/finishing-plan.json').read_text())
    denoiser = json.loads((project / 'config/denoiser.json').read_text())
    with (project / '.git/jarvis-midnight-assembly.lock').open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            pictures = validate_inputs(args.render_root, args.audio, args.captions, plan, denoiser)
            if args.assemble:
                if args.output is None or not args.output.resolve().is_relative_to(project / 'work'):
                    parser.error('Assembly requires a new output inside ignored project work/.')
                print(json.dumps(assemble(pictures, args.audio, args.captions, args.output, plan)))
            else:
                print(json.dumps({'verified_frames': len(pictures), 'publishable': False,
                                  'finished_video_created': False}))
        except ValueError as error:
            parser.error(str(error))


if __name__ == '__main__':
    main()
