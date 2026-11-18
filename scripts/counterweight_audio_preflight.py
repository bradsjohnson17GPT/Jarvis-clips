#!/usr/bin/env python3
"""Build Counterweight Gate's audio-only preflight from its existing clean take.

The action plan supplies intended sound cues; it is not proof of animated sync.
No picture, voice generation, upload draft, schedule or publication is created.
"""
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
    return re.findall(r'[a-z0-9]+', text.lower())


def measure(path):
    log = run(['ffmpeg', '-hide_banner', '-i', str(path), '-af',
               'loudnorm=I=-16:TP=-3:LRA=8:print_format=json', '-f', 'null', '-']).stderr.decode()
    return json.JSONDecoder().raw_decode(log[log.rfind('{'):])[0], log


def make_effects(path, duration, actions):
    import numpy as np
    import soundfile as sf
    rate = 48000
    rng = np.random.default_rng(658217)
    track = np.zeros((round(duration * rate), 2), dtype=np.float64)
    events = []

    def noise(seconds, low, high):
        length = round(seconds * rate)
        spectrum = np.fft.rfft(rng.normal(size=length))
        hz = np.fft.rfftfreq(length, 1 / rate)
        spectrum *= (hz >= low) & (hz <= high)
        signal = np.fft.irfft(spectrum, length)
        return signal / max(float(np.max(np.abs(signal))), 1e-9)

    def add(at, signal, gain, pan, kind):
        assert 0 <= at < duration
        offset = round(at * rate)
        signal = signal[:len(track) - offset] * gain
        track[offset:offset + len(signal), 0] += signal * math.sqrt((1 - pan) / 2)
        track[offset:offset + len(signal), 1] += signal * math.sqrt((1 + pan) / 2)
        events.append({'at_seconds': at, 'kind': kind, 'gain': gain, 'pan': pan,
                       'sync_status': 'planned_action_cue_not_verified_against_animation'})

    for at in [actions['first_gate_stop'], actions['second_gate_stop']]:
        t = np.arange(round(.32 * rate)) / rate
        timber = (np.sin(2 * np.pi * 98 * t) * np.exp(-18 * t) +
                  .40 * np.sin(2 * np.pi * 237 * t) * np.exp(-25 * t) +
                  .22 * noise(.32, 120, 1800) * np.exp(-32 * t))
        timber *= np.minimum(t / .003, 1)
        add(at, timber, .075, -.10, 'original_soft_timber_gate_stop')
    for at in actions['stair_foot_plants']:
        t = np.arange(round(.13 * rate)) / rate
        step = (noise(.13, 80, 1300) + .35 * np.sin(2 * np.pi * 125 * t))
        step *= np.exp(-35 * t) * np.minimum(t / .004, 1)
        add(at, step, .022, .15, 'original_boot_on_stone_tread')
    for index, at in enumerate(actions['stone_deposits']):
        t = np.arange(round(.19 * rate)) / rate
        stone = (.45 * noise(.19, 600, 6500) * np.exp(-45 * t) +
                 np.sin(2 * np.pi * (820 + 75 * index) * t) * np.exp(-38 * t) +
                 .25 * np.sin(2 * np.pi * 1710 * t) * np.exp(-55 * t))
        stone *= np.minimum(t / .002, 1)
        add(at, stone, .043, .22, 'original_stone_into_counterweight_basket')
    start, end = actions['counterweight_and_gate_travel']
    t = np.arange(round((end - start) * rate)) / rate
    creak = noise(end - start, 230, 1050) * (.30 + .70 * np.sin(2 * np.pi * 6 * t) ** 2)
    creak *= np.minimum(t / .10, 1) * np.minimum((end - start - t) / .13, 1)
    add(start, creak, .027, .15, 'original_hemp_pulley_travel')
    t = np.arange(round(.15 * rate)) / rate
    stop = (np.sin(2 * np.pi * 154 * t) + .15 * noise(.15, 300, 2500)) * np.exp(-35 * t)
    stop *= np.minimum(t / .003, 1)
    add(actions['raised_gate_stop'], stop, .035, -.10, 'original_raised_gate_stop')
    start, end = actions['cart_roll']
    t = np.arange(round((end - start) * rate)) / rate
    roll = noise(end - start, 80, 750) * (.45 + .55 * np.sin(2 * np.pi * 4.1 * t) ** 8)
    roll *= np.minimum(t / .18, 1) * np.minimum((end - start - t) / .22, 1)
    add(start, roll, .025, -.05, 'original_rubber_cart_wheels_on_paving')
    assert np.isfinite(track).all() and float(np.max(np.abs(track))) < .25
    sf.write(path, track, rate, subtype='PCM_24')
    return events


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--music', type=Path, required=True)
    parser.add_argument('--asr-cache', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    story = json.loads((root / 'stories/counterweight-gate.json').read_text())
    plan_path = root / 'assets/stories/counterweight-gate/action-plan.json'
    plan = json.loads(plan_path.read_text())
    captions = json.loads((root / 'assets/stories/counterweight-gate/caption-plan.json').read_text())
    voice_config = json.loads((root / 'config/motivational-voice.json').read_text())
    narration_dir = root / story['private_existing_narration']
    timing = json.loads((narration_dir / 'narration-timing.json').read_text())
    clean_record = json.loads((narration_dir / 'clean-speech-record.json').read_text())
    narrator = narration_dir / 'narration-clean.wav'
    assert digest(narrator) == story['clean_narration_sha256'] == clean_record['clean_sha256'] == plan['timing_basis']['clean_narration_sha256']
    assert digest(narration_dir / 'narration-paced.wav') == timing['sha256'] == clean_record['raw_paced_sha256']
    assert digest(narration_dir / 'narration-timing.json') == plan['timing_basis']['word_timing_source_sha256']
    assert normalized(story['narration']) == normalized(' '.join(w['text'] for w in timing['words']))
    assert timing['voice'] == voice_config['selected_voice'] == 'am_michael'
    assert digest(root / captions['ass_file']) == captions['ass_sha256']
    assert normalized(' '.join(c['text'] for c in captions['cues'])) == normalized(story['narration'])
    music = story['music']
    assert music['rights_verified'] and music['commercial_use'] and music['attribution'] in story['description']
    assert music['page'] in story['description'] and music['license'] in story['description']
    assert digest(args.music) == music['sha256']
    picture = plan['picture_target']
    duration, samples = picture['duration_seconds'], picture['exact_audio_samples']
    assert picture['frames'] == 578 and picture['fps'] == 24 and samples == 1156000
    assert abs(duration - timing['duration_seconds']) < .04
    music_start = float(music['start'])
    music_probe = json.loads(run(['ffprobe', '-v', 'error', '-show_format', '-of', 'json', str(args.music)]).stdout)
    assert float(music_probe['format']['duration']) >= music_start + duration
    args.output.mkdir(parents=True, exist_ok=False)
    fx = args.output / 'original-gate-stone-cart-effects.wav'
    events = make_effects(fx, duration, plan['actions'])
    processing = voice_config['speech_processing']
    gain = processing['music_base_gain']
    assert 0 < gain <= .05
    graph = (f'[0:a]aresample=48000,pan=stereo|c0=c0|c1=c0,apad=whole_len={samples},atrim=end_sample={samples},asplit=2[narr][side];'
             f'[1:a]atrim=duration={duration},asetpts=PTS-STARTPTS,aresample=48000,highpass=f=60,volume={gain},afade=t=in:d=1.0,afade=t=out:st={duration - 1.5}:d=1.5[music];'
             f'[music][side]sidechaincompress=threshold=0.025:ratio={processing["sidechain_ratio"]}:attack=15:release=300,asplit=2[duck_mix][duck_stem];'
             f'[narr][duck_mix][2:a]amix=inputs=3:normalize=0:duration=longest,atrim=end_sample={samples},alimiter=limit=0.85[mix]')
    mix = args.output / 'mixed-master.wav'
    ducked = args.output / 'ducked-music.wav'
    run(['ffmpeg', '-v', 'error', '-y', '-i', str(narrator), '-ss', str(music_start), '-i', str(args.music), '-i', str(fx),
         '-filter_complex', graph, '-map', '[mix]', '-t', str(duration), '-ar', '48000', '-ac', '2', '-c:a', 'pcm_s24le', str(mix),
         '-map', '[duck_stem]', '-t', str(duration), '-ar', '48000', '-ac', '2', '-c:a', 'pcm_s16le', str(ducked)])
    measured, _ = measure(mix)
    filters = (f'loudnorm=I=-16:TP=-3:LRA=8:measured_I={measured["input_i"]}:measured_TP={measured["input_tp"]}:measured_LRA={measured["input_lra"]}:measured_thresh={measured["input_thresh"]}:offset={measured["target_offset"]}:linear=true,'
               f'aresample=48000,apad=whole_len={samples},atrim=end_sample={samples},asetpts=N/SR/TB')
    encoded = args.output / 'mixed-preflight.m4a'
    run(['ffmpeg', '-v', 'error', '-y', '-i', str(mix), '-af', filters, '-ar', '48000', '-ac', '2', '-c:a', 'aac', '-b:a', '192k', str(encoded)])
    run(['ffmpeg', '-v', 'error', '-xerror', '-i', str(encoded), '-f', 'null', '-'])
    probe = json.loads(run(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(encoded)]).stdout)
    stream = probe['streams'][0]
    assert stream['codec_name'] == 'aac' and stream['channels'] == 2 and stream['sample_rate'] == '48000'
    assert abs(float(stream['duration']) - duration) < .005
    actual, log = measure(encoded)
    (args.output / 'encoded-loudness.log').write_text(log)
    assert -17 <= float(actual['input_i']) <= -15 and float(actual['input_tp']) <= -2
    import numpy as np
    from faster_whisper import WhisperModel
    raw = run(['ffmpeg', '-v', 'error', '-i', str(encoded), '-ac', '1', '-ar', '16000', '-f', 'f32le', 'pipe:1']).stdout
    model = WhisperModel('base.en', device='cpu', compute_type='int8', cpu_threads=2, download_root=str(args.asr_cache), local_files_only=True)
    segments, _ = model.transcribe(np.frombuffer(raw, dtype=np.float32), language='en', beam_size=5, word_timestamps=True, vad_filter=False)
    transcript = ' '.join(s.text.strip() for s in segments)
    asr = {'transcript': transcript, 'expected': story['narration'], 'exact_normalized_match': normalized(transcript) == normalized(story['narration'])}
    (args.output / 'encoded-asr.json').write_text(json.dumps(asr, indent=2) + '\n')
    assert asr['exact_normalized_match'], 'Mixed preflight ASR differs; inspect retained evidence before any use.'
    def mono(path):
        b = run(['ffmpeg', '-v', 'error', '-i', str(path), '-ac', '1', '-ar', '48000', '-f', 'f32le', 'pipe:1']).stdout
        return np.frombuffer(b, dtype=np.float32).astype(np.float64)
    speech, music_stem = mono(narrator), mono(ducked)
    length = min(len(speech), len(music_stem)) // 960 * 960
    srms = np.sqrt(np.mean(speech[:length].reshape(-1, 960) ** 2, axis=1))
    mrms = np.sqrt(np.mean(music_stem[:length].reshape(-1, 960) ** 2, axis=1))
    active = srms > 10 ** (-36 / 20)
    assert np.count_nonzero(active) > 100
    difference = 20 * np.log10(np.maximum(mrms[active], 1e-12) / srms[active])
    essence = run(['ffmpeg', '-v', 'error', '-i', str(encoded), '-map', '0:a:0', '-c:a', 'copy', '-f', 'adts', 'pipe:1']).stdout
    record = {'id': story['id'], 'prepared_at_utc': datetime.now(timezone.utc).isoformat(),
              'status': 'encoded_audio_preflight_only_animation_sync_and_subjective_review_pending', 'script': str(Path(__file__).relative_to(root)), 'script_sha256': digest(Path(__file__)),
              'action_plan_sha256': digest(plan_path), 'narration_sha256': digest(narrator), 'narrator': timing['voice'], 'narration_regenerated': False,
              'spoken_script_unchanged': True, 'spoken_words': len(timing['words']), 'duration_seconds': duration,
              'actual_aac_stream_duration_seconds': float(stream['duration']), 'exact_target_pcm_samples': samples,
              'aac_sha256': digest(encoded), 'aac_essence_adts_sha256': hashlib.sha256(essence).hexdigest(),
              'mixed_master_sha256': digest(mix), 'effects_sha256': digest(fx), 'ducked_music_stem_sha256': digest(ducked),
              'audio_stream': {'codec': 'aac', 'channels': 2, 'sample_rate': 48000}, 'encoded_loudness': actual,
              'encoded_full_decode_passed': True, 'encoded_asr_exact_normalized_match': True, 'caption_sha256': captions['ass_sha256'], 'caption_phrases': 18,
              'music': {'title': music['title'], 'artist': music['artist'], 'sha256': music['sha256'], 'excerpt_start_seconds': music_start,
                        'source': music['page'], 'license': music['license'], 'attribution': music['attribution'],
                        'base_gain': gain, 'sidechain_ratio': processing['sidechain_ratio'],
                        'changes': 'Different excerpt trimmed/faded and strongly sidechain-ducked beneath unchanged cleaned original stock male narration and new gate/stone/cart effects.'},
              'music_stem_comparison': {'method': '20ms RMS windows with source speech above-36dBFS; relative to unchanged clean narration, before shared final loudness gain',
                                        'median_music_relative_to_speech_db': float(np.median(difference)), 'p95_music_relative_to_speech_db': float(np.percentile(difference, 95)),
                                        'subjective_audibility_or_masking_established': False},
              'effects': events, 'external_effect_samples': [], 'source_audio_retained': False,
              'actual_animation_sync_verified': False, 'subjective_audio_listening_claimed': False,
              'continuous_video_watching_claimed': False, 'finished_movie_exists': False, 'publisher_draft_created': False, 'publishable': False,
              'limits': 'ASR, decode, levels and stem comparisons are technical checks. No subjective listening, continuous motion or actual finished-film sound/caption synchronization is claimed. Reuse this soundtrack only if the later actual animated events match the cue plan; otherwise revise with retained evidence.'}
    (args.output / 'audio-preflight-record.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps({k: record[k] for k in ['status', 'duration_seconds', 'aac_sha256', 'encoded_loudness', 'encoded_asr_exact_normalized_match', 'publishable']}))


if __name__ == '__main__':
    main()
