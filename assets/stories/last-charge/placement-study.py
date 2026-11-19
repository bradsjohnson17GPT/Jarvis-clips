"""Original native lift-over-rail, supported placement and release diagnostic.

The retained narration and prior studies are inputs/records, never regenerated.
This is silent action development, not a complete story or posting candidate.
"""
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
base=ROOT/'assets/stories/last-charge/staging-study.py';assert sha(base)=='647468191e2d5fe41986877b0374a249d32032a7fe264aea4404fe103932194a'
source_hash=sha(__file__);frozen=out/'frozen-placement-study.py';fb=out/'frozen-base-staging.py'
for src,dst in [(Path(__file__),frozen),(base,fb)]:
 if dst.exists():assert sha(src)==sha(dst)
 else:shutil.copyfile(src,dst)
voice=ROOT/'work/preproduction/last-charge/narration-v1/narration-clean.wav';assert sha(voice)=='33562e4149c22087cc3be49171cb7fda90cb7746fbefc9b031c89a1384aced1a'
inputs={'source_sha256':source_hash,'base_source_sha256':sha(base),'clean_narration_sha256':sha(voice),'native_dimensions':[720,1280],'fps':24,'motion_frames':48,'orientation_still_item':1001,'audio_present':False}
if (out/'source-inputs.json').exists():assert json.loads((out/'source-inputs.json').read_text())==inputs
else:write(out/'source-inputs.json',inputs)
old=sys.argv
try:
 sys.argv=[str(fb),'--','--output',str(out/'base-scene')];ns=runpy.run_path(str(fb),run_name='__owned_base__')
finally:sys.argv=old
scene=ns['scene'];camera=ns['camera'];actors=ns['actors'];lamps=ns['lamps'];mats=ns['mats']
manifest={'frozen_source':str(frozen),'source_sha256':source_hash,'width':720,'height':1280,'frame_numbers':list(range(1,49))+[1001],'cycles_samples':12,'kind':'silent48frame_placement_release_and_one_route_orientation_still','spatial_upscale':False,'frame_interpolation':False}
if (out/'render-manifest.json').exists():assert json.loads((out/'render-manifest.json').read_text())==manifest
else:write(out/'render-manifest.json',manifest)
# Raise each original fixture to clear the existing handrail. No old source/cache changes.
rest_top=1.08
for i,(x,y,z) in enumerate(ns['rests']):
 scene.objects[f'Original lamp rest {i+1}'].location.z=rest_top-.03
 rod=scene.objects[f'Lamp rest support {i+1}'];mesh_depth=max(v.co.z for v in rod.data.vertices)-min(v.co.z for v in rod.data.vertices)
 a,b=Vector((x,y,.34)),Vector((x,y,rest_top-.06));rod.location=(a+b)/2;rod.scale.z=(b-a).length/mesh_depth
ns['cube']('Original bracket wall mount',(-1.83,ns['shop_front']+.030,1.39),(.10,.03,.12),mats['brass'],bevel=.012)
ns['rod']('Original bracket mounting connector',(-1.83,ns['shop_front']+.030,1.39),(-1.83,ns['shop_front']-.08,1.39),.022,mats['brass'])

def balance():
 for lamp in lamps:
  on=bool(lamp['light'].energy);lamp['light'].energy=55 if on else 0;lamp['glow'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value=1.7 if on else .025
 mats['cell'].node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.016,.04,.05,1)

def cam(loc,target,lens):
 camera.location=loc;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.lens=lens

def render(n,checks,kind):
 path=out/'frames'/f'{n:05d}.png';rp=path.with_suffix('.json')
 if path.exists() and rp.exists():
  r=json.loads(rp.read_text());assert r['source_sha256']==source_hash and r['raw_image_sha256']==sha(path);return r
 assert not path.exists(),'Existing unreceipted output is held.'
 scene.frame_set(n);scene.render.filepath=str(path);bpy.context.view_layer.update();bpy.ops.render.render(write_still=True)
 r={'study_frame':n,'kind':kind,'source_sha256':source_hash,'raw_image_sha256':sha(path),'dimensions':[720,1280],'numeric_checks':checks,'actual_visual_review_pending':True};write(rp,r);return r
requested=set(args.frames or list(range(1,49))+[1001]);assert requested<=set(range(1,49))|{1001}
if 1001 in requested:
 ns['set_pose'](2);ns['place_actor']('rose',(-.28,-.05,.08),yaw=math.pi,mode='carry');bpy.context.view_layer.update()
 rig=actors['rose']['root'];lamps[0]['root'].location=rig.matrix_world@Vector((.30,-.35,.45));lamps[0]['root'].rotation_euler=rig.rotation_euler.copy();balance()
 objects=[o for o in list(rig.children_recursive)+list(lamps[0]['root'].children_recursive) if o.type in {'MESH','CURVE'}]
 points=[o.matrix_world@Vector(c) for o in objects for c in o.bound_box];center=Vector(tuple((min(v[i] for v in points)+max(v[i] for v in points))/2 for i in range(3)));direction=Vector((1.0,.55,.4)).normalized();distance=2.5
 for attempt in range(40):
  cam(center+direction*distance,center,45);bpy.context.view_layer.update();screen=[world_to_camera_view(scene,camera,o.matrix_world@Vector(c)) for o in objects for c in o.bound_box]
  if min(v.x for v in screen)>.07 and max(v.x for v in screen)<.93 and min(v.y for v in screen)>.06 and max(v.y for v in screen)<.94 and min(v.z for v in screen)>0:break
  distance*=1.06
 else:raise AssertionError('Route-facing primary objects do not fit portrait bounds.')
 face=rig.matrix_world.to_quaternion()@Vector((0,-1,0));hand=actors['rose']['hands']['right'].matrix_world.translation;grip=lamps[0]['root'].matrix_world@Vector((0,0,.55))
 assert face.y>.999 and (hand-grip).length<1e-5
 render(1001,{'world_facing':list(face),'desired_route_direction':[0,1,0],'hand_to_handle_center':(hand-grip).length,'static_not_walking':True},'route_facing_static_orientation_only')
ns['set_pose'](3);balance();actors['far']['root'].location=(-2.25,2.26,.08)
actors['traveler']['root'].location.x=-.35
ns['area']('Original soft action-side fill',(3,4,4),(.54,.95,1.3),80,4,(.49,.62,1.0))
rose=actors['rose'];root=rose['root'];root.location=(.54,.85,.08);root.rotation_euler=(0,0,math.pi/2)
shoulder=Vector((.255,0,1.16));cal_elbow=Vector((.28,-.29,1.25));cal_hand=Vector((.10,-.57,1.41));L1=(cal_elbow-shoulder).length;L2=(cal_hand-cal_elbow).length
# Bend the carrying elbow toward the action, not up around the shoulder.
pole=Vector((0,-1,0))
sleeves=[o for o in rose['limbs'] if 'right original sleeve' in o.name];upper=min(sleeves,key=lambda o:(o.location-(shoulder+cal_elbow)/2).length);fore=next(o for o in sleeves if o!=upper);ball=next(o for o in rose['limbs'] if 'right rounded elbow' in o.name);hand=rose['hands']['right'];depth={o.name:max(v.co.z for v in o.data.vertices)-min(v.co.z for v in o.data.vertices) for o in sleeves}
# One owned head pivot keeps all face/hair/glasses parts together.
bpy.context.view_layer.update();head=ns['empty']('Rose original action head pivot');head.parent=root;head.location=(0,0,1.28);bpy.context.view_layer.update()
parts=[o for o in root.children if o not in rose['limbs'] and any(w in o.name for w in ['original head','hair cap','silver bun','eye white','pupil','brow','spectacle','nose','small smile',' ear'])]
for ob in parts:
 world=ob.matrix_world.copy();ob.parent=head;ob.matrix_world=world
# Exact opposite profile keeps the working hand on the camera side.
cam((.54,5.2,2.6),(.54,.95,1.00),52)
initial=Vector((.44,-.13,.97));lift=Vector((.44,-.13,1.69));over=Vector((.10,-.44,1.64));contact=Vector((.10,-.44,1.55));fixed_lamp=Vector((.98,.95,rest_top))
lamps[0]['root'].rotation_euler=(0,0,math.pi)
def ease(t):t=max(0,min(1,t));return t*t*(3-2*t)
def path(points,cuts,p):
 for i,(lo,hi) in enumerate(zip(cuts,cuts[1:])):
  if p<=hi:return points[i].lerp(points[i+1],ease((p-lo)/(hi-lo)))
 return points[-1].copy()
def elbow_for(target,bend_pole):
 d=target-shoulder;length=d.length;assert abs(L1-L2)+1e-6<length<L1+L2-1e-6
 axis=d.normalized();a=(L1*L1-L2*L2+length*length)/(2*length);normal=bend_pole-axis*bend_pole.dot(axis);assert normal.length>.01;return shoulder+axis*a+normal.normalized()*math.sqrt(max(0,L1*L1-a*a))
def rod_pose(ob,a,b):
 # End the sleeve at the wrist rather than burying the mitten center.
 if ob is fore:b=b-(b-a).normalized()*.05
 d=b-a;ob.location=(a+b)/2;ob.rotation_euler=d.to_track_quat('Z','Y').to_euler();ob.scale=(1,1,d.length/depth[ob.name])
def separation(lo,hi,lo2,hi2):return max(max(lo[i]-hi2[i],lo2[i]-hi[i]) for i in range(3))
def pose(n):
 t=(n-1)/24;placing=t<=1.25
 if placing:target=path([initial,lift,over,contact],[0,.38,.78,1],min(1,t/1.25));release=0
 else:
  release=max(0,min(1,(t-1.28)/.55));target=path([contact,Vector((.26,-.35,1.60)),Vector((.43,-.28,1.28)),Vector((.30,-.20,1.05))],[0,.30,.72,1],release)
 bend_pole=pole.lerp(Vector((.8,-.3,-1)),ease((release-.4)/.6))
 elbow=elbow_for(target,bend_pole);rod_pose(upper,shoulder,elbow);rod_pose(fore,elbow,target);ball.location=elbow;hand.location=target
 head.rotation_euler.x=math.radians(8)*ease(min(1,t/.5));bpy.context.view_layer.update()
 world_hand=hand.matrix_world.translation
 lamps[0]['root'].location=world_hand-Vector((0,0,.55)) if placing else fixed_lamp
 lamp=lamps[0]['root'].location.copy();lamps[0]['spot'].rotation_euler=(lamps[0]['root'].rotation_euler.to_quaternion().inverted()@Vector((-.3,0,-1))).to_track_quat('-Z','Y').to_euler();bpy.context.view_layer.update()
 grip=lamps[0]['root'].matrix_world@Vector((0,0,.55));grip_error=(world_hand-grip).length
 # Conservative entire lamp/cell bounding box versus the handrail's enclosing box.
 lo=lamp+Vector((-.145,-.186,0));hi=lamp+Vector((.145,.186,.568));rail_lo=Vector((.835,-.735,.935));rail_hi=Vector((.925,2.655,1.025));rail_sep=separation(lo,hi,rail_lo,rail_hi);assert rail_sep>.004
 sole_error=max(abs(min((o.matrix_world@Vector(c)).z for c in o.bound_box)-.08) for o in rose['feet']);assert sole_error<1e-5
 length_error=max(abs((elbow-shoulder).length-L1),abs((target-elbow).length-L2));assert length_error<1e-5
 if placing:assert grip_error<1e-5 and lamp.z>=.499
 else:assert (lamp-fixed_lamp).length<1e-6
 if t>=1.25:assert abs(lamp.z-rest_top)<1e-5
 return {'seconds':t,'placing':placing,'release_progress':release,'lamp_base':list(lamp),'hand_to_handle_center':grip_error,'lamp_whole_box_to_rail_box_separation':rail_sep,'rest_top':rest_top,'lamp_base_above_rest':lamp.z-rest_top,'static_shoe_sole_error':sole_error,'upper_forearm_length_error':length_error,'source_lamp_marks':[l['marks'] for l in lamps],'independent_pool_powers':[l['light'].energy for l in lamps],'scope':'Fixed static feet, fixed arm lengths, grip coincidence before release and conservative lamp/rail boxes. No full-body swept collision, walking, fingers, scene/caption/audio continuity verdict.'}
checks={n:pose(n) for n in range(1,49)}
for n in range(1,49):
 if n in requested:render(n,pose(n),'native_lift_placement_release_diagnostic')
rows=[json.loads((out/'frames'/f'{n:05d}.json').read_text()) for n in range(1,49) if (out/'frames'/f'{n:05d}.json').exists()]
write(out/'placement-samples.json',{'inputs':inputs,'all48_numeric_poses_checked':True,'completed_motion_frames':[r['study_frame'] for r in rows],'all48_motion_frames_complete':len(rows)==48,'numeric_checks':checks,'raw_receipts':rows,'actual_visual_review_pending':True,'finished_story_exists':False,'publishable':False})
bpy.ops.wm.save_as_mainfile(filepath=str(out/'placement-study.blend'))
print(json.dumps({'source_sha256':source_hash,'native_motion_frames_existing':len(rows),'orientation_still_exists':(out/'frames/01001.png').exists(),'finished_story_exists':False,'publishable':False}),flush=True)
