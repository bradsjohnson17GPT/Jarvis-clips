"""Original grouped stone transfers and complementary gate rise, frames319..438.

Uses the reviewed owned scene and version2 action clock. The cut onto the
landing elides travel; no within-shot root teleport, stone pop or new voice.
This authored development is not a physical simulation or a finished Short.
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

args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--acting-blend',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
p.add_argument('--width',type=int,choices=[360,720],default=720)
p.add_argument('--frames',type=int,nargs='+',default=[319,334,349,364,367,378,395,438])
p.add_argument('--all-motion',action='store_true')
p.add_argument('--check-only',action='store_true')
p.add_argument('--resume',action='store_true')
o=p.parse_args(args)
root=next(a for a in Path(__file__).resolve().parents if (a/'AGENTS.md').exists())
expected='7691e1f0daed54ea5addc4eb644cd18fcd8dc1e90fa9b132e646968d84660b0f'
assert hashlib.sha256(o.acting_blend.read_bytes()).hexdigest()==expected
plan_path=root/'assets/stories/counterweight-gate/action-plan-v2.json'
plan_hash=hashlib.sha256(plan_path.read_bytes()).hexdigest()
assert plan_hash=='e3f7aaffcfffd92bcf1cf9b57d001898b98b5573bc1e45e5abf78e09e49de7ce'
actions=json.loads(plan_path.read_text())['actions']
pickups,releases,impacts=[actions[k] for k in ['stone_pickups','stone_releases','stone_deposits']]
wanted=[] if o.check_only else list(range(319,439)) if o.all_motion else sorted(set(o.frames))
assert not wanted or (min(wanted)>=319 and max(wanted)<=438)
source_hash=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
if o.output.exists() and any(o.output.iterdir()) and not o.resume:
    raise SystemExit('Existing output held. Explicit identical-source/settings resume required.')
o.output.mkdir(parents=True,exist_ok=True);(o.output/'frames').mkdir(exist_ok=True)
frozen=o.output/'frozen-stone-loading-study.py'
if frozen.exists():
    assert hashlib.sha256(frozen.read_bytes()).hexdigest()==source_hash
elif frozen.resolve()!=Path(__file__).resolve():
    shutil.copyfile(Path(__file__),frozen)
manifest={'frozen_source':str(frozen.resolve()),'source_sha256':source_hash,'input_acting_blend_sha256':expected,
          'width':o.width,'height':o.width*16//9,'frame_numbers':wanted,'expected_frames':len(wanted),'samples':8,
          'scope':'stone transfer/gate rise development only; not full story'}
manifest_path=o.output/'render-manifest.json'
if manifest_path.exists():
    assert json.loads(manifest_path.read_text())==manifest,'Refuse mixed source/settings/cache'
else:
    manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
bpy.ops.wm.open_mainfile(filepath=str(o.acting_blend.resolve()))
S=bpy.context.scene;S.render.fps=24
S.render.resolution_x,S.render.resolution_y=o.width,o.width*16//9
S.render.resolution_percentage=100;S.cycles.samples=8;S.render.threads=2
hero=bpy.data.objects['Courier master'];gate=bpy.data.objects['Vertical gate lift root']
basket=bpy.data.objects['Separate counterweight basket root'];cart=bpy.data.objects['Free parcel cart, separate from counterweight']
rope=bpy.data.objects['Continuous original gate-to-basket rope'];camera=S.camera
for a in [hero,*hero.children_recursive]:
    a.animation_data_clear()
    if a.type=='EMPTY':
        a.rotation_mode='XYZ';a.rotation_euler=(0,0,0)
hero.location=(3.42,.53,0);hero.rotation_euler=(0,0,-math.pi/4)
bpy.context.view_layer.update()
boot_soles=[a for a in hero.children_recursive if a.name.startswith('Boot sole')]
lowest=min((a.matrix_world@Vector(c)).z for a in boot_soles for c in a.bound_box)
hero.location.z+=1.65-lowest
cart.location=(.30,-1.55,0)
for a,y in zip([bpy.data.objects['Waiting adult A'],bpy.data.objects['Waiting adult B']],[-3.7,-5.0]):a.location.y=y
rocks=sorted([a for a in basket.children if a.name.startswith('Original loose counterweight stone')],key=lambda a:a.name)
assert len(rocks)==8
for a in rocks:
    a.parent=None;a.animation_data_clear();a.hide_render=False;a.scale*=.65
for a in S.objects:
    if a.name.startswith(('Loose stone supply on solid loading landing','Original stone at actual hand contact')):
        a.hide_render=True
platform=bpy.data.objects['Solid side loading platform']
material=platform.data.materials[0]


def cube(name,loc,size):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    a=bpy.context.object;a.name=name;a.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    a.data.materials.append(material)
    b=a.modifiers.new('Original small edge bevel','BEVEL');b.width=.015;b.segments=2
    a.modifiers.new('Original weighted corners','WEIGHTED_NORMAL')
    return a


tray=cube('Original raised loose-stone tray',(3.48,1.12,2.58),(.55,.44,.04))
plinth=cube('Original solid tray support on landing',(3.48,1.12,2.115),(.45,.30,.93))
assert tray.location.x-tray.dimensions.x/2 > 2.70+.36+.05
assert plinth.location.x-plinth.dimensions.x/2 >= platform.location.x-platform.dimensions.x/2
assert plinth.location.y+plinth.dimensions.y/2 <= platform.location.y+platform.dimensions.y/2
arms={}
for side in [-1,1]:
    shoulder=next(a for a in hero.children if a.name=='Shoulder '+str(side))
    elbow=next(a for a in shoulder.children if a.name.startswith('Elbow'))
    hand=next(a for a in elbow.children if a.name.startswith('Courier hand'))
    arms[side]=shoulder,elbow,hand
neck=next(a for a in hero.children if a.name.startswith('Expressive neck'))


def smooth(q):
    q=max(0,min(1,q));return q*q*(3-2*q)


def solve(side,target):
    shoulder,elbow,hand=arms[side];target=Vector(target)
    bpy.context.view_layer.update();local=hero.matrix_world.inverted()@target
    origin=shoulder.location.copy();delta=local-origin;d=delta.length
    l1,l2=elbow.location.length,hand.location.length
    assert abs(l1-l2)+.0001<d<l1+l2-.0001,(side,d,list(target))
    direction=delta.normalized();along=(l1*l1-l2*l2+d*d)/(2*d)
    height=math.sqrt(max(0,l1*l1-along*along));pref=Vector((side,-.5,-.15))
    bend=(pref-direction*pref.dot(direction)).normalized()
    e=origin+direction*along+bend*height
    q1=elbow.location.normalized().rotation_difference((e-origin).normalized())
    q2=hand.location.normalized().rotation_difference((local-e).normalized())
    shoulder.rotation_mode=elbow.rotation_mode='QUATERNION'
    shoulder.rotation_quaternion=q1;elbow.rotation_quaternion=q1.inverted()@q2
    bpy.context.view_layer.update();error=(hand.matrix_world.translation-target).length
    assert error<.0001
    return error


groups=[[0,1,2],[3,4,5],[6,7]]
zmin=min(v.co.z*rocks[0].scale.z for v in rocks[0].data.vertices)
zmax=max(v.co.z*rocks[0].scale.z for v in rocks[0].data.vertices)
source_centers=[Vector((3.48,1.08,2.60-zmin+layer)) for layer in [.26,.13,0]]
group_offsets=[Vector((-.09,-.04,0)),Vector((.09,-.04,0)),Vector((0,.06,0))]
release_center=Vector((3.00,.28,3.26))
palm_offset=Vector((-.06,-.03,-.13))
source_positions={n:source_centers[g]+group_offsets[j] for g,ids in enumerate(groups) for j,n in enumerate(ids)}
rest_offsets={n:Vector(((n%3-1)*.20,((n//3)%2-.5)*.22,-.62-zmin+(zmax-zmin)*(n//6))) for n in range(8)}
relaxed={side:hero.matrix_world@Vector((side*.35,-.10,.85)) for side in [-1,1]}


def carry(g,t):
    q=smooth((t-pickups[g])/(releases[g]-pickups[g]))
    control=Vector((2.60,.80,(source_centers[g].z+release_center.z)/2+.12))
    center=source_centers[g]*(1-q)**2+control*(2*q*(1-q))+release_center*q*q
    return center,center+palm_offset


def pose(frame):
    t=(frame-1)/24;rise=smooth((t-actions['counterweight_and_gate_travel'][0])/(actions['counterweight_and_gate_travel'][1]-actions['counterweight_and_gate_travel'][0]))
    lift=2.2*rise;gate.location.z=lift;basket.location.z=3.15-lift
    points=rope.data.splines[0].points;points[0].co.z=2.3+lift;points[-1].co.z=3.15-lift
    states=[]
    for g,ids in enumerate(groups):
        for j,n in enumerate(ids):
            if t<=pickups[g]:pos=source_positions[n];state='source'
            elif t<releases[g]:pos=carry(g,t)[0]+group_offsets[j];state='carried'
            elif t<impacts[g]:
                q=(t-releases[g])/(impacts[g]-releases[g]);begin=release_center+group_offsets[j];finish=Vector((2.70,0,3.15))+rest_offsets[n]
                xy=smooth(q/.5)
                pos=Vector((begin.x+(finish.x-begin.x)*xy,begin.y+(finish.y-begin.y)*xy,begin.z+(finish.z-begin.z)*q*q));state='falling'
            else:pos=Vector((2.70,0,float(basket.location.z)))+rest_offsets[n];state='landed'
            rocks[n].location=pos;rocks[n].hide_render=False
            states.append({'id':n,'group':g,'state':state,'center_world':list(pos)})
    target=relaxed[-1]
    if t<=releases[0]:target=carry(0,t)[1]
    elif t<pickups[1]:target=carry(0,releases[0])[1].lerp(carry(1,pickups[1])[1],smooth((t-releases[0])/(pickups[1]-releases[0])))
    elif t<=releases[1]:target=carry(1,t)[1]
    elif t<pickups[2]:target=carry(1,releases[1])[1].lerp(carry(2,pickups[2])[1],smooth((t-releases[1])/(pickups[2]-releases[1])))
    elif t<=releases[2]:target=carry(2,t)[1]
    else:target=carry(2,releases[2])[1].lerp(relaxed[-1],smooth((t-releases[2])/(actions['hands_clear_of_basket']-releases[2])))
    errors={str(side):solve(side,target if side==-1 else relaxed[side]) for side in [-1,1]}
    neck.rotation_euler=(.03,0,.12*math.sin((t-13.25)*2))
    bpy.context.view_layer.update()
    sole_min=min((a.matrix_world@Vector(c)).z for a in boot_soles for c in a.bound_box)
    assert abs(sole_min-1.65)<.0001
    hand=arms[-1][2].matrix_world.translation
    carried=[s for s in states if s['state']=='carried']
    nearest=min((hand-Vector(s['center_world'])).length for s in carried) if carried else None
    # A mitten/group proximity measure, not finger grasp or mesh collision proof.
    if nearest is not None:assert nearest<.15,(frame,nearest)
    for s in states:
        if s['state'] not in ['falling','landed']:continue
        ob=rocks[s['id']]
        vertices=[ob.matrix_world@v.co for v in ob.data.vertices]
        if min(v.z for v in vertices)<float(basket.location.z)-.22:
            assert all(abs(v.x-2.70)<.3001 and abs(v.y)<.2601 for v in vertices),(frame,s['id'],'stone crosses basket wall')
    if t>=actions['hands_clear_of_basket']:
        for side in [-1,1]:
            h=arms[side][2].matrix_world.translation
            assert not (abs(h.x-2.70)<.46 and abs(h.y)<.42),'Hand inside expanded basket travel column'
    assert len(states)==8 and len({s['id'] for s in states})==8 and all(not a.hide_render for a in rocks)
    return {'frame':frame,'seconds':t,'shot':0 if frame<367 else 1,'gate_lift':lift,'basket_attachment_z':float(basket.location.z),'rope_polyline_length':sum((a.co.xyz-b.co.xyz).length for a,b in zip(points,points[1:])),'hero_world':list(hero.location),'sole_min_z':sole_min,'hand_errors':errors,'nearest_carried_stone_center_to_mitten':nearest,'stones':states}


CAMERAS=[((1.3,3.0,4.8),(3.1,.65,2.7),40),((8,-6,5.3),(1.3,.35,2.7),40)]
def view(shot,lenses=None):
    location,target,lens=CAMERAS[shot];camera.location=location
    camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.lens=lenses[shot] if lenses else lens
    bpy.context.view_layer.update()


records=[];extents=[0,0]
for frame in range(319,439):
    r=pose(frame);records.append(r);shot=r['shot'];view(shot)
    objects=[a for actor in [hero,basket] for a in actor.children_recursive if a.type=='MESH' and not a.hide_render]+rocks+[tray]
    if shot==1:objects += [a for a in gate.children if a.type=='MESH']+[rope]
    projected=[world_to_camera_view(S,camera,a.matrix_world@Vector(c)) for a in objects for c in a.bound_box]
    assert all(a.z>0 for a in projected)
    extents[shot]=max(extents[shot],max(max(abs(a.x-.5),abs(a.y-.5)) for a in projected))
lenses=[row[2]*min(1,.43/extents[i]) for i,row in enumerate(CAMERAS)]
assert max(a['rope_polyline_length'] for a in records)-min(a['rope_polyline_length'] for a in records)<.00001
assert abs(records[-1]['gate_lift']-2.2)<.0001
assert all(s['state']=='landed' for s in records[48]['stones'])


def complete_png(path):
    if not path.exists() or path.stat().st_size<36:return False
    with path.open('rb') as f:h=f.read(24);f.seek(-12,2);tail=f.read()
    return h[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>II',h[16:24])==(o.width,o.width*16//9) and tail==b'\x00\x00\x00\x00IEND\xaeB`\x82'


for frame in wanted:
    pose(frame);view(records[frame-319]['shot'],lenses)
    path=o.output/'frames'/f'{frame:05d}.png';receipt=path.with_suffix('.json')
    if complete_png(path) and receipt.exists():
        old=json.loads(receipt.read_text());actual=hashlib.sha256(path.read_bytes()).hexdigest()
        assert old['source_sha256']==source_hash and old['frame']==frame and old['input_acting_blend_sha256']==expected and old['raw_image_sha256']==actual
    else:
        if path.exists():
            held=o.output/'unverified';held.mkdir(exist_ok=True);path.replace(held/(path.stem+'-'+hashlib.sha256(path.read_bytes()).hexdigest()[:16]+'.png'))
        S.render.filepath=str(path);bpy.ops.render.render(write_still=True);actual=hashlib.sha256(path.read_bytes()).hexdigest()
        receipt.write_text(json.dumps({'frame':frame,'source_sha256':source_hash,'input_acting_blend_sha256':expected,'raw_image_sha256':actual},indent=2)+'\n')
    records[frame-319]['raw_image_sha256']=actual
assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==source_hash
report={'id':'counterweight-gate','status':'stone_transfer_and_gate_rise_development_not_full_story','source_sha256':source_hash,'input_acting_blend_sha256':expected,'action_plan_sha256':plan_hash,'fps':24,'test_frames':120,'story_frame_range':[319,438],'duration_seconds':5.0,'rendered_frame_numbers':wanted,'dimensions':[o.width,o.width*16//9],'samples':8,'all120_pose_checks_passed':True,'persistent_stone_object_count':8,'groups':groups,'stone_scale_multiplier':.65,'stone_pickup_seconds':pickups,'stone_release_seconds':releases,'stone_impact_seconds':impacts,'hands_clear_seconds':actions['hands_clear_of_basket'],'cut_boundaries':[[366,367]],'shot_lenses_mm':lenses,'records':records,'checks_scope':'Arm endpoint, static sole support, persistent8objectstate/proximity, stone wall-containment below rim and rope invariants; not full-body swept collision, finger grasp, weight or rigid-body certification.','landing_transition':'Cut from prior top-tread scene elides move onto landing; not an unbroken path.','external_assets_added':[],'visual_inspection_pending':True,'full_story_animation':False,'publishable':False}
(o.output/'stone-loading-study.json').write_text(json.dumps(report,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str((o.output/'stone-loading-study.blend').resolve()))
