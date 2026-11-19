"""Bounded notice/head-turn development in the existing eight-stone scene.

Reuses the completed stone scene's original geometry, restoring its empty-basket
and source-tray state. No new voice or final-story/publication claim.
"""
import argparse, hashlib, json, math, shutil, struct, sys
from pathlib import Path
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--stone-blend',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
p.add_argument('--width',type=int,choices=[360,720],default=720)
p.add_argument('--frames',type=int,nargs='+',default=[198,210,225,226,244,262])
p.add_argument('--all-motion',action='store_true')
p.add_argument('--check-only',action='store_true')
p.add_argument('--resume',action='store_true')
o=p.parse_args(args)
expected='0adb6d86642ceb6973beba1db77228841c987903aca7134755a56748811b6873'
assert hashlib.sha256(o.stone_blend.read_bytes()).hexdigest()==expected
source_hash=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
wanted=[] if o.check_only else list(range(198,263)) if o.all_motion else sorted(set(o.frames))
assert not wanted or (min(wanted)>=198 and max(wanted)<=262)
if o.output.exists() and any(o.output.iterdir()) and not o.resume:raise SystemExit('Existing output held; explicit identical-source resume required.')
o.output.mkdir(parents=True,exist_ok=True);(o.output/'frames').mkdir(exist_ok=True)
frozen=o.output/'frozen-notice-study.py'
if frozen.exists():assert hashlib.sha256(frozen.read_bytes()).hexdigest()==source_hash
elif frozen.resolve()!=Path(__file__).resolve():shutil.copyfile(Path(__file__),frozen)
manifest={'frozen_source':str(frozen.resolve()),'source_sha256':source_hash,'input_stone_blend_sha256':expected,'width':o.width,'height':o.width*16//9,'frame_numbers':wanted,'expected_frames':len(wanted),'samples':8,'scope':'notice/head-turn development, not full story'}
m=o.output/'render-manifest.json'
if m.exists():assert json.loads(m.read_text())==manifest,'Refuse mixed source/settings/cache'
else:m.write_text(json.dumps(manifest,indent=2)+'\n')
bpy.ops.wm.open_mainfile(filepath=str(o.stone_blend.resolve()))
S=bpy.context.scene;S.render.fps=24;S.cycles.samples=8;S.render.threads=2
S.render.resolution_x,S.render.resolution_y=o.width,o.width*16//9;S.render.resolution_percentage=100
hero=bpy.data.objects['Courier master'];gate=bpy.data.objects['Vertical gate lift root']
basket=bpy.data.objects['Separate counterweight basket root'];cart=bpy.data.objects['Free parcel cart, separate from counterweight']
rope=bpy.data.objects['Continuous original gate-to-basket rope'];camera=S.camera
tray=bpy.data.objects['Original raised loose-stone tray'];plinth=bpy.data.objects['Original solid tray support on landing']
rocks=sorted([a for a in S.objects if a.name.startswith('Original loose counterweight stone')],key=lambda a:a.name)
assert len(rocks)==8
for a in [hero,*hero.children_recursive]:
 a.animation_data_clear()
 if a.type=='EMPTY':a.rotation_mode='XYZ';a.rotation_euler=(0,0,0)
hero.location=(-.52,-.66,-.075);hero.rotation_euler=(0,0,math.pi-.4)
cart.location=(.30,-1.55,0);gate.location.z=0;basket.location.z=3.15
points=rope.data.splines[0].points;points[0].co.z=2.3;points[-1].co.z=3.15
zmin=min(v.co.z*rocks[0].scale.z for v in rocks[0].data.vertices)
groups=[[0,1,2],[3,4,5],[6,7]]
source_centers=[Vector((3.48,1.08,2.60-zmin+layer)) for layer in [.26,.13,0]]
offsets=[Vector((-.09,-.04,0)),Vector((.09,-.04,0)),Vector((0,.06,0))]
for g,ids in enumerate(groups):
 for j,n in enumerate(ids):rocks[n].location=source_centers[g]+offsets[j];rocks[n].hide_render=False
waiting=[bpy.data.objects['Waiting adult A'],bpy.data.objects['Waiting adult B']]
for actor,y,yaw in zip(waiting,[-3.7,-5.0],[.10,.16]):
 actor.location.y=y;next(a for a in actor.children if a.name.startswith('Expressive neck')).rotation_euler.z=yaw
bpy.context.view_layer.update()
legs={}
for side,name in [(-1,'Left hip'),(1,'Right hip')]:
 hip=next(a for a in hero.children if a.name==name);knee=next(a for a in hip.children if a.name.startswith('Knee'))
 feet=[a for a in knee.children if a.name.startswith(('Boot sole','Courier boot'))]
 ankle=bpy.data.objects.new('Notice planted ankle '+str(side),None);S.collection.objects.link(ankle);ankle.parent=knee;ankle.location=(0,0,-.4)
 bpy.context.view_layer.update()
 for a in feet:world=a.matrix_world.copy();a.parent=ankle;a.matrix_world=world
 legs[side]=(hip,knee,ankle,feet)
neck=next(a for a in hero.children if a.name.startswith('Expressive neck'))
mouth=[next(a for a in neck.children if a.name==name) for name in ['Mouth left','Mouth right']]
mouth_lengths=[max(v.co.z for v in a.data.vertices)-min(v.co.z for v in a.data.vertices) for a in mouth]
arms={}
for side in [-1,1]:
 shoulder=next(a for a in hero.children if a.name=='Shoulder '+str(side));elbow=next(a for a in shoulder.children if a.name.startswith('Elbow'));hand=next(a for a in elbow.children if a.name.startswith('Courier hand'));arms[side]=(shoulder,elbow,hand)
def smooth(q):
 q=max(0,min(1,q));return q*q*(3-2*q)
def solve(side, target):
    shoulder, elbow, hand = arms[side]
    target = Vector(target)
    bpy.context.view_layer.update()
    local = hero.matrix_world.inverted() @ target
    A = shoulder.location.copy()
    delta = local - A
    distance = delta.length
    l1, l2 = elbow.location.length, hand.location.length
    assert abs(l1 - l2) + .001 < distance < l1 + l2 - .001
    direction = delta.normalized()
    projection = (l1 * l1 - l2 * l2 + distance * distance) / (2 * distance)
    height = math.sqrt(max(0, l1 * l1 - projection * projection))
    preference = Vector((side, -.5, -.15))
    perpendicular = (preference - direction * preference.dot(direction)).normalized()
    E = A + direction * projection + perpendicular * height
    upper = elbow.location.normalized().rotation_difference((E - A).normalized())
    lower = hand.location.normalized().rotation_difference((local - E).normalized())
    shoulder.rotation_mode = elbow.rotation_mode = 'QUATERNION'
    shoulder.rotation_quaternion = upper
    elbow.rotation_quaternion = upper.inverted() @ lower
    bpy.context.view_layer.update()
    error = (hand.matrix_world.translation - target).length
    assert error < .0001
    return error


def solve_leg(side):
    hip, knee, ankle, feet = legs[side]
    target = Vector((-.52 - side * .145, -.66, .065))
    bpy.context.view_layer.update()
    local = hero.matrix_world.inverted() @ target
    A = hip.location.copy()
    delta = local - A
    distance = delta.length
    l1, l2 = knee.location.length, ankle.location.length
    assert abs(l1 - l2) + .0001 < distance < l1 + l2 - .0001, (side, distance)
    direction = delta.normalized()
    along = (l1*l1 - l2*l2 + distance*distance)/(2*distance)
    height = math.sqrt(max(0, l1*l1 - along*along))
    pref = Vector((0, -1, 0))
    perpendicular = (pref - direction * pref.dot(direction)).normalized()
    E = A + direction * along + perpendicular * height
    q1 = knee.location.normalized().rotation_difference((E-A).normalized())
    q2 = ankle.location.normalized().rotation_difference((local-E).normalized())
    hip.rotation_mode = knee.rotation_mode = ankle.rotation_mode = 'QUATERNION'
    hip.rotation_quaternion = q1
    knee.rotation_quaternion = q1.inverted() @ q2
    bpy.context.view_layer.update()
    ankle.rotation_quaternion = knee.matrix_world.to_quaternion().inverted() @ hero.matrix_world.to_quaternion()
    bpy.context.view_layer.update()
    error = (ankle.matrix_world.translation-target).length
    sole = next(a for a in feet if a.name.startswith('Boot sole'))
    sole_min = min((sole.matrix_world @ Vector(c)).z for c in sole.bound_box)
    assert error < .0001 and abs(sole_min) < .0001, (side,error,sole_min)
    return {'side':side,'ankle_world':list(ankle.matrix_world.translation),'target_error':error,'sole_min_z':sole_min}



def pose(frame):
 t=(frame-1)/24;q=smooth((frame-198)/30)
 hero.location=(-.52,-.66,-.075);hero.rotation_euler.z=math.pi-.4
 feet=[solve_leg(side) for side in [-1,1]]
 errors={str(side):solve(side,hero.matrix_world@Vector((side*.34,-.12,.78))) for side in [-1,1]}
 bpy.context.view_layer.update()
 aim=Vector((2.70,0,2.88));head_origin=neck.matrix_world.translation
 delta=aim-head_origin
 final_yaw=math.atan2(delta.x,-delta.y)-hero.rotation_euler.z
 final_pitch=-math.atan2(delta.z,math.hypot(delta.x,delta.y))
 initial_pitch=.035*math.sin((196/24)*2)+.1
 neck.rotation_mode='XYZ';neck.rotation_euler=(initial_pitch*(1-q)+final_pitch*q,0,-.5*(1-q)+final_yaw*q)
 concern=1-q
 center=Vector((0,-.199,.137+.010*concern));corners=[Vector((-.059,-.188,.137-.017*concern)),Vector((.059,-.188,.137-.017*concern))]
 for ob,length,(first,last) in zip(mouth,mouth_lengths,[(corners[0],center),(center,corners[1])]):
  ob.location=(first+last)/2;ob.rotation_euler=(last-first).to_track_quat('Z','Y').to_euler();ob.scale.z=(last-first).length/length
 for side in [-1,1]:next(a for a in neck.children if a.name=='Eyebrow '+str(side)).rotation_euler.y=side*(.10-.28*concern)
 bpy.context.view_layer.update()
 actual_forward=neck.matrix_world.to_quaternion()@Vector((0,-1,0));gaze_dot=actual_forward.normalized().dot(delta.normalized())
 if q==1:assert gaze_dot>.9999,(frame,gaze_dot)
 assert all(not a.hide_render for a in rocks)
 assert all(a.location.z>2.6 for a in rocks)
 assert gate.location.z==0 and abs(basket.location.z-3.15)<.0001
 return {'frame':frame,'seconds':t,'shot':0 if frame<226 else 1,'hero_location':list(hero.location),'hero_yaw':hero.rotation_euler.z,'neck_euler':list(neck.rotation_euler),'head_turn_fraction':q,'gaze_direction_dot_basket_target':gaze_dot,'hand_errors':errors,'feet':feet,'gate_lift':0,'basket_attachment_z':3.15,'rope_polyline_length':sum((a.co.xyz-b.co.xyz).length for a,b in zip(points,points[1:])),'source_stones':[{'id':n,'center_world':list(a.location),'hide_render':a.hide_render} for n,a in enumerate(rocks)]}
CAMERAS=[((1.8,-.65,2.15),(-.52,-.66,1.55),45),((8,-6,5.3),(1.0,.15,2.65),40)]
def view(shot,lenses=None):
 location,target,lens=CAMERAS[shot];camera.location=location;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.lens=lenses[shot] if lenses else lens;bpy.context.view_layer.update()
records=[];extents=[0,0]
for frame in range(198,263):
 r=pose(frame);records.append(r);shot=r['shot'];view(shot)
 objects=[a for a in neck.children_recursive if a.type=='MESH' and not a.hide_render] if shot==0 else [a for actor in [hero,gate,basket] for a in actor.children_recursive if a.type=='MESH' and not a.hide_render]+[rope,tray,plinth]+rocks
 projected=[world_to_camera_view(S,camera,a.matrix_world@Vector(c)) for a in objects for c in a.bound_box]
 assert all(a.z>0 for a in projected)
 extents[shot]=max(extents[shot],max(max(abs(a.x-.5),abs(a.y-.5)) for a in projected))
lenses=[row[2]*min(1,.42/extents[i]) for i,row in enumerate(CAMERAS)]
assert max(r['rope_polyline_length'] for r in records)-min(r['rope_polyline_length'] for r in records)<.00001
assert records[0]['hero_location']==records[-1]['hero_location']
def complete_png(path):
 if not path.exists() or path.stat().st_size<36:return False
 with path.open('rb') as f:h=f.read(24);f.seek(-12,2);tail=f.read()
 return h[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>II',h[16:24])==(o.width,o.width*16//9) and tail==b'\x00\x00\x00\x00IEND\xaeB`\x82'
for frame in wanted:
 pose(frame);view(records[frame-198]['shot'],lenses);path=o.output/'frames'/f'{frame:05d}.png';receipt=path.with_suffix('.json')
 if complete_png(path) and receipt.exists():
  old=json.loads(receipt.read_text());actual=hashlib.sha256(path.read_bytes()).hexdigest();assert old['source_sha256']==source_hash and old['frame']==frame and old['input_stone_blend_sha256']==expected and old['raw_image_sha256']==actual
 else:
  if path.exists():raise SystemExit('Unverified frame held; inspect before recovery.')
  S.render.filepath=str(path);bpy.ops.render.render(write_still=True);actual=hashlib.sha256(path.read_bytes()).hexdigest();receipt.write_text(json.dumps({'frame':frame,'source_sha256':source_hash,'input_stone_blend_sha256':expected,'raw_image_sha256':actual},indent=2)+'\n')
 records[frame-198]['raw_image_sha256']=actual
assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==source_hash
report={'id':'counterweight-gate','source_sha256':source_hash,'input_stone_blend_sha256':expected,'scope':'notice/head-turn development only','story_frames':[198,262],'fps':24,'frames':65,'rendered_frame_numbers':wanted,'dimensions':[o.width,o.width*16//9],'samples':8,'all65_pose_checks_passed':True,'shot_lenses_mm':lenses,'cut_boundaries':[[225,226]],'persistent_stone_objects':8,'same_raised_tray_geometry_as_completed_stone_test':True,'records':records,'visual_inspection_pending':True,'full_story_animation':False,'publishable':False}
(o.output/'notice-study.json').write_text(json.dumps(report,indent=2)+'\n');bpy.ops.wm.save_as_mainfile(filepath=str((o.output/'notice-study.blend').resolve()))
