"""Original counterweight-gate staging study; four stills, no full video renderer.

Build with Blender --background --threads 2 --python this_file -- --output PATH --stills.
The authored mechanism illustrates fiction; it is not a rigid-body simulation.
"""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'AGENTS.md').exists())
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
parser = argparse.ArgumentParser()
parser.add_argument('--output', required=True, type=Path)
parser.add_argument('--stills', action='store_true')
options = parser.parse_args(args)
OUT = options.output
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
S = bpy.context.scene
S.render.engine = 'CYCLES'
S.cycles.device = 'CPU'
S.cycles.samples = 4
S.cycles.use_denoising = False
S.cycles.max_bounces = 3
S.cycles.diffuse_bounces = 1
S.cycles.glossy_bounces = 1
S.cycles.use_adaptive_sampling = True
S.cycles.adaptive_threshold = .12
S.render.resolution_x, S.render.resolution_y = 720, 1280
S.render.resolution_percentage = 100
S.render.threads_mode = 'FIXED'
S.render.threads = 2
S.render.image_settings.file_format = 'PNG'
S.view_settings.view_transform = 'AgX'
S.view_settings.look = 'AgX - Medium High Contrast'
S.world.use_nodes = True
S.world.node_tree.nodes['Background'].inputs['Color'].default_value = (.40, .47, .56, 1)
S.world.node_tree.nodes['Background'].inputs['Strength'].default_value = .55


def material(name, color, metal=0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Roughness'].default_value = .55
    p.inputs['Metallic'].default_value = metal
    return m


stone = material('Courtyard | warm limestone', (.52, .43, .30))
ground = material('Courtyard | muted sage paving', (.25, .31, .26))
wood = material('Gate | chestnut timber', (.24, .10, .045))
edge = material('Gate | warm worn edge', (.43, .24, .095))
iron = material('Mechanism | dark forged iron', (.045, .065, .075), .55)
rope_mat = material('Mechanism | unbroken hemp rope', (.52, .37, .18))
basket_mat = material('Counterweight | blue basket', (.065, .20, .22), .20)
rock_mat = material('Counterweight | loose grey stones', (.27, .30, .29))
cart_mat = material('Parcel cart | honey timber', (.49, .27, .09))
rubber = material('Cart | grounded rubber wheels', (.025, .03, .028))
parcel = material('Cart | wrapped parcels', (.57, .42, .24))


def empty(name, loc=(0, 0, 0), parent=None):
    a = bpy.data.objects.new(name, None)
    S.collection.objects.link(a)
    a.parent = parent
    a.location = loc
    return a


def cube(name, loc, size, mat, parent=None, bevel=.025):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    a = bpy.context.object
    a.name = name
    a.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    a.parent = parent
    a.data.materials.append(mat)
    if bevel:
        b = a.modifiers.new('Soft original edges', 'BEVEL')
        b.width, b.segments = bevel, 2
        a.modifiers.new('Weighted corner normals', 'WEIGHTED_NORMAL')
    return a


def cylinder(name, loc, radius, depth, mat, parent=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=radius, depth=depth, location=loc)
    a = bpy.context.object
    a.name = name
    a.parent = parent
    a.data.materials.append(mat)
    a.modifiers.new('Weighted cylinder normals', 'WEIGHTED_NORMAL')
    return a


def rod(name, a, b, radius, mat, parent=None):
    a, b = Vector(a), Vector(b)
    ob = cylinder(name, (a + b) / 2, radius, (b - a).length, mat, parent)
    ob.rotation_euler = (b - a).to_track_quat('Z', 'Y').to_euler()
    return ob


def polyrope(name, points):
    curve = bpy.data.curves.new(name, 'CURVE')
    curve.dimensions = '3D'
    curve.bevel_depth = .022
    curve.bevel_resolution = 2
    sp = curve.splines.new('POLY')
    sp.points.add(len(points) - 1)
    for p, v in zip(sp.points, points):
        p.co = (*v, 1)
    ob = bpy.data.objects.new(name, curve)
    S.collection.objects.link(ob)
    curve.materials.append(rope_mat)
    return ob


cube('Original flat courtyard floor', (1, 0, -.1), (16, 16, .2), ground)
for x in [-1.43, 1.43]:
    cube('Original stone gate tower', (x, 0, 2.7), (.40, .58, 5.4), stone)
    cube('Gate tower cap', (x, 0, 5.42), (.58, .76, .18), edge)
cube('Overhead original pulley support', (.6, 0, 5.40), (4.4, .35, .25), wood)
for x in [-1.19, 1.19]:
    cube('Gate travel guide', (x, .03, 2.55), (.11, .30, 5.05), iron)
gate = empty('Vertical gate lift root')
for i in range(9):
    cube('Original individual timber gate slat', (-1.04 + i * .26, 0, 1.15), (.22, .16, 2.3), wood, gate)
for z in [.08, .46, 1.55, 2.22]:
    cube('Gate horizontal brace', (0, -.035, z), (2.32, .22, .16), edge, gate)
cube('Reachable lifting handle', (-.52, -.22, .39), (.72, .10, .10), iron, gate)
for x in [-1.2, 1.2]:
    cube('Visible upper travel stop', (x, -.12, 4.57), (.30, .36, .15), iron)
for x in [0, 2.55]:
    a = cylinder('Overhead quarter-turn rope pulley', (x, 0, 5.05), .15, .10, iron)
    a.rotation_euler[0] = math.pi / 2
    rod('Pulley support bracket', (x, 0, 5.08), (x, 0, 5.40), .045, iron)

basket = empty('Separate counterweight basket root', (2.70, 0, 3.15))
# One closed-thickness open box avoids overlapping coplanar wall/base surfaces.
vertices = []
for hx, hy, z in [(.36, .32, -.74), (.36, .32, -.22), (.30, .26, -.62), (.30, .26, -.22)]:
    vertices += [(-hx, -hy, z), (hx, -hy, z), (hx, hy, z), (-hx, hy, z)]
faces = [(3, 2, 1, 0), (8, 9, 10, 11)]
for i in range(4):
    j = (i + 1) % 4
    faces += [(i, j, 4 + j, 4 + i), (4 + i, 4 + j, 12 + j, 12 + i),
              (8 + i, 12 + i, 12 + j, 8 + j)]
mesh = bpy.data.meshes.new('Original continuous basket wall mesh')
mesh.from_pydata(vertices, [], faces)
mesh.update()
box = bpy.data.objects.new('Counterweight basket continuous box', mesh)
S.collection.objects.link(box)
box.parent = basket
box.data.materials.append(basket_mat)
box.modifiers.new('Weighted basket normals', 'WEIGHTED_NORMAL')
for x in [-.30, .30]:
    rod('Basket strap joins exact rope attachment', (0, 0, 0), (x, 0, -.24), .025, iron, basket)
rocks = []
for i in range(8):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=.15)
    a = bpy.context.object
    a.name = 'Original loose counterweight stone'
    a.parent = basket
    a.location = ((i % 3 - 1) * .19, ((i // 3) % 2 - .5) * .22, -.47 + (i // 6) * .18)
    a.scale = (1, .85, .75)
    a.data.materials.append(rock_mat)
    rocks.append(a)

cube('Solid side loading platform', (3.55, 1.10, .825), (1.12, 1.2, 1.65), stone)
for i in range(3):
    z = (i + 1) * .55
    cube('Original side loading step', (3.55, 3.10 - i * .56, z / 2), (1.08, .56, z), stone)
cube('Loose-stone supply bin', (4.45, .65, .50), (.65, .7, 1.0), wood)

cart = empty('Free parcel cart, separate from counterweight', (.30, -1.3, 0))
cube('Original parcel cart deck', (0, 0, .38), (.86, .94, .14), cart_mat, cart)
for x in [-.44, .44]:
    for y in [-.30, .30]:
        a = cylinder('Cart wheel, radius equals center height', (x, y, .16), .16, .11, rubber, cart)
        a.rotation_euler[1] = math.pi / 2
for z, size in [(.65, (.70, .76, .40)), (.97, (.52, .58, .24))]:
    cube('Fictional parcel on free cart', (0, .03, z), size, parcel, cart)
for x in [-.31, .31]:
    cube('Original cart handle upright', (x, -.55, .70), (.055, .06, .70), iron, cart)
cube('Original cart push grip', (0, -.55, 1.02), (.68, .065, .065), iron, cart)

source = ROOT / 'assets/stories/downward-beacon/scene.blend'
with bpy.data.libraries.load(str(source), link=False) as (src, dst):
    dst.objects = src.objects
loaded = [a for a in dst.objects if a]
hero = next(a for a in loaded if a.name == 'Courier master')
kept = {hero, *hero.children_recursive}
for a in loaded:
    if a in kept:
        S.collection.objects.link(a)
        a.animation_data_clear()
    else:
        bpy.data.objects.remove(a, do_unlink=True)
hero.location, hero.rotation_euler, hero.scale = (0, 0, 0), (0, 0, 0), (1, 1, 1)
for a in hero.children_recursive:
    if a.name.startswith(('Left hip', 'Right hip', 'Knee', 'Expressive neck')):
        a.rotation_euler = (0, 0, 0)
    if a.name.startswith(('Shoulder ', 'Elbow')):
        a.rotation_mode = 'XYZ'
        a.rotation_euler = (0, 0, 0)
bpy.context.view_layer.update()
sole = min((a.matrix_world @ Vector(c)).z for a in hero.children_recursive if a.type == 'MESH' for c in a.bound_box)


def place_actor(x, y, floor_z=0, angle=math.pi):
    hero.location = (x, y, floor_z - sole)
    hero.rotation_euler = (0, 0, angle)


def area(name, loc, power, color, size, target):
    d = bpy.data.lights.new(name, 'AREA')
    d.energy, d.color, d.size = power, color, size
    a = bpy.data.objects.new(name, d)
    S.collection.objects.link(a)
    a.location = loc
    a.rotation_euler = (Vector(target) - a.location).to_track_quat('-Z', 'Y').to_euler()


area('Courtyard broad morning key', (-4, -4, 7), 1300, (1, .78, .52), 5, (0, 0, 2))
area('Courtyard cool soft fill', (5, -1, 5), 700, (.52, .72, 1), 4, (0, 0, 2))
cam_data = bpy.data.cameras.new('Mechanism overview camera')
cam = bpy.data.objects.new('Mechanism overview camera', cam_data)
S.collection.objects.link(cam)
cam.location = (14, -6, 4.8)
cam.rotation_euler = (Vector((1.2, .20, 2.65)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
cam_data.lens = 46
cam_data.sensor_fit = 'VERTICAL'
S.camera = cam
ropes = []


def pose(name, lift, loaded_stones, passing=False, at_loading_steps=False):
    global ropes
    for ob in ropes:
        bpy.data.objects.remove(ob, do_unlink=True)
    gate.location.z = lift
    basket.location.z = 3.15 - lift
    for ob in rocks:
        ob.hide_render = not loaded_stones
    points = [(-.15, 0, 2.3 + lift), (-.15, 0, 5.05)]
    for i in range(1, 13):
        t = i * math.pi / 24
        points.append((-.15 * math.cos(t), 0, 5.05 + .15 * math.sin(t)))
    points.append((2.55, 0, 5.20))
    for i in range(1, 13):
        t = i * math.pi / 24
        points.append((2.55 + .15 * math.sin(t), 0, 5.05 + .15 * math.cos(t)))
    points.append((2.70, 0, basket.location.z))
    ropes = [polyrope('Continuous original gate-to-basket rope', points)]
    if at_loading_steps:
        place_actor(3.3, .90, 1.65, -math.pi / 2)
    elif passing:
        place_actor(-.50, .72, 0, math.pi)
    else:
        place_actor(-.72, -.70)
    cart.location.y = 1.35 if passing else -1.55
    # Purposeful story blocking views, rather than one empty wide shot for every pose.
    if at_loading_steps:
        view, target, lens = (6.5, -4.8, 3.3), (2.8, .30, 1.85), 36
    elif passing:
        view, target, lens = (1.8, -6.5, 2.4), (0, .20, 1.40), 38
    else:
        view, target, lens = (2.5, -7.0, 2.6), (0, -.50, 1.30), 43
    cam.location = view
    cam.rotation_euler = (Vector(target) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam_data.lens = lens
    bpy.context.view_layer.update()
    rope_length = sum((Vector(a) - Vector(b)).length for a, b in zip(points, points[1:]))
    wheel_floor = min((a.matrix_world @ Vector(c)).z for a in cart.children if a.name.startswith('Cart wheel') for c in a.bound_box)
    assert abs(wheel_floor) < 1e-5, wheel_floor
    return {'name': name, 'gate_lift': lift, 'basket_rope_attachment_z': float(basket.location.z), 'rope_polyline_length': rope_length, 'cart_lowest_wheel_z': wheel_floor, 'courier_sole_ground_offset_applied': -sole, 'loaded_stones_visible': loaded_stones, 'passing': passing, 'is_finished_motion_or_acting': False}


records = []
for name, lift, filled, passing, steps in [
    ('01-closed-gate-and-cart', 0, False, False, False),
    ('02-lifted-attempt-rope-response', 1.10, False, False, False),
    ('03-loaded-basket-gate-open', 2.20, True, False, True),
    ('04-free-cart-through-held-gate', 2.20, True, True, False),
]:
    records.append(pose(name, lift, filled, passing, steps))
    if options.stills:
        S.render.filepath = str(OUT / (name + '.png'))
        bpy.ops.render.render(write_still=True)
assert max(r['rope_polyline_length'] for r in records) - min(r['rope_polyline_length'] for r in records) < 1e-5
report = {'id': 'counterweight-gate', 'status': 'mechanism_stills_only_not_a_finished_video', 'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'project_owned_courier_sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'original_geometry': ['courtyard', 'vertical timber gate', 'guides/stops', 'two pulleys', 'continuous rope', 'separate hanging basket', 'stones', 'side loading steps/platform', 'free parcel cart'], 'external_models_or_footage': [], 'dimensions': [720, 1280], 'samples': 4, 'rigid_body_simulation': False, 'staging_grounding_and_rope_invariants_checked': True, 'poses': records, 'remaining_work': ['Actual hand/rope/basket interaction and stone deposits', 'Two distinct failed attempts in timed motion', 'Waiting adults and their specific movement payoff', 'Cinematic close/medium shots and final shot timing', 'Full native animation, soundtrack/captions and encoded finished review'], 'publishable': False}
(OUT / 'mechanism-study.json').write_text(json.dumps(report, indent=2) + '\n')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'mechanism-study.blend'))
