"""One shared original Counterweight Gate scene, driven by reviewed motion targets.

New original courtyard/lighting, consistent eight-stone geometry and supported
waiting-foot preparation. No old movie frames, new voice or publishing action.
"""
import argparse,base64,hashlib,json,math,shutil,struct,sys,zlib
from pathlib import Path
import bpy
from mathutils import Euler,Quaternion,Vector
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--stone-blend',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
p.add_argument('--width',type=int,choices=[360,720],default=720);p.add_argument('--frames',type=int,nargs='+',default=[48,110,165,217,244,292,343,386,478,564])
p.add_argument('--check-only',action='store_true');p.add_argument('--all-motion',action='store_true');p.add_argument('--approved-review',type=Path);p.add_argument('--resume',action='store_true');o=p.parse_args(args)
root=next(a for a in Path(__file__).resolve().parents if (a/'AGENTS.md').exists())
expected_blend='0adb6d86642ceb6973beba1db77228841c987903aca7134755a56748811b6873'
expected_cache='997f85f1227c6b1178f39b30b3e8d420ac0f14214f15a7a1670fccbf7d19e232'
assert hashlib.sha256(o.stone_blend.read_bytes()).hexdigest()==expected_blend
cache=root/'assets/stories/counterweight-gate/integrated/motion-cache.zlib.b64';assert hashlib.sha256(cache.read_bytes()).hexdigest()==expected_cache
meta=json.loads(cache.with_name('motion-cache.json').read_text());raw=zlib.decompress(base64.b64decode(cache.read_text()));assert hashlib.sha256(raw).hexdigest()==meta['uncompressed_json_sha256'];motion=json.loads(raw);assert motion['frames']==578
source_hash=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
if o.all_motion:
 assert o.approved_review and json.loads(o.approved_review.read_text())['source_sha256']==source_hash
 assert json.loads(o.approved_review.read_text())['disposition']=='use_for_full_native_render'
wanted=[] if o.check_only else list(range(1,579)) if o.all_motion else sorted(set(o.frames));assert not wanted or min(wanted)>=1 and max(wanted)<=578
if o.output.exists() and any(o.output.iterdir()) and not o.resume:raise SystemExit('Existing output held. Explicit identical-source/settings resume required.')
o.output.mkdir(parents=True,exist_ok=True);(o.output/'frames').mkdir(exist_ok=True)
frozen=o.output/'frozen-integrated-scene.py';fcache=o.output/'frozen-motion-cache.zlib.b64'
for current,fixed,expected in [(Path(__file__),frozen,source_hash),(cache,fcache,expected_cache)]:
 if fixed.exists():assert hashlib.sha256(fixed.read_bytes()).hexdigest()==expected
 elif current.resolve()!=fixed.resolve():shutil.copyfile(current,fixed)
manifest={'frozen_source':str(frozen.resolve()),'source_sha256':source_hash,'motion_cache_sha256':expected_cache,'input_stone_blend_sha256':expected_blend,'width':o.width,'height':o.width*16//9,'frame_numbers':list(range(1,579)),'expected_frames':578,'samples':16,'scope':'Shared-scene source with explicit sample renders; count actual receipts, not allowed frame range, as completed images.'}
mp=o.output/'render-manifest.json'
if mp.exists():assert json.loads(mp.read_text())==manifest,'Refuse mixed source/settings/cache'
else:mp.write_text(json.dumps(manifest,indent=2)+'\n')
bpy.ops.wm.open_mainfile(filepath=str(o.stone_blend.resolve()))
S=bpy.context.scene;S.render.fps=24;S.cycles.samples=16;S.render.threads=2
S.render.resolution_x,S.render.resolution_y=o.width,o.width*16//9;S.render.resolution_percentage=100
hero=bpy.data.objects['Courier master'];waiting=[bpy.data.objects['Waiting adult A'],bpy.data.objects['Waiting adult B']];actors=[hero,*waiting]
cart=bpy.data.objects['Free parcel cart, separate from counterweight'];gate=bpy.data.objects['Vertical gate lift root'];basket=bpy.data.objects['Separate counterweight basket root'];rope=bpy.data.objects['Continuous original gate-to-basket rope'];camera=S.camera
rocks=sorted([a for a in S.objects if a.name.startswith('Original loose counterweight stone')],key=lambda a:a.name);assert len(rocks)==8
parts=[]
for index,(actor,x,y) in enumerate(zip(actors,[0,-.2,.2],[0,-3.7,-5])):
 for a in [actor,*actor.children_recursive]:
  a.animation_data_clear()
  if a.type=='EMPTY':a.rotation_mode='XYZ';a.rotation_euler=(0,0,0)
 actor.location=(x,y,0);actor.rotation_euler=(0,0,math.pi);bpy.context.view_layer.update()
 soles=[a for a in actor.children_recursive if a.name.startswith('Boot sole')];actor.location.z-=min((a.matrix_world@Vector(c)).z for a in soles for c in a.bound_box);bpy.context.view_layer.update()
 legs={};arms={};neutral=[]
 for side,name in [(-1,'Left hip'),(1,'Right hip')]:
  hip=next(a for a in actor.children if a.name.startswith(name));knee=next(a for a in hip.children if a.name.startswith('Knee'));feet=[a for a in knee.children if a.name.startswith(('Boot sole','Courier boot'))]
  ankle=bpy.data.objects.new('Integrated planted ankle '+str(index)+' '+str(side),None);S.collection.objects.link(ankle);ankle.parent=knee;ankle.location=(0,0,-.4);bpy.context.view_layer.update()
  for a in feet:world=a.matrix_world.copy();a.parent=ankle;a.matrix_world=world
  bpy.context.view_layer.update();legs[side]=(hip,knee,ankle,feet);neutral.append(list(ankle.matrix_world.translation))
  shoulder=next(a for a in actor.children if a.name.startswith('Shoulder '+str(side)));elbow=next(a for a in shoulder.children if a.name.startswith('Elbow'));hand=next(a for a in elbow.children if a.name.startswith('Courier hand'));arms[side]=(shoulder,elbow,hand)
 neck=next(a for a in actor.children if a.name.startswith('Expressive neck'));mouth=[next(a for a in neck.children if a.name.startswith(name)) for name in ['Mouth left','Mouth right']]
 parts.append({'actor':actor,'index':index,'scale':actor.scale.x,'neutral_root':list(actor.location),'neutral_feet':neutral,'legs':legs,'arms':arms,'neck':neck,'mouth':mouth,'mouth_lengths':[max(v.co.z for v in a.data.vertices)-min(v.co.z for v in a.data.vertices) for a in mouth],'eyes':[a for a in neck.children if a.name.startswith(('Eye -1','Eye 1'))],'catchlights':[(a,a.location.z,a.scale.copy()) for a in neck.children if a.name.startswith('Eye catchlight')]})
wheels=[a for a in cart.children if a.name.startswith('Cart wheel')]
# New project-owned procedural courtyard. No sampled textures or outside models.
def material(name,color):
 m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes['Principled BSDF'];n.inputs['Base Color'].default_value=(*color,1);n.inputs['Roughness'].default_value=.75;return m
def cube(name,loc,size,mat):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);a=bpy.context.object;a.name=name;a.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);a.data.materials.append(mat);b=a.modifiers.new('Original courtyard eased corners','BEVEL');b.width=.035;b.segments=2;a.modifiers.new('Original courtyard normals','WEIGHTED_NORMAL');return a
wall=material('Integrated courtyard | warm plaster',(.57,.40,.25));trim=material('Integrated courtyard | limestone edging',(.51,.46,.34));green=material('Integrated courtyard | olive foliage',(.11,.24,.075));trunk=material('Integrated courtyard | bark',(.16,.075,.03));pot=material('Integrated courtyard | terracotta',(.38,.15,.075))
floor=bpy.data.objects['Original flat courtyard floor'];fm=material('Integrated courtyard | original paving',(.45,.43,.34));floor.data.materials[0]=fm;n=fm.node_tree.nodes;l=fm.node_tree.links;geo=n.new('ShaderNodeNewGeometry');brick=n.new('ShaderNodeTexBrick');brick.inputs['Color1'].default_value=(.47,.43,.32,1);brick.inputs['Color2'].default_value=(.34,.36,.29,1);brick.inputs['Mortar'].default_value=(.16,.19,.15,1);brick.inputs['Scale'].default_value=1.5;brick.inputs['Mortar Size'].default_value=.018;brick.inputs['Brick Width'].default_value=.8;brick.inputs['Row Height'].default_value=.6;l.new(geo.outputs['Position'],brick.inputs['Vector']);l.new(brick.outputs['Color'],n['Principled BSDF'].inputs['Base Color'])
for x in [-5.8,6.4]:cube('Original low courtyard boundary',(x,0,.55),(.25,14,1.1),wall);cube('Original courtyard coping',(x,0,1.12),(.34,14,.12),trim)
for x in [-3.5,3.5]:cube('Original far street wall',(x,-7,1.7),(4.6,.25,3.4),wall)
cube('Original far street lintel',(0,-7,3.25),(2.4,.25,.30),trim)
for x in [-4.8,4.8]:
 for y in [-3,2]:
  cube('Original planted courtyard pot',(x,y,.23),(.58,.58,.46),pot)
  bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=.42,location=(x,y,.65));bpy.context.object.name='Original clipped olive shrub';bpy.context.object.data.materials.append(green)
for x,y in [(-3.5,5.5),(3.7,6.0)]:
 bpy.ops.mesh.primitive_cylinder_add(vertices=8,radius=.11,depth=1.8,location=(x,y,.9));bpy.context.object.name='Original courtyard tree trunk';bpy.context.object.data.materials.append(trunk)
 for dx,dz,rad in [(-.3,2.0,.75),(.35,2.2,.8),(0,2.65,.7)]:
  bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=rad,location=(x+dx,y,dz));bpy.context.object.name='Original courtyard tree canopy';bpy.context.object.data.materials.append(green)
for a in list(S.objects):
 if a.type=='LIGHT':bpy.data.objects.remove(a,do_unlink=True)
for name,loc,power,color,size in [('Warm courtyard key',(-3,-4,8),1800,(1,.80,.62),5),('Cool courtyard fill',(5,-1,5),650,(.65,.80,1),5),('Courtyard rim',(-2,6,7),900,(1,.87,.68),4)]:
 d=bpy.data.lights.new(name,'AREA');a=bpy.data.objects.new(name,d);S.collection.objects.link(a);a.location=loc;a.rotation_euler=(Vector((0,0,1.5))-a.location).to_track_quat('-Z','Y').to_euler();d.energy=power;d.color=color;d.shape='DISK';d.size=size
S.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.38,.48,.62,1);S.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.35
def solve_chain(actor, first, second, endpoint, target, preference):
    target = Vector(target)
    bpy.context.view_layer.update()
    local = actor.matrix_world.inverted() @ target
    origin = first.location.copy()
    delta = local - origin
    distance = delta.length
    l1, l2 = second.location.length, endpoint.location.length
    assert abs(l1 - l2) + .00001 < distance <= l1 + l2 + .00001, (actor.name, first.name, distance, l1, l2, list(actor.location), list(target))
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


def smooth(q):
 q=max(0,min(1,q));return q*q*(3-2*q)
def mix(a,b,q):return [x+(y-x)*q for x,y in zip(a,b)]
def waiting_state(index,frame):
 if frame>=439:return motion['waiting_passage'][frame-439][index-1]
 p=parts[index];t=(frame-1)/24;target=motion['waiting_passage'][0][index-1];root_pos=mix(p['neutral_root'],target['root'],smooth((t-16.7)/.3));feet=[]
 for j in [0,1]:
  start,end=(17.0,17.5) if j==0 else (17.55,18.15);q=max(0,min(1,(t-start)/(end-start)));v=mix(p['neutral_feet'][j],target['feet'][j],smooth(q));v[2]+=.045*p['scale']*math.sin(math.pi*q);feet.append(v)
 actor=p['actor'];actor.location=root_pos;bpy.context.view_layer.update();hands=[list(actor.matrix_world@Vector((side*.34,-.12,.78))) for side in [-1,1]]
 return {'root':root_pos,'yaw':math.pi,'feet':feet,'hands':hands,'neck':[.02,0,.10 if index==1 else .16]}
def expression(p,concern,t):
 neck=p['neck'];center=Vector((0,-.199,.137+.010*concern));corners=[Vector((-.059,-.188,.15-.030*concern)),Vector((.059,-.188,.15-.030*concern))]
 for ob,length,(first,last) in zip(p['mouth'],p['mouth_lengths'],[(corners[0],center),(center,corners[1])]):ob.location=(first+last)/2;ob.rotation_euler=(last-first).to_track_quat('Z','Y').to_euler();ob.scale.z=(last-first).length/length
 for side in [-1,1]:next(a for a in neck.children if a.name.startswith('Eyebrow '+str(side))).rotation_euler.y=side*(.10-.28*concern)
 blink=1
 for at in [2.1,6.4,8.7,12.4,15.7,19.3,22.5]:
  d=abs(t-at-p['index']*.06)
  if d<.10:blink=min(blink,.15+.85*d/.10)
 for eye in p['eyes']:eye.scale.z=blink
 for light,original_z,original_scale in p['catchlights']:
  light.location.z=.277+(original_z-.277)*blink
  light.scale=original_scale*blink
 return blink
def apply_actor(p,r,t,concern):
 actor=p['actor'];actor.location=r['root'];actor.rotation_euler=(0,0,r['yaw']);feet=[];errors=[]
 for side,target in zip([-1,1],r['feet']):
  hip,knee,ankle,meshes=p['legs'][side];err=solve_chain(actor,hip,knee,ankle,target,(0,-1,0));ankle.rotation_mode='QUATERNION';ankle.rotation_quaternion=knee.matrix_world.to_quaternion().inverted()@actor.matrix_world.to_quaternion();bpy.context.view_layer.update();sole=next(a for a in meshes if a.name.startswith('Boot sole'));z=min((sole.matrix_world@Vector(c)).z for c in sole.bound_box);expected=target[2]-.065*p['scale'];assert abs(z-expected)<.0001,(t,p['index'],side,z,expected);assert z>-.0001;feet.append({'side':side,'ankle_world':list(ankle.matrix_world.translation),'sole_min_z':z,'target_error':err})
 for side,target in zip([-1,1],r['hands']):errors.append(solve_chain(actor,*p['arms'][side],target,(side,-.5,-.15)))
 p['neck'].rotation_euler=r['neck'];blink=expression(p,concern,t);return {'cast_index':p['index'],'root':list(actor.location),'feet':feet,'hand_errors':errors,'blink_factor':blink}
CUTS=[92,140,198,226,263,319,367,439,499]
CAMERAS=[((-3.6,-4.2,2.7),(0,-.9,1.15),20.333589),((-3.25,-1.9,2.2),(-.52,-.3,.95),19.159978),((1.4,-1,2.15),(-.15,-3.9,1.25),17.872408),((1.8,-.65,2.15),(-.52,-.66,1.55),42.791922),((8,-6,5.3),(1,.15,2.65),17.697201),((7,5.4,4.2),(3.7,2.15,1.8),29),((1.3,3,4.8),(3.1,.65,2.7),18.231915),((8,-6,5.3),(1.3,.35,2.7),20.635916),(None,None,31.930495),((-.85,6.5,2.0),(-.1,-.8,1.0),32)]
def pose(frame):
 t=(frame-1)/24;r=motion['hero'][frame-1];shot=sum(frame>=c for c in CUTS)
 gate.location.z=r['gate'];basket.location.z=3.15-r['gate'];points=rope.data.splines[0].points;points[0].co.z=2.3+r['gate'];points[-1].co.z=3.15-r['gate'];cart.location=(.30,r['cart_y'],0)
 for wheel in wheels:wheel.rotation_mode='QUATERNION';wheel.rotation_quaternion=Euler((0,math.pi/2,0)).to_quaternion()@Quaternion(Vector((0,0,1)),r['wheel'])
 centers=motion['source_stones'] if frame<319 else motion['stone_centers'][min(frame,438)-319]
 for rock,pos in zip(rocks,centers):rock.location=pos;rock.hide_render=False
 cast=[apply_actor(parts[0],r,t,r['concern'])]
 for index in [1,2]:cast.append(apply_actor(parts[index],waiting_state(index,frame),t,.45*smooth((t-3.1)/2.0)*(1-smooth((t-16.4)/.8))))
 location,target,lens=CAMERAS[shot]
 if shot==8:location=(1.05,r['root'][1]-3.6,2.35);target=(.30,r['root'][1]+.55,1.0)
 camera.location=location;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.lens=lens;bpy.context.view_layer.update()
 return {'frame':frame,'seconds':t,'shot':shot,'cast':cast,'gate_lift':float(gate.location.z),'basket_attachment_z':float(basket.location.z),'rope_length':sum((a.co.xyz-b.co.xyz).length for a,b in zip(points,points[1:])),'camera_lens_mm':lens,'persistent_stones':8}
records=[pose(f) for f in range(1,579)]
assert max(r['rope_length'] for r in records)-min(r['rope_length'] for r in records)<.00001
assert all(len(r['cast'])==3 and r['persistent_stones']==8 for r in records)
def complete_png(path):
 if not path.exists() or path.stat().st_size<36:return False
 with path.open('rb') as f:h=f.read(24);f.seek(-12,2);tail=f.read()
 return h[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>II',h[16:24])==(o.width,o.width*16//9) and tail==b'\x00\x00\x00\x00IEND\xaeB`\x82'
for frame in wanted:
 pose(frame);path=o.output/'frames'/f'{frame:05d}.png';receipt=path.with_suffix('.json')
 if complete_png(path) and receipt.exists():
  old=json.loads(receipt.read_text());actual=hashlib.sha256(path.read_bytes()).hexdigest();assert old['source_sha256']==source_hash and old['frame']==frame and old['motion_cache_sha256']==expected_cache and old['raw_image_sha256']==actual
 else:
  if path.exists():raise SystemExit('Unverified image retained; inspect before recovery.')
  S.render.filepath=str(path);bpy.ops.render.render(write_still=True);actual=hashlib.sha256(path.read_bytes()).hexdigest();receipt.write_text(json.dumps({'frame':frame,'source_sha256':source_hash,'motion_cache_sha256':expected_cache,'input_stone_blend_sha256':expected_blend,'raw_image_sha256':actual},indent=2)+'\n')
 records[frame-1]['raw_image_sha256']=actual
assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==source_hash
report={'id':'counterweight-gate','source_sha256':source_hash,'motion_cache_sha256':expected_cache,'input_stone_blend_sha256':expected_blend,'scope':'One shared original full-timeline scene; only listed frames actually rendered. No completed-film claim.','fps':24,'planned_frames':578,'rendered_frame_numbers':wanted,'dimensions':[o.width,o.width*16//9],'samples':16,'all578_pose_endpoint_and_sole_checks_passed':True,'records':records,'cut_boundaries':[[c-1,c] for c in CUTS],'shared_tray_and_eight_stones_throughout':True,'waiting_to_ready_pose_preparation_seconds':[16.7,18.15],'new_external_assets':[],'narration_regenerated':False,'audio_remixed':False,'full_encoded_movie_exists':False,'visual_inspection_pending':True,'publishable':False,'checks_scope':'Sampled endpoints, sole planes and rope state; not full-body swept collision, realism, subjective listening or whole-film editorial approval.'}
(o.output/'integrated-scene.json').write_text(json.dumps(report,indent=2)+'\n');bpy.ops.wm.save_as_mainfile(filepath=str((o.output/'integrated-scene.blend').resolve()))
