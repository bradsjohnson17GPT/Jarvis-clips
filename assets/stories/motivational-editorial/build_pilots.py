import json,hashlib,subprocess,importlib.util,math
from pathlib import Path
import numpy as np
import soundfile as sf
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).parent;R=Path('/workspace/work/jarvis-clips');SR=48000
def run(a):return subprocess.run(a,check=True,capture_output=True,text=True).stdout
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert h(P/'goggins.mp4')=='cc90382989bcc545730910dff4819da3cc1569f8f551739c8f812c7436eccc79'
assert h(P/'jocko.mp4')=='7fdae3fbaa989b158cb76367fbb447de970bda4a191dbb43a3dcc278adb7ce4e'
review=json.loads((P/'audio-event-review.json').read_text())
j=next(x for x in review['clips'] if x['name']=='jocko_quote');assert j['music_max']<.02 and j['speech_mean']>.9
spec=importlib.util.spec_from_file_location('finish',R/'scripts/finish_story.py');f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';bold='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
def picture(src,start,duration,crop,out,extra=''):
    vf=crop+',scale=720:1280:flags=lanczos,setsar=1,fps=30'
    if extra:vf+=','+extra
    run(['ffmpeg','-v','error','-y','-ss',str(start),'-i',str(src),'-t',str(duration),'-an','-vf',vf,'-c:v','libx264','-threads','2','-preset','fast','-crf','18','-pix_fmt','yuv420p',str(out)])
def concat(parts,out):
    lst=out.with_suffix('.txt');lst.write_text(''.join("file '"+str(p)+"'\n" for p in parts))
    run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',str(lst),'-c','copy',str(out)])
def speech(src,out,ss=None,dur=None):
    a=['ffmpeg','-v','error','-y']
    if ss is not None:a+=['-ss',str(ss)]
    a+=['-i',str(src)]
    if dur is not None:a+=['-t',str(dur)]
    a+=['-af','highpass=f=75,loudnorm=I=-18:LRA=7:TP=-3','-ar',str(SR),'-ac','1','-c:a','pcm_s24le',str(out)];run(a)
def note_picture(duration,out):
    # Original continuous diagram: an ink line is written, the controllable action
    # is circled, and a visible check lands. It illustrates the spoken example.
    folder=P/'note-frames';folder.mkdir(exist_ok=True);fps=15;count=math.ceil(duration*fps)
    ft=ImageFont.truetype(font,28);fb=ImageFont.truetype(bold,31);small=ImageFont.truetype(font,19)
    for i in range(count):
        t=i/fps;im=Image.new('RGB',(720,1280),'#12232b');d=ImageDraw.Draw(im)
        d.rounded_rectangle((75,225,656,1060),radius=20,fill='#080f16')
        d.rounded_rectangle((62,210,642,1045),radius=18,fill='#f6f1e5')
        d.text((100,265),'THE NEXT STEP',font=fb,fill='#16343d')
        d.line((100,320,605,320),fill='#d0c5af',width=2)
        lines=[('WHAT HAPPENED',360,0.4,fb,'#63747a'),('Missed a deadline',412,1.2,ft,'#1c343a'),('WHAT I CONTROL',555,3.1,fb,'#63747a'),('Send a realistic plan',612,4.3,ft,'#1c343a'),('ONE ACTION TODAY',820,6.3,fb,'#63747a'),('Send one useful update',875,7.1,ft,'#1c343a')]
        for text,y,start,fo,color in lines:
            n=min(len(text),max(0,int((t-start)*36)));d.text((100,y),text[:n],font=fo,fill=color)
        if t>4.8:
            end=min(360,int((t-4.8)*300));d.arc((82,590,609,666),start=0,end=end,fill='#d99b25',width=6)
        if t>7.8:
            p=min(1,(t-7.8)/.5);a=(100,960);b=(121,983);c=(171,925)
            if p<.35:point=(a[0]+(b[0]-a[0])*p/.35,a[1]+(b[1]-a[1])*p/.35);d.line((a,point),fill='#2a8776',width=8)
            else:d.line((a,b),fill='#2a8776',width=8);q=(p-.35)/.65;d.line((b,(b[0]+(c[0]-b[0])*q,b[1]+(c[1]-b[1])*q)),fill='#2a8776',width=8)
        im.save(folder/f'{i:04d}.png')
    run(['ffmpeg','-v','error','-y','-framerate',str(fps),'-i',str(folder/'%04d.png'),'-t',str(duration),'-vf','fps=30,setsar=1','-an','-c:v','libx264','-threads','2','-crf','18','-preset','fast','-pix_fmt','yuv420p',str(out)])
def mix_and_caption(name,pic,voice,words,duration,music,mstart,label,commentary_window):
    cfg=json.loads((R/'config/licensed-music.json').read_text())['tracks'][music];mf=Path('/workspace/work/nextday-root-2026-11-17')/(music.lower()+'.mp3');assert h(mf)==cfg['sha256']
    outdir=P/name;outdir.mkdir(exist_ok=True);ass=outdir/'captions.ass';groups=f.captions(words,ass);s=ass.read_text().replace('DejaVu Sans,61,','DejaVu Sans,70,')
    s+=f'Dialogue: 2,0:00:00.00,{f.ass_time(duration)},Story,,0,0,0,,{{\\an7\\pos(65,120)\\fs28\\c&HFFFFFF&}}{label}\n'
    lo,hi=commentary_window;s+=f'Dialogue: 2,{f.ass_time(lo)},{f.ass_time(hi)},Story,,0,0,0,,{{\\an7\\pos(65,205)\\fs26\\c&HFFFFFF&}}ORIGINAL COMMENTARY\n'
    footer='The appearance of U.S. Department of War (DoW)\\Nvisual information does not imply or constitute\\NDoW endorsement.'
    s+=f'Dialogue: 2,0:00:00.00,{f.ass_time(duration)},Story,,0,0,0,,{{\\an2\\pos(510,1810)\\fs26\\c&HFFFFFF&\\bord2}}{footer}\n';ass.write_text(s)
    impacts=np.zeros((round(duration*SR),2),dtype=np.float32)
    at=lo if lo>.2 else 4.0;n=round(.22*SR);t=np.arange(n)/SR;x=np.sin(2*np.pi*(85*t-35*t*t))*np.sin(np.pi*t/.22)**2*.017;ix=round(at*SR);impacts[ix:ix+n]+=x[:,None];sf.write(outdir/'original-effects.wav',impacts,SR,subtype='PCM_24')
    flt='[0:a]aformat=sample_rates=48000:channel_layouts=stereo,asplit=2[v][sc];[1:a]aformat=sample_rates=48000:channel_layouts=stereo,volume=0.065,afade=t=in:d=0.7,afade=t=out:st='+str(duration-1.1)+':d=1.1[m];[m][sc]sidechaincompress=threshold=0.024:ratio=7:attack=18:release=240[duck];[v][duck][2:a]amix=inputs=3:normalize=0,atrim=duration='+str(duration)+'[mix]'
    run(['ffmpeg','-v','error','-y','-i',str(voice),'-ss',str(mstart),'-t',str(duration),'-i',str(mf),'-i',str(outdir/'original-effects.wav'),'-filter_complex',flt,'-map','[mix]','-c:a','pcm_s24le',str(outdir/'pre-level.wav')])
    stderr=subprocess.run(['ffmpeg','-hide_banner','-i',str(outdir/'pre-level.wav'),'-af','loudnorm=I=-16:TP=-2:LRA=9:print_format=json','-f','null','-'],check=True,capture_output=True,text=True).stderr;q=json.loads(stderr[stderr.rfind('{'):stderr.rfind('}')+1]);norm='loudnorm=I=-16:TP=-2:LRA=9:linear=true:measured_I='+q['input_i']+':measured_LRA='+q['input_lra']+':measured_TP='+q['input_tp']+':measured_thresh='+q['input_thresh']+':offset='+q['target_offset']
    run(['ffmpeg','-v','error','-y','-i',str(outdir/'pre-level.wav'),'-af',norm,'-ar',str(SR),'-c:a','pcm_s24le',str(outdir/'mixed-master.wav')])
    credits='Music: '+cfg['attribution']+' | '+cfg['page']+' | '+cfg['license']+' | Changes: excerpt trimmed/faded and ducked beneath speech and original edit effects. Historical footage: DVIDS, U.S. government interview. '+footer.replace('\\N',' ')+' Generic synthetic commentary is not the depicted speaker.'
    final=outdir/'video.mp4';run(['ffmpeg','-v','error','-y','-i',str(pic),'-i',str(outdir/'mixed-master.wav'),'-map','0:v','-map','1:a','-t',str(duration),'-vf','ass='+str(ass),'-c:v','libx264','-threads','2','-crf','18','-preset','fast','-c:a','aac','-b:a','192k','-ar',str(SR),'-ac','2','-movflags','+faststart','-metadata','comment='+credits,str(final)])
    report={'id':name,'duration':duration,'sha256':h(final),'bytes':final.stat().st_size,'words':words,'caption_groups':groups,'music':cfg,'music_excerpt_start':mstart,'commentary_window':commentary_window,'credits':credits,'status':'rendered_requires_inspection'};(outdir/'edit-record.json').write_text(json.dumps(report,indent=2)+'\n');print(name,report['bytes'],report['sha256'],flush=True)
def goggins():
    name='goggins-practice-the-weak-skill';d=json.loads((P/'goggins-commentary-audio-final/narration-timing.json').read_text());duration=d['duration_seconds'];voice=P/'goggins-voice.wav';speech(P/'goggins-commentary-audio-final/narration-paced.wav',voice)
    times=[0,4,8,13,duration];sources=[(538,210),(516,270),(248,210),(326,210)];parts=[]
    for i,(start,x) in enumerate(sources):
        if times[i]>=duration:break
        length=min(times[i+1],duration)-times[i];o=P/f'gp-{i}.mp4';picture(P/'goggins.mp4',start,length,f'crop=324:576:{x}:0',o);parts.append(o)
    pic=P/'goggins-picture.mp4';concat(parts,pic);mix_and_caption(name,pic,voice,d['words'],duration,'Juggernaut',184,'DAVID GOGGINS • NAVY ARCHIVE • 2018',(0,duration))
def jocko():
    name='jocko-turn-a-mistake-into-a-plan';d=json.loads((P/'jocko-commentary-audio/narration-timing.json').read_text());middle=d['duration_seconds'];a=3.9;b=5.2;duration=a+middle+b;pieces=[]
    for key,src,start,dur in [('a',P/'jocko.mp4',61.4,a),('middle',P/'jocko-commentary-audio/narration-paced.wav',None,None),('b',P/'jocko.mp4',66.25,b)]:
        o=P/('jocko-speech-'+key+'.wav');speech(src,o,start,dur);x,sr=sf.read(o,dtype='float32');target=round((a if key=='a' else b if key=='b' else middle)*SR);x=np.pad(x[:target],(0,max(0,target-len(x))));pieces.append(x)
    voice=P/'jocko-voice.wav';sf.write(voice,np.concatenate(pieces),SR,subtype='PCM_24')
    src=json.loads((P/'jocko-transcript.json').read_text());words=[]
    for segment in src:
        for w in segment['words']:
            if 61.33<=w['start']<65.25:
                text=w['word'].strip();start=max(0,w['start']-61.4);end=min(a,w['end']-61.4)
            elif 66.21<=w['start']<71.4:
                text=w['word'].strip();start=max(0,w['start']-66.25)+a+middle;end=min(b,w['end']-66.25)+a+middle
            else:continue
            if text.lower()=='problem':text+='.'
            if text.lower()=='forward':text+='.'
            if text.lower()=='get':text='Get'
            if end>start:words.append({'text':text,'start':start,'end':end})
    for w in d['words']:words.append({'text':w['text'],'start':w['start']+a,'end':w['end']+a})
    words.sort(key=lambda x:x['start']);parts=[]
    for key,st,du in [('a',61.4,a),('b',66.25,b)]:
        o=P/('jocko-picture-'+key+'.mp4');picture(P/'jocko.mp4',st,du,'crop=324:576:230:0',o,extra='');parts.append(o)
    diagram=P/'action-plan.mp4';note_picture(middle,diagram);pic=P/'jocko-picture.mp4';concat([parts[0],diagram,parts[1]],pic)
    mix_and_caption(name,pic,voice,words,duration,'Ascension',122,'JOCKO WILLINK • ARMY INTERVIEW • 2019',(a,a+middle))
if __name__ == "__main__":
    goggins();jocko()
