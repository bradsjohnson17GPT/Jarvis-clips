#!/usr/bin/env python3
"""Download only the pinned, reviewed natural-narration model and stock voices."""
import argparse
import hashlib
import json
import tempfile
import urllib.request
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', required=True, type=Path)
    args = p.parse_args()
    config = json.loads((Path(__file__).resolve().parents[1] / 'config/natural-voice.json').read_text())
    args.output.mkdir(parents=True, exist_ok=True)
    for key in ['model', 'voices']:
        row = config[key]
        target = args.output / row['filename']
        if target.exists():
            if hashlib.sha256(target.read_bytes()).hexdigest() != row['sha256']:
                raise SystemExit(f'Existing {target.name} has unreviewed bytes; inspect it before replacement.')
            print(f'Verified {target.name}')
            continue
        if not row['url'].startswith('https://'):
            raise SystemExit('Reviewed downloads must use HTTPS.')
        with tempfile.TemporaryDirectory(prefix='reviewed-narrator-', dir=args.output) as folder:
            download = Path(folder) / 'download'
            with urllib.request.urlopen(row['url'], timeout=60) as response, download.open('wb') as output:
                if not response.url.startswith('https://'):
                    raise SystemExit('Download redirected to an insecure source.')
                total = 0
                while chunk := response.read(1024 * 1024):
                    total += len(chunk)
                    if total > 512 * 1024 * 1024:
                        raise SystemExit('Model exceeds the reviewed download-size limit.')
                    output.write(chunk)
            if hashlib.sha256(download.read_bytes()).hexdigest() != row['sha256']:
                raise SystemExit(f'{target.name} does not match the reviewed hash; not installed.')
            download.replace(target)
            print(f'Downloaded and verified {target.name}')


if __name__ == '__main__':
    main()
