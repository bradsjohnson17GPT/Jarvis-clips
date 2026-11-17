# Scene-based story production

The quality reset retires the old stock-card pipeline for new posts. Its validation and reproduction functions remain available for the archive. Both legacy CLIs now refuse a normal render during this reset; `--legacy-reproduction` is only for reproducing an archived file. The CI workflow runs safeguards without regenerating the rejected batch.

The new pilot is `stories/downward-beacon.json`: an original fantasy story with a consistent courier, floating-town environment, a physical clue, a mechanical action and an answering light. Its finished camera sequence and animation use original Blender geometry. The reviewed pilot is already published; never render or publish a duplicate as new work. Reference analyses are in docs/trends/. No source rights are inferred from a tutorial's success or public viewing.

`config/natural-voice.json` pins the reviewed Kokoro ONNX model and generic stock voice pack by SHA-256. Runtime MIT and first-party model Apache-2.0 metadata and commercial-use statement were reviewed. The weights are downloaded into task-owned local storage, never committed. Use requirements-quality.txt in a task-owned virtual environment. The old Piper model is retained solely for archive reproduction.

Download the pinned weights with `python scripts/download_natural_voice.py --output work/models/kokoro`. It verifies existing bytes, refuses mismatches, and hash-checks each download before installation. `config/denoiser.json` records the official free Open Image Denoise release, matching archive digest and license. The original Blender scene is archived under assets/stories/downward-beacon/.

Generate narration as coherent narrative paragraphs rather than caption-sized utterances. `scripts/story_audio.py` verifies model hashes, synthesizes or reuses the voice master, obtains word timestamps from the actual recording, stops on a script mismatch, and inserts planned pauses into both the sound and timing record. It uses FFmpeg decoding to avoid a PyAV compatibility issue. Timing and an accurate transcript do not prove compelling delivery.

```sh
python scripts/story_audio.py stories/downward-beacon.json \
  --models /path/to/reviewed/models --output work/beacon/narration
```

Once the actual animated picture has passed visual review, `scripts/finish_story.py` checks its portrait framing/duration, hash-verifies the reviewed music, renders speech-timed captions, synthesizes original effects for story actions, ducks the score under narration, and measures the encoded audio after a complete decode. The source picture's audio is never automatically retained. Use an even native portrait size, preserve the actual render dimensions, and record any frame interpolation truthfully.

```sh
python scripts/finish_story.py stories/downward-beacon.json \
  --picture work/beacon/picture.mp4 --narration-dir work/beacon/narration \
  --music /path/to/reviewed/ascension.mp3 --output work/beacon/final.mp4
```

Inspect the actual final frames through every cut, clear clue framing, object motion, character continuity, the reveal and the full mixed audio. A sound/caption preflight with a temporary static picture is only an engineering check; it is not a completed story or a posting candidate. Never copy such a placeholder into the media library or count it toward output.

A final MP4 and source records may be committed for an inspectable preview after editorial review. Publication remains a separate action requiring a supported connected route and actual scheduling/publication evidence. The current Metricool account-level limit has not been resolved; do not treat successful draft saves as publication. Keep detailed receipts, account details and credits private under ignored work/.
