"""Original adult teamwork illustration. Development scene, never an upload by itself.

Blender 4.3: blender -b --python scene.py -- --output /task/work --preview
No downloaded meshes, textures, likenesses or reference-media assets are used.
"""
import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

FPS = 24
DURATION = 21.0693333333


def material(name, rgb, rough=.55, metal=0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*rgb, 1)
    m.use_nodes = True
    n = m.node_tree.nodes.get('Principled BSDF')
    n.inputs['Base Color'].default_value = (*rgb, 1)
    n.inputs['Roughness'].default_value = rough
    n.inputs['Metallic'].default_value = metal
    return m


def box(name, pos, size, mat, bevel=.04):
    bpy.ops.mesh.primitive_cube_add(size=1, location=pos)
    o = bpy.context.object
    o.name = name
    o.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        m = o.modifiers.new('Soft manufactured edges', 'BEVEL')
        m.width, m.segments = bevel, 3
        o.modifiers.new('Weighted corner normals', 'WEIGHTED_NORMAL')
    o.data.materials.append(mat)
    return o


def oval(name, pos, scale, mat, parent=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=16, location=pos)
    o = bpy.context.object
    o.name, o.scale = name, scale
    o.data.materials.append(mat)
    for p in o.data.polygons:
        p.use_smooth = True
    if parent:
        o.parent = parent
    return o


def line(name, pts, radius, mat, parent=None):
    d = bpy.data.curves.new(name, 'CURVE')
    d.dimensions = '3D'
    d.bevel_depth, d.bevel_resolution = radius, 3
    s = d.splines.new('BEZIER')
    s.bezier_points.add(len(pts)-1)
    for p, co in zip(s.bezier_points, pts):
        p.co, p.handle_left_type, p.handle_right_type = co, 'AUTO', 'AUTO'
    o = bpy.data.objects.new(name, d)
    bpy.context.collection.objects.link(o)
    d.materials.append(mat)
    if parent:
        o.parent = parent
    return o


def rod(name, a, b, radius, mat):
    a, b = Vector(a), Vector(b)
    bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=radius, depth=1)
    o = bpy.context.object
    o.name = name
    o.data.materials.append(mat)
    for p in o.data.polygons:
        p.use_smooth = True
    move_rod(o, a, b, 1)
    return o


def key(o, prop, frame):
    o.keyframe_insert(data_path=prop, frame=frame)


def move_rod(o, a, b, frame):
    a, b = Vector(a), Vector(b)
    o.location = (a+b)/2
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = (b-a).to_track_quat('Z', 'Y')
    o.scale.z = (b-a).length
    for prop in ['location', 'rotation_quaternion', 'scale']:
        key(o, prop, frame)


def label(name, text, pos, size, mat):
    d = bpy.data.curves.new(name, 'FONT')
    d.body, d.size, d.align_x = text, size, 'CENTER'
    d.extrude, d.bevel_depth = .001, .0005
    o = bpy.data.objects.new(name, d)
    bpy.context.collection.objects.link(o)
    o.location, o.rotation_euler = pos, (math.pi/2, 0, 0)
    d.materials.append(mat)
    return o


def smooth(a, b, t):
    u = max(0, min(1, t))
    u = u*u*(3-2*u)
    return Vector(a).lerp(Vector(b), u)


def ease(start, end, t):
    u = max(0, min(1, (t-start)/(end-start)))
    return u*u*(3-2*u)


def person(name, x, y, skin, shirt, hair, trousers, style):
    root = Vector((x, y, 0))
    box(name+' adult torso', root+Vector((0, 0, 1.40)), (.47, .31, .64), shirt, .11)
    box(name+' waist', root+Vector((0, .015, 1.06)), (.38, .28, .19), trousers, .05)
    for side in [-1, 1]:
        rod(name+' leg'+str(side), root+Vector((side*.115, .015, 1.05)), root+Vector((side*.13, -.01, .20)), .085, trousers)
        box(name+' shoe'+str(side), root+Vector((side*.13, -.065, .10)), (.20, .32, .15), SHOES, .055)
    oval(name+' neck', root+Vector((0, 0, 1.78)), (.082, .085, .15), skin)
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=root+Vector((0, 0, 2.02)))
    head = bpy.context.object
    head.name = name+' head rig'
    head.scale = (.78, .78, .78)
    oval(name+' adult face', (0, 0, 0), (.225, .205, .295), skin, head)
    oval(name+' hair', (0, .025, .215), (.233, .20, .13), hair, head)
    if style == 'bun':
        oval(name+' tied hair', (0, .19, .22), (.15, .15, .145), hair, head)
    else:
        oval(name+' side part', (-.075, -.015, .245), (.16, .18, .09), hair, head)
    for side in [-1, 1]:
        oval(name+' ear'+str(side), (side*.219, 0, -.015), (.048, .052, .08), skin, head)
        oval(name+' eye'+str(side), (side*.085, -.186, .055), (.052, .024, .043), WHITE, head)
        oval(name+' pupil'+str(side), (side*.085+.008, -.209, .053), (.022, .012, .029), INK, head)
        oval(name+' eye light'+str(side), (side*.085+.002, -.220, .065), (.007, .005, .008), WHITE, head)
    oval(name+' nose', (0, -.197, -.02), (.045, .065, .075), skin, head)
    mouth = line(name+' expression', [(-.075, -.187, -.115), (0, -.207, -.12), (.075, -.187, -.115)], .008, LIP, head)
    brows = []
    for side in [-1, 1]:
        brows.append(line(name+' brow'+str(side), [(side*.045, -.191, .121), (side*.09, -.187, .13), (side*.135, -.165, .117)], .010, hair, head))
    arms = {}
    for side in [-1, 1]:
        a = root+Vector((side*.26, 0, 1.65))
        b = root+Vector((side*.34, -.04, 1.20))
        c = root+Vector((side*.29, -.10, 1.03))
        arms[side] = (rod(name+' upper arm'+str(side), a, b, .078, shirt), rod(name+' forearm'+str(side), b, c, .056, skin), oval(name+' palm'+str(side), c, (.065, .055, .088), skin), a)
    return {'name':name, 'root':root, 'head':head, 'mouth':mouth, 'brows':brows, 'arms':arms}


def arm(p, side, hand, frame):
    up, low, palm, shoulder = p['arms'][side]
    hand = Vector(hand)
    elbow = shoulder.lerp(hand, .52)+Vector((side*.07, -.13, -.10))
    move_rod(up, shoulder, elbow, frame)
    move_rod(low, elbow, hand, frame)
    palm.location = hand
    key(palm, 'location', frame)


def expression(p, smile, yaw, frame):
    p['head'].rotation_euler = (0, .025*smile, yaw)
    key(p['head'], 'rotation_euler', frame)
    for i, point in enumerate(p['mouth'].data.splines[0].bezier_points):
        point.co.z = -.12 + (abs(i-1)*.027-.009)*smile
        point.keyframe_insert(data_path='co', frame=frame)


def camera(name, pos, target, lens):
    bpy.ops.object.camera_add(location=pos)
    o = bpy.context.object
    o.name = name
    o.rotation_euler = (Vector(target)-o.location).to_track_quat('-Z', 'Y').to_euler()
    o.data.lens, o.data.sensor_fit, o.data.sensor_height = lens, 'VERTICAL', 36
    o.data.clip_start = .05
    return o


def area(name, pos, power, color, size, target):
    bpy.ops.object.light_add(type='AREA', location=pos)
    o = bpy.context.object
    o.name, o.data.energy, o.data.color, o.data.shape, o.data.size = name, power, color, 'DISK', size
    o.rotation_euler = (Vector(target)-o.location).to_track_quat('-Z', 'Y').to_euler()


def main():
    global WHITE, INK, LIP, SHOES
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--preview', action='store_true')
    parser.add_argument('--render', action='store_true')
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    args.output.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    WHITE = material('Warm porcelain', (.88,.86,.77))
    INK = material('Soft charcoal ink', (.018,.025,.031))
    LIP = material('Warm expression', (.22,.07,.055))
    SHOES = material('Leather shoes', (.027,.034,.039), .38)
    wood = material('Walnut', (.20,.105,.055), .45)
    teal = material('Deep teal plaster', (.032,.105,.12))
    blue = material('Blue sketch ink', (.055,.23,.35))
    sand = material('Linen wall', (.48,.40,.29))
    gold = material('Brushed brass', (.58,.37,.12), .3, .5)
    floor = material('Oak floor', (.24,.16,.095))
    box('Floor', (0,0,-.07), (9,8,.12), floor)
    box('Rear wall', (0,1.85,1.8), (8,.15,3.8), teal)
    box('Left wall', (-2.3,0,1.8), (.15,4,3.8), sand)
    for z in [.1,3.45]:
        box('Wall trim'+str(z), (0,1.74,z), (7,.055,.06), gold, .009)
    # The board is a physical prop, never a full-screen caption card.
    box('Board wood frame', (.1,1.02,1.80), (1.67,.075,1.32), wood, .055)
    box('Writable ivory surface', (.1,.972,1.80), (1.55,.022,1.20), WHITE, .025)
    label('Board heading', 'OUR PLAN', (.1,.949,2.24), .115, blue)
    for x,z in [(-.37,1.98),(.12,1.98),(.50,1.55)]:
        pts=[(x+.105*math.cos(a),.942,z+.078*math.sin(a)) for a in [i*2*math.pi/16 for i in range(17)]]
        line('Proposed blue idea', pts, .011, blue)
    line('First idea connection', [(-.25,.94,1.98),(-.12,.94,1.98),(.01,.94,1.98)], .009, blue)
    line('Second idea connection', [(.23,.94,1.94),(.39,.94,1.77),(.48,.94,1.64)], .009, blue)
    cross_a=line('First rejecting stroke', [(-.44,.926,2.08),(-.10,.926,1.79),(.34,.926,1.42)], .022, INK)
    cross_b=line('Second rejecting stroke', [(.36,.924,2.07),(-.04,.924,1.73),(-.43,.924,1.41)], .022, INK)
    new_path=line('A new team branch', [(-.42,.922,1.48),(-.48,.922,1.70),(-.35,.922,1.95)], .014, blue)
    # Background context: a low table, plants, window mullions and original wall art.
    box('Side credenza', (-1.25,1.30,.48), (.80,.50,.80), wood, .055)
    pot=material('Terracotta', (.39,.15,.07))
    oval('Planter', (-1.25,1.28,1.03), (.16,.16,.20), pot)
    leaves=material('Olive leaves', (.12,.22,.13))
    for i in range(5):
        x=-1.25+.14*math.sin(i*2); y=1.28+.1*math.cos(i*2)
        rod('Plant stem',(-1.25,1.28,1.1),(x,y,1.6+i*.05),.013,leaves)
        o=oval('Plant leaf',(x,y,1.50+i*.05),(.065,.035,.18),leaves)
        o.rotation_euler.y=.4*math.sin(i)
    for x in [-2.15,-1.75]:
        box('Window upright', (x,1.72,2.55), (.035,.08,1.0), wood, .007)
    lead=person('Leader', .63,.22,material('Leader skin',(.62,.37,.22)),material('Burgundy overshirt',(.24,.055,.075)),material('Leader dark hair',(.055,.035,.026)),material('Leader trousers',(.075,.09,.115)),'short')
    colleague=person('Designer', -.59,-.14,material('Designer skin',(.34,.18,.095)),material('Teal knit',(.045,.25,.27)),material('Designer hair',(.022,.018,.015)),material('Designer trousers',(.11,.115,.12)),'short')
    third=person('Teammate', -1.40,.20,material('Teammate skin',(.70,.48,.33)),material('Ochre blouse',(.61,.33,.085)),material('Teammate hair',(.10,.045,.025)),material('Teammate trousers',(.10,.14,.17)),'bun')
    marker=rod('Shared physical marker',(0,0,0),(0,.18,0),.024,INK)
    marker_tip=oval('Marker drawing nib',(0,0,0),(.016,.030,.016),INK)
    cams=[
        camera('01 Establish the team',(2.1,-5.1,2.75),(-.05,.45,1.35),49),
        camera('02 A plan gets crossed out',(.75,-2.5,2.35),(.0,.92,1.79),61),
        camera('03 The designer stops offering',(.15,-2.4,2.16),(-.59,-.14,1.94),66),
        camera('04 Return the marker',(1.6,-4.2,2.65),(.0,.25,1.50),53),
        camera('05 Shared hands',(.55,-1.6,1.78),(-.04,.12,1.39),72),
        camera('06 Their next version',(-2.9,-4.9,2.7),(-.40,.40,1.50),47),
    ]
    starts=[0,2.90,4.9,14.16,17.45,18.30]
    scene=bpy.context.scene
    for t,cam in zip(starts,cams):
        mark=scene.timeline_markers.new(cam.name,frame=round(t*FPS)+1)
        mark.camera=cam
    scene.camera=cams[0]
    # Bake poses in delivery frames; no frame interpolation is assumed or used.
    total=math.ceil(DURATION*FPS)
    for f in range(1,total+1):
        t=(f-1)/FPS
        resting=Vector((.84,-.02,1.13))
        if 2.90<=t<3.8:
            tip=smooth((-.44,.926,2.08),(.34,.926,1.42),(t-2.90)/.9)
            hand=tip-Vector((0,.17,0))
        elif 3.8<=t<4.05:
            tip=smooth((.34,.926,1.42),(.36,.926,2.07),(t-3.8)/.25)
            hand=tip-Vector((0,.17,0))
        elif 4.05<=t<4.85:
            tip=smooth((.36,.924,2.07),(-.43,.924,1.41),(t-4.05)/.8)
            hand=tip-Vector((0,.17,0))
        elif t<2.9:
            hand=smooth(resting,(-.44,.756,2.08),ease(1.7,2.9,t))
        elif t<14.5:
            hand=smooth((-.43,.754,1.41),resting,ease(4.85,5.8,t))
        else:
            hand=smooth(resting,(.045,0,1.40),ease(14.5,17.75,t))
        receiving=smooth((-.35,-.35,1.10),(-.085,0,1.52),ease(15.1,17.75,t))
        if t>=18.1:
            draw=smooth((-.42,.922,1.48),(-.35,.922,1.95),ease(18.8,20.2,t))
            receiving=smooth((-.085,0,1.52),draw-Vector((0,.17,0)),ease(18.1,18.8,t))
        if t>17.9:
            hand=smooth(hand,(.87,.05,1.12),ease(17.9,18.6,t))
        arm(lead,1,hand,f)
        arm(lead,-1,(.37,-.03,1.17),f)
        arm(colleague,1,receiving,f)
        arm(colleague,-1,(-.87,-.26,1.10),f)
        arm(third,1,smooth((-1.14,-.02,1.25),(-1.02,.10,1.55),ease(18.8,20.5,t)),f)
        arm(third,-1,(-1.65,-.02,1.16),f)
        new_confidence=ease(17.7,20.3,t)
        expression(lead,-.35+.85*ease(14.5,20,t),-.22-.10*ease(14.5,17.5,t),f)
        expression(colleague,-.70+1.5*new_confidence,.15+.08*new_confidence,f)
        expression(third,-.2+.9*new_confidence,.30,f)
        owner_hand=receiving if t>=17.8 else hand
        if 16.8<=t<18.1:
            u=ease(16.8,17.6,t)
            mstart=smooth(hand+Vector((0,.01,0)),(-.02,-.045,1.37),u)
            mend=smooth(hand+Vector((0,.17,0)),(-.02,-.045,1.63),u)
        elif 18.1<=t<18.8:
            u=ease(18.1,18.8,t)
            mstart=smooth((-.02,-.045,1.37),owner_hand+Vector((0,.01,0)),u)
            mend=smooth((-.02,-.045,1.63),owner_hand+Vector((0,.17,0)),u)
        else:
            mstart,mend=owner_hand+Vector((0,.01,0)),owner_hand+Vector((0,.17,0))
        move_rod(marker,mstart,mend,f)
        marker_tip.location=mend
        key(marker_tip,'location',f)
        for stroke,start,end in [(cross_a,2.90,3.80),(cross_b,4.05,4.85),(new_path,18.8,20.2)]:
            stroke.data.bevel_factor_end=ease(start,end,t)
            stroke.data.keyframe_insert(data_path='bevel_factor_end',frame=f)
        # Clear the crossed-out draft during the historical interview cut.
        for stroke in [cross_a,cross_b]:
            stroke.hide_render=t>=14.1
            key(stroke,'hide_render',f)
    area('Warm window key',(-3,-2,4.7),600,(1,.77,.54),3.6,(0,.4,1.5))
    area('Cool room fill',(3,-1,3.8),330,(.61,.79,1),3.0,(0,.4,1.5))
    area('Soft rear rim',(0,1.5,3.5),400,(1,.66,.35),2.0,(0,.1,1.5))
    scene.world.color=(.10,.10,.10)
    scene.render.engine='CYCLES'
    scene.cycles.device='CPU'
    scene.cycles.samples=24
    # This Blender build has no bundled OIDN. Keep rendering functional;
    # any final denoising must use the separately reviewed external route.
    scene.cycles.use_denoising=False
    scene.render.resolution_x,scene.render.resolution_y=720,1280
    scene.render.resolution_percentage=100
    scene.render.fps=FPS
    scene.frame_start,scene.frame_end=1,total
    scene.render.image_settings.file_format='PNG'
    scene.view_settings.view_transform='AgX'
    scene.render.film_transparent=False
    scene.frame_set(18)
    bpy.ops.wm.save_as_mainfile(filepath=str(args.output/'team-ownership-development.blend'))
    samples=[(.70,cams[0]),(3.45,cams[1]),(6.00,cams[2]),(16.8,cams[3]),(17.8,cams[4]),(20.5,cams[5])]
    if args.preview:
        scene.render.resolution_percentage=60
        scene.cycles.samples=32
        for t,cam in samples:
            scene.frame_set(round(t*FPS)+1)
            scene.camera=cam
            scene.render.filepath=str(args.output/f'preview-{t:05.2f}.png')
            bpy.ops.render.render(write_still=True)
    if args.render:
        scene.render.resolution_percentage=100
        for f in range(1,total+1):
            t=(f-1)/FPS
            if 7.36<=t<14.16:
                continue  # Cleared actual interview belongs here in the final edit.
            dest=args.output/'frames'/f'{f:05d}.png'
            if dest.exists():
                continue
            dest.parent.mkdir(exist_ok=True,parents=True)
            scene.frame_set(f)
            scene.camera=next(cam for start,cam in reversed(list(zip(starts,cams))) if t>=start)
            scene.render.filepath=str(dest)
            bpy.ops.render.render(write_still=True)
    (args.output/'scene-record.json').write_text(json.dumps({'status':'original_development_scene_not_final_video','fps':FPS,'timeline_seconds':DURATION,'delivery_resolution':[720,1280],'actual_preview_times':[t for t,_ in samples] if args.preview else [],'external_meshes_textures_or_likenesses':False,'audio_record':'assets/stories/team-ownership/audio-preflight.json','publishable':False},indent=2)+'\n')


if __name__=='__main__':
    main()
