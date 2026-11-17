#!/usr/bin/env python3
"""Mix inspected original story picture with recorded narration and reviewed music."""
import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path


def run(cmd):
    return subprocess.run(cmd, check=True, capture_output=True, text=True)


def ass_time(seconds):
    ticks = round(seconds * 100)
    return f'{ticks // 360000}:{ticks // 6000 % 60:02}:{ticks // 100 % 60:02}.{ticks % 100:02}'


def captions(words, target):
    header = '''[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Story,DejaVu Sans,61,&H0098D5FF,&H00FFFFFF,&H00120F0B,&H70000000,-1,0,0,0,100,100,0,0,1,3.4,1.6,5,100,160,0,1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
'''
    groups, current = [], []
    for word in words:
        if current and (len(current) == 3 or len(' '.join(w['text'] for w in current + [word])) > 25):
            groups.append(current)
            current = []
        current.append(word)
        if word['text'].endswith(('.', ':', '...', ',')):
            groups.append(current)
            current = []
    if current:
        groups.append(current)
    rows = []
    for index, group in enumerate(groups):
        start = max(0, group[0]['start'] - 0.03)
        end = group[-1]['end'] + 0.22
        if index + 1 < len(groups):
            end = min(end, groups[index + 1][0]['start'] - 0.03)
        text = r'{\an5\pos(510,1500)\fad(45,65)}'
        lead = round((group[0]['start'] - start) * 100)
        text += '{\\k' + str(lead) + '}'
        for j, word in enumerate(group):
            until = group[j + 1]['start'] if j + 1 < len(group) else end
            ticks = max(1, round((until - word['start']) * 100))
            safe = word['text'].replace('{', '').replace('}', '').replace('\\', '')
            text += '{\\k' + str(ticks) + '}' + safe + (' ' if j + 1 < len(group) else '')
        rows.append(f'Dialogue: 0,{ass_time(start)},{ass_time(end)},Story,,0,0,0,,{text}')
    target.write_text(header + '\n'.join(rows) + '\n')
    return [{'start': g[0]['start'], 'end': g[-1]['end'], 'text': ' '.join(w['text'] for w in g)} for g in groups]


def effects(path, duration):
    import numpy as np
    import soundfile as sf
    sr = 48000
    rng = np.random.default_rng(1126)
    track = np.zeros((round(duration * sr), 2), dtype=np.float32)
    def add(start, signal, gain, pan=0):
        i = round(start * sr)
        signal = signal[:max(0, len(track) - i)] * gain
        track[i:i + len(signal), 0] += signal * math.sqrt((1 - pan) / 2)
        track[i:i + len(signal), 1] += signal * math.sqrt((1 + pan) / 2)
    def noise(length, low, high):
        n = round(length * sr)
        x = rng.normal(size=n)
        spectrum = np.fft.rfft(x)
        frequencies = np.fft.rfftfreq(n, 1 / sr)
        spectrum *= ((frequencies >= low) & (frequencies <= high))
        x = np.fft.irfft(spectrum, n=n)
        return x / max(np.max(np.abs(x)), 1e-9)
    wind = noise(duration, 100, 1100)
    t = np.arange(len(wind)) / sr
    add(0, wind * (0.6 + 0.4 * np.sin(t * 0.4)) * np.minimum(t / 1.2, 1) * np.minimum((duration - t) / 1.5, 1), 0.012)
    for start in [8.5, 10.2]:
        x = noise(0.48, 900, 6500)
        x *= np.sin(np.linspace(0, np.pi, len(x))) ** 2
        add(start, x, 0.045, -0.25)
    for start in [14.05, 14.26, 14.50, 14.70]:
        t = np.arange(round(0.1 * sr)) / sr
        x = (np.sin(2 * np.pi * 340 * t) + 0.3 * np.sin(2 * np.pi * 920 * t)) * np.exp(-t * 55) * np.minimum(t / 0.004, 1)
        add(start, x, 0.045, 0.1)
    t = np.arange(round(2.2 * sr)) / sr
    whoosh = noise(2.2, 80, 1500) * np.sin(np.pi * t / 2.2) ** 2
    add(16.25, whoosh, 0.055)
    for start, frequency in [(20.55, 660), (21.0, 990)]:
        t = np.arange(round(1.8 * sr)) / sr
        chime = (np.sin(2 * np.pi * frequency * t) + 0.22 * np.sin(2 * np.pi * frequency * 2.01 * t)) * np.exp(-t * 2.8) * np.minimum(t / 0.012, 1)
        add(start, chime, 0.065, 0.25)
    sf.write(path, track, sr, subtype='PCM_24')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('manifest', type=Path)
    p.add_argument('--picture', type=Path, required=True)
    p.add_argument('--narration-dir', type=Path, required=True)
    p.add_argument('--music', type=Path, required=True)
    p.add_argument('--music-start', type=float, help='Override the reviewed manifest excerpt start.')
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    story = json.loads(args.manifest.read_text())
    timing = json.loads((args.narration_dir / 'narration-timing.json').read_text())
    narration = args.narration_dir / 'narration-paced.wav'
    if hashlib.sha256(narration.read_bytes()).hexdigest() != timing['sha256']:
        raise SystemExit('Narration does not match the inspected timing record.')
    music = story['music']
    music_start = args.music_start if args.music_start is not None else float(music.get('start', 0))
    if not music['rights_verified'] or not music['commercial_use'] or not music['attribution'] in story['description']:
        raise SystemExit('The music needs reviewed rights and its required description credit.')
    if hashlib.sha256(args.music.read_bytes()).hexdigest() != music['sha256']:
        raise SystemExit('The music bytes do not match the reviewed recording.')
    probe = json.loads(run(['ffprobe', '-v', 'error', '-show_format', '-show_streams', '-of', 'json', str(args.picture)]).stdout)
    video = next(x for x in probe['streams'] if x['codec_type'] == 'video')
    duration = float(probe['format']['duration'])
    if abs(video['width'] / video['height'] - 9 / 16) > 0.005 or abs(duration - timing['duration_seconds']) > 0.6:
        raise SystemExit('Picture framing/duration does not match the portrait story edit.')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temp = args.output.parent / (args.output.stem + '-work')
    temp.mkdir(exist_ok=True)
    subtitle = temp / 'captions.ass'
    caption_groups = captions(timing['words'], subtitle)
    fx = temp / 'original-effects.wav'
    effects(fx, duration)
    mix = temp / 'mix.wav'
    graph = (
        f'[0:a]highpass=f=65,lowpass=f=10000,loudnorm=I=-18:TP=-3:LRA=7,aresample=48000,pan=stereo|c0=c0|c1=c0,apad,atrim=duration={duration},asplit=2[narr][side];'
        f'[1:a]atrim=duration={duration},asetpts=PTS-STARTPTS,highpass=f=60,loudnorm=I=-25:TP=-4:LRA=9,aresample=48000,afade=t=in:d=0.8,afade=t=out:st={max(0,duration-1.6)}:d=1.6[music];'
        '[music][side]sidechaincompress=threshold=0.025:ratio=6:attack=15:release=300[duck];'
        '[narr][duck][2:a]amix=inputs=3:normalize=0:duration=longest,alimiter=limit=0.85[mix]'
    )
    run(['ffmpeg', '-v', 'error', '-y', '-i', str(narration), '-ss', str(music_start), '-i', str(args.music), '-i', str(fx), '-filter_complex', graph, '-map', '[mix]', '-t', str(duration), '-c:a', 'pcm_s24le', str(mix)])
    measured = run(['ffmpeg', '-hide_banner', '-i', str(mix), '-af', 'loudnorm=I=-16:TP=-2:LRA=8:print_format=json', '-f', 'null', '-']).stderr
    values = json.JSONDecoder().raw_decode(measured[measured.rfind('{'):])[0]
    loudness = f'loudnorm=I=-16:TP=-2:LRA=8:measured_I={values["input_i"]}:measured_TP={values["input_tp"]}:measured_LRA={values["input_lra"]}:measured_thresh={values["input_thresh"]}:offset={values["target_offset"]}:linear=true'
    run(['ffmpeg', '-v', 'error', '-y', '-i', str(args.picture), '-i', str(mix), '-vf', f'ass={subtitle}', '-af', loudness, '-map', '0:v:0', '-map', '1:a:0', '-t', str(duration), '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-ac', '2', '-metadata', 'title=' + story['title'], '-metadata', 'comment=' + story['description'], '-movflags', '+faststart', str(args.output)])
    encoded_probe = json.loads(run(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_type,codec_name,width,height,sample_rate,channels,r_frame_rate,nb_frames:format=duration', '-of', 'json', str(args.output)]).stdout)
    audio_stream = next((stream for stream in encoded_probe['streams'] if stream['codec_type'] == 'audio'), {})
    if audio_stream.get('codec_name') != 'aac' or audio_stream.get('channels') != 2 or audio_stream.get('sample_rate') != '48000':
        raise SystemExit('Actual encoded output does not contain the required stereo 48 kHz AAC stream.')
    # Complete decode, then remeasure the encoded file rather than only the master.
    run(['ffmpeg', '-v', 'error', '-i', str(args.output), '-f', 'null', '-'])
    encoded = run(['ffmpeg', '-hide_banner', '-i', str(args.output), '-af', 'loudnorm=I=-16:TP=-2:LRA=8:print_format=json', '-f', 'null', '-']).stderr
    actual = json.JSONDecoder().raw_decode(encoded[encoded.rfind('{'):])[0]
    if float(actual['input_tp']) > -1.0:
        raise SystemExit('Encoded true peak exceeds the -1 dBTP guard; inspect and remix.')
    report = {'id': story['id'], 'status': 'rendered_preview_not_published', 'output_sha256': hashlib.sha256(args.output.read_bytes()).hexdigest(), 'bytes': args.output.stat().st_size, 'duration': duration, 'width': video['width'], 'height': video['height'], 'encoded_streams': encoded_probe, 'encoded_loudness': actual, 'narration_sha256': timing['sha256'], 'music': {'title': music['title'], 'artist': music['artist'], 'sha256': music['sha256'], 'excerpt_start': music_start, 'duration': duration, 'license': music['license'], 'attribution': music['attribution']}, 'caption_groups': caption_groups, 'audio_version': 'kokoro-narrative-original-effects-licensed-score-v1', 'qa': {'complete_decode': True, 'caption_timing_basis': 'ASR of actual narration master, edited with the same pauses', 'editorial_review': 'Required separately; technical checks do not prove compelling storytelling or natural delivery.'}}
    args.output.with_suffix('.qa.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ['caption_groups', 'encoded_loudness', 'qa']}))


if __name__ == '__main__':
    main()
