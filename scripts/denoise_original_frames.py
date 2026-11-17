#!/usr/bin/env python3
"""Denoise completed original scene PNGs without resizing or replacing raw frames.

Uses the reviewed standalone OIDN release because the local Blender lacks it.
This is a technical picture pass, not an editorial quality or publication gate.
"""
import argparse
import hashlib
import json
import struct
import subprocess
import tarfile
import tempfile
import time
from pathlib import Path, PurePosixPath


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def verify_release(archive, root, expected):
    if digest(archive) != expected:
        raise ValueError('OIDN archive does not match the reviewed release digest.')
    checked = 0
    with tarfile.open(archive, 'r:gz') as package:
        for member in package.getmembers():
            parts = PurePosixPath(member.name).parts
            if not member.isfile() or len(parts) < 3 or parts[1] not in {'bin', 'lib'}:
                continue
            installed = root.joinpath(*parts[1:]).resolve()
            if not installed.is_relative_to(root):
                raise ValueError('Installed OIDN file resolves outside the reviewed bundle.')
            released = package.extractfile(member)
            h = hashlib.sha256()
            for chunk in iter(lambda: released.read(1024 * 1024), b''):
                h.update(chunk)
            if digest(installed) != h.hexdigest():
                raise ValueError(f'Installed OIDN release file mismatch: {installed.name}')
            checked += 1
    if not checked:
        raise ValueError('No installed OIDN runtime files were verified.')
    return root / 'bin' / 'oidnDenoise', checked


def complete_png(path, dimensions):
    if not path.exists() or path.stat().st_size < 36:
        return False
    with path.open('rb') as stream:
        header = stream.read(24)
        stream.seek(-12, 2)
        tail = stream.read(12)
    return (header[:8] == b'\x89PNG\r\n\x1a\n' and
            struct.unpack('>II', header[16:24]) == tuple(dimensions) and
            tail == b'\x00\x00\x00\x00IEND\xaeB`\x82')


def write_pfm(path, pixels):
    import numpy as np
    height, width, _ = pixels.shape
    with path.open('wb') as stream:
        stream.write(f'PF\n{width} {height}\n-1.0\n'.encode())
        np.flipud(pixels).astype('<f4').tofile(stream)


def read_pfm(path, dimensions):
    import numpy as np
    with path.open('rb') as stream:
        if stream.readline().strip() != b'PF':
            raise ValueError('Unexpected OIDN image format.')
        width, height = map(int, stream.readline().split())
        if (width, height) != tuple(dimensions):
            raise ValueError('OIDN changed the picture dimensions.')
        scale = float(stream.readline())
        pixels = np.fromfile(stream, dtype='<f4' if scale < 0 else '>f4')
    pixels = np.flipud(pixels.reshape(height, width, 3))
    if not np.isfinite(pixels).all():
        raise ValueError('OIDN returned nonfinite pixels.')
    return pixels


def main():
    import numpy as np
    from PIL import Image
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--render-root', required=True, type=Path)
    parser.add_argument('--oidn-archive', required=True, type=Path)
    parser.add_argument('--oidn-root', required=True, type=Path)
    parser.add_argument('--limit', type=int, default=0, help='Maximum new frames this batch; zero means all currently complete.')
    parser.add_argument('--frames', type=int, nargs='+')
    args = parser.parse_args()
    project = Path(__file__).resolve().parents[1]
    config = json.loads((project / 'config/denoiser.json').read_text())
    root = args.render_root.resolve()
    manifest = json.loads((root / 'render-manifest.json').read_text())
    source = Path(manifest['frozen_source'])
    if not source.is_absolute():
        source = project / source
    if digest(source) != manifest['source_sha256']:
        raise ValueError('The frozen scene source does not match this frame cache.')
    dimensions = [manifest['width'], manifest['height']]
    tool, verified_files = verify_release(args.oidn_archive.resolve(), args.oidn_root.resolve(), config['archive_sha256'])
    output = root / 'denoised'
    output.mkdir(exist_ok=True)
    wanted = set(args.frames or manifest['frame_numbers'])
    if not wanted.issubset(set(manifest['frame_numbers'])):
        raise ValueError('Requested frame is outside the original-scene frame manifest.')
    processed, cached, incomplete = 0, 0, 0
    for number in sorted(wanted):
        src = root / 'frames' / f'{number:05d}.png'
        if not complete_png(src, dimensions):
            incomplete += 1
            continue  # The renderer may still be writing this file; never touch it.
        dst, receipt_path = output / src.name, output / f'{number:05d}.json'
        source_hash = digest(src)
        if receipt_path.exists() and complete_png(dst, dimensions):
            old = json.loads(receipt_path.read_text())
            if (old['source_png_sha256'] == source_hash and
                old['oidn_archive_sha256'] == config['archive_sha256'] and
                old.get('method') == 'OIDN2.5.1 CPU RT LDR/sRGB high, beauty-only' and
                old['output_png_sha256'] == digest(dst)):
                cached += 1
                continue
        with Image.open(src) as image:
            if image.mode == 'RGBA' and image.getchannel('A').getextrema() != (255, 255):
                raise ValueError('This pass supports opaque original scene frames only.')
            pixels = np.asarray(image.convert('RGB'), dtype=np.float32) / 255
        started = time.monotonic()
        with tempfile.TemporaryDirectory(prefix=f'oidn-{number:05d}-', dir=output) as temp:
            inp, out = Path(temp) / 'input.pfm', Path(temp) / 'output.pfm'
            write_pfm(inp, pixels)
            subprocess.run([str(tool), '--device', 'cpu', '--ldr', str(inp), '--srgb',
                            '--threads', '2', '--affinity', '0', '--maxmem', '512',
                            '--quality', 'high', '--output', str(out)],
                           capture_output=True, check=True)
            clean = read_pfm(out, dimensions)
            temporary = output / f'{number:05d}.png.tmp'
            Image.fromarray(np.rint(np.clip(clean, 0, 1) * 255).astype('uint8')).save(temporary, format='PNG')
            temporary.replace(dst)
        receipt = {'frame': number, 'frozen_scene_sha256': manifest['source_sha256'],
                   'source_png_sha256': source_hash, 'output_png_sha256': digest(dst),
                   'oidn_archive_sha256': config['archive_sha256'], 'verified_runtime_files': verified_files,
                   'method': 'OIDN2.5.1 CPU RT LDR/sRGB high, beauty-only',
                   'dimensions': dimensions, 'resized': False, 'raw_source_preserved': True,
                   'seconds': round(time.monotonic() - started, 3), 'publishable': False}
        receipt_path.write_text(json.dumps(receipt, indent=2) + '\n')
        processed += 1
        if args.limit and processed >= args.limit:
            break
    print(json.dumps({'processed_new': processed, 'valid_cache_hits': cached,
                      'not_yet_complete': incomplete, 'verified_runtime_files': verified_files,
                      'dimensions_preserved': dimensions, 'publishable': False}))


if __name__ == '__main__':
    main()
