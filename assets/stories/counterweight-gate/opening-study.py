"""Integrated first paragraph: two attempts and waiting cast, not full story.

Use the reviewed original acting blend. No new narration or audio is generated. Existing source/receipt checks support explicit recovery of partial task-owned renders.
"""
import argparse
import hashlib
import json
import math
import shutil
import sys
from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--acting-blend', required=True, type=Path)
p.add_argument('--output', required=True, type=Path)
p.add_argument('--width', type=int, choices=[360, 720], default=720)
p.add_argument('--frames', type=int, nargs='+', default=[92, 95, 110, 135, 165])
p.add_argument('--all-motion', action='store_true')
p.add_argument('--resume', action='store_true')
o = p.parse_args(argv)
expected = '7691e1f0daed54ea5addc4eb644cd18fcd8dc1e90fa9b132e646968d84660b0f'
assert hashlib.sha256(o.acting_blend.read_bytes()).hexdigest() == expected
wanted = list(range(1, 198)) if o.all_motion else sorted(set(o.frames))
assert wanted and min(wanted) >= 1 and max(wanted) <= 197
root = next(a for a in Path(__file__).resolve().parents if (a / 'AGENTS.md').exists())
plan_path = root / 'assets/stories/counterweight-gate/action-plan.json'
plan = json.loads(plan_path.read_text())
release, stop = plan['actions']['first_gate_release'], plan['actions']['first_gate_stop']
assert release == 2.65 and stop == 3.125
second_release, second_stop = plan['actions']['second_gate_release'], plan['actions']['second_gate_stop']
assert second_release == 5.1 and second_stop == 134 / 24
source_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
if o.output.exists() and any(o.output.iterdir()) and not o.resume:
    raise SystemExit('Existing output is held; inspect it and use explicit resume only for this same frozen source.')
o.output.mkdir(parents=True, exist_ok=True)
(o.output / 'frames').mkdir(exist_ok=True)
frozen = o.output / 'frozen-opening-study.py'
if frozen.exists():
    assert hashlib.sha256(frozen.read_bytes()).hexdigest() == source_hash
elif frozen.resolve() != Path(__file__).resolve():
    shutil.copyfile(Path(__file__), frozen)
manifest_path = o.output / 'render-manifest.json'
manifest = {'frozen_source': str(frozen.resolve()), 'source_sha256': source_hash,
            'input_acting_blend_sha256': expected, 'width': o.width, 'height': o.width * 16 // 9,
            'frame_numbers': wanted, 'expected_frames': len(wanted), 'samples': 8,
            'scope': 'first paragraph development; not a full finished story'}
if manifest_path.exists():
    prior = json.loads(manifest_path.read_text())
    assert prior == manifest, 'Refuse mixed source/settings/cache.'
else:
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
bpy.ops.wm.open_mainfile(filepath=str(o.acting_blend.resolve()))
S = bpy.context.scene
S.cycles.samples = 8
S.render.threads = 2
S.render.fps = 24
S.render.resolution_x, S.render.resolution_y = o.width, o.width * 16 // 9
S.render.resolution_percentage = 100
hero = bpy.data.objects['Courier master']
gate = bpy.data.objects['Vertical gate lift root']
basket = bpy.data.objects['Separate counterweight basket root']
cart = bpy.data.objects['Free parcel cart, separate from counterweight']
rope = bpy.data.objects['Continuous original gate-to-basket rope']
camera = S.camera
for a in [hero, *hero.children_recursive]:
    a.animation_data_clear()
    if a.type == 'EMPTY':
        a.rotation_mode = 'XYZ'
        a.rotation_euler = (0, 0, 0)
hero.location, hero.rotation_euler = (-.52, -.66, -.065), (0, 0, math.pi)
cart.location = (.45, -1.50, 0)
for a in basket.children:
    if a.name.startswith('Original loose counterweight stone'):
        a.hide_render = True
for a, y in zip([bpy.data.objects['Waiting adult A'], bpy.data.objects['Waiting adult B']], [-3.7, -5.0]):
    a.location.y = y
# Independent ankle pivots preserve existing boots while feet remain planted.
bpy.context.view_layer.update()
legs = {}
for side, name in [(-1, 'Left hip'), (1, 'Right hip')]:
    hip = next(a for a in hero.children if a.name == name)
    knee = next(a for a in hip.children if a.name.startswith('Knee'))
    feet = [a for a in knee.children if a.name.startswith(('Boot sole', 'Courier boot'))]
    ankle = bpy.data.objects.new('Opening planted ankle ' + str(side), None)
    S.collection.objects.link(ankle)
    ankle.parent = knee
    ankle.location = (0, 0, -.4)
    bpy.context.view_layer.update()
    for a in feet:
        world = a.matrix_world.copy()
        a.parent = ankle
        a.matrix_world = world
    legs[side] = (hip, knee, ankle, feet)
waiting = [bpy.data.objects['Waiting adult A'], bpy.data.objects['Waiting adult B']]
neck = next(a for a in hero.children if a.name.startswith('Expressive neck'))
mouth = [next(a for a in neck.children if a.name == name) for name in ['Mouth left', 'Mouth right']]
mouth_lengths = [max(v.co.z for v in a.data.vertices) - min(v.co.z for v in a.data.vertices) for a in mouth]
arms = {}
for side in [-1, 1]:
    shoulder = next(a for a in hero.children if a.name == 'Shoulder ' + str(side))
    elbow = next(a for a in shoulder.children if a.name.startswith('Elbow'))
    hand = next(a for a in elbow.children if a.name.startswith('Courier hand'))
    arms[side] = (shoulder, elbow, hand)


def smooth(a, b, t):
    q = max(0, min(1, (t - a) / (b - a)))
    return q * q * (3 - 2 * q)


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
    t = (frame-1)/24
    reaction = smooth(5.8, 6.5, t)
    crouch = 0
    if t < 3.25:
        fall = max(0,min(1,(t-release)/(stop-release)))
        lift = 1.1*(1-fall*fall)
    elif t < 3.95:
        lift = 0
        crouch = smooth(3.25,3.95,t)
    elif t < 4.70:
        rise = smooth(3.95,4.70,t)
        lift = 1.1*rise
        crouch = 1-rise
    else:
        fall = max(0,min(1,(t-second_release)/(second_stop-second_release)))
        lift = 1.1*(1-fall*fall)
    hero.location = (-.52, -.66 + .11*crouch, -.075 - .425*crouch)
    hero.rotation_euler.z = math.pi - .4*reaction
    cart.location = (.30,-1.55,0)  # one common staging position across opening and cart study
    gate.location.z = lift
    basket.location.z = 3.15-lift
    points = rope.data.splines[0].points
    points[0].co.z,points[-1].co.z = 2.3+lift,3.15-lift
    feet = [solve_leg(side) for side in [-1,1]]
    targets = {}
    for side,x in [(-1,-.27),(1,-.77)]:
        grip = Vector((x,-.22,.39+lift))
        high_grip = Vector((x,-.22,1.49))
        free = Vector((0,-1.0,1.05)) if side==-1 else Vector((-.77,-.95,1.05))
        if t < 3.25:
            departure = smooth(1.10,2.05,t) if side==-1 else smooth(release,release+.20,t)
            target = high_grip.lerp(free,departure)
        elif t < 3.95:
            target = free.lerp(Vector((x,-.22,.39)),crouch)
        elif t < 4.70:
            target = grip
        else:
            departure = smooth(4.80,second_release,t) if side==-1 else smooth(second_release,second_release+.20,t)
            target = high_grip.lerp(free,departure)
        if reaction:
            bpy.context.view_layer.update()
            relaxed = hero.matrix_world @ Vector((side*.34,-.12,.78))
            target = target.lerp(relaxed,reaction)
        targets[side] = {'target':list(target),'error':solve(side,target)}
    concern = smooth(stop,3.50,t) if t<3.8 else smooth(second_stop,5.80,t)
    neck.rotation_euler = (.035*math.sin(t*2)+.10*concern,0,(1.15*(1-reaction)-.5*reaction))
    center = Vector((0,-.199,.137+.010*concern))
    corners = [Vector((-.059,-.188,.137-.017*concern)),Vector((.059,-.188,.137-.017*concern))]
    for ob,length,(first,last) in zip(mouth,mouth_lengths,[(corners[0],center),(center,corners[1])]):
        ob.location=(first+last)/2
        ob.rotation_euler=(last-first).to_track_quat('Z','Y').to_euler()
        ob.scale.z=(last-first).length/length
    for side in [-1,1]:
        next(a for a in neck.children if a.name=='Eyebrow '+str(side)).rotation_euler.y=side*(.10-.28*concern)
    for actor,yaw in zip(waiting,[.10,.16]):
        next(a for a in actor.children if a.name.startswith('Expressive neck')).rotation_euler.z=yaw*reaction
    bpy.context.view_layer.update()
    rope_length=sum((a.co.xyz-b.co.xyz).length for a,b in zip(points,points[1:]))
    return {'frame':frame,'seconds':t,'shot':0 if frame<92 else 1 if frame<140 else 2,
            'gate_lift':lift,'basket_attachment_z':float(basket.location.z),'rope_polyline_length':rope_length,
            'hero_location':list(hero.location),'hero_yaw':hero.rotation_euler.z,'crouch_fraction':crouch,
            'hand_targets':targets,'feet':feet,'concern_expression_fraction':concern}


CAMERAS=[((-3.60,-4.20,2.70),(0,-.90,1.15),34),
         ((-3.25,-1.90,2.20),(-.52,-.3,.95),38),
         ((1.40,-1.0,2.15),(-.15,-3.9,1.25),40)]
def view(shot,lenses=None):
    location,target,lens=CAMERAS[shot]
    camera.location=location
    camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.lens=lenses[shot] if lenses else lens
    bpy.context.view_layer.update()


# Each shot has one fixed lens fitted over that entire shot's subject motion.
extents=[0,0,0]
records=[]
for frame in range(1,198):
    record=pose(frame);records.append(record);shot=record['shot'];view(shot)
    actors=[hero,cart] if shot==0 else [hero] if shot==1 else waiting
    projected=[world_to_camera_view(S,camera,a.matrix_world@Vector(c)) for actor in actors
               for a in actor.children_recursive if a.type=='MESH' and not a.hide_render for c in a.bound_box]
    assert all(v.z>0 for v in projected)
    extents[shot]=max(extents[shot],max(max(abs(v.x-.5),abs(v.y-.5)) for v in projected))
lenses=[row[2]*min(1,.42/extents[i]) for i,row in enumerate(CAMERAS)]
assert max(r['rope_polyline_length'] for r in records)-min(r['rope_polyline_length'] for r in records)<.00001
assert abs(records[75]['gate_lift'])<.00001 and abs(records[134]['gate_lift'])<.00001
assert records[94]['crouch_fraction']>.99

def complete_png(path):
    import struct
    if not path.exists() or path.stat().st_size<36:return False
    with path.open('rb') as stream:
        header=stream.read(24);stream.seek(-12,2);tail=stream.read()
    return header[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>II',header[16:24])==(o.width,o.width*16//9) and tail==b'\x00\x00\x00\x00IEND\xaeB`\x82'

for frame in wanted:
    pose(frame);view(records[frame-1]['shot'],lenses)
    path=o.output/'frames'/f'{frame:05d}.png';receipt=path.with_suffix('.json')
    if complete_png(path) and receipt.exists():
        old=json.loads(receipt.read_text());actual=hashlib.sha256(path.read_bytes()).hexdigest()
        assert old['source_sha256']==source_hash and old['input_acting_blend_sha256']==expected and old['frame']==frame and old['raw_image_sha256']==actual
        records[frame-1]['raw_image_sha256']=actual
        continue
    if path.exists():
        held=o.output/'unverified';held.mkdir(exist_ok=True)
        old_sha=hashlib.sha256(path.read_bytes()).hexdigest()
        path.replace(held/f'{frame:05d}-{old_sha[:16]}.png')
    S.render.filepath=str(path);bpy.ops.render.render(write_still=True)
    actual=hashlib.sha256(path.read_bytes()).hexdigest();records[frame-1]['raw_image_sha256']=actual
    receipt.write_text(json.dumps({'frame':frame,'source_sha256':source_hash,'input_acting_blend_sha256':expected,'raw_image_sha256':actual},indent=2)+'\n')
assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==source_hash
report={'id':'counterweight-gate','status':'first_paragraph_opening_development_not_full_story','source_sha256':source_hash,
        'input_acting_blend_sha256':expected,'action_plan_sha256':hashlib.sha256(plan_path.read_bytes()).hexdigest(),
        'fps':24,'test_frames':197,'duration_seconds':197/24,'expected_audio_samples':394000,
        'rendered_frame_numbers':wanted,'dimensions':[o.width,o.width*16//9],'samples':8,
        'all_197_kinematic_pose_invariants_checked':True,'shot_lenses_mm':lenses,'records':records,
        'gate_stop_frames':[76,135],'cut_boundaries':[[91,92],[139,140]],
        'second_attempt_animated':True,'waiting_cast_reaction_shown':True,'queue_walk_animated':False,
        'full_story_animation_started':False,'visual_inspection_pending':True,'publishable':False}
(o.output/'opening-study.json').write_text(json.dumps(report,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str((o.output/'opening-study.blend').resolve()))
