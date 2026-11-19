"""Native opening proof and one-second fixed-bone lamp-release diagnostic.

Reuses the owned scene source, not old pictures or performances. Silent study
only; it does not render the walk, full narrative, captions or final soundtrack.
"""
import argparse
import hashlib
import json
import math
import runpy
import shutil
import sys
from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

ROOT=next(p for p in Path(__file__).resolve().parents if (p/'AGENTS.md').exists())
p=argparse.ArgumentParser()
p.add_argument('--output',required=True,type=Path)
mode=p.add_mutually_exclusive_group()
mode.add_argument('--only-opening',action='store_true')
mode.add_argument('--only-motion',action='store_true')
p.add_argument('--motion-frames',type=int,nargs='+',help='Bounded critical poses; omit to fill all24matching frames.')
args=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
out=args.output.resolve();out.mkdir(parents=True,exist_ok=True);(out/'frames').mkdir(exist_ok=True)
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
source_hash=digest(Path(__file__))
base=ROOT/'assets/stories/last-charge/staging-study.py'
assert digest(base)=='647468191e2d5fe41986877b0374a249d32032a7fe264aea4404fe103932194a'
story=json.loads((ROOT/'stories/last-charge.json').read_text())
voice=ROOT/story['private_existing_narration']/'narration-clean.wav'
assert digest(voice)==story['clean_narration_sha256']=='33562e4149c22087cc3be49171cb7fda90cb7746fbefc9b031c89a1384aced1a'
frozen=out/'frozen-opening-release-study.py';frozen_base=out/'frozen-base-staging.py'
for src,dst in [(Path(__file__),frozen),(base,frozen_base)]:
    if dst.exists():assert digest(dst)==digest(src)
    else:shutil.copyfile(src,dst)
inputs={'source_sha256':source_hash,'base_scene_source_sha256':digest(base),'existing_clean_narration_sha256':digest(voice),'native_dimensions':[720,1280],'fps':24,'motion_frames':24,'opening_study_item':1001,'audio_in_study':False}
ip=out/'source-inputs.json'
if ip.exists():assert json.loads(ip.read_text())==inputs
else:ip.write_text(json.dumps(inputs,indent=2)+'\n')
old_argv=sys.argv
try:
    sys.argv=[str(frozen_base),'--','--output',str(out/'base-scene')]
    ns=runpy.run_path(str(frozen_base),run_name='__original_stage_base__')
finally:sys.argv=old_argv
scene=ns['scene'];camera=ns['camera'];actors=ns['actors'];lamps=ns['lamps']
wall_front=ns['shop_front']+.045
ns['cube']('Original added bracket wall plate',(-1.83,wall_front-.015,1.39),(.10,.03,.12),ns['mats']['brass'],bevel=.012)
ns['rod']('Original added bracket mounting connector',(-1.83,wall_front-.015,1.39),(-1.83,ns['shop_front']-.08,1.39),.022,ns['mats']['brass'])
manifest={'frozen_source':str(frozen),'source_sha256':source_hash,'base_scene_source_sha256':digest(base),'width':720,'height':1280,'frame_numbers':list(range(1,25))+[1001],'cycles_samples':12,'kind':'one_opening_proof_and24native_contact_release_samples_not_full_story','spatial_upscale':False,'frame_interpolation':False}
mp=out/'render-manifest.json'
if mp.exists():assert json.loads(mp.read_text())==manifest
else:mp.write_text(json.dumps(manifest,indent=2)+'\n')

def balance_lamps():
    for lamp in lamps:
        if lamp['light'].energy:lamp['light'].energy=55
        lamp['glow'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value=1.7 if lamp['light'].energy else .025
    ns['mats']['cell'].node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.016,.04,.05,1)
    ns['mats']['cell'].node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.8

def render_item(number,kind,checks):
    image=out/'frames'/f'{number:05d}.png';receipt=image.with_suffix('.json')
    if image.exists() and receipt.exists():
        prior=json.loads(receipt.read_text());assert prior['source_sha256']==source_hash and prior['raw_image_sha256']==digest(image)
        return prior
    assert not image.exists(),'Unreceipted existing output is held, not replaced.'
    scene.frame_set(number);scene.render.filepath=str(image);bpy.context.view_layer.update()
    bpy.ops.render.render(write_still=True)
    row={'study_item':number,'kind':kind,'source_sha256':source_hash,'base_scene_source_sha256':digest(base),'raw_image_sha256':digest(image),'dimensions':[720,1280],'numeric_checks':checks,'actual_visual_review_pending':True}
    receipt.write_text(json.dumps(row,indent=2)+'\n');return row

def bounds(objects):
    points=[world_to_camera_view(scene,camera,ob.matrix_world@Vector(c)) for ob in objects for c in ob.bound_box]
    return {'min_x':min(p.x for p in points),'max_x':max(p.x for p in points),'min_y':min(p.y for p in points),'max_y':max(p.y for p in points),'min_depth':min(p.z for p in points)}

if not args.only_motion:
    ns['set_pose'](1);balance_lamps()
    rose=actors['rose']['root'];door=scene.objects['Rose shop door'];bracket=scene.objects['Rose empty personal lamp bracket']
    objects=[o for o in list(rose.children_recursive)+list(lamps[0]['root'].children_recursive)+[door,bracket] if o.type in {'MESH','CURVE'}]
    coordinates=[ob.matrix_world@Vector(c) for ob in objects for c in ob.bound_box]
    center=Vector(tuple((min(p[i] for p in coordinates)+max(p[i] for p in coordinates))/2 for i in range(3)))
    direction=Vector((.8,-1.0,.35)).normalized();distance=3.0;camera.data.lens=45
    for attempt in range(40):
        camera.location=center+direction*distance;camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler();bpy.context.view_layer.update();b=bounds(objects)
        if b['min_x']>.07 and b['max_x']<.93 and b['min_y']>.06 and b['max_y']<.94 and b['min_depth']>0:break
        distance*=1.06
    else:raise AssertionError('Opening subject bounds do not fit.')
    checks={'rose_lamp_door_bracket_projected_bounds':b,'cell_mark_count':lamps[0]['marks'],'independent_lamp_pool_powers':[l['light'].energy for l in lamps],'bounds_do_not_establish_visibility_through_occluders':True}
    render_item(1001,'close_opening_lamp_and_own_empty_bracket',checks)

if not args.only_opening:
    ns['set_pose'](3);balance_lamps()
    actors['far']['root'].location=(-2.25,2.26,.08)
    bpy.context.view_layer.update()
    rose=actors['rose'];root=rose['root'];hand=rose['hands']['right']
    shoulder=Vector((.255,0,1.16));initial_elbow=Vector((.28,-.29,1.25));initial_hand=Vector((.10,-.57,1.41))
    upper_length=(initial_elbow-shoulder).length;fore_length=(initial_hand-initial_elbow).length
    sleeves=[o for o in rose['limbs'] if 'right original sleeve' in o.name]
    assert len(sleeves)==2
    upper=min(sleeves,key=lambda o:(o.location-(shoulder+initial_elbow)/2).length)
    fore=next(o for o in sleeves if o!=upper)
    elbow_ball=next(o for o in rose['limbs'] if 'right rounded elbow' in o.name)
    mesh_lengths={o.name:max(v.co.z for v in o.data.vertices)-min(v.co.z for v in o.data.vertices) for o in sleeves}
    initial_axis=(initial_hand-shoulder).normalized();initial_a=(upper_length**2-fore_length**2+(initial_hand-shoulder).length**2)/(2*(initial_hand-shoulder).length)
    pole=(initial_elbow-shoulder-initial_axis*initial_a).normalized()
    lamp_matrix=lamps[0]['root'].matrix_world.copy();fixed_base=lamps[0]['root'].location.copy()
    fixed_handle=lamp_matrix@Vector((0,0,.55))
    sole_plane=root.location.z
    def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)
    def target_at(progress):
        # Lift away from the grip, retract while above the frame, then lower
        # beside the chest. This avoids a straight path through the lamp cap.
        a=initial_hand;b=Vector((.27,-.48,1.49));c=Vector((.43,-.32,1.28));d=Vector((.30,-.20,1.05))
        if progress<.30:return a.lerp(b,smooth(progress/.30))
        if progress<.72:return b.lerp(c,smooth((progress-.30)/.42))
        return c.lerp(d,smooth((progress-.72)/.28))
    def solve_elbow(target):
        axis=target-shoulder;distance=axis.length
        assert abs(upper_length-fore_length)+1e-6<distance<upper_length+fore_length-1e-6
        axis.normalize();a=(upper_length**2-fore_length**2+distance**2)/(2*distance)
        normal=pole-axis*pole.dot(axis);assert normal.length>.01;normal.normalize()
        return shoulder+axis*a+normal*math.sqrt(max(0,upper_length**2-a*a))
    def position_rod(ob,a,b):
        v=b-a;ob.location=(a+b)/2;ob.rotation_euler=v.to_track_quat('Z','Y').to_euler();ob.scale=(1,1,v.length/mesh_lengths[ob.name])
    def box_distance(point,lo,hi):
        return math.sqrt(sum(max(lo[i]-point[i],0,point[i]-hi[i])**2 for i in range(3)))
    # Validate the entire requested path before spending native render time.
    for n in range(1,25):
        progress=max(0,min(1,((n-1)/24-.05)/.65));target=target_at(progress);elbow=solve_elbow(target)
        world=root.matrix_world@target;relative=lamp_matrix.inverted()@world
        assert box_distance(relative,(-.145,-.145,.3525),(.145,.145,.4175))>.06
        assert box_distance(relative,(-.13,-.18,.0),(.13,.13,.35))>.06
        assert abs((elbow-shoulder).length-upper_length)<1e-5 and abs((target-elbow).length-fore_length)<1e-5
    requested=set(args.motion_frames or range(1,25));assert requested.issubset(set(range(1,25)))
    records=[]
    for number in range(1,25):
        local_t=(number-1)/24;progress=max(0,min(1,(local_t-.05)/.65));target=target_at(progress);elbow=solve_elbow(target)
        position_rod(upper,shoulder,elbow);position_rod(fore,elbow,target);elbow_ball.location=elbow;hand.location=target
        bpy.context.view_layer.update();world_hand=hand.matrix_world.translation;relative=lamp_matrix.inverted()@world_hand
        cap_clearance=box_distance(relative,(-.145,-.145,.3525),(.145,.145,.4175))-.06
        body_clearance=box_distance(relative,(-.13,-.18,.0),(.13,.13,.35))-.06
        assert cap_clearance>0 and body_clearance>0
        sole_error=max(abs(min((ob.matrix_world@Vector(v)).z for v in ob.bound_box)-sole_plane) for ob in rose['feet'])
        assert sole_error<1e-5 and (lamps[0]['root'].location-fixed_base).length<1e-7
        length_error=max(abs((elbow-shoulder).length-upper_length),abs((target-elbow).length-fore_length));assert length_error<1e-5
        checks={'local_seconds':local_t,'planned_story_seconds':10.5+local_t,'release_progress':progress,'fixed_upper_arm_length':upper_length,'fixed_forearm_length':fore_length,'bone_length_error':length_error,'hand_center_to_handle_center':(world_hand-fixed_handle).length,'mitten_sphere_clearance_from_lamp_cap_box':cap_clearance,'mitten_sphere_clearance_from_lamp_body_box':body_clearance,'static_shoe_sole_plane_error':sole_error,'lamp_root_unchanged':True,'first_cell_marks':lamps[0]['marks'],'independent_pool_powers':[l['light'].energy for l in lamps]}
        if number in requested:render_item(number,'native_contact_release_sample',checks)
        receipt=out/'frames'/f'{number:05d}.json'
        if receipt.exists():records.append(json.loads(receipt.read_text()))
    if len(records)==24:
        assert records[0]['numeric_checks']['hand_center_to_handle_center']<1e-5
        assert records[-1]['numeric_checks']['hand_center_to_handle_center']>.4
        (out/'contact-release-samples.json').write_text(json.dumps({'inputs':inputs,'frames':records,'all24_numeric_samples_passed':True,'actual_visual_review_pending':True,'scope':'Fixed bone lengths, sampled mitten/cap/body boxes, fixed lamp and static soles. No full-body swept collision, fingers, walking, gaze or narrative continuity verdict.','audio_present':False,'finished_story_exists':False,'publishable':False},indent=2)+'\n')
    else:
        (out/'partial-contact-samples.json').write_text(json.dumps({'completed_frames':[r['study_item'] for r in records],'target_frames':24,'all24_numeric_path_samples_checked':True,'actual_visual_review_pending':True,'finished_motion_study_exists':False,'publishable':False},indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(out/'opening-release-study.blend'))
print(json.dumps({'source_sha256':source_hash,'only_opening':args.only_opening,'only_motion':args.only_motion,'native_release_samples_existing':sum((out/'frames'/f'{n:05d}.png').exists() for n in range(1,25)),'opening_proof_exists':(out/'frames/01001.png').exists(),'finished_video_exists':False,'publishable':False}),flush=True)
