#!/usr/bin/env python3
"""Download the reviewed voice model and check its pinned content hashes."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=ROOT / "work/models")
    args = parser.parse_args()
    voice = json.loads((ROOT / "config/audio.json").read_text())["voice"]
    args.directory.mkdir(parents=True, exist_ok=True)
    for suffix, url_key, hash_key in ((".onnx", "model_url", "model_sha256"), (".onnx.json", "config_url", "config_sha256")):
        path = args.directory / (voice["id"] + suffix)
        expected = voice[hash_key]
        if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            subprocess.run(["curl", "--fail", "--location", "--silent", "--show-error", "--proto", "=https", "--proto-redir", "=https", "--max-time", "180", "--output", str(path), voice[url_key]], check=True)
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError("Downloaded voice changed; review the new model before use")
        print(f"Verified {path.name}")


if __name__ == "__main__":
    main()

