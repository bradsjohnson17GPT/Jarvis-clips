"""Mix the original Apollo 13 explainer with its timed male narration.

Only the caption formatter is shared with the older story renderer. Sound cues
are generated for this adapter animation and do not reuse the lighthouse cues.
"""
import argparse
import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf


def run(args):
    return subprocess.run(args,check=True,capture_output=True,text=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--story',type=Path,required=True)
    p.add_argument('--picture',type=Path,required=True)
    p.add_argument('--narration',type=Path,required=True)
    p.add_argument('--music',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    root=Path(__file__).resolve().parents[3]
    story=json.loads(args.story.read_text())
    assert story['visual_source']['rights_verified'] is True
    timing=json.loads((args.narration/'narration-timing.json').read_text())
    voice=args.narration/'narration-paced.wav'
    assert hashlib.sha256(voice.read_bytes()).hexdigest()==timing['sha256']
    music=story['music']
    assert music['rights_verified'] and music['commercial_use']
    assert music['attribution'] in story['description']
    assert hashlib.sha256(args.music.read_bytes()).hexdigest()==music['sha256']
    cfg=json.loads((root/story['voice_config']).read_text())
    assert cfg['selected_voice']==timing['voice']=='am_michael'
    args.output.parent.mkdir(parents=True,exist_ok=True)
    work=args.output.parent/'mix'
    work.mkdir(exist_ok=True)
    duration=timing['duration_seconds']
    spec=importlib.util.spec_from_file_location('caption_formatter',root/'scripts/finish_story.py')
    f=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(f)
    ass=work/'captions.ass'
    groups=f.captions(timing['words'],ass)
    text=ass.read_text().replace('DejaVu Sans,61,','DejaVu Sans,67,')
    text=text.replace(r'\pos(510,1500)',r'\pos(540,1535)')
    ass.write_text(text)
    sr=48000
    fx=np.zeros((round(duration*sr),2),dtype=np.float32)
    # Quiet tactile clicks for joining the illustrative adapter. No fake archive
    # alarm, spacecraft radio, or celebrity speech is synthesized.
    for start,freq in [(16.62,420),(17.28,650)]:
        t=np.arange(round(.13*sr))/sr
        click=np.sin(2*np.pi*freq*t)*np.exp(-t*38)*np.minimum(t/.005,1)*.026
        index=round(start*sr)
        fx[index:index+len(click)]+=click[:,None]
    sf.write(work/'original-effects.wav',fx,sr,subtype='PCM_24')
    chain=cfg['speech_processing']['synthetic_narration']
    graph=(f'[0:a]{chain},aresample=48000,aformat=channel_layouts=stereo,apad,atrim=duration={duration},asplit=2[v][sc];'
           f'[1:a]aformat=sample_rates=48000:channel_layouts=stereo,volume=0.05,afade=t=in:d=0.7,afade=t=out:st={duration-1.3}:d=1.3[m];'
           '[m][sc]sidechaincompress=threshold=0.024:ratio=9:attack=12:release=250[duck];'
           f'[v][duck][2:a]amix=inputs=3:normalize=0,atrim=duration={duration}[mix]')
    run(['ffmpeg','-v','error','-y','-i',str(voice),'-ss',str(story['music_start']),'-t',str(duration),'-i',str(args.music),'-i',str(work/'original-effects.wav'),'-filter_complex',graph,'-map','[mix]','-c:a','pcm_s24le',str(work/'pre-level.wav')])
    measured=run(['ffmpeg','-hide_banner','-i',str(work/'pre-level.wav'),'-af','loudnorm=I=-16:TP=-2:LRA=9:print_format=json','-f','null','-']).stderr
    q=json.loads(measured[measured.rfind('{'):measured.rfind('}')+1])
    norm=('loudnorm=I=-16:TP=-2:LRA=9:linear=true:'+f'measured_I={q["input_i"]}:measured_LRA={q["input_lra"]}:measured_TP={q["input_tp"]}:measured_thresh={q["input_thresh"]}:offset={q["target_offset"]}')
    run(['ffmpeg','-v','error','-y','-i',str(work/'pre-level.wav'),'-af',norm,'-ar','48000','-c:a','pcm_s24le',str(work/'mixed-master.wav')])
    run(['ffmpeg','-v','error','-y','-i',str(args.picture),'-i',str(work/'mixed-master.wav'),'-t',str(duration),'-vf','ass='+str(ass),'-map','0:v:0','-map','1:a:0','-c:v','libx264','-threads','2','-preset','fast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-ar','48000','-ac','2','-movflags','+faststart','-metadata','title='+story['title'],'-metadata','comment='+story['description'],str(args.output)])
    report={'id':story['id'],'status':'finished_development_preview_requires_actual_inspection','sha256':hashlib.sha256(args.output.read_bytes()).hexdigest(),'bytes':args.output.stat().st_size,'duration':duration,'voice':'am_michael','narration_sha256':timing['sha256'],'caption_groups':groups,'music':music,'music_excerpt_start':story['music_start'],'source_audio_used':False,'effects':'Two original quiet adapter-connection clicks at16.62/17.28s; no reused lighthouse cues.','publication':None}
    args.output.with_suffix('.assembly.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['caption_groups','music']}),flush=True)


if __name__=='__main__':
    main()
