"""Bounded original stair-contact development, story frames263..318 only.

Reuse the reviewed acting assets and existing cue clock. This is a step-to climb
of the three authored treads, not a full movie, stone deposit or physics model.
"""
import argparse
import hashlib
import json
import math
import shutil
import struct
import sys
from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--acting-blend', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--width', type=int, choices=[360, 720], default=720)
p.add_argument('--frames', type=int, nargs='+', default=[263, 279, 280, 292, 304, 310, 318])
p.add_argument('--all-motion', action='store_true')
p.add_argument('--check-only', action='store_true')
p.add_argument('--resume', action='store_true')
o = p.parse_args(argv)
root = next(a for a in Path(__file__).resolve().parents if (a / 'AGENTS.md').exists())
expected = '7691e1f0daed54ea5addc4eb644cd18fcd8dc1e90fa9b132e646968d84660b0f'
assert hashlib.sha256(o.acting_blend.read_bytes()).hexdigest() == expected
plan_path = root / 'assets/stories/counterweight-gate/action-plan.json'
plan_hash = hashlib.sha256(plan_path.read_bytes()).hexdigest()
assert plan_hash == '20a9a83af01b0b50d1dee276cc8e16e680aa7597879ad56a1956d0ff87c4c1ce'
plan = json.loads(plan_path.read_text())
assert plan['actions']['stair_foot_plants'] == [11.625, 12.125, 12.625]
wanted = [] if o.check_only else list(range(263, 319)) if o.all_motion else sorted(set(o.frames))
assert not wanted or (min(wanted) >= 263 and max(wanted) <= 318)
source_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
if o.output.exists() and any(o.output.iterdir()) and not o.resume:
    raise SystemExit('Existing output retained. Explicit same-source/settings resume required.')
o.output.mkdir(parents=True, exist_ok=True)
(o.output / 'frames').mkdir(exist_ok=True)
frozen = o.output / 'frozen-stair-motion-study.py'
if frozen.exists():
    assert hashlib.sha256(frozen.read_bytes()).hexdigest() == source_hash
elif frozen.resolve() != Path(__file__).resolve():
    shutil.copyfile(Path(__file__), frozen)
manifest_path = o.output / 'render-manifest.json'
manifest = {'frozen_source': str(frozen.resolve()), 'source_sha256': source_hash,
            'input_acting_blend_sha256': expected, 'width': o.width, 'height': o.width * 16 // 9,
            'frame_numbers': wanted, 'expected_frames': len(wanted), 'samples': 8,
            'scope': 'stair development only; not full story'}
if manifest_path.exists():
    assert json.loads(manifest_path.read_text()) == manifest, 'Refuse mixed source/settings/cache.'
else:
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
bpy.ops.wm.open_mainfile(filepath=str(o.acting_blend.resolve()))
S = bpy.context.scene
S.render.fps = 24
S.render.resolution_x, S.render.resolution_y = o.width, o.width * 16 // 9
S.render.resolution_percentage = 100
S.cycles.samples, S.render.threads = 8, 2
hero = bpy.data.objects['Courier master']
cart = bpy.data.objects['Free parcel cart, separate from counterweight']
gate = bpy.data.objects['Vertical gate lift root']
basket = bpy.data.objects['Separate counterweight basket root']
rope = bpy.data.objects['Continuous original gate-to-basket rope']
camera = S.camera
for a in [hero, *hero.children_recursive]:
    a.animation_data_clear()
    if a.type == 'EMPTY':
        a.rotation_mode = 'XYZ'
        a.rotation_euler = (0, 0, 0)
hero.location, hero.rotation_euler = (3.70, 3.35, -.205), (0, 0, 0)
cart.location = (.30, -1.55, 0)
gate.location.z, basket.location.z = 0, 3.15
rope.data.splines[0].points[0].co.z = 2.3
rope.data.splines[0].points[-1].co.z = 3.15
for a in basket.children:
    if a.name.startswith('Original loose counterweight stone'):
        a.hide_render = True
for a in S.objects:
    if a.name.startswith('Original stone at actual hand contact'):
        a.hide_render = True
for a, y in zip([bpy.data.objects['Waiting adult A'], bpy.data.objects['Waiting adult B']], [-3.7, -5.0]):
    a.location.y = y
legs, arms = {}, {}
for side, name in [(-1, 'Left hip'), (1, 'Right hip')]:
    hip = next(a for a in hero.children if a.name == name)
    knee = next(a for a in hip.children if a.name.startswith('Knee'))
    feet = [a for a in knee.children if a.name.startswith(('Boot sole', 'Courier boot'))]
    ankle = bpy.data.objects.new('Stair independent ankle ' + str(side), None)
    S.collection.objects.link(ankle)
    ankle.parent, ankle.location = knee, (0, 0, -.4)
    bpy.context.view_layer.update()
    for a in feet:
        world = a.matrix_world.copy()
        a.parent, a.matrix_world = ankle, world
    legs[side] = hip, knee, ankle, feet
    shoulder = next(a for a in hero.children if a.name == 'Shoulder ' + str(side))
    elbow = next(a for a in shoulder.children if a.name.startswith('Elbow'))
    hand = next(a for a in elbow.children if a.name.startswith('Courier hand'))
    arms[side] = shoulder, elbow, hand
neck = next(a for a in hero.children if a.name.startswith('Expressive neck'))
steps = sorted([a for a in S.objects if a.name.startswith('Original side loading step')], key=lambda a: a.dimensions.z)
platform = bpy.data.objects['Solid side loading platform']
surfaces = [(-1, 3.35, 0.0)] + [(i, a.location.y, a.location.z + a.dimensions.z / 2) for i, a in enumerate(steps)]
assert [round(row[2], 5) for row in surfaces] == [0, .55, 1.1, 1.65]


def smooth(q):
    q = max(0, min(1, q))
    return q * q * (3 - 2 * q)


def chain(first, second, endpoint, target, preference):
    target = Vector(target)
    bpy.context.view_layer.update()
    local = hero.matrix_world.inverted() @ target
    origin = first.location.copy()
    delta = local - origin
    distance = delta.length
    l1, l2 = second.location.length, endpoint.location.length
    assert abs(l1 - l2) + .0001 < distance < l1 + l2 - .0001, (first.name, distance)
    direction = delta.normalized()
    along = (l1*l1 - l2*l2 + distance*distance) / (2*distance)
    height = math.sqrt(max(0, l1*l1 - along*along))
    pref = Vector(preference)
    bend = (pref - direction * pref.dot(direction)).normalized()
    elbow = origin + direction*along + bend*height
    q1 = second.location.normalized().rotation_difference((elbow-origin).normalized())
    q2 = endpoint.location.normalized().rotation_difference((local-elbow).normalized())
    first.rotation_mode = second.rotation_mode = 'QUATERNION'
    first.rotation_quaternion = q1
    second.rotation_quaternion = q1.inverted() @ q2
    bpy.context.view_layer.update()
    error = (endpoint.matrix_world.translation - target).length
    assert error < .0001
    return error


# Each lead plant keeps the existing three impact times. The other foot joins
# that tread before the next rise, so neither leg skips a double-height riser.
lead_times = plan['actions']['stair_foot_plants']
schedule = {
    -1: [(11.0, lead_times[0]), (11.875, lead_times[1]), (12.375, lead_times[2])],
    1: [(lead_times[0], 11.875), (lead_times[1], 12.375), (lead_times[2], 12.875)]
}


def foot_target(side, t):
    y, floor = surfaces[0][1:]
    support = -1
    for index, (start, end) in enumerate(schedule[side]):
        next_support, next_y, next_floor = surfaces[index + 1]
        if t >= end:
            support, y, floor = next_support, next_y, next_floor
            continue
        if t <= start:
            return Vector((3.70 + side*.145, y, floor+.065)), True, support
        q = (t-start)/(end-start)
        # Lift above the new riser first; only then advance the flat sole over
        # its front edge. A direct diagonal path would pass through the riser.
        lift = (next_floor-floor+.10)*smooth(q/.38)
        if q > .82:
            lift = (next_floor-floor) + .10*(1-smooth((q-.82)/.18))
        travel = smooth((q-.38)/.44)
        return Vector((3.70+side*.145, y+(next_y-y)*travel, floor+.065+lift)), False, None
    return Vector((3.70+side*.145, y, floor+.065)), True, support


def support_height(x, y):
    heights = [0.0]
    for a in [*steps, platform]:
        if abs(x-a.location.x) <= a.dimensions.x/2+.00001 and abs(y-a.location.y) <= a.dimensions.y/2+.00001:
            heights.append(a.location.z+a.dimensions.z/2)
    return max(heights)


def pose(frame):
    t = (frame-1)/24
    targets = {side: foot_target(side, t) for side in [-1,1]}
    assert any(a[1] for a in targets.values()), 'At least one planted foot throughout climb'
    # Lower foot determines maximum supported hip elevation. Body only rises
    # to the next level after the leading foot has planted and the trailer lifts.
    hero.location = (3.70, .10+sum(a[0].y for a in targets.values())/2, min(a[0].z for a in targets.values())+.64-.91)
    feet = []
    for side, (target, stance, support) in targets.items():
        hip,knee,ankle,meshes = legs[side]
        error = chain(hip,knee,ankle,target,(0,-1,0))
        ankle.rotation_mode = 'QUATERNION'
        ankle.rotation_quaternion = knee.matrix_world.to_quaternion().inverted() @ hero.matrix_world.to_quaternion()
        bpy.context.view_layer.update()
        sole = next(a for a in meshes if a.name.startswith('Boot sole'))
        corners = [sole.matrix_world@Vector(c) for c in sole.bound_box]
        sole_z = min(a.z for a in corners)
        clearance = min(a.z-support_height(a.x,a.y) for a in corners)
        assert clearance > -.0001, (frame,side,'sole intersects tread',clearance)
        assert abs(sole_z-(target.z-.065)) < .0001
        if stance:
            assert abs(sole_z-surfaces[support+1][2]) < .0001
        feet.append({'side':side,'stance':stance,'support_tread_index':support,'ankle_world':list(ankle.matrix_world.translation),'target_error':error,'sole_min_z':sole_z,'min_sampled_sole_corner_surface_clearance':clearance})
    hands = []
    for side in [-1,1]:
        swing = .10*math.sin((t-11)*math.tau*2)*side
        target = hero.matrix_world@Vector((side*.36,-.16+swing,.93))
        hands.append(chain(*arms[side],target,(side,-.5,-.15)))
    neck.rotation_euler = (.06,0,-.12*smooth((t-12.875)/.30))
    bpy.context.view_layer.update()
    return {'frame':frame,'seconds':t,'hero_world':list(hero.location),'feet':feet,'hand_target_errors':hands}


camera.location = (7.0,5.4,4.2)
camera.rotation_euler = (Vector((3.70,2.15,1.80))-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.lens = 38
records,extent = [],0
for frame in range(263,319):
    record = pose(frame)
    records.append(record)
    actors = [hero,*steps]
    objects = [a for a in hero.children_recursive if a.type=='MESH' and not a.hide_render]+steps
    projections = [world_to_camera_view(S,camera,a.matrix_world@Vector(c)) for a in objects for c in a.bound_box]
    assert all(a.z>0 for a in projections)
    extent = max(extent,max(max(abs(a.x-.5),abs(a.y-.5)) for a in projections))
camera.data.lens *= min(1,.42/extent)
previous = {}
for record in records:
    for foot in record['feet']:
        old = previous.get(foot['side'])
        if old and old['stance'] and foot['stance'] and old['support_tread_index']==foot['support_tread_index']:
            assert (Vector(old['ankle_world'])-Vector(foot['ankle_world'])).length < .0001
        previous[foot['side']] = foot


def complete_png(path):
    if not path.exists() or path.stat().st_size<36:
        return False
    with path.open('rb') as f:
        h=f.read(24);f.seek(-12,2);tail=f.read()
    return h[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>II',h[16:24])==(o.width,o.width*16//9) and tail==b'\x00\x00\x00\x00IEND\xaeB`\x82'


for frame in wanted:
    pose(frame)
    path=o.output/'frames'/f'{frame:05d}.png';receipt=path.with_suffix('.json')
    if complete_png(path) and receipt.exists():
        r=json.loads(receipt.read_text());actual=hashlib.sha256(path.read_bytes()).hexdigest()
        assert r['source_sha256']==source_hash and r['input_acting_blend_sha256']==expected and r['frame']==frame and r['raw_image_sha256']==actual
    else:
        if path.exists():
            held=o.output/'unverified';held.mkdir(exist_ok=True)
            path.replace(held/(path.stem+'-'+hashlib.sha256(path.read_bytes()).hexdigest()[:16]+'.png'))
        S.render.filepath=str(path);bpy.ops.render.render(write_still=True)
        actual=hashlib.sha256(path.read_bytes()).hexdigest()
        receipt.write_text(json.dumps({'frame':frame,'source_sha256':source_hash,'input_acting_blend_sha256':expected,'raw_image_sha256':actual},indent=2)+'\n')
    records[frame-263]['raw_image_sha256']=actual
assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==source_hash
report={'id':'counterweight-gate','status':'stair_contact_development_not_full_story','source_sha256':source_hash,'input_acting_blend_sha256':expected,'action_plan_sha256':plan_hash,'fps':24,'test_frames':56,'story_frame_range':[263,318],'duration_seconds':56/24,'rendered_frame_numbers':wanted,'dimensions':[o.width,o.width*16//9],'samples':8,'all56_poses_checked':True,'lead_plant_story_frames':[280,292,304],'follow_plant_story_frames':[286,298,310],'foot_schedule':schedule,'camera_lens_mm':camera.data.lens,'records':records,'geometry_scope':'Existing three .55-high treads retained; step-to movement, not construction guidance. End on top tread at landing height, later movement onto landing unbuilt.','checks_scope':'Ankle/sole contacts and sampled sole bounding-box corners against authored treads, not full-body swept collision or rigid-body certification.','external_assets_added':[],'visual_inspection_pending':True,'full_story_animation':False,'publishable':False}
(o.output/'stair-motion-study.json').write_text(json.dumps(report,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str((o.output/'stair-motion-study.blend').resolve()))
