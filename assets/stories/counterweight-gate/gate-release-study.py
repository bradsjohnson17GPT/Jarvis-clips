"""First failed gate attempt: bounded 90-frame development study, not full story.

Use the reviewed original acting blend. No new narration or audio is generated.
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
p.add_argument('--frames', type=int, nargs='+', default=[1, 48, 66, 76, 90])
p.add_argument('--all-motion', action='store_true')
o = p.parse_args(argv)
expected = '7691e1f0daed54ea5addc4eb644cd18fcd8dc1e90fa9b132e646968d84660b0f'
assert hashlib.sha256(o.acting_blend.read_bytes()).hexdigest() == expected
wanted = list(range(1, 91)) if o.all_motion else sorted(set(o.frames))
assert wanted and min(wanted) >= 1 and max(wanted) <= 90
root = next(a for a in Path(__file__).resolve().parents if (a / 'AGENTS.md').exists())
plan_path = root / 'assets/stories/counterweight-gate/action-plan.json'
plan = json.loads(plan_path.read_text())
release, stop = plan['actions']['first_gate_release'], plan['actions']['first_gate_stop']
assert release == 2.65 and stop == 3.125
o.output.mkdir(parents=True, exist_ok=False)
(o.output / 'frames').mkdir()
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


def pose(frame):
    t = (frame - 1) / 24
    fall = max(0, min(1, (t - release) / (stop - release)))
    lift = 1.10 * (1 - fall * fall)
    gate.location.z = lift
    basket.location.z = 3.15 - lift
    points = rope.data.splines[0].points
    points[0].co.z, points[-1].co.z = 2.3 + lift, 3.15 - lift
    targets = {}
    for side, x in [(-1, -.27), (1, -.77)]:
        departure = smooth(1.10, 2.05, t) if side == -1 else smooth(release, release + .20, t)
        grip = Vector((x, -.22, 1.49))
        toward_cart = Vector((0, -1.0, 1.05)) if side == -1 else Vector((-.77, -.95, 1.05))
        target = grip.lerp(toward_cart, departure)
        targets[side] = {'target': list(target), 'error': solve(side, target), 'grip_departure': departure}
    neck.rotation_euler = (.035 * math.sin(t * 2) + .10 * smooth(stop, 3.50, t), 0, 1.15 * smooth(.95, 2.10, t))
    # Change the inherited smile into an original neutral/concerned expression;
    # it is voiceover, not lip-sync or a real speaker's identity.
    concern = smooth(stop, 3.50, t)
    center = Vector((0, -.199, .137 + .010 * concern))
    corners = [Vector((-.059, -.188, .137 - .017 * concern)), Vector((.059, -.188, .137 - .017 * concern))]
    for a, length, (first, last) in zip(mouth, mouth_lengths, [(corners[0], center), (center, corners[1])]):
        a.location = (first + last) / 2
        a.rotation_euler = (last - first).to_track_quat('Z', 'Y').to_euler()
        a.scale.z = (last - first).length / length
    for side in [-1, 1]:
        brow = next(a for a in neck.children if a.name == 'Eyebrow ' + str(side))
        brow.rotation_euler.y = side * (.10 - .28 * concern)
    bpy.context.view_layer.update()
    sole = min((a.matrix_world @ Vector(c)).z for a in hero.children_recursive if a.name.startswith('Boot sole') for c in a.bound_box)
    assert abs(sole) < .0001
    rope_length = sum((a.co.xyz - b.co.xyz).length for a, b in zip(points, points[1:]))
    if t <= release:
        assert targets[1]['grip_departure'] == 0
    if t >= release + .20:
        assert targets[1]['target'][1] < -.85
    return {'frame': frame, 'seconds': t, 'gate_lift': lift, 'basket_attachment_z': float(basket.location.z),
            'rope_polyline_length': rope_length, 'hand_targets': targets, 'sole_min_z': sole,
            'right_holding_hand_released': targets[1]['grip_departure'] > 0, 'concern_expression_fraction': concern}


# Fixed camera fit uses the whole motion's subject bounds; no frame-by-frame
# lens breathing. The upper gate/rope can be cropped in this contact test.
camera.location = (-3.60, -4.20, 2.70)
camera.rotation_euler = (Vector((0, -.90, 1.15)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
camera.data.lens = 34
extent = 0
records = []
for frame in range(1, 91):
    records.append(pose(frame))
    projected = [world_to_camera_view(S, camera, a.matrix_world @ Vector(c)) for actor in [hero, cart]
                 for a in actor.children_recursive if a.type == 'MESH' and not a.hide_render for c in a.bound_box]
    extent = max(extent, max(max(abs(v.x - .5), abs(v.y - .5)) for v in projected))
camera.data.lens *= min(1, .42 / extent)
assert max(r['rope_polyline_length'] for r in records) - min(r['rope_polyline_length'] for r in records) < .00001
assert records[75]['seconds'] == stop and abs(records[75]['gate_lift']) < .00001
for frame in wanted:
    pose(frame)
    path = o.output / 'frames' / f'{frame:05d}.png'
    S.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    records[frame - 1]['raw_image_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
report = {'id': 'counterweight-gate', 'status': 'first_failed_attempt_development_not_full_story',
          'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'input_acting_blend_sha256': expected,
          'action_plan_sha256': hashlib.sha256(plan_path.read_bytes()).hexdigest(), 'fps': 24, 'test_frames': 90,
          'duration_seconds': 3.75, 'rendered_frame_numbers': wanted, 'dimensions': [S.render.resolution_x, S.render.resolution_y],
          'samples': 8, 'holding_hand_release_seconds': release, 'floor_stop_seconds': stop, 'floor_stop_frame': 76,
          'all_90_kinematic_pose_invariants_checked': True, 'camera_lens_mm': camera.data.lens, 'records': records,
          'kinematics_not_rigid_body_validation': True, 'queue_and_second_attempt_animated': False,
          'visual_inspection_pending': True, 'full_story_animation_started': False, 'publishable': False}
(o.output / 'gate-release-study.json').write_text(json.dumps(report, indent=2) + '\n')
shutil.copyfile(Path(__file__), o.output / 'frozen-gate-release-study.py')
(o.output / 'render-manifest.json').write_text(json.dumps({'frozen_source': str((o.output / 'frozen-gate-release-study.py').resolve()),
    'source_sha256': report['source_sha256'], 'width': S.render.resolution_x, 'height': S.render.resolution_y,
    'frame_numbers': wanted, 'expected_frames': len(wanted), 'samples': 8, 'scope': 'first failed attempt development, not full story'}, indent=2) + '\n')
bpy.ops.wm.save_as_mainfile(filepath=str((o.output / 'gate-release-study.blend').resolve()))
