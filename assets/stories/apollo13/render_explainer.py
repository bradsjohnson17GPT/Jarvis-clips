"""Original animated schematic for the historical Apollo 13 adapter story.

Uses one individually reviewed NASA archive photograph and original geometry.
The schematic is explanatory, not an engineering reconstruction or build guide.
"""
import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 24
INK = '#0a1b24'
WHITE = '#f2f1e9'
GOLD = '#e6b85c'
CYAN = '#6ed4de'
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'


def ease(x):
    x = max(0, min(1, x))
    return x*x*(3-2*x)


def label(d, x, y, text, size=30, color=WHITE, bold=False, anchor='mm'):
    d.text((x, y), text, fill=color,
           font=ImageFont.truetype(BOLD if bold else FONT, size), anchor=anchor)


def make_background():
    im = Image.new('RGB', (W, H), INK)
    d = ImageDraw.Draw(im)
    for y in range(H):
        q = math.exp(-((y-800)/650)**2)
        d.line((0, y, W, y), fill=(round(10+5*q), round(27+15*q), round(36+18*q)))
    for x in range(45, W, 55):
        d.line((x, 300, x, 1380), fill='#18323d', width=1)
    for y in range(335, 1380, 55):
        d.line((45, y, W-45, y), fill='#18323d', width=1)
    d.ellipse((95, 1060, 1000, 1230), fill='#081720')
    return im


def square_filter(d, x, y, scale=1):
    def pt(a,b):return (x+a*scale,y+b*scale)
    def box(a,b,c,e):return pt(a,b)+pt(c,e)
    a=240
    d.polygon([pt(0,0),pt(70,-48),pt(a+70,-48),pt(a,0)],fill='#d2d6ce')
    d.polygon([pt(a,0),pt(a+70,-48),pt(a+70,a-48),pt(a,a)],fill='#617785')
    d.rounded_rectangle(box(0,0,a,a),radius=15*scale,fill='#afbbc0',outline='#e7e8dc',width=round(4*scale))
    d.rounded_rectangle(box(21,21,a-21,a-21),radius=7*scale,fill='#152832')
    for v in range(31,a-25,16):
        d.line(pt(24,v)+pt(a-24,v),fill='#667d84',width=round(3*scale))
        d.line(pt(v,24)+pt(v,a-24),fill='#667d84',width=round(3*scale))
    d.line(pt(16,16)+pt(a-16,16),fill=WHITE,width=round(4*scale))


def round_port(d, x, y, scale=1):
    def pt(a,b):return (x+a*scale,y+b*scale)
    def box(a,b,c,e):return pt(a,b)+pt(c,e)
    r=118
    d.polygon([pt(0,-r),pt(135,-r-30),pt(135,r-30),pt(0,r)],fill='#506975')
    d.ellipse(box(20,-r-30,250,r-30),fill='#526f79',outline='#89a2a8',width=round(4*scale))
    d.ellipse(box(-r,-r,r,r),fill='#adbdc0',outline='#e0e6df',width=round(5*scale))
    d.ellipse(box(-r+22,-r+22,r-22,r-22),fill='#0a1d27',outline='#758e98',width=round(6*scale))
    d.arc(box(-r+35,-r+35,r-35,r-35),205,325,fill=CYAN,width=round(7*scale))


def frame(t, bg, photo):
    if t < 3.0 or t >= 22.4:
        # A photographed historical object, explicitly identified as a still.
        phase = t/3 if t < 3 else (t-22.4)/2.5
        zoom = 1.0+0.035*ease(phase)
        ch = photo.height/zoom
        cw = ch*W/H
        cx = photo.width*.49
        cy = photo.height*.5
        im = photo.crop((cx-cw/2,cy-ch/2,cx+cw/2,cy+ch/2)).resize((W,H), Image.Resampling.LANCZOS)
        overlay = Image.new('RGBA',(W,H))
        od = ImageDraw.Draw(overlay)
        for y in range(410):
            a = round(180*(1-y/410))
            od.line((0,y,W,y),fill=(5,15,23,a))
        for y in range(1250,H):
            a = round(180*((y-1250)/(H-1250)))
            od.line((0,y,W,y),fill=(5,15,23,a))
        im = Image.alpha_composite(im.convert('RGBA'),overlay).convert('RGB')
        d = ImageDraw.Draw(im)
        label(d,70,118,'APOLLO 13  •  1970',34,bold=True,anchor='lm')
        label(d,70,181,'THE ACTUAL ADAPTER',27,anchor='lm')
        label(d,540,1780,'Archive photograph: NASA / AS13-62-8929',25)
        return im
    im = bg.copy()
    d = ImageDraw.Draw(im)
    label(d,70,118,'APOLLO 13  •  1970',34,bold=True,anchor='lm')
    label(d,70,181,'ORIGINAL EXPLANATORY ANIMATION',24,anchor='lm')
    if 4.68 <= t < 7.45:
        # A purposeful portrait close-up, drawn at full output resolution.
        scale=1.78+.04*ease((t-4.68)/2.7)
        square_filter(d,275,660,scale)
        label(d,540,1230,'SQUARE CANISTER',40,bold=True)
        label(d,540,1290,'Command module',30,color='#a9c2cc')
        label(d,540,1780,'Simplified illustration  •  Historical sources: NASA',25,color='#a9c2cc')
        return im
    if 7.45 <= t < 10.72:
        scale=1.9+.04*ease((t-7.45)/3.2)
        round_port(d,475,850,scale)
        label(d,540,1230,'ROUND CONNECTION',40,bold=True)
        label(d,540,1290,'Lunar module',30,color='#a9c2cc')
        label(d,540,1780,'Simplified illustration  •  Historical sources: NASA',25,color='#a9c2cc')
        return im
    # Movement follows the recorded narration: square 4.68, connection 9.28,
    # adapter 12.74, built 16.62, carbon-dioxide outcome 18.3–20.14.
    approach = 95*ease((t-6.9)/1.5)
    retreat = 45*ease((t-9.2)/.7)
    x, y = 105+approach-retreat, 720
    square_filter(d,x,y)
    round_port(d,810,840)
    label(d,x+120,1060,'SQUARE CANISTER',27,bold=True)
    label(d,810,1060,'ROUND CONNECTION',27,bold=True)
    label(d,x+120,1110,'Command module',24,color='#a9c2cc')
    label(d,810,1110,'Lunar module',24,color='#a9c2cc')
    if 6.9 < t < 11.6:
        q = ease((t-7.2)/.7)
        end = x+310 + (670-x-310)*q
        d.line((x+310,840,end,840),fill=GOLD,width=5)
        if q>.9:
            d.line((645,812,672,840,645,868),fill=GOLD,width=5)
        label(d,540,1198,'Different interfaces',30,GOLD,bold=True)
    if 10.96 < t < 17.9:
        # Procedural ground-to-crew relay, not invented archival dialogue.
        crew_active=t>=16.28
        for xx,title,sub,active in [(165,'GROUND TEAM','design + test',not crew_active),(625,'CREW','assemble',crew_active)]:
            d.rounded_rectangle((xx,305,xx+290,430),radius=15,fill='#193541',outline=GOLD if active else '#4a6672',width=3)
            label(d,xx+145,350,title,27,bold=True)
            label(d,xx+145,397,sub,23,color='#a9c2cc')
        q=ease((t-11.4)/1.4)
        end=470+145*q
        d.line((470,368,end,368),fill=GOLD,width=4)
        if q>.9:d.line((597,350,615,368,597,386),fill=GOLD,width=4)
        if t>=12.5:label(d,540,476,'PROCEDURE SENT TO THE CREW',24,color='#b5ccd3')
        for text,px,begin in [('PLASTIC BAG',260,12.9),('CARD',540,13.4),('TAPE',820,13.8)]:
            f=ease((t-begin)/.65)
            if f>0:
                yy=610-30*f
                label(d,px,yy,text,25,color='#e9dfc9',bold=True)
    if t>=12.5:
        f=ease((t-12.5)/3.8)
        left=x+310
        right=690
        middle=(left+right)/2
        layer=Image.new('RGBA',(W,H))
        ld=ImageDraw.Draw(layer)
        # The original opaque solid is replaced with visibly flexible plastic:
        # irregular edges, translucent folds and an identifiable card panel.
        # This remains a symbolic connection, not the literal NASA geometry.
        points=[(left-13,735),(left+32,709),(middle-18,717),
                (middle+28,701),(right+14,769),(right+8,835),
                (right+17,917),(middle+20,979),(middle-22,961),
                (left-15,968),(left+2,891),(left-9,803)]
        ld.polygon(points,fill=(183,220,229,round(36*f)),outline=(208,235,236,round(205*f)))
        card=ease((t-13.45)/1.1)
        if card>0:
            ld.polygon([(middle-45,757),(middle+18,747),(middle+39,920),(middle-33,941)],
                       fill=(174,135,82,round(190*card)),outline=(228,202,158,round(220*card)))
            ld.line((middle-29,776,middle+16,912),fill=(101,77,50,round(180*card)),width=3)
        folds=[[(left+5,748),(middle-6,790),(right-3,778)],
               [(left+2,944),(middle-5,876),(right+1,916)],
               [(middle+24,715),(middle+3,791),(middle+21,836)],
               [(left-2,800),(left+27,840),(left+8,891)],
               [(middle-20,953),(middle+3,919),(middle+14,962)]]
        for fold in folds:ld.line(fold,fill=(222,242,239,round(130*f)),width=3)
        im=Image.alpha_composite(im.convert('RGBA'),layer).convert('RGB')
        d=ImageDraw.Draw(im)
        if t>16.25:
            lock=ease((t-16.25)/1.0)
            for px in [left+6,right-4]:
                extent=round(125*lock)
                tape=[(px-11,840-extent),(px+10,838-extent),(px+13,843-extent),
                      (px+10,840+extent),(px-10,842+extent),(px-13,835+extent)]
                d.polygon(tape,fill='#c4c4b9',outline='#e2e1d4')
                d.line((px-5,850-extent,px+4,845+extent),fill='#8b928e',width=2)
            label(d,540,1200,'AN IMPROVISED ADAPTER',30,GOLD,bold=True)
    if t>18.26:
        q=ease((t-18.26)/1.6)
        for j in range(13):
            px=830-((t*110+j*43)%620)
            py=840+15*math.sin(j+t*2)
            color=CYAN if px<400 else '#dbb66d'
            rr=4+q*3
            d.ellipse((px-rr,py-rr,px+rr,py+rr),fill=color)
        label(d,540,430,'CO₂ REMOVAL RESTORED',36,CYAN,bold=True)
    label(d,540,1780,'Simplified illustration  •  Historical sources: NASA',25,color='#a9c2cc')
    return im


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--photo',type=Path,required=True)
    p.add_argument('--timing',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--stills-only',action='store_true')
    args=p.parse_args()
    assert hashlib.sha256(args.photo.read_bytes()).hexdigest()=='9496d19e11d5e2da3eb35a36529346aa0a1607c4ba93e2e6c963d8c709bffc1f'
    duration=json.loads(args.timing.read_text())['duration_seconds']
    args.output.mkdir(parents=True,exist_ok=True)
    photo=Image.open(args.photo).convert('RGB')
    bg=make_background()
    for t in [1,5,8.7,10,13.5,16.7,19.5,23.4]:
        frame(t,bg,photo).save(args.output/f'preview-{t:.1f}.jpg')
    if args.stills_only:
        print('Original schematic review stills rendered; no finished video.',flush=True)
        return
    count=math.ceil(duration*FPS)
    target=args.output/'picture.mp4'
    command=['ffmpeg','-v','error','-y','-f','rawvideo','-pixel_format','rgb24',
             '-video_size',f'{W}x{H}','-framerate',str(FPS),'-i','pipe:0','-an',
             '-c:v','libx264','-threads','2','-preset','fast','-crf','18',
             '-pix_fmt','yuv420p','-movflags','+faststart',str(target)]
    proc=subprocess.Popen(command,stdin=subprocess.PIPE)
    for i in range(count):
        proc.stdin.write(frame(i/FPS,bg,photo).tobytes())
        if i%96==0:print(f'Picture frame {i}/{count}',flush=True)
    proc.stdin.close()
    if proc.wait()!=0:raise SystemExit('Picture encode failed.')
    report={'status':'silent_development_picture_requires_audio_and_inspection',
            'width':W,'height':H,'fps':FPS,'native_frames':count,
            'duration':count/FPS,'photo_sha256':hashlib.sha256(args.photo.read_bytes()).hexdigest(),
            'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
            'original_geometry':'Procedural original animated 2D/extruded schematic, not a simulation or archive footage.',
            'source_audio_used':False}
    (args.output/'picture-source.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)


if __name__=='__main__':
    main()
