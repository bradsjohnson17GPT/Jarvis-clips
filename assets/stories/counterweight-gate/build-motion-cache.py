"""Compile original reviewed controller records into a compact shared-scene input.

No image/audio is regenerated. The compressed JSON is original animation data,
not media, a third-party model, or proof that a final movie has been rendered.
"""
import argparse,base64,hashlib,json,math,zlib
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--records',type=Path,required=True);p.add_argument('--output',type=Path,required=True);o=p.parse_args()
root=next(a for a in Path(__file__).resolve().parents if (a/'AGENTS.md').exists())
specs=[('opening','opening-motion-v1','opening-study.json','opening-study.py'),('notice','notice-motion-v1','notice-study.json','notice-study.py'),('stair','stair-motion-v1','stair-motion-study.json','stair-motion-study.py'),('stone','stone-motion-v1','stone-loading-study.json','stone-loading-study.py'),('passage','passage-motion-v1','passage-study.json','passage-study.py')]
records={};provenance=[]
for key,folder,name,source in specs:
 path=o.records/folder/name;blob=path.read_bytes();r=json.loads(blob);source_path=root/'assets/stories/counterweight-gate'/source
 assert hashlib.sha256(source_path.read_bytes()).hexdigest()==r['source_sha256']
 records[key]={a['frame']:a for a in r['records']};provenance.append({'part':key,'source':str(source_path.relative_to(root)),'source_sha256':r['source_sha256'],'record_sha256':hashlib.sha256(blob).hexdigest(),'recorded_frames':len(r['records'])})
def smooth(q):
 q=max(0,min(1,q));return q*q*(3-2*q)
def transform(root,yaw,v,scale=1):
 c,s=math.cos(yaw),math.sin(yaw);x,y,z=v
 return [root[0]+scale*(c*x-s*y),root[1]+scale*(s*x+c*y),root[2]+scale*z]
def lerp(a,b,q):return [x+(y-x)*q for x,y in zip(a,b)]
plan=json.loads((root/'assets/stories/counterweight-gate/action-plan-v2.json').read_text());a=plan['actions'];pick,release,impact=[a[k] for k in ['stone_pickups','stone_releases','stone_deposits']]
source_stones=[s['center_world'] for s in records['stone'][319]['stones']]
centers=[[source_stones[g][0]+.09,source_stones[g][1]+.04,source_stones[g][2]] for g in [0,3,6]]
def carry(g,t):
 q=smooth((t-pick[g])/(release[g]-pick[g]));start=centers[g];end=[3,.28,3.26];control=[2.6,.80,(start[2]+end[2])/2+.12]
 center=[x*(1-q)**2+y*2*q*(1-q)+z*q*q for x,y,z in zip(start,control,end)]
 return [center[0]-.06,center[1]-.03,center[2]-.13]
def foots(r):return [next(f['ankle_world'] for f in r['feet'] if f['side']==side) for side in [-1,1]]
hero=[];waiting=[]
for frame in range(1,579):
 t=(frame-1)/24;wheel=0;carty=-1.55;gate=0
 if frame<=197:
  r=records['opening'][frame];pos=r['hero_location'];yaw=r['hero_yaw'];hands=[r['hand_targets'][str(side)]['target'] for side in [-1,1]];feet=foots(r);concern=r['concern_expression_fraction'];reaction=smooth((t-5.8)/.7);neck=[.035*math.sin(t*2)+.10*concern,0,1.15*(1-reaction)-.5*reaction];gate=r['gate_lift']
 elif frame<=262:
  r=records['notice'][frame];pos=r['hero_location'];yaw=r['hero_yaw'];hands=[transform(pos,yaw,[side*.34,-.12,.78]) for side in [-1,1]];feet=foots(r);neck=r['neck_euler'];concern=1-r['head_turn_fraction']
 elif frame<=318:
  r=records['stair'][frame];pos=r['hero_world'];yaw=0;hands=[transform(pos,yaw,[side*.36,-.16+.10*math.sin((t-11)*math.tau*2)*side,.93]) for side in [-1,1]];feet=foots(r);neck=[.06,0,-.12*smooth((t-12.875)/.30)];concern=.12
 elif frame<=438:
  r=records['stone'][frame];pos=r['hero_world'];yaw=-math.pi/4;feet=[transform(pos,yaw,[side*.145,0,.13]) for side in [-1,1]];relaxed={side:transform(pos,yaw,[side*.35,-.10,.85]) for side in [-1,1]};target=relaxed[-1]
  if t<=release[0]:target=carry(0,t)
  elif t<pick[1]:target=lerp(carry(0,release[0]),carry(1,pick[1]),smooth((t-release[0])/(pick[1]-release[0])))
  elif t<=release[1]:target=carry(1,t)
  elif t<pick[2]:target=lerp(carry(1,release[1]),carry(2,pick[2]),smooth((t-release[1])/(pick[2]-release[1])))
  elif t<=release[2]:target=carry(2,t)
  else:target=lerp(carry(2,release[2]),relaxed[-1],smooth((t-release[2])/(a['hands_clear_of_basket']-release[2])))
  hands=[target,relaxed[1]];neck=[.03,0,.12*math.sin((t-13.25)*2)];concern=.12*(1-smooth((t-15.25)/1.2));gate=r['gate_lift']
 else:
  r=records['passage'][frame];h=r['actors'][0];pos=h['root_world'];yaw=math.pi;feet=foots(h);carty=r['cart_world'][1];hands=[[.30-side*.25,carty-.55,1.02] for side in [-1,1]];neck=[.01,0,-.08];concern=0;gate=r['gate_lift'];wheel=r['wheel_rotation_radians'];cast=[]
  for index,scale,total,cycles in [(1,.96,5.25,6),(2,1.04,5.65,6)]:
   actor=r['actors'][index];distance=actor['distance'];phase=distance/(total/cycles);motion=smooth(distance/((total/cycles)*.3));aroot=actor['root_world'];ahands=[transform(aroot,math.pi,[side*.34,-.12+.10*math.sin(phase*math.tau+side*math.pi/2)*motion,.78],scale) for side in [-1,1]];cast.append({'root':aroot,'yaw':math.pi,'hands':ahands,'feet':foots(actor),'neck':[.01,0,0]})
  waiting.append(cast)
 hero.append({'root':pos,'yaw':yaw,'hands':hands,'feet':feet,'neck':neck,'concern':concern,'gate':gate,'cart_y':carty,'wheel':wheel})
data={'version':1,'fps':24,'frames':578,'hero':hero,'waiting_passage':waiting,'source_stones':source_stones,'stone_centers':[[s['center_world'] for s in records['stone'][frame]['stones']] for frame in range(319,439)]}
def rounded(x):
 if isinstance(x,float):return round(x,6)
 if isinstance(x,list):return [rounded(a) for a in x]
 if isinstance(x,dict):return {k:rounded(v) for k,v in x.items()}
 return x
raw=json.dumps(rounded(data),separators=(',',':')).encode();encoded=base64.b64encode(zlib.compress(raw,9)).decode()+'\n';o.output.mkdir(parents=True,exist_ok=True)
(o.output/'motion-cache.zlib.b64').write_text(encoded)
meta={'format':'Base64 of zlib-compressed UTF-8 JSON; original numerical animation targets only','version':1,'frames':578,'fps':24,'uncompressed_json_sha256':hashlib.sha256(raw).hexdigest(),'encoded_file_sha256':hashlib.sha256(encoded.encode()).hexdigest(),'provenance':provenance,'base_original_stone_scene_sha256':'0adb6d86642ceb6973beba1db77228841c987903aca7134755a56748811b6873','action_plan':'assets/stories/counterweight-gate/action-plan-v2.json','action_plan_sha256':hashlib.sha256((root/'assets/stories/counterweight-gate/action-plan-v2.json').read_bytes()).hexdigest(),'rounding_decimal_places':6,'source_audio_changed':False,'old_media_reencoded_or_rendered':False,'full_movie_exists':False}
(o.output/'motion-cache.json').write_text(json.dumps(meta,indent=2)+'\n');print(json.dumps({'frames':578,'json_bytes':len(raw),'encoded_bytes':len(encoded),'encoded_sha256':meta['encoded_file_sha256']}))
