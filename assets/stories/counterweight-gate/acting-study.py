"""Original Counterweight Gate contact/blocking study, not a full animation.

Requires the reviewed v4 mechanism blend and renders only four critical stills.
Do not turn these poses into an upload or infer motion quality from them.
"""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Quaternion, Vector

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--mechanism-blend', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--stills', action='store_true')
options = parser.parse_args(argv)
expected_blend = '92bec68a5847e281b4fc0844d868017d947b6bef529e2566c2a8e7fa30e426b4'
assert hashlib.sha256(options.mechanism_blend.read_bytes()).hexdigest() == expected_blend
options.output.mkdir(parents=True, exist_ok=False)
bpy.ops.wm.open_mainfile(filepath=str(options.mechanism_blend.resolve()))
S = bpy.context.scene
S.cycles.samples = 8
S.render.threads = 2
S.render.resolution_percentage = 100
S.render.image_settings.file_format = 'PNG'
hero = bpy.data.objects['Courier master']
gate = bpy.data.objects['Vertical gate lift root']
basket = bpy.data.objects['Separate counterweight basket root']
cart = bpy.data.objects['Free parcel cart, separate from counterweight']
rope = bpy.data.objects['Continuous original gate-to-basket rope']
camera = S.camera
rocks = [a for a in basket.children if a.name.startswith('Original loose counterweight stone')]
all_hero = [hero, *hero.children_recursive]


def material(name, color):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Roughness'].default_value = .65
    return m


def reset_actor(actor):
    for a in [actor, *actor.children_recursive]:
        a.animation_data_clear()
        if a.type == 'EMPTY':
            a.rotation_mode = 'XYZ'
            a.rotation_euler = (0, 0, 0)


def place_actor(actor, x, y, floor=0, angle=math.pi, scale=1):
    reset_actor(actor)
    actor.location = (x, y, 0)
    actor.rotation_euler.z = angle
    actor.scale = (scale,) * 3
    bpy.context.view_layer.update()
    lowest = min((a.matrix_world @ Vector(c)).z
                 for a in actor.children_recursive if a.name.startswith('Boot sole')
                 for c in a.bound_box)
    actor.location.z += floor - lowest
    bpy.context.view_layer.update()


def clone_adult(name, color):
    # Copies of project-owned geometry only, with independent joints/material slots.
    mapping = {}
    for old in all_hero:
        new = old.copy()
        new.animation_data_clear()
        if new.data:
            new.data = old.data.copy()
        S.collection.objects.link(new)
        mapping[old] = new
    for old, new in mapping.items():
        new.parent = mapping.get(old.parent)
    actor = mapping[hero]
    actor.name = name
    coat = material(name + ' original coat', color)
    scarf = material(name + ' original scarf', (.08, .30, .33) if name.endswith('A') else (.66, .49, .20))
    for a in actor.children_recursive:
        if a.type == 'MESH':
            for slot in a.material_slots:
                if slot.material and 'amber jacket' in slot.material.name.lower():
                    slot.material = coat
                elif slot.material and 'vermilion scarf' in slot.material.name.lower():
                    slot.material = scarf
    return actor


waiting = [clone_adult('Waiting adult A', (.31, .12, .075)),
           clone_adult('Waiting adult B', (.22, .23, .36))]

# The v4 platform skirt would clip the descending basket by about 7cm.
# Move it clear of the basket's full travel, preserve a solid supporting landing,
# and align the contiguous step treads to that landing.
platform = bpy.data.objects['Solid side loading platform']
platform.location = (3.70, .75, .825)
platform.dimensions = (1.08, 1.20, 1.65)
steps = sorted([a for a in S.objects if a.name.startswith('Original side loading step')],
               key=lambda a: a.dimensions.z)
for index, a in enumerate(steps):
    a.location.x = 3.70
    a.location.y = 2.75 - index * .56
bpy.data.objects['Loose-stone supply bin'].hide_render = True
# Small original stone supply on top of the landing, within the actor's next action.
for index in range(5):
    ob = rocks[index].copy()
    ob.data = rocks[index].data.copy()
    S.collection.objects.link(ob)
    ob.parent = None
    ob.name = 'Loose stone supply on solid loading landing'
    ob.location = (3.94 + (index % 2) * .12, 1.02 + (index // 2) * .11, 1.76)
    ob.hide_render = False


def mechanism(lift, loaded):
    gate.location.z = lift
    basket.location.z = 3.15 - lift
    for rock in rocks:
        rock.hide_render = not loaded
    points = rope.data.splines[0].points
    points[0].co.z = 2.3 + lift
    points[-1].co.z = 3.15 - lift


def actor_parts(actor, side):
    shoulder = next(a for a in actor.children if a.name.startswith('Shoulder ' + str(side)))
    elbow = next(a for a in shoulder.children if a.name.startswith('Elbow'))
    hand = next(a for a in elbow.children if a.name.startswith('Courier hand'))
    return shoulder, elbow, hand


def solve_hand(actor, side, target):
    """Two-segment solve uses the actual off-axis mitten-center vector."""
    shoulder, elbow, hand = actor_parts(actor, side)
    target = Vector(target)
    bpy.context.view_layer.update()
    local_target = actor.matrix_world.inverted() @ target
    origin = shoulder.location.copy()
    delta = local_target - origin
    distance = delta.length
    first = elbow.location.length
    second = hand.location.length
    assert abs(first - second) + .001 < distance < first + second - .001, (side, distance)
    direction = delta.normalized()
    projection = (first * first - second * second + distance * distance) / (2 * distance)
    height = math.sqrt(max(0, first * first - projection * projection))
    preference = Vector((side, -.5, -.15))
    perpendicular = (preference - direction * preference.dot(direction)).normalized()
    elbow_position = origin + direction * projection + perpendicular * height
    upper_rotation = elbow.location.normalized().rotation_difference((elbow_position - origin).normalized())
    lower_rotation = hand.location.normalized().rotation_difference((local_target - elbow_position).normalized())
    shoulder.rotation_mode = elbow.rotation_mode = 'QUATERNION'
    shoulder.rotation_quaternion = upper_rotation
    elbow.rotation_quaternion = upper_rotation.inverted() @ lower_rotation
    bpy.context.view_layer.update()
    actual = hand.matrix_world.translation
    error = (actual - target).length
    assert error < .0001, error
    return {'side': side, 'target_world': list(target), 'actual_hand_center_world': list(actual),
            'center_target_error_scene_units': error, 'scope': 'mitten-center contact, not finger articulation or continuous motion'}


def look(location, target, lens):
    camera.location = location
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat('-Z', 'Y').to_euler()
    camera.data.lens = lens


def fit_subjects(actors, margin=.08):
    """Keep every subject bound inside the portrait frame, then inspect the pixels."""
    bpy.context.view_layer.update()
    points = [a.matrix_world @ Vector(c) for actor in actors
              for a in actor.children_recursive if a.type == 'MESH' and not a.hide_render
              for c in a.bound_box]
    projected = [world_to_camera_view(S, camera, p) for p in points]
    extent_x = max(abs(p.x - .5) for p in projected)
    extent_y = max(abs(p.y - .5) for p in projected)
    camera.data.lens *= min(1, (.5 - margin) / extent_x, (.5 - margin) / extent_y)
    bpy.context.view_layer.update()
    projected = [world_to_camera_view(S, camera, p) for p in points]
    assert all(margin - .001 <= p.x <= 1 - margin + .001 and
               margin - .001 <= p.y <= 1 - margin + .001 and p.z > 0 for p in projected)


def line(passed=False):
    positions = [(-.20, -.70 if passed else -3.3, .96),
                 (.20, -2.10 if passed else -4.7, 1.04)]
    for actor, (x, y, scale) in zip(waiting, positions):
        place_actor(actor, x, y, scale=scale)


def bounds(actor):
    return min((a.matrix_world @ Vector(c)).z
               for a in actor.children_recursive if a.name.startswith('Boot sole')
               for c in a.bound_box)


records = []
def save_pose(name, note, contacts, floor):
    bpy.context.view_layer.update()
    ground_error = bounds(hero) - floor
    assert abs(ground_error) < .0001
    for actor in waiting:
        assert abs(bounds(actor)) < .0001
    record = {'name': name, 'note': note, 'contacts': contacts,
              'camera': {'location': list(camera.location), 'lens_mm': camera.data.lens},
              'hero_sole_support_z': floor, 'hero_sole_support_error': ground_error,
              'waiting_adults': [{'location': list(a.location), 'sole_min_z': bounds(a)} for a in waiting],
              'continuous_motion_reviewed': False}
    if options.stills:
        path = options.output / (name + '.png')
        S.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        record['raw_image_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
    records.append(record)


mechanism(1.10, False)
line()
cart.location = (.30, -1.55, 0)
place_actor(hero, -.52, -.66)
contacts = [solve_hand(hero, side, (x, -.22, 1.49)) for side, x in [(-1, -.27), (1, -.77)]]
look((-3.30, -3.10, 2.30), (-.40, -.35, 1.18), 38)
save_pose('01-two-hands-on-gate', 'Actual hand centers meet the bar; waiting line remains on the same approach side.', contacts, 0)

mechanism(0, False)
place_actor(hero, .30, -2.55)
contacts = [solve_hand(hero, side, (x, -2.10, 1.02)) for side, x in [(-1, .55), (1, .05)]]
next(a for a in hero.children if a.name.startswith('Expressive neck')).rotation_euler.z = .60
look((-3.80, -3.60, 2.45), (.30, -1.96, 1.03), 36)
fit_subjects([hero, cart])
save_pose('02-hands-on-cart-gate-closed', 'Courier has returned to the free cart; the gate is visibly closed. This static pose is not a completed failed-attempt animation.', contacts, 0)

mechanism(0, False)
place_actor(hero, 3.42, .53, floor=1.65, angle=-math.pi / 4)
contacts = [solve_hand(hero, -1, (2.94, .23, 3.13))]
carried = rocks[0].copy()
carried.data = rocks[0].data.copy()
S.collection.objects.link(carried)
carried.parent = None
carried.name = 'Original stone at actual hand contact above basket'
carried.location = (2.83, .18, 3.13)
carried.hide_render = False
look((6.60, -3.65, 4.10), (3.12, .35, 2.70), 46)
save_pose('03-hand-stone-and-basket-rim', 'A supported adult reaches over the empty basket; the separate stone is at the mitten edge. Platform remains outside basket travel. Deposit/climb motion is still unbuilt.', contacts, 1.65)
carried.hide_render = True

mechanism(2.20, True)
cart.location = (.30, 1.70, 0)
place_actor(hero, .30, .70)
line(passed=True)
contacts = [solve_hand(hero, side, (x, 1.15, 1.02)) for side, x in [(-1, .55), (1, .05)]]
look((2.75, 5.50, 2.70), (.15, -.20, 1.45), 38)
save_pose('04-cart-through-and-line-following', 'Adult courier and cart are beyond the raised gate; the same two adults have advanced toward the opening. This is a payoff blocking pose, not proof of walking animation.', contacts, 0)

assert platform.location.x - platform.dimensions.x / 2 > 2.70 + .36 + .05
report = {'id': 'counterweight-gate', 'status': 'four_contact_and_queue_blocking_poses_not_a_finished_video',
          'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'input_mechanism_blend_sha256': expected_blend, 'dimensions': [720, 1280],
          'cycles_samples': 8, 'poses': records, 'new_waiting_adults': 2,
          'platform_basket_travel_x_clearance': platform.location.x - platform.dimensions.x / 2 - (2.70 + .36),
          'external_assets_added': [], 'motion_started': False, 'publishable': False,
          'visual_inspection_pending': True}
(options.output / 'acting-study.json').write_text(json.dumps(report, indent=2) + '\n')
bpy.ops.wm.save_as_mainfile(filepath=str((options.output / 'acting-study.blend').resolve()))
