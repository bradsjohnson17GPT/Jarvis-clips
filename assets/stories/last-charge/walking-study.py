"""Original native route-facing gait and carry diagnostic; no finished story."""
import argparse,hashlib,json,math,runpy,shutil,sys
from pathlib import Path
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'AGENTS.md').exists())
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--frames',type=int,nargs='+');args=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
out=args.output.resolve();out.mkdir(parents=True,exist_ok=True);(out/'frames').mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):Path(p).write_text(json.dumps(x,indent=2)+'\n')
base=ROOT/'assets/stories/last-charge/staging-study.py';placement=ROOT/'assets/stories/last-charge/placement-study.py'
assert sha(base)=='647468191e2d5fe41986877b0374a249d32032a7fe264aea4404fe103932194a';assert sha(placement)=='1dc6ff18d05a9e5d0001a7db703216634793739465fd6e1e7f981ed9276b47cd'
source_hash=sha(__file__);frozen=out/'frozen-walking-study.py';fb=out/'frozen-base-staging.py'
for src,dst in [(Path(__file__),frozen),(base,fb)]:
 if dst.exists():assert sha(src)==sha(dst)
 else:shutil.copyfile(src,dst)
voice=ROOT/'work/preproduction/last-charge/narration-v1/narration-clean.wav';assert sha(voice)=='33562e4149c22087cc3be49171cb7fda90cb7746fbefc9b031c89a1384aced1a'
inputs={'source_sha256':source_hash,'base_source_sha256':sha(base),'placement_reference_sha256':sha(placement),'existing_clean_narration_sha256':sha(voice),'native_dimensions':[720,1280],'fps':24,'motion_frames':31,'cycle_intervals':30,'audio_present':False}
if (out/'source-inputs.json').exists():assert json.loads((out/'source-inputs.json').read_text())==inputs
else:write(out/'source-inputs.json',inputs)
old=sys.argv
try:
 sys.argv=[str(fb),'--','--output',str(out/'base-scene')];ns=runpy.run_path(str(fb),run_name='__owned_base__')
finally:sys.argv=old
scene=ns['scene'];camera=ns['camera'];actors=ns['actors'];lamps=ns['lamps'];mats=ns['mats']
manifest={'frozen_source':str(frozen),'source_sha256':source_hash,'width':720,'height':1280,'frame_numbers':list(range(1,32)),'cycles_samples':12,'kind':'silent31frame_route_walk_and_carried_lamp_diagnostic','spatial_upscale':False,'frame_interpolation':False}
if (out/'render-manifest.json').exists():assert json.loads((out/'render-manifest.json').read_text())==manifest
else:write(out/'render-manifest.json',manifest)
# Reuse the same authored environment with the reviewed support-height correction.
for i,(x,y,z) in enumerate(ns['rests']):
 scene.objects[f'Original lamp rest {i+1}'].location.z=1.05
 rod=scene.objects[f'Lamp rest support {i+1}'];dep=max(v.co.z for v in rod.data.vertices)-min(v.co.z for v in rod.data.vertices);rod.location.z=(.34+1.02)/2;rod.scale.z=(1.02-.34)/dep
ns['cube']('Original bracket wall mount',(-1.83,ns['shop_front']+.030,1.39),(.10,.03,.12),mats['brass'],bevel=.012)
ns['rod']('Original bracket mounting connector',(-1.83,ns['shop_front']+.030,1.39),(-1.83,ns['shop_front']-.08,1.39),.022,mats['brass'])
ns['area']('Original soft route-facing fill',(1,3,3),(0,0,1.0),100,4,(.45,.58,1.0))
ns['set_pose'](2);ns['place_actor']('rose',(0,-.37,.04),yaw=math.pi,mode='carry',stride=0)
actors['far']['root'].location=(-2.25,2.26,.08);actors['traveler']['root'].location.x=-.35
for lamp in lamps:
 on=bool(lamp['light'].energy);lamp['light'].energy=55 if on else 0;lamp['glow'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value=1.7 if on else .025
mats['cell'].node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.016,.04,.05,1)
rose=actors['rose'];root=rose['root'];bpy.context.view_layer.update()
def depth(ob):return max(v.co.z for v in ob.data.vertices)-min(v.co.z for v in ob.data.vertices)
def rod_pose(ob,a,b,dep):
 v=b-a;ob.location=(a+b)/2;ob.rotation_euler=v.to_track_quat('Z','Y').to_euler();ob.scale=(1,1,v.length/dep)
def solve(a,b,L1,L2,pole):
 delta=b-a;d=delta.length;assert abs(L1-L2)+1e-6<d<L1+L2-1e-6
 axis=delta/d;q=(L1*L1-L2*L2+d*d)/(2*d);normal=pole-axis*pole.dot(axis);assert normal.length>.01;return a+axis*q+normal.normalized()*math.sqrt(max(0,L1*L1-q*q))
legs={}
for side,x in [('left',-.14),('right',.14)]:
 rods=[o for o in rose['limbs'] if side+' trouser' in o.name];upper=max(rods,key=lambda o:o.location.z);lower=next(o for o in rods if o!=upper);foot=next(o for o in rose['feet'] if side+' shoe' in o.name);knee=ns['sphere']('Rose '+side+' original rounded walking knee',(x,0,.43),(.16,.16,.16),mats['pants'],root)
 legs[side]={'upper':upper,'lower':lower,'upper_depth':depth(upper),'lower_depth':depth(lower),'foot':foot,'knee':knee,'x':x}
# Preserve the reviewed right-arm segment lengths, with the mitten visible beyond the cuff.
shoulder=Vector((.255,0,1.16));cal_elbow=Vector((.28,-.29,1.25));cal_hand=Vector((.10,-.57,1.41));A1=(cal_elbow-shoulder).length;A2=(cal_hand-cal_elbow).length
sleeves=[o for o in rose['limbs'] if 'right original sleeve' in o.name];arm_upper=max(sleeves,key=lambda o:o.location.z);arm_fore=next(o for o in sleeves if o!=arm_upper);aball=next(o for o in rose['limbs'] if 'right rounded elbow' in o.name);hand=rose['hands']['right'];ad={o.name:depth(o) for o in sleeves}
carry=Vector((.30,-.35,1.0));elbow=solve(shoulder,carry,A1,A2,Vector((.8,-.3,-1)))
rod_pose(arm_upper,shoulder,elbow,ad[arm_upper.name]);rod_pose(arm_fore,elbow,carry-(carry-elbow).normalized()*.05,ad[arm_fore.name]);aball.location=elbow;hand.location=carry
lamps[0]['root'].rotation_euler=(0,0,math.pi)
def ease(p):return p*p*(3-2*p)
def foot_target(phase,side):
 half=phase*2 if phase<=.5 else (phase-.5)*2
 if side=='left':y=-.47+.4*ease(half) if phase<=.5 else -.07;swing=0<phase<.5
 else:y=-.27 if phase<=.5 else -.27+.4*ease(half);swing=.5<phase<1
 lift=.07*math.sin(math.pi*half)**2 if swing else 0
 return Vector((.14 if side=='left' else -.14,y,.22+lift)),swing

def pose(n):
 phase=(n-1)/30;root.location=(0,-.37+.4*phase,.04+.01*math.sin(math.tau*phase)**2);bpy.context.view_layer.update();inv=root.matrix_world.inverted();feet={}
 for side,leg in legs.items():
  ankle,swing=foot_target(phase,side);hip=root.matrix_world@Vector((leg['x'],0,.76));knee=solve(hip,ankle,.33,.29,Vector((0,1,0)));a,b,c=inv@hip,inv@knee,inv@ankle
  rod_pose(leg['upper'],a,b,leg['upper_depth']);rod_pose(leg['lower'],b,c,leg['lower_depth']);leg['knee'].location=b;leg['foot'].location=inv@(ankle-Vector((0,0,.07)));leg['foot'].rotation_euler=(0,0,0)
  err=max(abs((knee-hip).length-.33),abs((ankle-knee).length-.29));assert err<1e-5
  feet[side]={'ankle':list(ankle),'swing':swing,'leg_length_error':err}
 bpy.context.view_layer.update();world_hand=hand.matrix_world.translation;lamps[0]['root'].location=world_hand-Vector((0,0,.55));lamps[0]['spot'].rotation_euler=(lamps[0]['root'].rotation_euler.to_quaternion().inverted()@Vector((0,0,-1))).to_track_quat('-Z','Y').to_euler();bpy.context.view_layer.update()
 for side,leg in legs.items():
  corners=[leg['foot'].matrix_world@Vector(c) for c in leg['foot'].bound_box];sole=min(v.z for v in corners);assert sole>=.08-1e-5
  if not feet[side]['swing']:assert abs(sole-.08)<1e-5
  assert min(v.y for v in corners)>-.6725 and max(v.y for v in corners)<2.6725
  feet[side]['actual_shoe_sole_plane']=sole;feet[side]['actual_shoe_world_center']=list(leg['foot'].matrix_world.translation)
 grip=lamps[0]['root'].matrix_world@Vector((0,0,.55));grip_error=(grip-world_hand).length;assert grip_error<1e-5
 face=root.matrix_world.to_quaternion()@Vector((0,-1,0));assert face.y>.999
 return {'phase':phase,'seconds':(n-1)/24,'root':list(root.location),'feet':feet,'hand_to_handle_center':grip_error,'arm_length_error':max(abs((elbow-shoulder).length-A1),abs((carry-elbow).length-A2)),'world_facing':list(face),'lamp_mark_count':lamps[0]['marks'],'independent_pool_powers':[l['light'].energy for l in lamps],'scope':'Sampled fixed leg lengths, actual flat shoe soles/envelope, anchored stance feet and carry grip. No foot roll, support-force, full-body swept collision, acting or full-film pass.'}
checks={n:pose(n) for n in range(1,32)}
for side,lo,hi in [('right',1,16),('left',16,31)]:
 anchor=Vector(checks[lo]['feet'][side]['actual_shoe_world_center']);assert max((Vector(checks[n]['feet'][side]['actual_shoe_world_center'])-anchor).length for n in range(lo,hi+1))<1e-5
# Fit the union of actual primary object bounds across every requested gait pose.
objects=[o for o in list(root.children_recursive)+list(lamps[0]['root'].children_recursive) if o.type in {'MESH','CURVE'}];points=[]
for n in range(1,32):
 pose(n);points.extend(o.matrix_world@Vector(c) for o in objects for c in o.bound_box)
center=Vector(tuple((min(v[i] for v in points)+max(v[i] for v in points))/2 for i in range(3)));direction=Vector((.18,1.0,.40)).normalized();distance=3.0;camera.data.lens=45
for attempt in range(40):
 camera.location=center+direction*distance;camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler();bpy.context.view_layer.update();screen=[world_to_camera_view(scene,camera,v) for v in points]
 if min(v.x for v in screen)>.07 and max(v.x for v in screen)<.93 and min(v.y for v in screen)>.06 and max(v.y for v in screen)<.94 and min(v.z for v in screen)>0:break
 distance*=1.06
else:raise AssertionError('Moving primary bounds do not fit portrait frame.')
requested=set(args.frames or range(1,32));assert requested<=set(range(1,32))
for n in sorted(requested):
 check=pose(n);path=out/'frames'/f'{n:05d}.png';rp=path.with_suffix('.json')
 if path.exists() and rp.exists():
  r=json.loads(rp.read_text());assert r['source_sha256']==source_hash and r['raw_image_sha256']==sha(path);continue
 assert not path.exists(),'Existing unreceipted frame is held.'
 scene.frame_set(n);scene.render.filepath=str(path);bpy.ops.render.render(write_still=True);write(rp,{'study_frame':n,'source_sha256':source_hash,'raw_image_sha256':sha(path),'dimensions':[720,1280],'numeric_checks':check,'actual_visual_review_pending':True})
rows=[json.loads((out/'frames'/f'{n:05d}.json').read_text()) for n in range(1,32) if (out/'frames'/f'{n:05d}.json').exists()]
write(out/'walking-samples.json',{'inputs':inputs,'all31_numeric_poses_checked':True,'stance_foot_world_drift_below_1e_minus5':True,'all31_raw_frames_complete':len(rows)==31,'completed_frames':[r['study_frame'] for r in rows],'numeric_checks':checks,'raw_receipts':rows,'actual_visual_review_pending':True,'finished_story_exists':False,'publishable':False})
bpy.ops.wm.save_as_mainfile(filepath=str(out/'walking-study.blend'));print(json.dumps({'source_sha256':source_hash,'native_raw_frames_existing':len(rows),'finished_story_exists':False,'publishable':False}),flush=True)
