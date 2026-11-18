"""Two-second original cart-contact/walking development test, not the full story.

The reviewed acting blend supplies only project-owned original assets. At most
48 frames at24fps can be rendered. Native360x640 is a development option only.
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
from mathutils import Euler, Quaternion, Vector

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--acting-blend', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--width', type=int, choices=[360, 720], default=720)
parser.add_argument('--frames', nargs='+', type=int, default=[1, 13, 25, 37, 48])
parser.add_argument('--all-motion', action='store_true')
options = parser.parse_args(argv)
expected = '7691e1f0daed54ea5addc4eb644cd18fcd8dc1e90fa9b132e646968d84660b0f'
assert hashlib.sha256(options.acting_blend.read_bytes()).hexdigest() == expected
wanted = list(range(1, 49)) if options.all_motion else sorted(set(options.frames))
assert wanted and min(wanted) >= 1 and max(wanted) <= 48
options.output.mkdir(parents=True, exist_ok=False)
(options.output / 'frames').mkdir()
bpy.ops.wm.open_mainfile(filepath=str(options.acting_blend.resolve()))
S = bpy.context.scene
S.render.fps = 24
S.render.resolution_x = options.width
S.render.resolution_y = options.width * 16 // 9
S.render.resolution_percentage = 100
S.cycles.samples = 8
S.render.threads = 2
hero = bpy.data.objects['Courier master']
cart = bpy.data.objects['Free parcel cart, separate from counterweight']
camera = S.camera
for a in [hero, *hero.children_recursive]:
    a.animation_data_clear()
    if a.type == 'EMPTY':
        a.rotation_mode = 'XYZ'
        a.rotation_euler = (0, 0, 0)
hero.location = (0, 0, -.065)
hero.rotation_euler.z = math.pi
bpy.context.view_layer.update()

# Original procedural paving stripes make real world-space foot travel visible.
floor = bpy.data.objects['Original flat courtyard floor']
material = floor.data.materials[0].copy()
floor.data.materials[0] = material
nodes, links = material.node_tree.nodes, material.node_tree.links
geometry = nodes.new('ShaderNodeNewGeometry')
separate = nodes.new('ShaderNodeSeparateXYZ')
multiply = nodes.new('ShaderNodeMath'); multiply.operation = 'MULTIPLY'; multiply.inputs[1].default_value = 2
fraction = nodes.new('ShaderNodeMath'); fraction.operation = 'FRACT'
threshold = nodes.new('ShaderNodeMath'); threshold.operation = 'LESS_THAN'; threshold.inputs[1].default_value = .025
mix = nodes.new('ShaderNodeMixRGB'); mix.inputs[1].default_value = (.25, .31, .26, 1); mix.inputs[2].default_value = (.13, .18, .15, 1)
links.new(geometry.outputs['Position'], separate.inputs[0]); links.new(separate.outputs['Y'], multiply.inputs[0])
links.new(multiply.outputs[0], fraction.inputs[0]); links.new(fraction.outputs[0], threshold.inputs[0])
links.new(threshold.outputs[0], mix.inputs[0]); links.new(mix.outputs[0], nodes['Principled BSDF'].inputs['Base Color'])

# Introduce ankle pivots while preserving the reviewed boot/sole geometry.
legs = {}
for side, name in [(-1, 'Left hip'), (1, 'Right hip')]:
    hip = next(a for a in hero.children if a.name == name)
    knee = next(a for a in hip.children if a.name.startswith('Knee'))
    feet = [a for a in knee.children if a.name.startswith(('Boot sole', 'Courier boot'))]
    ankle = bpy.data.objects.new('Original planted ankle ' + str(side), None)
    S.collection.objects.link(ankle)
    ankle.parent = knee
    ankle.location = (0, 0, -.4)
    bpy.context.view_layer.update()
    for a in feet:
        old_world = a.matrix_world.copy()
        a.parent = ankle
        a.matrix_world = old_world
    legs[side] = (hip, knee, ankle, feet)
bpy.context.view_layer.update()


def solve_chain(actor, first, second, endpoint, target, preference):
    target = Vector(target)
    bpy.context.view_layer.update()
    local = actor.matrix_world.inverted() @ target
    origin = first.location.copy()
    delta = local - origin
    distance = delta.length
    l1, l2 = second.location.length, endpoint.location.length
    assert abs(l1 - l2) + .0001 < distance < l1 + l2 - .0001, distance
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


arms = {}
for side in [-1, 1]:
    shoulder = next(a for a in hero.children if a.name == 'Shoulder ' + str(side))
    elbow = next(a for a in shoulder.children if a.name.startswith('Elbow'))
    hand = next(a for a in elbow.children if a.name.startswith('Courier hand'))
    arms[side] = (shoulder, elbow, hand)

for a, y in zip([bpy.data.objects['Waiting adult A'], bpy.data.objects['Waiting adult B']], [-3.7, -5.0]):
    a.location.y = y
wheels = [a for a in cart.children if a.name.startswith('Cart wheel')]
velocity = 3.25 / (508 / 24 - 18.75)
period, duty = .72, .60
lead = velocity * period * duty / 2
records = []
previous_feet = {}
for frame in range(1, 49):
    t = (frame - 1) / 24
    distance = velocity * t
    hero.location = (.30, -2.55 + distance, -.145 + .01 * math.cos(t * math.tau * 2 / period))
    cart.location = (.30, -1.55 + distance, 0)
    foot_records = []
    for side, offset in [(-1, 0), (1, .5)]:
        absolute_phase = t / period + offset
        cycle = math.floor(absolute_phase)
        phase = absolute_phase - cycle
        cycle_start = (cycle - offset) * period
        plant_y = -2.55 + velocity * cycle_start + lead
        stance = phase <= duty
        if stance:
            y, lift = plant_y, 0
        else:
            progress = (phase - duty) / (1 - duty)
            smooth = progress * progress * (3 - 2 * progress)
            y, lift = plant_y + velocity * period * smooth, .12 * math.sin(math.pi * progress)
        # Courier faces+Y; local leg X offsets reverse in world space.
        target = (.30 - side * .145, y, .065 + lift)
        hip, knee, ankle, feet = legs[side]
        error = solve_chain(hero, hip, knee, ankle, target, (0, -1, 0))
        ankle.rotation_mode = 'QUATERNION'
        knee_world = knee.matrix_world.to_quaternion()
        ankle.rotation_quaternion = knee_world.inverted() @ hero.matrix_world.to_quaternion()
        bpy.context.view_layer.update()
        sole = next(a for a in feet if a.name.startswith('Boot sole'))
        sole_min = min((sole.matrix_world @ Vector(c)).z for c in sole.bound_box)
        assert abs(sole_min - lift) < .0001, (frame, side, sole_min, lift)
        drift = 0
        previous = previous_feet.get(side)
        if stance and previous and previous['stance'] and previous['cycle'] == cycle:
            drift = (ankle.matrix_world.translation - Vector(previous['ankle_world'])).length
            assert drift < .0001, drift
        foot = {'side': side, 'stance': stance, 'cycle': cycle, 'phase': phase, 'sole_min_z': sole_min,
                'ankle_world': list(ankle.matrix_world.translation), 'target_error': error, 'same_stance_world_drift': drift}
        foot_records.append(foot)
        previous_feet[side] = foot
    hand_errors = []
    for side, x in [(-1, .55), (1, .05)]:
        hand_errors.append(solve_chain(hero, *arms[side], (x, cart.location.y - .55, 1.02), (side, -.5, -.15)))
    for wheel in wheels:
        wheel.rotation_mode = 'QUATERNION'
        wheel.rotation_quaternion = Euler((0, math.pi / 2, 0)).to_quaternion() @ Quaternion(Vector((0, 0, 1)), -distance / .16)
    # Approach-side technical view keeps both ray endpoints inside the arch's
    # clear X span; the earlier outside tracking view crossed a stone post.
    # This back/side contact view is not a final editorial camera sequence.
    camera.location = (1.05, hero.location.y - 3.60, 2.35)
    target = Vector((.30, hero.location.y + .55, 1.00))
    camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
    camera.data.lens = 34
    bpy.context.view_layer.update()
    projected = [world_to_camera_view(S, camera, a.matrix_world @ Vector(c)) for actor in [hero, cart]
                 for a in actor.children_recursive if a.type == 'MESH' and not a.hide_render for c in a.bound_box]
    extent = max(max(abs(p.x - .5), abs(p.y - .5)) for p in projected)
    camera.data.lens *= min(1, .43 / extent)
    bpy.context.view_layer.update()
    record = {'frame': frame, 'test_seconds': t, 'planned_story_seconds': 18.75 + t,
              'hero_world': list(hero.location), 'cart_world': list(cart.location), 'cart_travel': distance,
              'hand_center_errors': hand_errors, 'feet': foot_records, 'wheel_rotation_radians': -distance / .16}
    if frame in wanted:
        path = options.output / 'frames' / f'{frame:05d}.png'
        S.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        record['raw_image_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
    records.append(record)
report = {'id': 'counterweight-gate', 'status': 'two_second_contact_walk_test_not_finished_story',
          'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'input_acting_blend_sha256': expected,
          'fps': 24, 'test_frames': 48, 'rendered_frame_numbers': wanted, 'dimensions': [S.render.resolution_x, S.render.resolution_y],
          'samples': 8, 'all_48_frame_pose_invariants_checked': True, 'records': records,
          'foot_plant_method': 'Two-link original leg solver, world-space stance ankle locks and independent ankle counter-rotation; source boot geometry preserved.',
          'walking_period_seconds': period, 'stance_fraction': duty, 'cart_velocity_scene_units_per_second': velocity,
          'external_assets_added': [], 'queue_walk_animated': False, 'full_story_animation_started': False,
          'subjective_continuous_motion_review_claimed': False, 'visual_inspection_pending': True, 'publishable': False}
(options.output / 'cart-motion-study.json').write_text(json.dumps(report, indent=2) + '\n')
shutil.copyfile(Path(__file__), options.output / 'frozen-cart-motion-study.py')
(options.output / 'render-manifest.json').write_text(json.dumps({'frozen_source': str((options.output / 'frozen-cart-motion-study.py').resolve()),
    'source_sha256': report['source_sha256'], 'width': S.render.resolution_x, 'height': S.render.resolution_y,
    'frame_numbers': wanted, 'expected_frames': len(wanted), 'samples': 8, 'scope': 'two-second development motion test or selected samples, not full story'}, indent=2) + '\n')
bpy.ops.wm.save_as_mainfile(filepath=str((options.output / 'cart-motion-study.blend').resolve()))
