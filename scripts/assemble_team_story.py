#!/usr/bin/env python3
"""Prepare real speech captions; assemble only complete, verified story inputs.

No publishing API is called. A rendered candidate still needs editorial review.
"""
import argparse
import hashlib
import json
import subprocess
import textwrap
from pathlib import Path


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(args):
    return subprocess.run(list(map(str, args)), capture_output=True, check=True)


def stamp(seconds):
    n = round(seconds * 100)
    return f'{n//360000}:{n//6000%60:02}:{n//100%60:02}.{n%100:02}'


def safe(text):
    return text.replace('{', '').replace('}', '').replace('\\', '')


def prepare_captions(audio, plan, target):
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 720
PlayResY: 1280
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Main,DejaVu Sans,45,&H00FFFFFF,&H00FFFFFF,&H00101010,&H70000000,-1,0,0,0,100,100,0,0,1,2.8,1,5,36,36,0,1
Style: Identity,DejaVu Sans,23,&H00FFFFFF,&H00FFFFFF,&H00101010,&H70000000,-1,0,0,0,100,100,0,0,1,1.8,0,7,30,30,30,1
Style: Notice,DejaVu Sans,20,&H00FFFFFF,&H00FFFFFF,&H00101010,&H70000000,0,0,0,0,100,100,0,0,3,3,0,2,35,35,35,1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""
    groups, current = [], []
    for word in audio['words']:
        if current and (len(current) >= 3 or
                        len(' '.join(w['text'] for w in current+[word])) > 25 or
                        current[-1]['speaker'] != word['speaker']):
            groups.append(current)
            current = []
        current.append(word)
        if word['text'].endswith(('.', ',', ':', '?', '!')):
            groups.append(current)
            current = []
    if current:
        groups.append(current)
    assert [w['text'] for g in groups for w in g] == [w['text'] for w in audio['words']]
    rows, cues = [], []
    for i, group in enumerate(groups):
        start = max(0, group[0]['start']-.025)
        end = min(audio['speech_assembly_seconds'], group[-1]['end']+.18)
        if i+1 < len(groups):
            end = min(end, groups[i+1][0]['start']-.025)
        middle = (group[0]['start']+group[-1]['end'])/2
        if 7.36 <= middle < 14.16:
            y = 1010
        elif middle < 2.9 or 14.16 <= middle < 17.45:
            y = 235
        elif middle >= 18.3:
            y = 175
        else:
            y = 1050
        pieces = []
        for word in group:
            t = safe(word['text'])
            if t.lower().strip('.,:!?') in {'plan', 'ownership', 'marker'}:
                t = r'{\c&H00D4FF&}'+t+r'{\c&HFFFFFF&}'
            pieces.append(t)
        text = rf'{{\an5\pos(360,{y})\fad(25,45)}}'+' '.join(pieces)
        rows.append(f'Dialogue: 2,{stamp(start)},{stamp(end)},Main,,0,0,0,,{text}')
        cues.append({'start':start, 'end':end, 'text':' '.join(w['text'] for w in group),
                     'speaker':group[0]['speaker'], 'position':[360,y]})
    for start, end in [(0,7.36),(14.16,plan['expected_picture_duration_seconds'])]:
        rows.append(f'Dialogue: 1,{stamp(start)},{stamp(end)},Identity,,0,0,0,,Illustration')
    rows.append('Dialogue: 1,0:00:07.36,0:00:14.16,Identity,,0,0,0,,Jocko Willink | 2019 interview')
    notice = plan['captions_and_context']['required_notice']
    lines = textwrap.wrap(notice, width=60)
    assert ' '.join(lines).split() == notice.split()
    text = r'{\an2\pos(360,1240)}'+r'\N'.join(safe(t) for t in lines)
    rows.append(f'Dialogue: 1,0:00:07.36,0:00:14.16,Notice,,0,0,0,,{text}')
    target.write_text(header+'\n'.join(rows)+'\n')
    return cues


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--render-root', required=True, type=Path)
    parser.add_argument('--picture-input', required=True, type=Path)
    parser.add_argument('--audio', required=True, type=Path)
    parser.add_argument('--work', required=True, type=Path)
    parser.add_argument('--output', type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--assemble', action='store_true')
    mode.add_argument('--historical-preflight', action='store_true')
    args = parser.parse_args()
    project = Path(__file__).resolve().parents[1]
    asset = project/'assets/stories/team-ownership'
    plan = json.loads((asset/'finishing-plan.json').read_text())
    audio = json.loads((asset/'audio-preflight.json').read_text())
    manifest = json.loads((args.render_root/'render-manifest.json').read_text())
    if manifest['source_sha256'] != plan['frozen_scene_sha256']:
        raise ValueError('Render cache is from a different scene revision.')
    if digest(args.picture_input) != plan['historical_picture']['prepared_picture_sha256']:
        raise ValueError('Historical picture differs from its inspected input.')
    if digest(args.audio) != plan['audio']['encoded_container_sha256']:
        raise ValueError('Audio differs from the inspected complete soundtrack.')
    args.work.mkdir(parents=True, exist_ok=True)
    subtitle = (args.work/'speech-and-context.ass').resolve()
    cues = prepare_captions(audio, plan, subtitle)
    caption_record = {'status':'prepared_not_final_editorial_review', 'publishable':False,
                      'word_count':len(audio['words']), 'cue_count':len(cues),
                      'caption_sha256':digest(subtitle), 'all_spoken_words_preserved_once':True,
                      'speaker_boundaries_preserved':True, 'cues':cues}
    (args.work/'caption-record.json').write_text(json.dumps(caption_record,indent=2)+'\n')
    if not (args.assemble or args.historical_preflight):
        print(json.dumps({k:caption_record[k] for k in ['status','word_count','cue_count','publishable']}))
        return
    if args.output is None or args.output.exists():
        raise ValueError('Choose a new task-owned output file for this video operation.')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Task-owned filter paths only; no shell command interpolation is used.
    if any(c in str(subtitle) for c in "'[];,\n"):
        raise ValueError('Choose a simple task-owned subtitle path.')
    if args.historical_preflight:
        run(['ffmpeg','-v','error','-y','-i',args.picture_input,'-ss',str(177/24),
             '-t',str(163/24),'-i',args.audio,
             '-vf',f"setpts=PTS+{177/24}/TB,ass={subtitle},setpts=N/(24*TB)",
             '-map','0:v:0','-map','1:a:0','-r','24','-fps_mode','cfr',
             '-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k',
             '-ar','48000','-ac','2','-movflags','+faststart',args.output])
        run(['ffmpeg','-v','error','-i',args.output,'-f','null','-'])
        report = {'status':'historical_caption_preflight_only', 'publishable':False,
                  'finished_short':False,'output_sha256':digest(args.output)}
    else:
        # Never fall back to raw, missing, stale or placeholder picture.
        reviewed_denoiser = json.loads((project/'config/denoiser.json').read_text())
        pictures = {}
        for frame in manifest['frame_numbers']:
            src = args.render_root/'frames'/f'{frame:05d}.png'
            clean = args.render_root/'denoised'/src.name
            receipt = args.render_root/'denoised'/f'{frame:05d}.json'
            if not (src.exists() and clean.exists() and receipt.exists()):
                raise ValueError(f'Original frame {frame} is not ready for assembly.')
            r = json.loads(receipt.read_text())
            if (r['frozen_scene_sha256'] != plan['frozen_scene_sha256'] or
                r['source_png_sha256'] != digest(src) or r['output_png_sha256'] != digest(clean) or
                r['oidn_archive_sha256'] != reviewed_denoiser['archive_sha256'] or
                r['dimensions'] != [720,1280] or r['resized']):
                raise ValueError(f'Original frame {frame} lacks matching native evidence.')
            pictures[frame] = clean
        historical = args.work/'historical-picture-frames'
        historical.mkdir(exist_ok=True)
        run(['ffmpeg','-v','error','-y','-i',args.picture_input,'-fps_mode','passthrough',
             '-frames:v','163',historical/'%05d.png'])
        for frame in range(178,341):
            pictures[frame] = historical/f'{frame-177:05d}.png'
        if sorted(pictures) != list(range(1,507)):
            raise ValueError('The exact 506-frame picture is incomplete.')
        log = args.work/'assembly.log'
        with log.open('wb') as error_stream:
            process = subprocess.Popen(['ffmpeg','-v','error','-y','-f','image2pipe','-framerate','24',
                '-vcodec','png','-i','pipe:0','-i',str(args.audio),'-map','0:v:0','-map','1:a:0',
                '-vf',f'ass={subtitle}','-r','24','-fps_mode','cfr','-c:v','libx264','-crf','18',
                '-pix_fmt','yuv420p','-c:a','copy','-movflags','+faststart',str(args.output)],
                stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=error_stream)
            try:
                for frame in range(1,507):
                    process.stdin.write(pictures[frame].read_bytes())
            finally:
                process.stdin.close()
                code = process.wait()
        if code:
            raise RuntimeError('Assembly failed; inspect the task-owned assembly.log.')
        run(['ffmpeg','-v','error','-i',args.output,'-f','null','-'])
        essence = run(['ffmpeg','-v','error','-i',args.output,'-map','0:a:0','-c:a','copy','-f','adts','pipe:1']).stdout
        if hashlib.sha256(essence).hexdigest() != plan['audio']['aac_essence_adts_sha256']:
            raise ValueError('Final AAC essence differs from the inspected soundtrack.')
        report = {'status':'assembled_pending_actual_editorial_and_final_qa_review',
                  'publishable':False,'frames':506,'full_decode_passed':True,
                  'inspected_audio_essence_unchanged':True,'output_sha256':digest(args.output)}
    probe = json.loads(run(['ffprobe','-v','error','-show_streams','-show_format',
                            '-of','json',args.output]).stdout)
    video = next(s for s in probe['streams'] if s['codec_type']=='video')
    encoded_audio = next(s for s in probe['streams'] if s['codec_type']=='audio')
    expected = 163 if args.historical_preflight else 506
    if (int(video['nb_frames']) != expected or [video['width'],video['height']] != [720,1280] or
        video['r_frame_rate'] != '24/1' or video['avg_frame_rate'] != '24/1' or
        abs(float(video['duration'])-expected/24) > .0001 or
        encoded_audio['codec_name'] != 'aac' or
        encoded_audio['channels'] != 2 or int(encoded_audio['sample_rate']) != 48000):
        raise ValueError('Encoded output does not match the picture/audio requirements.')
    report['actual_frames'] = int(video['nb_frames'])
    report['actual_dimensions'] = [video['width'],video['height']]
    report['actual_container_seconds'] = float(probe['format']['duration'])
    (args.work/'video-operation-record.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
