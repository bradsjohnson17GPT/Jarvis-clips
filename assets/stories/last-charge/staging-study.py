"""Four original native portrait staging poses, not a finished story renderer.

All cast, lamps, architecture and lighting are authored with Blender primitives.
No imported scene, model, image, texture, performance, font or soundtrack.
"""
import argparse
import hashlib
import json
import math
import shutil
import sys
from pathlib import Path

import bpy
from mathutils import Vector

parser = argparse.ArgumentParser()
parser.add_argument('--output', required=True, type=Path)
parser.add_argument('--stills', action='store_true')
args = parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
out = args.output.resolve()
out.mkdir(parents=True, exist_ok=True)
(out/'frames').mkdir(exist_ok=True)
source_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
frozen = out/'frozen-staging-study.py'
if frozen.exists():
    assert hashlib.sha256(frozen.read_bytes()).hexdigest() == source_hash
else:
    shutil.copyfile(__file__, frozen)

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 12
scene.cycles.use_denoising = False
scene.cycles.max_bounces = 4
scene.cycles.diffuse_bounces = 2
scene.cycles.glossy_bounces = 1
scene.cycles.use_adaptive_sampling = True
scene.cycles.adaptive_threshold = .10
scene.render.resolution_x, scene.render.resolution_y = 720,1280
scene.render.resolution_percentage = 100
scene.render.threads_mode = 'FIXED'
scene.render.threads = 2
scene.render.image_settings.file_format = 'PNG'
scene.render.film_transparent = False
scene.view_settings.view_transform = 'AgX'
scene.view_settings.look = 'AgX - Medium High Contrast'
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (.045,.08,.16,1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = .30

def material(name, rgb, metal=0, rough=.6, emission=0):
    m=bpy.data.materials.new(name);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*rgb,1)
    p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
    p.inputs['Emission Color'].default_value=(*rgb,1);p.inputs['Emission Strength'].default_value=emission
    return m

mats={
 'paving':material('Original cool river-stone paving',(.22,.29,.33)),
 'joint':material('Original paving joints',(.085,.13,.17)),
 'water':material('Original quiet canal water',(.025,.12,.17),.15,.22),
 'plank':material('Original worn footbridge boards',(.28,.15,.085)),
 'rail':material('Original painted bridge rail',(.10,.24,.25),.20),
 'shop':material('Original indigo shop plaster',(.11,.19,.29)),
 'house':material('Original muted sage neighbor plaster',(.21,.32,.28)),
 'trim':material('Original pale stone lintels',(.43,.46,.40)),
 'door':material('Original shop door teal',(.055,.15,.18)),
 'glass':material('Original dark window panels',(.045,.11,.18),.25,.25),
 'roof':material('Original dark clay roof',(.18,.12,.13)),
 'skin':material('Rose warm skin',(.57,.34,.22)),
 'traveler_skin':material('Traveler deep warm skin',(.29,.14,.085)),
 'neighbor_skin':material('Neighbors warm skin',(.62,.39,.25)),
 'silver':material('Rose silver hair',(.50,.55,.58)),
 'hair':material('Other cast dark hair',(.055,.035,.028)),
 'indigo':material('Rose indigo work coat',(.095,.16,.31)),
 'plum':material('Traveler plum coat',(.30,.10,.22)),
 'green':material('Far neighbor pale green apron',(.34,.49,.34)),
 'rust':material('Near neighbor rust coat',(.40,.17,.09)),
 'pants':material('Original cast slate trousers',(.08,.13,.19)),
 'boots':material('Original dark leather shoes',(.055,.045,.04)),
 'amber':material('Rose amber scarf',(.72,.34,.055)),
 'eye':material('Original eye whites',(.73,.75,.70)),
 'ink':material('Original pupils mouth and rims',(.012,.018,.025)),
 'brass':material('Original lamp brass frames',(.36,.23,.075),.7,.35),
 'cell':material('Original fictional cell housing',(.035,.105,.12),.25),
 'mark':material('Rose one amber charge mark',(.95,.40,.035),0,.4,.35),
 'mark2':material('Second cell two green marks',(.25,.68,.38),0,.4,.35),
 'mark3':material('Third cell three blue marks',(.25,.48,.86),0,.4,.35),
 'bag':material('Traveler original ochre bag',(.43,.27,.10)),
 'leaf':material('Original night foliage',(.08,.23,.15)),
 'pot':material('Original terracotta planters',(.29,.13,.085)),
}

def empty(name, loc=(0,0,0)):
    ob=bpy.data.objects.new(name,None);scene.collection.objects.link(ob);ob.location=loc
    return ob

def cube(name,loc,size,mat,parent=None,bevel=.035):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    ob=bpy.context.object;ob.name=name;ob.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:
        mod=ob.modifiers.new('Original softened edges','BEVEL');mod.width=bevel;mod.segments=3
        ob.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL')
    ob.data.materials.append(mat);ob.parent=parent
    return ob

def sphere(name,loc,size,mat,parent=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,location=loc)
    ob=bpy.context.object;ob.name=name;ob.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    ob.data.materials.append(mat);ob.parent=parent
    for f in ob.data.polygons:f.use_smooth=True
    return ob

def rod(name,a,b,r,mat,parent=None):
    a,b=Vector(a),Vector(b)
    bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=r,depth=(b-a).length,location=(a+b)/2)
    ob=bpy.context.object;ob.name=name;ob.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler()
    ob.data.materials.append(mat);ob.parent=parent
    for f in ob.data.polygons:f.use_smooth=True
    return ob

def curve(name,points,r,mat,parent=None):
    data=bpy.data.curves.new(name,'CURVE');data.dimensions='3D';data.bevel_depth=r;data.bevel_resolution=2
    sp=data.splines.new('POLY');sp.points.add(len(points)-1)
    for p,v in zip(sp.points,points):p.co=(*v,1)
    ob=bpy.data.objects.new(name,data);scene.collection.objects.link(ob);data.materials.append(mat);ob.parent=parent
    return ob

def ring(name,c,r,mat,parent=None):
    return curve(name,[(c[0]+r*math.cos(i*math.tau/32),c[1],c[2]+r*math.sin(i*math.tau/32)) for i in range(33)],.008,mat,parent)

# One short crossing with readable banks; no external environment image.
cube('Near original bank',(0,-3.2,-.15),(16,5.7,.30),mats['joint'])
cube('Far original bank',(0,4.2,-.15),(16,4.0,.30),mats['joint'])
cube('Original canal water',(0,1.0,-.26),(16,2.2,.06),mats['water'])
for side,ys in [('near',[-2.9,-2.45,-2.0,-1.55,-1.1,-.65]),('far',[2.6,3.05,3.5,3.95,4.4])]:
    for iy,y in enumerate(ys):
        for ix in range(-7,8):
            cube(f'Original {side} paver {iy}-{ix}',(ix*.49+(iy%2)*.24,y,.005),(.47,.43,.045),mats['paving'],bevel=.012)
for i in range(19):cube(f'Original bridge plank {i}',(0,-.59+i*.176,.04),(1.65,.165,.08),mats['plank'],bevel=.015)
for x in [-.88,.88]:
    for y in [-.65,.40,1.45,2.57]:rod('Original supported rail post',(x,y,.08),(x,y,.98),.035,mats['rail'])
    rod('Original continuous handrail',(x,-.69,.98),(x,2.61,.98),.045,mats['rail'])
rests=[(.98,.95,.94),(-.98,2.30,.94),(-.98,-.55,.94)]
for i,(x,y,z) in enumerate(rests):
    cube(f'Original lamp rest {i+1}',(x,y,z-.03),(.34,.36,.06),mats['brass'],bevel=.018)
    rod(f'Lamp rest support {i+1}',(x,y,.34),(x,y,z-.06),.025,mats['rail'])

def house(name,center,size,mat):
    x,y=center;w,d=size
    cube(name+' original walls',(x,y,1.25),(w,d,2.5),mat,bevel=.07)
    cube(name+' roof',(x,y,2.55),(w+.24,d+.22,.20),mats['roof'],bevel=.06)
    front=y-d/2-.045
    cube(name+' door',(x+.28,front,.92),(.72,.08,1.84),mats['door'])
    cube(name+' lintel',(x+.28,front-.02,1.91),(.91,.12,.12),mats['trim'])
    cube(name+' window',(x-.60,front,1.34),(.66,.07,.78),mats['glass'])
    for dx in [-.97,-.23]:cube(name+' window jamb',(x+dx,front-.045,1.34),(.06,.08,.91),mats['trim'],bevel=.01)
    cube(name+' window sill',(x-.60,front-.11,.91),(.88,.25,.09),mats['trim'])
    sphere(name+' knob',(x+.52,front-.08,.88),(.055,.055,.055),mats['brass'])
    return front

shop_front=house('Rose shop',(-2.60,-.94),(2.0,1.85),mats['shop'])
house('Far neighbor',(-2.38,3.48),(2.20,1.90),mats['house'])
cube('Original supported neighbor front step',(-2.38,2.30,.04),(2.20,.50,.08),mats['paving'],bevel=.015)
house('Far background', (2.75,4.50),(2.40,2.0),mats['shop'])
curve('Rose empty personal lamp bracket',[(-1.83,shop_front-.08,1.39),(-1.83,shop_front-.34,1.39),(-1.83,shop_front-.40,1.33)],.025,mats['brass'])
for x,y in [(-3.65,-2.10),(1.78,-1.15),(1.65,3.2),(-3.75,2.3)]:
    cube('Original planter',(x,y,.17),(.42,.44,.34),mats['pot'])
    for dx,dy,dz in [(-.08,0,.45),(.10,.04,.51),(0,-.08,.58)]:sphere('Original rounded shrub',(x+dx,y+dy,dz),(.35,.35,.40),mats['leaf'])

def actor(name,coat,skin,hair,glasses=False):
    root=empty(name+' original actor')
    cube(name+' rounded coat',(0,0,.99),(.49,.34,.53),coat,root,.11)
    cube(name+' coat hem',(0,0,.73),(.48,.33,.15),coat,root,.07)
    sphere(name+' neck',(0,0,1.27),(.16,.16,.18),skin,root)
    sphere(name+' original head',(0,0,1.49),(.42,.37,.48),skin,root)
    sphere(name+' hair cap',(0,.055,1.675),(.44,.35,.19),hair,root)
    if glasses:sphere(name+' silver bun',(0,.215,1.68),(.21,.21,.21),hair,root)
    for x in [-.095,.095]:
        sphere(name+' eye white',(x,-.178,1.56),(.065,.040,.070),mats['eye'],root)
        sphere(name+' pupil',(x,-.202,1.56),(.032,.018,.042),mats['ink'],root)
        curve(name+' brow',[(x-.04,-.191,1.62),(x,-.198,1.635),(x+.04,-.191,1.625)],.010,hair,root)
        if glasses:ring(name+' original round spectacle rim',(x,-.224,1.56),.071,mats['ink'],root)
    if glasses:rod(name+' spectacle bridge',(-.023,-.224,1.56),(.023,-.224,1.56),.007,mats['ink'],root)
    sphere(name+' nose',(0,-.211,1.49),(.065,.068,.085),skin,root)
    curve(name+' small smile',[(-.069,-.185,1.421),(0,-.203,1.405),(.069,-.185,1.421)],.008,mats['ink'],root)
    sphere(name+' left ear',(-.211,0,1.49),(.065,.11,.13),skin,root)
    sphere(name+' right ear',(.211,0,1.49),(.065,.11,.13),skin,root)
    if glasses:
        cube(name+' amber collar',(0,-.01,1.225),(.39,.35,.095),mats['amber'],root,.04)
        cube(name+' scarf tail',(-.13,-.188,1.10),(.095,.035,.28),mats['amber'],root,.018)
    return {'root':root,'coat':coat,'skin':skin,'name':name,'limbs':[],'hands':{},'feet':[]}

def limbs(a,mode='rest',stride=0):
    for ob in a['limbs']:bpy.data.objects.remove(ob,do_unlink=True)
    a['limbs']=[];a['hands']={};a['feet']=[];root=a['root'];name=a['name']
    for side,x,dy in [('left',-.14,-stride),('right',.14,stride)]:
        foot=cube(name+' '+side+' shoe',(x,dy,.07),(.19,.30,.14),mats['boots'],root,.045);a['limbs'].append(foot);a['feet'].append(foot)
        for p,q in [((x,0,.76),(x,dy/2,.43)),((x,dy/2,.43),(x,dy,.14))]:a['limbs'].append(rod(name+' '+side+' trouser',p,q,.079,mats['pants'],root))
    hand_positions={'left':(-.29,-.12,.82),'right':(.29,-.12,.82)}
    elbow_positions={'left':(-.31,-.04,.98),'right':(.31,-.04,.98)}
    if mode=='carry':hand_positions['right']=(.30,-.35,1.0);elbow_positions['right']=(.34,-.17,.97)
    if mode=='set':hand_positions['right']=(.10,-.57,1.41);elbow_positions['right']=(.28,-.29,1.25)
    for side,x in [('left',-.255),('right',.255)]:
        elbow,hand=elbow_positions[side],hand_positions[side]
        for p,q in [((x,0,1.16),elbow),(elbow,hand)]:a['limbs'].append(rod(name+' '+side+' original sleeve',p,q,.085,a['coat'],root))
        a['limbs'].append(sphere(name+' '+side+' rounded elbow',elbow,(.173,.173,.173),a['coat'],root))
        ob=sphere(name+' '+side+' mitten',hand,(.115,.11,.12),a['skin'],root);a['limbs'].append(ob);a['hands'][side]=ob

actors={
 'rose':actor('Rose',mats['indigo'],mats['skin'],mats['silver'],True),
 'traveler':actor('Traveler',mats['plum'],mats['traveler_skin'],mats['hair']),
 'far':actor('Far neighbor',mats['green'],mats['neighbor_skin'],mats['hair']),
 'near':actor('Near neighbor',mats['rust'],mats['neighbor_skin'],mats['hair']),
}
cube('Traveler persistent bag',(.32,.06,.61),(.28,.22,.32),mats['bag'],actors['traveler']['root'],.05)
curve('Traveler original bag strap',[(-.18,-.18,1.17),(.32,-.18,.72),(.32,.06,.61)],.019,mats['bag'],actors['traveler']['root'])

def lamp(name,marks,mark_mat):
    root=empty(name+' persistent lamp and cell')
    cube(name+' brass base',(0,0,.035),(.28,.28,.07),mats['brass'],root,.035)
    glow=material(name+' independent warm diffuser',(1.0,.53,.13),0,.5,2.3)
    sphere(name+' warm diffuser',(0,0,.218),(.205,.205,.25),glow,root)
    for x in [-.115,.115]:
        for y in [-.115,.115]:rod(name+' original frame',(x,y,.065),(x,y,.365),.014,mats['brass'],root)
    cube(name+' lamp cap',(0,0,.385),(.29,.29,.065),mats['brass'],root,.035)
    curve(name+' carry handle',[(-.10,0,.412),(-.10,0,.49),(0,0,.55),(.10,0,.49),(.10,0,.412)],.018,mats['brass'],root)
    cube(name+' separate fictional cell',(0,-.153,.205),(.115,.045,.225),mats['cell'],root,.02)
    for i in range(marks):cube(name+' charge mark '+str(i+1),(0,-.180,.14+i*.052),(.074,.012,.020),mark_mat,root,.005)
    data=bpy.data.lights.new(name+' independent downward warm pool','SPOT');data.energy=110;data.color=(1.0,.48,.14);data.spot_size=math.radians(90);data.spot_blend=.65;data.shadow_soft_size=.10
    ob=bpy.data.objects.new(name+' independent pool',data);scene.collection.objects.link(ob);ob.parent=root;ob.location=(0,-.24,.30)
    return {'root':root,'glow':glow,'light':data,'spot':ob,'marks':marks}

lamps=[lamp('First amber lamp',1,mats['mark']),lamp('Second green lamp',2,mats['mark2']),lamp('Third blue lamp',3,mats['mark3'])]

def power(l,on):
    l['light'].energy=110 if on else 0
    l['glow'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value=2.3 if on else .025

def area(name,loc,target,energy,size,color):
    d=bpy.data.lights.new(name,'AREA');d.energy=energy;d.shape='DISK';d.size=size;d.color=color
    ob=bpy.data.objects.new(name,d);scene.collection.objects.link(ob);ob.location=loc;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()

area('Original broad cool moon',(0,-2,7),(0,1,0),420,7,(.34,.49,1.0))
area('Original soft front fill',(3,-5,3),(0,0,1),120,5,(.49,.62,1.0))
camdata=bpy.data.cameras.new('Original portrait camera');camera=bpy.data.objects.new('Original portrait camera',camdata);scene.collection.objects.link(camera);scene.camera=camera
camdata.clip_end=100

def place_actor(key,loc,yaw=0,mode='rest',stride=0):
    a=actors[key];a['root'].location=loc;a['root'].rotation_euler=(0,0,yaw);limbs(a,mode,stride)

poses={1:'shopkeeper_one_personal_charge_and_waiting_traveler',2:'same_lamp_carried_to_crossing',3:'first_lamp_supported_on_rail_hand_still_at_handle',4:'three_independent_lamps_and_path_home'}
def set_pose(number):
    # All four adults and three lamp/cell identities persist across these poses.
    place_actor('rose',(-1.12,-1.60,.028),mode='carry')
    place_actor('traveler',(.18,2.91,.028))
    place_actor('far',(-1.73,2.26,.08),mode='carry')
    place_actor('near',(-3.30,-2.60,.028),mode='carry')
    cams={1:((2.5,-7.5,3.5),(-.60,.0,.95),36),2:((2.8,-3.2,2.15),(-.10,-.10,1.02),48),3:((3.5,-.2,2.15),(.25,.95,1.10),55),4:((5.4,-7.3,6.6),(0,.75,.70),45)}
    if number==2:place_actor('rose',(-.28,-.05,.08),mode='carry',stride=.08)
    if number==3:place_actor('rose',(.41,.85,.08),yaw=math.pi/2,mode='set')
    if number==4:
        place_actor('rose',(-.33,-.20,.08),yaw=math.pi,stride=.08)
        place_actor('traveler',(.25,-1.25,.028),stride=.07)
        place_actor('far',(-1.60,2.26,.08))
        place_actor('near',(-1.26,-.70,.028),yaw=-.3)
    bpy.context.view_layer.update()
    for i,l in enumerate(lamps):
        if number==4 or (number==3 and i==0):
            l['root'].location=rests[i];l['root'].rotation_euler=(0,0,0)
        else:
            key=['rose','far','near'][i];rig=actors[key]['root']
            l['root'].location=rig.matrix_world@Vector((.30,-.35,.45));l['root'].rotation_euler=rig.rotation_euler.copy()
        # Authored lighting proxy outside the opaque diffuser/cell; each source
        # follows only its own lamp. This is not a physical optics simulation.
        target=Vector((-l['root'].location.x,0,.08-l['root'].location.z)) if (number==4 or (number==3 and i==0)) else Vector((0,0,-.45))
        l['spot'].rotation_euler=(target-l['spot'].location).to_track_quat('-Z','Y').to_euler()
        power(l,i==0 or number==4)
    location,target,lens=cams[number];camera.location=location;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camdata.lens=lens
    scene.frame_set(number);bpy.context.view_layer.update()
    checks={}
    for key,a in actors.items():
        expected_z=a['root'].location.z
        soles=[min((ob.matrix_world@Vector(c)).z for c in ob.bound_box) for ob in a['feet']]
        assert all(abs(z-expected_z)<1e-5 for z in soles)
        checks[key+'_numeric_sole_plane_error']=max(abs(z-expected_z) for z in soles)
    if number<=3:
        grip=lamps[0]['root'].matrix_world@Vector((0,0,.55));hand=actors['rose']['hands']['right'].matrix_world.translation
        checks['rose_hand_to_first_handle_center']=(grip-hand).length
        assert checks['rose_hand_to_first_handle_center']<1e-5
    checks['first_cell_mark_count']=lamps[0]['marks'];checks['independent_lamp_mark_counts']=[l['marks'] for l in lamps]
    checks['lamp_pool_powers']=[l['light'].energy for l in lamps]
    if number in [3,4]:
        checks['first_lamp_base_to_rest_error']=abs(lamps[0]['root'].location.z-rests[0][2]);assert checks['first_lamp_base_to_rest_error']<1e-6
    return checks

manifest={'frozen_source':str(frozen),'source_sha256':source_hash,'width':720,'height':1280,'frame_numbers':[1,2,3,4],'kind':'four_static_staging_poses_not_story_frames','cycles_samples':12,'spatial_upscale':False,'frame_interpolation':False}
manifest_path=out/'render-manifest.json'
if manifest_path.exists():assert json.loads(manifest_path.read_text())==manifest
else:manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
set_pose(1)
bpy.ops.wm.save_as_mainfile(filepath=str(out/'last-charge-staging.blend'))
records=[]
for number,name in poses.items():
    checks=set_pose(number);image=out/'frames'/f'{number:05d}.png';receipt=image.with_suffix('.json')
    if args.stills:
        if image.exists() and receipt.exists():
            old=json.loads(receipt.read_text());assert old['source_sha256']==source_hash and old['raw_image_sha256']==hashlib.sha256(image.read_bytes()).hexdigest()
        else:
            assert not image.exists(),'Unreceipted image is held for inspection, not overwritten.'
            scene.render.filepath=str(image);bpy.ops.render.render(write_still=True)
            receipt.write_text(json.dumps({'frame':number,'pose':name,'source_sha256':source_hash,'raw_image_sha256':hashlib.sha256(image.read_bytes()).hexdigest(),'dimensions':[720,1280],'numeric_static_checks':checks,'actual_visual_inspection_pending':True},indent=2)+'\n')
    records.append({'frame':number,'pose':name,'numeric_static_checks':checks,'image_exists':image.exists(),'raw_sha256':hashlib.sha256(image.read_bytes()).hexdigest() if image.exists() else None})
report={'id':'last-charge','source_sha256':source_hash,'status':'four_original_static_staging_poses_only','dimensions':[720,1280],'samples':12,'poses':records,'new_external_assets':[],'cast_and_lamps_authored_from_original_primitives':True,'actual_visual_inspection_pending':True,'hand_checks_scope':'Hand center to first handle center and shoe sole planes in these four poses only. No finger-wrap, swept collision, walking/carry/set-down/release motion or full-body realism verdict.','actual_motion_frames_rendered':0,'finished_video_exists':False,'new_audio_created':False,'publishable':False}
(out/'staging-study.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'source_sha256':source_hash,'staging_poses':4,'rendered':args.stills,'finished_video_exists':False,'publishable':False}),flush=True)
