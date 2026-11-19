"""Bounded cart passage and same-cast walking payoff, frames439..578.

Reuses original stone-scene geometry and the reviewed planted-foot solver.
The return cut elides the landing-to-cart route. No new voice or full-film claim.
"""
import argparse,hashlib,json,math,shutil,struct,sys
from pathlib import Path
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Euler,Quaternion,Vector
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--stone-blend',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
p.add_argument('--width',type=int,choices=[360,720],default=720)
p.add_argument('--frames',type=int,nargs='+',default=[439,451,478,498,499,526,550,578])
p.add_argument('--all-motion',action='store_true');p.add_argument('--check-only',action='store_true');p.add_argument('--resume',action='store_true');o=p.parse_args(args)
expected='0adb6d86642ceb6973beba1db77228841c987903aca7134755a56748811b6873'
assert hashlib.sha256(o.stone_blend.read_bytes()).hexdigest()==expected
root=next(a for a in Path(__file__).resolve().parents if (a/'AGENTS.md').exists())
plan_path=root/'assets/stories/counterweight-gate/action-plan-v2.json';plan_hash=hashlib.sha256(plan_path.read_bytes()).hexdigest()
assert plan_hash=='e3f7aaffcfffd92bcf1cf9b57d001898b98b5573bc1e45e5abf78e09e49de7ce'
actions=json.loads(plan_path.read_text())['actions']
source_hash=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
wanted=[] if o.check_only else list(range(439,579)) if o.all_motion else sorted(set(o.frames));assert not wanted or min(wanted)>=439 and max(wanted)<=578
if o.output.exists() and any(o.output.iterdir()) and not o.resume:raise SystemExit('Existing output held. Explicit identical-source resume required.')
o.output.mkdir(parents=True,exist_ok=True);(o.output/'frames').mkdir(exist_ok=True);frozen=o.output/'frozen-passage-study.py'
if frozen.exists():assert hashlib.sha256(frozen.read_bytes()).hexdigest()==source_hash
elif frozen.resolve()!=Path(__file__).resolve():shutil.copyfile(Path(__file__),frozen)
manifest={'frozen_source':str(frozen.resolve()),'source_sha256':source_hash,'input_stone_blend_sha256':expected,'width':o.width,'height':o.width*16//9,'frame_numbers':wanted,'expected_frames':len(wanted),'samples':8,'scope':'cart passage and line development, not full story'}
m=o.output/'render-manifest.json'
if m.exists():assert json.loads(m.read_text())==manifest,'Refuse mixed source/settings/cache'
else:m.write_text(json.dumps(manifest,indent=2)+'\n')
bpy.ops.wm.open_mainfile(filepath=str(o.stone_blend.resolve()))
S=bpy.context.scene;S.render.fps=24;S.cycles.samples=8;S.render.threads=2
S.render.resolution_x,S.render.resolution_y=o.width,o.width*16//9;S.render.resolution_percentage=100
hero=bpy.data.objects['Courier master'];waiting=[bpy.data.objects['Waiting adult A'],bpy.data.objects['Waiting adult B']]
cart=bpy.data.objects['Free parcel cart, separate from counterweight'];gate=bpy.data.objects['Vertical gate lift root'];basket=bpy.data.objects['Separate counterweight basket root'];rope=bpy.data.objects['Continuous original gate-to-basket rope'];camera=S.camera
assert abs(gate.location.z-2.2)<.0001 and abs(basket.location.z-.95)<.0001
rocks=[a for a in S.objects if a.name.startswith('Original loose counterweight stone')];assert len(rocks)==8 and all(not a.hide_render for a in rocks)
stone_positions=[list(a.location) for a in rocks]
actor_specs=[(hero,.30,-2.55,3.25,4),(waiting[0],-.20,-3.7,5.25,6),(waiting[1],.20,-5.0,5.65,6)]
parts=[]
for index,(actor,x,y,total,cycles) in enumerate(actor_specs):
 for a in [actor,*actor.children_recursive]:
  a.animation_data_clear()
  if a.type=='EMPTY':a.rotation_mode='XYZ';a.rotation_euler=(0,0,0)
 actor.location=(x,y,0);actor.rotation_euler=(0,0,math.pi);bpy.context.view_layer.update()
 soles=[a for a in actor.children_recursive if a.name.startswith('Boot sole')]
 actor.location.z-=min((a.matrix_world@Vector(c)).z for a in soles for c in a.bound_box);bpy.context.view_layer.update()
 base_z=actor.location.z;scale=actor.scale.x;legs={};arms={}
 for side,name in [(-1,'Left hip'),(1,'Right hip')]:
  hip=next(a for a in actor.children if a.name.startswith(name));knee=next(a for a in hip.children if a.name.startswith('Knee'))
  feet=[a for a in knee.children if a.name.startswith(('Boot sole','Courier boot'))]
  ankle=bpy.data.objects.new('Passage planted ankle '+str(index)+' '+str(side),None);S.collection.objects.link(ankle);ankle.parent=knee;ankle.location=(0,0,-.4);bpy.context.view_layer.update()
  for a in feet:world=a.matrix_world.copy();a.parent=ankle;a.matrix_world=world
  bpy.context.view_layer.update();legs[side]={'hip':hip,'knee':knee,'ankle':ankle,'feet':feet,'initial_world':ankle.matrix_world.translation.copy()}
  shoulder=next(a for a in actor.children if a.name.startswith('Shoulder '+str(side)));elbow=next(a for a in shoulder.children if a.name.startswith('Elbow'));hand=next(a for a in elbow.children if a.name.startswith('Courier hand'));arms[side]=(shoulder,elbow,hand)
 neck=next(a for a in actor.children if a.name.startswith('Expressive neck'))
 parts.append({'index':index,'actor':actor,'start_x':x,'start_y':y,'base_z':base_z,'scale':scale,'total':total,'cycles':cycles,'stride':total/cycles,'legs':legs,'arms':arms,'neck':neck})
wheels=[a for a in cart.children if a.name.startswith('Cart wheel')]
def smooth(q):
 q=max(0,min(1,q));return q*q*(3-2*q)
def solve_chain(actor, first, second, endpoint, target, preference):
    target = Vector(target)
    bpy.context.view_layer.update()
    local = actor.matrix_world.inverted() @ target
    origin = first.location.copy()
    delta = local - origin
    distance = delta.length
    l1, l2 = second.location.length, endpoint.location.length
    assert abs(l1 - l2) + .00001 < distance <= l1 + l2 + .00001, (actor.name, first.name, distance, l1, l2, list(actor.location), list(target))
    direction = delta.normalized()
    along = (l1 * l1 - l2 * l2 + distance * distance) / (2 * distance)
    height = math.sqrt(max(0, l1 * l1 - along * along))
    preference = Vector(preference)
    perpendicular = (preference - direction * preference.dot(direction)).normalized()
    bend = origin + direction * along + perpendicular * height
    q1 = second.location.normalized().rotation_difference((bend - origin).normalized())
    q2 = endpoint.location.normalized().rotation_difference((local - bend).normalized())
    first.rotation_mode = second.rotation_mode = 'QUATERNION'
    first.rotation_quaternion = q1
    second.rotation_quaternion = q1.inverted() @ q2
    bpy.context.view_layer.update()
    error = (endpoint.matrix_world.translation - target).length
    assert error < .0001, error
    return error


def path_x(p,d):return p['start_x'] if p['index']==0 else p['start_x']+(-.40-p['start_x'])*smooth(max(0,d)/2)
def foot_plant(p,side,cycle,offset):
 stride=p['stride'];distance=stride*(cycle-offset)+stride*.60/2
 initial=p['legs'][side]['initial_world']
 return Vector((path_x(p,distance)+initial.x-p['start_x'],p['start_y']+distance,initial.z))
def move_actor(p,distance,t,previous):
 actor=p['actor'];stride=p['stride'];phase_distance=distance/stride
 motion=smooth(distance/(stride*.3));bob=.01*p['scale']*math.cos(phase_distance*math.tau*2)
 # A supported, slightly bent ready-step pose is present from this shot's cut.
 # Reuse the reviewed gait's forward/backward stance offsets; neutral-foot
 # starts held too long were unreachable and were rejected before rendering.
 actor.location=(path_x(p,distance),p['start_y']+distance,p['base_z']-.08*p['scale']+bob)
 feet=[]
 for side,offset in [(-1,0),(1,.5)]:
  phase_abs=phase_distance+offset;cycle=math.floor(phase_abs+1e-8);phase=max(0,phase_abs-cycle);stance=phase<=.60
  start=foot_plant(p,side,cycle,offset);finish=foot_plant(p,side,cycle+1,offset)
  if stance:target=start;lift=0
  else:
   q=(phase-.60)/.40;target=start.lerp(finish,smooth(q));lift=.12*p['scale']*math.sin(math.pi*q);target.z+=lift
  leg=p['legs'][side];hip,knee,ankle=leg['hip'],leg['knee'],leg['ankle'];error=solve_chain(actor,hip,knee,ankle,target,(0,-1,0))
  ankle.rotation_mode='QUATERNION';ankle.rotation_quaternion=knee.matrix_world.to_quaternion().inverted()@actor.matrix_world.to_quaternion();bpy.context.view_layer.update()
  sole=next(a for a in leg['feet'] if a.name.startswith('Boot sole'));sole_min=min((sole.matrix_world@Vector(c)).z for c in sole.bound_box)
  assert abs(sole_min-lift)<.0001,(p['index'],side,sole_min,lift)
  drift=0;old=previous.get((p['index'],side))
  if stance and old and old['stance'] and old['cycle']==cycle:
   drift=(ankle.matrix_world.translation-Vector(old['ankle_world'])).length;assert drift<.0001,drift
  f={'side':side,'cycle':cycle,'phase':phase,'stance':stance,'sole_min_z':sole_min,'lift':lift,'ankle_world':list(ankle.matrix_world.translation),'target_error':error,'same_stance_world_drift':drift};feet.append(f);previous[(p['index'],side)]=f
 hands=[]
 for side in [-1,1]:
  if p['index']==0:target=Vector((.30-side*.25,cart.location.y-.55,1.02))
  else:
   swing=.10*math.sin(phase_distance*math.tau+side*math.pi/2)*motion
   target=actor.matrix_world@Vector((side*.34,-.12+swing,.78))
  hands.append(solve_chain(actor,*p['arms'][side],target,(side,-.5,-.15)))
 p['neck'].rotation_euler=(.01,0,-.08 if p['index']==0 else 0)
 return {'cast_index':p['index'],'actor_name':actor.name,'root_world':list(actor.location),'distance':distance,'feet':feet,'hand_center_errors':hands}
def pose(frame,previous):
 t=(frame-1)/24;cart_distance=3.25*smooth((t-actions['cart_roll'][0])/(actions['cart_roll'][1]-actions['cart_roll'][0]))
 cart.location=(.30,-1.55+cart_distance,0)
 for wheel in wheels:wheel.rotation_mode='QUATERNION';wheel.rotation_quaternion=Euler((0,math.pi/2,0)).to_quaternion()@Quaternion(Vector((0,0,1)),-cart_distance/.16)
 q=smooth((t-actions['queue_start'])/(24.083333333333332-actions['queue_start']))
 actors=[move_actor(p,cart_distance if p['index']==0 else p['total']*q,t,previous) for p in parts]
 assert any(f['stance'] for a in actors for f in a['feet'])
 assert all(any(f['stance'] for f in a['feet']) for a in actors)
 assert abs(gate.location.z-2.2)<.0001 and abs(basket.location.z-.95)<.0001
 assert [list(a.location) for a in rocks]==stone_positions and all(not a.hide_render for a in rocks)
 if abs(cart.location.y)<.6:assert abs(cart.location.x)+.38<1.05
 return {'frame':frame,'seconds':t,'shot':0 if frame<499 else 1,'cart_travel':cart_distance,'cart_world':list(cart.location),'wheel_rotation_radians':-cart_distance/.16,'queue_progress':q,'actors':actors,'gate_lift':float(gate.location.z),'basket_attachment_z':float(basket.location.z),'rope_polyline_length':sum((a.co.xyz-b.co.xyz).length for a,b in zip(rope.data.splines[0].points,rope.data.splines[0].points[1:]))}
def view(r,lenses=None):
 if r['shot']==0:location=(1.05,r['actors'][0]['root_world'][1]-3.60,2.35);target=(.30,r['actors'][0]['root_world'][1]+.55,1.0);lens=34
 else:location=(-.85,4.0,2.6);target=(-.1,-.65,1.0);lens=34
 camera.location=location;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.lens=lenses[r['shot']] if lenses else lens;bpy.context.view_layer.update()
records=[];previous={};extents=[0,0]
for frame in range(439,579):
 r=pose(frame,previous);records.append(r);view(r)
 actors=[hero,cart] if r['shot']==0 else [hero,cart,*waiting]
 projected=[world_to_camera_view(S,camera,a.matrix_world@Vector(c)) for actor in actors for a in actor.children_recursive if a.type=='MESH' and not a.hide_render for c in a.bound_box]
 assert all(v.z>0 for v in projected);extents[r['shot']]=max(extents[r['shot']],max(max(abs(v.x-.5),abs(v.y-.5)) for v in projected))
lenses=[34*min(1,.43/e) for e in extents]
assert records[0]['cart_travel']==0 and abs(records[-1]['cart_travel']-3.25)<.0001
assert records[-1]['actors'][0]['root_world'][1]>.6
assert all(a['distance']>0 for a in records[-1]['actors'][1:])
assert max(r['rope_polyline_length'] for r in records)-min(r['rope_polyline_length'] for r in records)<.00001
def complete_png(path):
 if not path.exists() or path.stat().st_size<36:return False
 with path.open('rb') as f:h=f.read(24);f.seek(-12,2);tail=f.read()
 return h[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>II',h[16:24])==(o.width,o.width*16//9) and tail==b'\x00\x00\x00\x00IEND\xaeB`\x82'
for frame in wanted:
 r=pose(frame,{});view(r,lenses);path=o.output/'frames'/f'{frame:05d}.png';receipt=path.with_suffix('.json')
 if complete_png(path) and receipt.exists():
  old=json.loads(receipt.read_text());actual=hashlib.sha256(path.read_bytes()).hexdigest();assert old['source_sha256']==source_hash and old['frame']==frame and old['input_stone_blend_sha256']==expected and old['raw_image_sha256']==actual
 else:
  if path.exists():raise SystemExit('Unverified frame held; inspect before recovery.')
  S.render.filepath=str(path);bpy.ops.render.render(write_still=True);actual=hashlib.sha256(path.read_bytes()).hexdigest();receipt.write_text(json.dumps({'frame':frame,'source_sha256':source_hash,'input_stone_blend_sha256':expected,'raw_image_sha256':actual},indent=2)+'\n')
 records[frame-439]['raw_image_sha256']=actual
assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==source_hash
report={'id':'counterweight-gate','source_sha256':source_hash,'input_stone_blend_sha256':expected,'action_plan_sha256':plan_hash,'scope':'cart passage and same-cast walking development only','story_frames':[439,578],'fps':24,'frames':140,'rendered_frame_numbers':wanted,'dimensions':[o.width,o.width*16//9],'samples':8,'all140_pose_checks_passed':True,'shot_lenses_mm':lenses,'cut_boundaries':[[498,499]],'same_waiting_cast_moves':True,'records':records,'checks_scope':'Sampled foot/mitten endpoints, stance world locks, complementary loaded mechanism state and wheel distance; not full-body swept collision, natural gait or physics certification.','editorial_return_cut':'Elides travel back from the landing to the cart. No claim of an unbroken journey.','visual_inspection_pending':True,'full_story_animation':False,'publishable':False}
(o.output/'passage-study.json').write_text(json.dumps(report,indent=2)+'\n');bpy.ops.wm.save_as_mainfile(filepath=str((o.output/'passage-study.blend').resolve()))
