#!/usr/bin/env python3
"""Generate a narrated story take and speech-timed edit records.

Use narrative paragraphs, never caption-sized synthesis or forced time stretching.
The actual voice and final edit still require editorial inspection.
"""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path


def read_json(path):
    return json.loads(Path(path).read_text())


def normalize(word):
    return re.sub(r"[^a-z0-9']", '', word.lower().replace('’', "'"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--models', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--voice-input', type=Path, help='Reuse the reviewed full take rather than synthesize it again.')
    args = parser.parse_args()
    import numpy as np
    import soundfile as sf
    import onnxruntime as ort
    from kokoro_onnx import Kokoro
    from faster_whisper import WhisperModel
    project = Path(__file__).resolve().parents[1]
    story = read_json(args.manifest)
    config = read_json(project / story['voice_config'])
    args.output.mkdir(parents=True, exist_ok=True)
    model_paths = {}
    for key in ['model', 'voices']:
        row = config[key]
        path = args.models / row['filename']
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != row['sha256']:
            raise SystemExit(f'Unreviewed {key} bytes: expected {row["sha256"]}, received {actual}.')
        model_paths[key] = path
    if args.voice_input:
        voice, sr = sf.read(args.voice_input, dtype='float32')
        if voice.ndim != 1:
            raise SystemExit('Provide the mono narration master, not an already mixed soundtrack.')
    else:
        options = ort.SessionOptions()
        options.intra_op_num_threads = 2
        options.inter_op_num_threads = 1
        session = ort.InferenceSession(str(model_paths['model']), sess_options=options, providers=['CPUExecutionProvider'])
        engine = Kokoro.from_session(session, str(model_paths['voices']))
        paragraphs = story.get('narration_paragraphs', [story['narration']])
        if normalize(' '.join(paragraphs)) != normalize(story['narration']):
            raise SystemExit('Narrative paragraphs must match the approved story text.')
        parts = []
        for text in paragraphs:
            data, sr = engine.create(text, voice=config['selected_voice'], speed=config['speed'], lang=config['language'])
            if parts:
                parts.append(np.zeros(round(0.5 * sr), dtype=np.float32))
            parts.append(data)
        voice = np.concatenate(parts)
    raw = args.output / 'narration-master.wav'
    sf.write(raw, voice, sr, subtype='PCM_16')
    # Decode using FFmpeg so PyAV API changes cannot silently alter alignment.
    decoded = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(raw), '-f', 'f32le', '-ar', '16000', '-ac', '1', 'pipe:1'], capture_output=True, check=True).stdout
    model = WhisperModel('base.en', device='cpu', compute_type='int8', cpu_threads=2, download_root=str(args.models / 'whisper'))
    segments, _ = model.transcribe(np.frombuffer(decoded, dtype=np.float32), language='en', word_timestamps=True, beam_size=5, vad_filter=False)
    words = [{'start': w.start, 'end': w.end, 'text': w.word.strip(), 'confidence': w.probability} for segment in segments for w in segment.words]
    expected = story['narration'].split()
    (args.output / 'raw-alignment.json').write_text(json.dumps(words, indent=2) + '\n')
    if [normalize(w['text']) for w in words] != [normalize(w) for w in expected]:
        raise SystemExit('The ASR text differs from the story. Review the actual take and raw-alignment.json before proceeding.')
    for row, text in zip(words, expected):
        row['text'] = text
    pacing = story.get('pacing', {})
    inserts = []
    anchors = pacing.get('insert_after', {})
    for index, word in enumerate(words[:-1]):
        if word['text'] not in anchors:
            continue
        # Pick a quiet 5 ms window near the measured word boundary for the edit.
        boundary = (word['end'] + words[index + 1]['start']) / 2
        lo = max(0, round((boundary - 0.045) * sr))
        hi = min(len(voice), round((boundary + 0.045) * sr))
        win = max(1, round(0.005 * sr))
        energies = np.convolve(voice[lo:hi] ** 2, np.ones(win) / win, mode='valid')
        cut = lo + int(np.argmin(energies)) + win // 2
        inserts.append({'sample': cut, 'seconds': float(anchors[word['text']]), 'after_word_index': index})
    opening = float(pacing.get('opening_silence', 0.15))
    ending = float(pacing.get('ending_silence', 1.0))
    chunks = [np.zeros(round(opening * sr), dtype=np.float32)]
    offset = 0
    for insert in inserts:
        cut = insert['sample']
        left = voice[offset:cut].copy()
        fade = min(round(0.002 * sr), len(left))
        left[-fade:] *= np.linspace(1, 0, fade)
        chunks += [left, np.zeros(round(insert['seconds'] * sr), dtype=np.float32)]
        voice[cut:cut + fade] *= np.linspace(0, 1, fade)
        offset = cut
    chunks += [voice[offset:], np.zeros(round(ending * sr), dtype=np.float32)]
    final = np.concatenate(chunks)
    for index, word in enumerate(words):
        shift = opening + sum(i['seconds'] for i in inserts if i['after_word_index'] < index)
        word['start'] = round(word['start'] + shift, 4)
        word['end'] = round(max(word['end'] + shift, word['start'] + 0.06), 4)
    out = args.output / 'narration-paced.wav'
    sf.write(out, final, sr, subtype='PCM_16')
    report = {'voice': config['selected_voice'], 'speed': config['speed'], 'sample_rate': sr, 'duration_seconds': len(final) / sr, 'sha256': hashlib.sha256(out.read_bytes()).hexdigest(), 'words': words, 'inserted_pauses': inserts, 'qa_limit': 'ASR confirms text/timing only; inspect the finished audiovisual edit for delivery and story quality.'}
    (args.output / 'narration-timing.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ['words', 'inserted_pauses']}), flush=True)


if __name__ == '__main__':
    main()
