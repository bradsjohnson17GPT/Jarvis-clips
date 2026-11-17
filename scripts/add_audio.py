#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Add timed Piper narration, reviewed music, and original effects to a video.

Piper is a separately installed GPL-3.0 dependency. Its reviewed LJ Speech
voice is MIT-licensed in the voice repository and uses public-domain data.
Music defaults to an original composition; reviewed licensed tracks are optional.
"""
import argparse
import hashlib
import json
import math
import subprocess
import tempfile
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_RATE = 48000


def write_wav(path, samples, sample_rate=SAMPLE_RATE):
    if not np.all(np.isfinite(samples)):
        raise ValueError("Non-finite audio samples")
    if np.max(np.abs(samples), initial=0) > 0.99:
        raise ValueError("Audio mix would clip")
    channels = 1 if samples.ndim == 1 else samples.shape[1]
    pcm = (samples * 32767).astype("<i2")
    with wave.open(str(path), "wb") as out:
        out.setnchannels(channels)
        out.setsampwidth(2)
        out.setframerate(sample_rate)
        out.writeframes(pcm.tobytes())


def original_music(duration, seed, content_type):
    count = round(duration * SAMPLE_RATE)
    music = np.zeros((count, 2), dtype=np.float32)
    rng = np.random.default_rng(seed)
    tempo = {"animal_pov": 104, "workplace_comedy": 100, "everyday_humor": 92, "visual_surprises": 82, "fictional_micro_stories": 88}.get(content_type, 94)
    beat = 60 / tempo
    chords = ((48, 52, 55), (45, 48, 52), (41, 45, 48), (43, 47, 50))
    for step in range(math.ceil(duration / beat)):
        start = round(step * beat * SAMPLE_RATE)
        length = min(round(beat * 1.9 * SAMPLE_RATE), count - start)
        if length <= 0:
            continue
        t = np.arange(length, dtype=np.float32) / SAMPLE_RATE
        chord = chords[(step // 4) % len(chords)]
        note = chord[step % 3] + (12 if step % 2 else 0)
        frequency = 440 * 2 ** ((note - 69) / 12)
        envelope = np.minimum(t / 0.012, 1) * np.exp(-t * 4)
        tone = (np.sin(2 * np.pi * frequency * t) + 0.22 * np.sin(4 * np.pi * frequency * t)) * envelope * 0.014
        pan = rng.uniform(0.35, 0.65)
        music[start:start + length, 0] += tone * pan
        music[start:start + length, 1] += tone * (1 - pan)
        if step % 2 == 0:
            bass = np.sin(2 * np.pi * (frequency / 2) * t) * np.exp(-t * 7) * 0.009
            music[start:start + length] += bass[:, None]
    fade = min(round(0.3 * SAMPLE_RATE), count // 2)
    music[:fade] *= np.linspace(0, 1, fade)[:, None]
    music[-fade:] *= np.linspace(1, 0, fade)[:, None]
    return music


def voice_samples(voice, text, raw_path, available, maximum_tempo):
    from piper.config import SynthesisConfig
    with wave.open(str(raw_path), "wb") as out:
        voice.synthesize_wav(text, out, SynthesisConfig(length_scale=0.93, noise_scale=0.5, noise_w_scale=0.5))
    with wave.open(str(raw_path), "rb") as stream:
        rate = stream.getframerate()
        samples = np.frombuffer(stream.readframes(stream.getnframes()), dtype="<i2").astype(np.float32) / 32768
    audible = np.flatnonzero(np.abs(samples) > 0.003)
    if not len(audible):
        raise ValueError("Synthesized narration is silent")
    a, b = max(0, audible[0] - int(rate * 0.035)), min(len(samples), audible[-1] + int(rate * 0.09))
    samples = samples[a:b]
    # Piper may normalize to full scale; leave headroom before processing.
    source_peak = float(np.max(np.abs(samples)))
    if source_peak > 0.98:
        samples *= 0.98 / source_peak
    raw_duration = len(samples) / rate
    tempo = max(1.0, raw_duration / available * 1.015)
    if tempo > maximum_tempo:
        raise ValueError(f"Narration needs a shorter script: tempo {tempo:.2f}, text={text!r}")
    write_wav(raw_path, samples, rate)
    decoded = subprocess.check_output(["ffmpeg", "-v", "error", "-i", str(raw_path), "-af", f"atempo={tempo:.6f}", "-ac", "1", "-ar", str(SAMPLE_RATE), "-f", "f32le", "pipe:1"])
    speech = np.frombuffer(decoded, dtype="<f4").copy()
    if len(speech) > round(available * SAMPLE_RATE):
        raise ValueError("Narration would overlap the next caption")
    rms = float(np.sqrt(np.mean(speech ** 2)))
    gain = min(0.13 / max(rms, 1e-8), 0.67 / max(float(np.max(np.abs(speech))), 1e-8))
    speech *= gain
    return speech, tempo


def licensed_music(spec, work, music_file=None):
    """Decode an identified, reviewed track; never silently substitute a file."""
    from render import validate_music
    validate_music(spec)
    record = spec.get("audio", {}).get("licensed_music")
    if not record:
        if music_file is not None:
            raise ValueError("A music file requires a reviewed licensed_music record")
        return None
    if music_file is None:
        from render import download
        music_file = work / "licensed-music-source"
        download(record["download"], music_file)
    music_file = Path(music_file)
    if hashlib.sha256(music_file.read_bytes()).hexdigest() != record["sha256"]:
        raise ValueError("Licensed music bytes do not match the reviewed hash")
    total = round(spec["duration"] * SAMPLE_RATE)
    decoded = subprocess.check_output([
        "ffmpeg", "-v", "error", "-ss", str(record.get("start", 0)),
        "-i", str(music_file), "-t", str(spec["duration"]),
        "-ac", "2", "-ar", str(SAMPLE_RATE), "-f", "f32le", "pipe:1"
    ])
    samples = np.frombuffer(decoded, dtype="<f4").copy().reshape(-1, 2)
    if len(samples) < total - round(0.05 * SAMPLE_RATE):
        raise ValueError("Licensed music excerpt is shorter than the video")
    samples = np.pad(samples[:total], ((0, max(0, total - len(samples))), (0, 0)))
    rms = float(np.sqrt(np.mean(samples ** 2)))
    if not np.isfinite(rms) or rms < 1e-6:
        raise ValueError("Licensed music excerpt is silent or invalid")
    samples *= min(0.075 / rms, 0.35 / max(float(np.max(np.abs(samples))), 1e-8))
    fade = min(round(0.25 * SAMPLE_RATE), total // 2)
    samples[:fade] *= np.linspace(0, 1, fade)[:, None]
    samples[-fade:] *= np.linspace(1, 0, fade)[:, None]
    return samples


def add_audio(spec, video, destination, voice, work, settings, music_file=None):
    duration = spec["duration"]
    total = round(duration * SAMPLE_RATE)
    seed = int(hashlib.sha256(spec["id"].encode()).hexdigest()[:8], 16)
    music = licensed_music(spec, work, music_file)
    music_record = spec.get("audio", {}).get("licensed_music")
    if music is None:
        music = original_music(duration, seed, spec.get("content_type", "workplace_comedy"))
    voices = np.zeros(total, dtype=np.float32)
    effects = np.zeros(total, dtype=np.float32)
    duck = np.ones(total, dtype=np.float32)
    intervals = []
    for i, caption in enumerate(spec["captions"]):
        text = caption.get("narration") or caption["text"].replace("\n", " ").capitalize()
        start = caption["start"] + 0.08
        available = caption["end"] - start - 0.1
        if available <= 0:
            raise ValueError("Caption leaves no room for narration")
        speech, tempo = voice_samples(voice, text, work / f"speech-{i}.wav", available, settings["maximum_voice_tempo_factor"])
        offset = round(start * SAMPLE_RATE)
        end = offset + len(speech)
        if end > total:
            raise ValueError("Narration extends beyond the video")
        voices[offset:end] += speech
        duck[offset:end] = 0.3
        edge = min(round(0.025 * SAMPLE_RATE), len(speech) // 2)
        duck[offset:offset + edge] = np.linspace(1, 0.3, edge)
        duck[end - edge:end] = np.linspace(0.3, 1, edge)
        # A soft, original descending wooden pop marks each caption change.
        effect_start = round(caption["start"] * SAMPLE_RATE)
        size = min(round(0.075 * SAMPLE_RATE), total - effect_start)
        t = np.arange(size, dtype=np.float32) / SAMPLE_RATE
        pop = np.sin(2 * np.pi * (620 * t - 2400 * t * t)) * np.exp(-t * 65) * 0.035
        pop[:min(96, size)] *= np.linspace(0, 1, min(96, size))
        effects[effect_start:effect_start + size] += pop
        intervals.append({"text": text, "caption_start": caption["start"], "speech_start": start, "speech_end": end / SAMPLE_RATE, "caption_end": caption["end"], "tempo_factor": tempo})
    mix = music * duck[:, None] + voices[:, None] + effects[:, None]
    peak = float(np.max(np.abs(mix)))
    if peak > 0.95:
        mix *= 0.95 / peak
    write_wav(work / "mix.wav", mix)
    destination.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-y", "-i", str(video), "-i", str(work / "mix.wav"), "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-ar", str(SAMPLE_RATE), "-ac", "2", "-af", f"loudnorm=I={settings['target_lufs']}:TP={settings['true_peak_limit_db']}:LRA=7", "-t", str(duration), "-movflags", "+faststart", str(destination)], check=True)
    info = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,codec_name,sample_rate,channels:format=duration", "-of", "json", str(destination)]))
    audio_stream = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    if not audio_stream or audio_stream["codec_name"] != "aac" or audio_stream["channels"] != 2:
        raise ValueError("Final video has no valid stereo AAC stream")
    result = {"id": spec["id"], "audio": "timed_narration_licensed_music_and_original_effects" if music_record else "timed_narration_original_music_and_effects", "voice": settings["voice"], "music_rights": music_record or "Original procedural composition", "effects_rights": "Original synthesis", "narration_intervals": intervals, "video_sha256": hashlib.sha256(destination.read_bytes()).hexdigest(), "probe": info}
    destination.with_suffix(".audio.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", type=Path, default=ROOT / "work/models/en_US-ljspeech-high.onnx")
    parser.add_argument("--music-file", type=Path, help="Use the reviewed licensed track already downloaded")
    parser.add_argument("--legacy-reproduction", action="store_true", help="Reproduce archived files only; not for new publication")
    args = parser.parse_args()
    quality_path = ROOT / "config/quality.json"
    if quality_path.exists() and json.loads(quality_path.read_text()).get("mode") == "quality_reset" and not args.legacy_reproduction:
        parser.error("The old Piper narrator is retired. Use story_audio.py for new production.")
    from piper import PiperVoice
    from render import validate
    settings = json.loads((ROOT / "config/audio.json").read_text())
    if hashlib.sha256(args.model.read_bytes()).hexdigest() != settings["voice"]["model_sha256"]:
        raise ValueError("Unreviewed voice model")
    if hashlib.sha256(Path(str(args.model) + ".json").read_bytes()).hexdigest() != settings["voice"]["config_sha256"]:
        raise ValueError("Unreviewed voice configuration")
    spec = validate(json.loads(args.manifest.read_text()))
    voice = PiperVoice.load(args.model)
    with tempfile.TemporaryDirectory(prefix="jarvis-audio-") as temp:
        result = add_audio(spec, args.video.resolve(), args.output.resolve(), voice, Path(temp), settings, args.music_file)
    print(f"Added narration, original music and effects: {args.output}; {result['video_sha256']}")


if __name__ == "__main__":
    main()
