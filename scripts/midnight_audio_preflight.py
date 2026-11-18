#!/usr/bin/env python3
"""Prepare Midnight Bell audio/captions only; never create a posting candidate."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(args):
    return subprocess.run(args, check=True, capture_output=True)


def normalized(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def stamp(seconds):
    ticks = round(seconds * 100)
    return f'{ticks // 360000}:{ticks // 6000 % 60:02}:{ticks // 100 % 60:02}.{ticks % 100:02}'


def prepare_captions(words, duration, target):
    groups, group = [], []
    for word in words:
        if group and (len(group) == 3 or len(' '.join(x['text'] for x in group + [word])) > 25):
            groups.append(group)
            group = []
        group.append(word)
        if word['text'].endswith(('.', '?', '!')):
            groups.append(group)
            group = []
    if group:
        groups.append(group)
    header = '''[Script Info]
ScriptType: v4.00+
PlayResX: 720
PlayResY: 1280
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Speech,DejaVu Sans,42,&H00FFFFFF,&H00FFFFFF,&H00151515,&H70000000,-1,0,0,0,100,100,0,0,1,3,1,5,45,45,0,1
Style: Label,DejaVu Sans,18,&H00FFFFFF,&H00FFFFFF,&H00151515,&H70000000,-1,0,0,0,100,100,0,0,1,1.5,0,7,0,0,0,1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
'''
    rows = [f'Dialogue: 0,0:00:00.00,{stamp(duration)},Label,,0,0,0,,{{\\an7\\pos(24,24)}}Original fiction']
    cues = []
    for index, group in enumerate(groups):
        start = max(0, group[0]['start'] - .02)
        end = min(duration, group[-1]['end'] + .16)
        if index + 1 < len(groups):
            end = min(end, groups[index + 1][0]['start'] - .02)
        assert 0 <= start < end <= duration
        text = ' '.join(w['text'] for w in group)
        safe = text.replace('{', '').replace('}', '').replace('\\', '')
        rows.append(f'Dialogue: 1,{stamp(start)},{stamp(end)},Speech,,0,0,0,,{{\\an5\\pos(360,1040)\\fad(30,45)}}{safe}')
        cues.append({'start': start, 'end': end, 'text': text, 'position': [360, 1040]})
    assert normalized(' '.join(c['text'] for c in cues)) == normalized(' '.join(w['text'] for w in words))
    target.write_text(header + '\n'.join(rows) + '\n')
    return cues


def effects(path, duration, impacts, seated, recovered):
    import numpy as np
    import soundfile as sf
    rate = 48000
    rng = np.random.default_rng(4851)
    track = np.zeros((round(duration * rate), 2), dtype=np.float64)
    events = []

    def add(at, signal, gain, pan, kind):
        assert 0 <= at < duration
        offset = round(at * rate)
        signal = signal[:len(track) - offset] * gain
        track[offset:offset + len(signal), 0] += signal * math.sqrt((1 - pan) / 2)
        track[offset:offset + len(signal), 1] += signal * math.sqrt((1 + pan) / 2)
        events.append({'at_seconds': at, 'kind': kind, 'gain': gain, 'pan': pan})

    def band_noise(length, low, high):
        n = round(length * rate)
        spectrum = np.fft.rfft(rng.normal(size=n))
        frequencies = np.fft.rfftfreq(n, 1 / rate)
        spectrum *= (frequencies >= low) & (frequencies <= high)
        wave = np.fft.irfft(spectrum, n)
        return wave / max(float(np.max(np.abs(wave))), 1e-9)

    t = np.arange(round(duration * rate)) / rate
    ambience = band_noise(duration, 90, 550) * np.minimum(t / 1.2, 1) * np.minimum((duration - t) / 1.5, 1)
    add(0, ambience, .003, 0, 'original_quiet_station_air')
    for at in impacts:
        t = np.arange(round(1.1 * rate)) / rate
        bell = sum(weight * np.sin(2 * np.pi * 587.33 * ratio * t + phase) * np.exp(-decay * t)
                   for ratio, weight, decay, phase in [(1, 1, 4.2, 0), (2.71, .32, 6, .2), (4.06, .17, 8.5, .4), (5.43, .08, 12, .1)])
        bell *= np.minimum(t / .004, 1)
        bell /= max(float(np.max(np.abs(bell))), 1e-9)
        add(at, bell, .035 if at == 14.0 else .09, .15, 'original_wrench_bell_impact')
    t = np.arange(round(.075 * rate)) / rate
    click = band_noise(.075, 1000, 6500) * np.exp(-t * 80) * np.minimum(t / .002, 1)
    add(seated, click, .055, -.1, 'original_insulated_plug_seating_click')
    for delay, frequency in [(0, 587.33), (.16, 880)]:
        t = np.arange(round(.38 * rate)) / rate
        note = np.sin(2 * np.pi * frequency * t) * np.exp(-t * 11) * np.minimum(t / .008, 1)
        add(recovered + delay, note, .035, .1, 'original_battery_recovery_tone')
    assert float(np.max(np.abs(track))) < .4
    sf.write(path, track, rate, subtype='PCM_24')
    return events


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--narration-dir', type=Path, required=True)
    parser.add_argument('--scene-plan', type=Path, required=True)
    parser.add_argument('--music', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--asr-cache', type=Path, required=True)
    args = parser.parse_args()
    project = Path(__file__).resolve().parents[1]
    story = json.loads((project / 'stories/midnight-bell.json').read_text())
    timing = json.loads((args.narration_dir / 'narration-timing.json').read_text())
    plan = json.loads(args.scene_plan.read_text())
    narrator = args.narration_dir / 'narration-paced.wav'
    assert digest(narrator) == timing['sha256'] == '22bc37f7aafbdebbafe2295fbccc9faca92820065522a5ff175250f72f0064dd'
    assert timing['voice'] == 'af_heart'
    assert normalized(story['narration']) == normalized(' '.join(w['text'] for w in timing['words']))
    assert digest(project / story['visual_source']['scene_source']) == story['visual_source']['source_sha256']
    music = story['music']
    assert music['rights_verified'] and music['commercial_use'] and music['attribution'] in story['description']
    assert digest(args.music) == music['sha256']
    duration = 678 / 24
    assert abs(timing['duration_seconds'] - duration) < .04
    music_start = float(music['start'])
    probe = json.loads(run(['ffprobe', '-v', 'error', '-show_format', '-of', 'json', str(args.music)]).stdout)
    assert float(probe['format']['duration']) >= music_start + duration
    args.output.mkdir(parents=True, exist_ok=False)
    output = args.output
    cue_path = output / 'speech-and-context.ass'
    cues = prepare_captions(timing['words'], duration, cue_path)
    fx = output / 'original-bell-and-charger-effects.wav'
    events = effects(fx, duration, plan['physical_bell_impact_seconds'], plan['critical_actions']['charger_seated'], plan['critical_actions']['battery_recovers'])
    graph = (f'[0:a]highpass=f=65,lowpass=f=11000,loudnorm=I=-18:TP=-3:LRA=7,aresample=48000,pan=stereo|c0=c0|c1=c0,apad,atrim=duration={duration},asplit=2[narr][side];'
             f'[1:a]atrim=duration={duration},asetpts=PTS-STARTPTS,highpass=f=60,loudnorm=I=-24:TP=-4:LRA=9,aresample=48000,volume=0.45,afade=t=in:d=1.2,afade=t=out:st={duration-1.6}:d=1.6[music];'
             '[music][side]sidechaincompress=threshold=0.025:ratio=9:attack=15:release=300[duck];'
             f'[narr][duck][2:a]amix=inputs=3:normalize=0:duration=longest,atrim=duration={duration},alimiter=limit=0.85[mix]')
    mix = output / 'mixed-master.wav'
    run(['ffmpeg', '-v', 'error', '-y', '-i', str(narrator), '-ss', str(music_start), '-i', str(args.music), '-i', str(fx), '-filter_complex', graph, '-map', '[mix]', '-t', str(duration), '-ar', '48000', '-ac', '2', '-c:a', 'pcm_s24le', str(mix)])
    measured = run(['ffmpeg', '-hide_banner', '-i', str(mix), '-af', 'loudnorm=I=-16:TP=-3:LRA=8:print_format=json', '-f', 'null', '-']).stderr.decode()
    values = json.JSONDecoder().raw_decode(measured[measured.rfind('{'):])[0]
    filters = (f'loudnorm=I=-16:TP=-3:LRA=8:measured_I={values["input_i"]}:measured_TP={values["input_tp"]}:measured_LRA={values["input_lra"]}:measured_thresh={values["input_thresh"]}:offset={values["target_offset"]}:linear=true,'
               f'aresample=48000,apad=whole_len={round(duration*48000)},atrim=end_sample={round(duration*48000)},asetpts=N/SR/TB')
    encoded = output / 'mixed-preflight.m4a'
    run(['ffmpeg', '-v', 'error', '-y', '-i', str(mix), '-af', filters, '-t', str(duration), '-ar', '48000', '-ac', '2', '-c:a', 'aac', '-b:a', '192k', str(encoded)])
    run(['ffmpeg', '-v', 'error', '-i', str(encoded), '-f', 'null', '-'])
    actual_probe = json.loads(run(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(encoded)]).stdout)
    stream = actual_probe['streams'][0]
    assert stream['codec_name'] == 'aac' and stream['channels'] == 2 and stream['sample_rate'] == '48000'
    assert abs(float(actual_probe['format']['duration']) - duration) < .04
    log = run(['ffmpeg', '-hide_banner', '-i', str(encoded), '-af', 'loudnorm=I=-16:TP=-3:LRA=8:print_format=json', '-f', 'null', '-']).stderr.decode()
    actual = json.JSONDecoder().raw_decode(log[log.rfind('{'):])[0]
    assert -17 <= float(actual['input_i']) <= -15 and float(actual['input_tp']) <= -2
    (output / 'encoded-loudness.log').write_text(log)
    import numpy as np
    from faster_whisper import WhisperModel
    raw = run(['ffmpeg', '-v', 'error', '-i', str(encoded), '-ac', '1', '-ar', '16000', '-f', 'f32le', 'pipe:1']).stdout
    model = WhisperModel('base.en', device='cpu', compute_type='int8', cpu_threads=2, download_root=str(args.asr_cache), local_files_only=True)
    segments, _ = model.transcribe(np.frombuffer(raw, dtype=np.float32), language='en', beam_size=5, word_timestamps=True, vad_filter=False)
    transcript = ' '.join(segment.text.strip() for segment in segments)
    (output / 'encoded-asr.json').write_text(json.dumps({'transcript': transcript, 'expected': story['narration'], 'exact_normalized_match': normalized(transcript) == normalized(story['narration'])}, indent=2)+'\n')
    assert normalized(transcript) == normalized(story['narration']), 'Encoded mix ASR differs; inspect the private transcript and remix before proceeding.'
    essence = run(['ffmpeg', '-v', 'error', '-i', str(encoded), '-map', '0:a:0', '-c:a', 'copy', '-f', 'adts', 'pipe:1']).stdout
    record = {'id': story['id'], 'prepared_at_utc': datetime.now(timezone.utc).isoformat(), 'status': 'audio_and_caption_preflight_not_finished_video', 'publishable': False, 'narration_sha256': timing['sha256'], 'narrator': timing['voice'], 'narration_regenerated': False, 'spoken_script_unchanged': True, 'duration_seconds': duration, 'narration_duration_seconds': timing['duration_seconds'], 'aac_sha256': digest(encoded), 'aac_essence_adts_sha256': hashlib.sha256(essence).hexdigest(), 'effects_sha256': digest(fx), 'master_sha256': digest(mix), 'audio_stream': {'codec': 'aac', 'channels': 2, 'sample_rate': 48000}, 'encoded_loudness': actual, 'encoded_full_decode_passed': True, 'encoded_asr_exact_normalized_match': True, 'caption_sha256': digest(cue_path), 'word_count': len(timing['words']), 'caption_cues': cues, 'caption_label': 'Original fiction', 'effects': events, 'music': {'title': music['title'], 'artist': music['artist'], 'sha256': music['sha256'], 'excerpt_start_seconds': music_start, 'license': music['license'], 'attribution': music['attribution'], 'changes': 'Excerpt trimmed, faded and sidechain-ducked beneath unchanged original narration and new original bell/charging effects.'}, 'continuous_video_watching_claimed': False, 'subjective_audio_listening_claimed': False, 'finished_movie_exists': False, 'limits': 'ASR, levels and timestamps are engineering checks. No subjective listening, actual finished-film pacing or final caption/visual synchronization is claimed.'}
    (output / 'audio-caption-record.json').write_text(json.dumps(record, indent=2)+'\n')
    print(json.dumps({k: record[k] for k in ['status', 'duration_seconds', 'word_count', 'aac_sha256', 'caption_sha256', 'encoded_asr_exact_normalized_match', 'publishable']}))


if __name__ == '__main__':
    main()
