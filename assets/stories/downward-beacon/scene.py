"""The Downward Beacon — original stylized geometry, character, animation and cameras.
No imported character meshes, textures, game assets, motion clips or copyrighted logos.
Run Blender headlessly with --python downward_beacon.py -- --stills / --motion / --full.
"""
import bpy, math, random, json, time, sys, argparse
from pathlib import Path
from mathutils import Vector, Quaternion, Matrix, Euler
R=Path(__file__).resolve().parent; random.seed(1711)
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
ap=argparse.ArgumentParser();ap.add_argument('--stills',action='store_true');ap.add_argument('--audit',action='store_true');ap.add_argument('--motion',action='store_true');ap.add_argument('--full',action='store_true');ap.add_argument('--engine',default='CYCLES');ap.add_argument('--samples',type=int,default=16);ap.add_argument('--scale',type=int,default=100);ap.add_argument('--fps',type=int,default=24);ap.add_argument('--width',type=int,default=1080);ap.add_argument('--height',type=int,default=1920);ap.add_argument('--start',type=int);ap.add_argument('--end',type=int);o=ap.parse_args(args)
FPS=o.fps; END=round(33*FPS)
def F(t):return round(t*FPS)+1
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for x in list(bpy.data.materials):bpy.data.materials.remove(x)
S=bpy.context.scene;S.frame_start=1;S.frame_end=END;S.render.fps=FPS;S.render.resolution_x=o.width;S.render.resolution_y=o.height;S.render.resolution_percentage=o.scale;S.render.image_settings.file_format='PNG';S.render.film_transparent=False;S.render.threads_mode='FIXED';S.render.threads=2
S.render.engine=o.engine
if o.engine=='CYCLES':
 S.cycles.device='CPU';S.cycles.samples=o.samples;S.cycles.use_denoising=False;S.cycles.max_bounces=3;S.cycles.diffuse_bounces=1;S.cycles.glossy_bounces=1;S.cycles.transmission_bounces=2;S.cycles.transparent_max_bounces=4;S.cycles.use_adaptive_sampling=True;S.cycles.adaptive_threshold=.12;S.cycles.use_light_tree=True
else:S.eevee.taa_render_samples=o.samples
S.render.use_persistent_data=True;S.view_settings.view_transform='AgX';S.view_settings.look='AgX - Medium High Contrast';S.view_settings.exposure=.5
S.world.use_nodes=True;S.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.025,.05,.12,1);S.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.45

def mat(n,c,rough=.65,metal=0,emit=0):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
 if emit:p.inputs['Emission Color'].default_value=(*c,1);p.inputs['Emission Strength'].default_value=emit
 return m
M={
'rock':mat('Cliff | deep slate',(.10,.16,.23)), 'rock2':mat('Cliff | indigo strata',(.17,.24,.31)), 'soil':mat('Cut earth | cinnamon',(.29,.18,.13)), 'grass':mat('Island | blue-green moss',(.16,.33,.28)), 'path':mat('Warm sandstone path',(.47,.40,.29)),
'plaster':mat('Ivory plaster',(.73,.68,.53)), 'roof':mat('Storm blue roofs',(.055,.12,.20),.42), 'terracotta':mat('Burnt copper roofs',(.44,.17,.10)), 'wood':mat('Old cedar',(.22,.10,.055)), 'woodlight':mat('Cedar worn edges',(.39,.22,.105)),
'gold':mat('Beacon | aged brass',(.60,.36,.105),.30,.65), 'darkmetal':mat('Ink blue iron',(.04,.075,.11),.32,.60), 'window':mat('Warm window glass',(.95,.40,.08),.35,0,5.0),
'jacket':mat('Courier | amber jacket',(.84,.35,.045),.58), 'jacketlight':mat('Courier | golden cuffs',(.98,.56,.12)), 'pants':mat('Courier | navy trousers',(.045,.085,.15)), 'boots':mat('Courier | worn boots',(.105,.065,.043)), 'scarf':mat('Courier | vermilion scarf',(.69,.035,.035)), 'bag':mat('Courier | teal canvas bag',(.07,.22,.21)), 'skin':mat('Courier | warm skin',(.62,.34,.20),.65), 'hair':mat('Courier | dark auburn hair',(.065,.033,.024)), 'eye':mat('Courier | eyes',(.012,.021,.027),.24), 'white':mat('Paper | warm white',(.91,.88,.74)), 'paperfold':mat('Paper | shaded folds',(.66,.72,.70)), 'ink':mat('Note | charcoal ink',(.035,.055,.064)),
'cloud':mat('Cloud tops | lavender white',(.62,.70,.82)), 'cloudlight':mat('Cloud caps | pearl',(.78,.79,.86)), 'sea':mat('Ocean | deep cerulean',(.025,.16,.24),.24,.3), 'sea2':mat('Ocean | teal facets',(.04,.21,.27),.28,.25), 'light':mat('Beacon | golden lens',(.98,.66,.23),.25,0,8), 'answer':mat('Answer | ice blue lens',(.22,.69,1.0),.25,0,1), 'flower':mat('Star flowers',(.97,.69,.23),.5,0,.15)}

def parent(obj,p):
 if p:obj.parent=p
 return obj

def empty(n,loc=(0,0,0),p=None):
 a=bpy.data.objects.new(n,None);S.collection.objects.link(a);a.location=loc;parent(a,p);return a

def cube(n,loc,scale,ma,p=None,bevel=.035):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);a=bpy.context.object;a.name=n;a.dimensions=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);a.data.materials.append(ma);parent(a,p)
 if bevel:
  b=a.modifiers.new('Hand-crafted eased edges','BEVEL');b.width=bevel;b.segments=1;b.affect='EDGES';a.modifiers.new('Weighted face normals','WEIGHTED_NORMAL')
 return a

def cyl(n,loc,r,depth,ma,p=None,verts=12):
 bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=depth,location=loc);a=bpy.context.object;a.name=n;a.data.materials.append(ma);parent(a,p);b=a.modifiers.new('Edge glints','BEVEL');b.width=min(.025,r*.12);b.segments=1;a.modifiers.new('Weighted normals','WEIGHTED_NORMAL');return a

def ico(n,loc,scale,ma,p=None,sub=1):
 bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub,radius=1,location=loc);a=bpy.context.object;a.name=n;a.scale=scale;a.data.materials.append(ma);parent(a,p);return a

def mesh(n,v,faces,ma,p=None):
 data=bpy.data.meshes.new(n);data.from_pydata(v,[],faces);data.materials.append(ma);a=bpy.data.objects.new(n,data);S.collection.objects.link(a);parent(a,p);return a

def rod(n,a,b,r,ma,p=None):
 a,b=Vector(a),Vector(b);ob=cyl(n,(a+b)/2,r,(b-a).length,ma,p,8);ob.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return ob

def light(n,loc,color,power,size=4,kind='AREA',target=None,p=None):
 d=bpy.data.lights.new(n,kind);d.color=color;d.energy=power
 if kind=='AREA':d.shape='DISK';d.size=size
 if kind=='SPOT':d.spot_size=math.radians(28);d.spot_blend=.6;d.shadow_soft_size=.18
 a=bpy.data.objects.new(n,d);S.collection.objects.link(a);a.location=loc;parent(a,p)
 if target:a.rotation_euler=(Vector(target)-a.location).to_track_quat('-Z','Y').to_euler()
 return a

def key(ob,t,prop,val):
 setattr(ob,prop,val);ob.keyframe_insert(data_path=prop,frame=F(t))

def linear(ob):
 if ob.animation_data and ob.animation_data.action:
  for fc in ob.animation_data.action.fcurves:
   for k in fc.keyframe_points:k.interpolation='LINEAR'

def roof(n,center,w,d,h,ma,p=None):
 x,y,z=center;v=[(x-w/2,y-d/2,z),(x+w/2,y-d/2,z),(x+w/2,y+d/2,z),(x-w/2,y+d/2,z),(x,y-d/2,z+h),(x,y+d/2,z+h)]
 return mesh(n,v,[(0,1,4),(3,5,2),(0,4,5,3),(1,2,5,4),(0,3,2,1)],ma,p)

def house(n,loc,w=1,d=1,h=1,roofmat=None):
 g=empty(n,loc);cube(n+' plaster',(0,0,h/2),(w,d,h),M['plaster'],g,.05);roof(n+' roof',(0,0,h),w+.16,d+.18,.45,roofmat or M['roof'],g)
 cube(n+' door',(0,-d/2-.02,.32),(.24,.05,.60),M['wood'],g,.02)
 for x in [-w*.29,w*.29]:
  cube(n+' window',(x,-d/2-.04,h*.66),(.19,.045,.22),M['window'],g,.015)
  cube(n+' sill',(x,-d/2-.07,h*.52),(.25,.10,.04),M['wood'],g,.01)
  cube(n+' cross',(x,-d/2-.07,h*.66),(.025,.03,.22),M['wood'],g,.004)
 cube(n+' chimney',(w*.3,d*.2,h+.3),(.18,.19,.6),M['rock2'],g,.02)
 for x in [-w/2+.06,w/2-.06]:cube(n+' beams',(x,-d/2-.035,h/2),(.06,.04,h),M['woodlight'],g,.008)
 return g

def island(n,c,r,z,depth):
 N=9;ang=[i*math.tau/N for i in range(N)];rad=[r*(.84+random.random()*.2) for _ in ang];v=[]
 for level,factor in [(z,1),(z-.48,1.03),(z-depth*.65,.64),(z-depth,.12)]:v.extend([(c[0]+math.cos(a)*rad[i]*factor,c[1]+math.sin(a)*rad[i]*factor,level) for i,a in enumerate(ang)])
 faces=[tuple(range(N))];idx=[3]
 for ring in range(3):
  for i in range(N):faces.append((ring*N+i,(ring+1)*N+i,(ring+1)*N+(i+1)%N,ring*N+(i+1)%N));idx.append([2,0,1][ring])
 faces.append(tuple(range(3*N,4*N)));idx.append(0)
 a=mesh(n,v,faces,M['rock']);a.data.materials.append(M['rock2']);a.data.materials.append(M['soil']);a.data.materials.append(M['grass'])
 for p,i in zip(a.data.polygons,idx):p.material_index=i
 for _ in range(11):
  aa=random.random()*math.tau;rr=r*.92;ico('Suspended cliff stones',(c[0]+math.cos(aa)*rr,c[1]+math.sin(aa)*rr,z-.8-random.random()*depth*.5),(.3,.25,.5),M['rock2'])
 return a

# Floating town and the lower coastal town are original geometry.
island('The upper floating island',(0,0),4.35,.28,3.8)
for loc,w,d,h,m in [((-2.65,1.0,.30),1.35,1.25,1.35,M['terracotta']),((2.5,1.2,.30),1.25,1.15,1.10,M['roof']),((-2.3,-.50,.30),.95,.8,1.05,M['roof']),((2.45,-.5,.30),.9,.85,.85,M['terracotta'])]:house('Upper town cottage',loc,w,d,h,m)
for x in [-3.2,-2.6,-2.0,-1.4,-.8,-.2,.4,1.0,1.6]:cube('Walkway stone',(x,-1.50,.32),(.55,.75,.10),M['path'],bevel=.04)
for x in [-3.6,-2.8,-2.0,-1.2,-.4,.4,1.2,2.0,2.8,3.6]:
 yy=-2.9+abs(x)*.10;cube('Cliff rail post',(x,yy,.61),(.10,.10,.68),M['wood'],bevel=.012)
for x in [-3.2,-2.4,-1.6,-.8,0,.8,1.6,2.4,3.2]:cube('Cliff rail',(x,-2.9+abs(x)*.1,.83),(.88,.08,.08),M['woodlight'],bevel=.01)
for _ in range(24):
 x=random.uniform(-3.6,3.6);y=random.uniform(-2.5,2.6)
 if abs(x)<1.2 or abs(y+1.5)<.6:continue
 rod('Flower stem',(x,y,.29),(x,y,.49),.012,M['grass']);ico('Star-shaped flower',(x,y,.50),(.08,.08,.07),M['flower'])
# Lighthouse: eight-sided, bronze-framed lantern and original external spiral stair.
cyl('Lighthouse ivory shaft',(0,.1,2.3),.68,4.1,M['plaster'],verts=8)
for z in [.55,2.0,3.45]:cyl('Lighthouse stone band',(0,.1,z),.715,.15,M['rock2'],verts=8)
cube('Lighthouse blue door',(0,-.597,1.02),(.42,.06,1.3),M['darkmetal'],bevel=.05)
for z in [1.85,3.2]:cube('Tower slit window',(.05,-.609,z),(.16,.04,.37),M['window'],bevel=.02)
cyl('Lantern balcony',(0,.1,4.25),1.18,.18,M['woodlight'],verts=12)
for i in range(12):
 a=math.tau*i/12;x=1.12*math.cos(a);y=.1+1.12*math.sin(a)
 # Keep the action-camera side open, with a low decorative rim instead of occluding hands.
 if y>.15:rod('Gallery railing',(x,y,4.34),(x,y,4.93),.024,M['darkmetal'])
for i in range(34):
 a=i*.19;x=1.0*math.cos(a);y=.1+1.0*math.sin(a);z=.36+i*.113
 st=cube('Spiral timber stair',(x,y,z),(.48,.29,.075),M['woodlight'],bevel=.012);st.rotation_euler[2]=a
cyl('Lantern floor',(0,.1,4.58),.85,.15,M['darkmetal'],verts=8)
for i in range(8):
 a=math.tau*i/8;rod('Lantern bronze upright',(.77*math.cos(a),.1+.77*math.sin(a),4.65),(.77*math.cos(a),.1+.77*math.sin(a),6.39),.038,M['gold'])
cyl('Lantern eave',(0,.1,6.42),.98,.12,M['darkmetal'],verts=8)
bpy.ops.mesh.primitive_cone_add(vertices=8,radius1=1.05,radius2=.18,depth=.62,location=(0,.1,6.78));bpy.context.object.name='Lighthouse faceted blue roof';bpy.context.object.data.materials.append(M['roof'])
cyl('Lighthouse finial',(0,.1,7.24),.035,.40,M['gold'],verts=8)
# Original optical assembly and animated down-tilt.
optic=empty('Main beacon gimbal',(0,.10,5.52))
cube('Bronze optical case',(0,.06,0),(.62,.58,.48),M['gold'],optic,.06)
lens=cyl('Main golden lens',(0,.39,0),.265,.11,M['light'],optic,16);lens.rotation_euler[0]=math.pi/2
rim=cyl('Lens iron rim',(0,.34,0),.315,.075,M['darkmetal'],optic,16);rim.rotation_euler[0]=math.pi/2
for x in [-.39,.39]:cube('Gimbal side mount',(x,0,-.12),(.11,.45,.47),M['darkmetal'],bevel=.025,p=optic)
spot=light('Actual moving spotlight',(0,.45,0),(1.0,.70,.30),5000,kind='SPOT',p=optic);spot.rotation_euler[0]=math.pi/2

def beam(n,p,color,length=24,radius=2.0,strength=.004):
 # A bounded, homogeneous emission volume has naturally soft ray-length edges.
 # No opaque triangular surface sheet and no costly scattering simulation.
 ma=bpy.data.materials.new(n+' soft emission volume');ma.use_nodes=True;nt=ma.node_tree;nt.nodes.clear();out=nt.nodes.new('ShaderNodeOutputMaterial');vol=nt.nodes.new('ShaderNodeVolumePrincipled');vol.inputs['Density'].default_value=0;vol.inputs['Emission Color'].default_value=(*color,1);vol.inputs['Emission Strength'].default_value=strength;nt.links.new(vol.outputs['Volume'],out.inputs['Volume'])
 bpy.ops.mesh.primitive_cone_add(vertices=16,radius1=.025,radius2=radius,depth=length,location=(0,.47+length/2,0),rotation=(-math.pi/2,0,0));obj=bpy.context.object;obj.name=n;obj.data.materials.append(ma);parent(obj,p);return obj,vol.inputs['Emission Strength']
mainbeam,mainalpha=beam('Main visible volumetric-style beam',optic,(1.0,.72,.33),26,1.8,.004)
for t,pitch,yaw in [(0,0,-.10),(17.3,0,-.10),(18.0,-.08,-.10),(21,-.76,-.115),(33,-.76,-.115)]:key(optic,t,'rotation_euler',(pitch,0,yaw))
# The physical crank.
crankbase=empty('Crank frame',(.28,-.68,5.36));crankbase.rotation_euler[2]=2.1
rod('Crank support',(.28,-.68,4.3),(.28,-.68,5.36),.065,M['darkmetal'])
wheel=empty('Rotating handwheel',(0,0,0),crankbase)
bpy.ops.mesh.primitive_torus_add(major_segments=16,minor_segments=6,location=(0,0,0),major_radius=.19,minor_radius=.022,rotation=(math.pi/2,0,0));w=bpy.context.object;w.name='Brass wheel ring';w.data.materials.append(M['gold']);parent(w,wheel)
for a in [0,math.pi/3,math.pi*2/3]:rod('Wheel spoke',(-.17*math.cos(a),0,-.17*math.sin(a)),(.17*math.cos(a),0,.17*math.sin(a)),.014,M['gold'],wheel)
for x in [-.15,.15]:rod('Wheel grip',(x,0,0),(x,-.10,0),.024,M['woodlight'],wheel)
for t,a in [(0,0),(17.8,0),(18.3,.12),(20.5,1.8),(33,1.8)]:key(wheel,t,'rotation_euler',(0,a,0))
# Original consistent young-adult courier rig.
char=empty('Courier master');limbs={}
cube('Navy pelvis',(0,0,.93),(.46,.29,.18),M['pants'],char,.035)
cube('Amber fitted jacket',(0,0,1.19),(.56,.34,.52),M['jacket'],char,.05)
cube('Jacket front seam',(0,-.183,1.19),(.016,.018,.43),M['jacketlight'],char,.004)
for z in [1.07,1.22,1.36]:ico('Brass jacket button',(.035,-.20,z),(.016,.012,.016),M['gold'],char)
strap=cube('Canvas diagonal satchel strap',(.02,-.193,1.19),(.070,.030,.61),M['bag'],char,.01);strap.rotation_euler[1]=-.58
cube('Courier satchel',(.34,.10,.97),(.31,.19,.35),M['bag'],char,.04);cube('Satchel flap',(.34,-.006,1.07),(.31,.025,.15),M['woodlight'],char,.025);cube('Satchel clasp',(.34,-.025,1.02),(.055,.02,.075),M['gold'],char,.008)
for side in [-1,1]:
 hip=empty('Left hip' if side<0 else 'Right hip',(side*.145,0,.91),char);cube('Trouser thigh',(0,0,-.19),(.205,.24,.38),M['pants'],hip,.035);knee=empty('Knee',(0,0,-.38),hip);cube('Trouser shin',(0,0,-.18),(.18,.21,.36),M['pants'],knee,.03);cube('Courier boot',(0,-.055,-.365),(.225,.35,.17),M['boots'],knee,.035);cube('Boot sole',(0,-.055,-.445),(.23,.36,.04),M['darkmetal'],knee,.008);limbs['leg'+str(side)]=(hip,knee)
 sh=empty('Shoulder '+str(side),(side*.34,0,1.36),char);sh.rotation_mode='QUATERNION';cube('Jacket upper sleeve',(0,0,-.145),(.20,.22,.29),M['jacket'],sh,.035);el=empty('Elbow '+str(side),(0,0,-.30),sh);el.rotation_mode='QUATERNION';cube('Jacket forearm',(0,0,-.14),(.175,.20,.28),M['jacket'],el,.03);cube('Golden jacket cuff',(0,0,-.282),(.18,.21,.075),M['jacketlight'],el,.015);cube('Courier hand',(0,-.005,-.335),(.15,.16,.14),M['skin'],el,.028);limbs['arm'+str(side)]=(sh,el)
neck=empty('Expressive neck',(0,0,1.48),char);cube('Neck',(0,0,.025),(.19,.19,.14),M['skin'],neck,.03)
cube('Courier angular face',(0,-.003,.245),(.405,.35,.43),M['skin'],neck,.065)
cube('Hair crown',(0,.006,.455),(.43,.36,.105),M['hair'],neck,.035)
cube('Hair back',(0,.145,.28),(.41,.08,.31),M['hair'],neck,.025)
for x,h in [(-.15,.11),(-.075,.16),(0,.105),(.075,.08),(.15,.065)]:cube('Swept auburn fringe',(x,-.17,.40-h*.15),(.09,.07,h),M['hair'],neck,.018)
cube('Nose bridge',(0,-.197,.245),(.074,.095,.092),M['skin'],neck,.020)
eyes=[]
for side in [-1,1]:
 eye=cube('Eye '+str(side),(side*.105,-.182,.277),(.060,.025,.065),M['eye'],neck,.012);eyes.append(eye)
 ico('Eye catchlight',(side*.105-.01,-.198,.29),(.009,.007,.011),M['white'],neck)
 brow=cube('Eyebrow '+str(side),(side*.105,-.191,.333),(.085,.018,.016),M['hair'],neck,.005);brow.rotation_euler[1]=side*.1
 cube('Ear '+str(side),(side*.215,.005,.24),(.055,.11,.13),M['skin'],neck,.024)
# A small curved smile, no synthesized lip-sync or copied identity.
rod('Mouth left',(-.059,-.188,.15),(0,-.199,.137),.009,M['hair'],neck);rod('Mouth right',(0,-.199,.137),(.059,-.188,.15),.009,M['hair'],neck)
cube('Red scarf collar',(0,0,1.49),(.43,.38,.12),M['scarf'],char,.035)
scarf=empty('Scarf tail hinge',(.13,.15,1.49),char);cube('Wind-tossed scarf tail',(0,.22,-.055),(.16,.48,.07),M['scarf'],scarf,.018)
# Root travel and shot transitions.
for t,loc,rz in [(0,(-3.0,-1.50,.34),math.pi/2),(5,(-1.9,-1.5,.34),math.pi/2),(10,(-.05,-1.5,.34),math.pi/2),(13,(.50,-1.05,.34),.22),(17.49,(.5,-1.05,.34),.22),(17.5,(0,-.86,4.28),2.1),(33,(0,-.86,4.28),2.1)]:
 key(char,t,'location',loc);key(char,t,'rotation_euler',(0,0,rz))
linear(char)
for i in range(0,F(13),4):
 t=(i-1)/FPS;phase=math.tau*t*.65;amount=1 if t<11.9 else max(0,(13-t)/1.1)
 for side in [-1,1]:
  hip,knee=limbs['leg'+str(side)];hip.rotation_euler[0]=side*.31*math.sin(phase)*amount;hip.keyframe_insert('rotation_euler',frame=max(1,i));knee.rotation_euler[0]=max(0,-side*math.sin(phase))*.38*amount;knee.keyframe_insert('rotation_euler',frame=max(1,i))
  sh,el=limbs['arm'+str(side)];sh.rotation_quaternion=Euler((-side*.34*math.sin(phase)*amount,0,side*.06)).to_quaternion();sh.keyframe_insert('rotation_quaternion',frame=max(1,i));el.rotation_quaternion=Euler((-.12,0,0)).to_quaternion();el.keyframe_insert('rotation_quaternion',frame=max(1,i))
for t,rot in [(0,(.02,0,0)),(10,(-.02,0,.12)),(12.6,(.16,0,.1)),(14,(.25,0,.1)),(16,(-.35,0,-.25)),(17.4,(-.25,0,-.25)),(17.5,(.20,0,0)),(20,(-.05,0,.1)),(22,(.35,0,0)),(33,(.23,-.08,.05))]:key(neck,t,'rotation_euler',rot)
for t in [0,2,4,6,8,10,12,14,16,18,20,22,24,26,28,30,33]:key(scarf,t,'rotation_euler',(math.sin(t*1.8)*.11,math.sin(t*1.2)*.08,math.sin(t*1.55)*.20))
for eye in eyes:
 for t in [0,6.0,6.10,6.22,15.0,15.10,15.22,27.4,27.5,27.62,33]:key(eye,t,'scale',(1,1,.1 if t in [6.10,15.10,27.5] else 1))
# Two-bone arm solves for actual wheel grips; hand motion follows the rotating mechanism.
Cmat=Matrix.Translation((0,-.86,4.28)) @ Matrix.Rotation(2.1,4,'Z');Ci=Cmat.inverted();Wmat=Matrix.Translation((.28,-.68,5.36)) @ Matrix.Rotation(2.1,4,'Z')
for t in [17.5,17.8,18.1,18.3,18.6,18.9,19.2,19.5,19.8,20.1,20.4,20.5,21.5,33]:
 phase=max(0,min(1,(t-18.0)/2.5))*1.8
 for side in [-1,1]:
  sh,el=limbs['arm'+str(side)];T=Ci @ (Wmat @ (Matrix.Rotation(phase,4,'Y') @ Vector((side*.15,-.08,0))))
  A=Vector((side*.34,0,1.36));D=T-A;dd=min(.595,max(.10,D.length));d=D.normalized();a=(.30**2-.30**2+dd**2)/(2*dd);hh=math.sqrt(max(0,.30**2-a*a));pref=Vector((side*.6,-.2,-.6));perp=(pref-d*pref.dot(d)).normalized();E=A+d*a+perp*hh
  q=Vector((0,0,-1)).rotation_difference((E-A).normalized());qq=Vector((0,0,-1)).rotation_difference((T-E).normalized());blend=max(0,min(1,(t-17.5)/.6));sh.rotation_quaternion=Quaternion().slerp(q,blend);el.rotation_quaternion=Quaternion().slerp(q.inverted()@qq,blend);sh.keyframe_insert('rotation_quaternion',frame=F(t));el.keyframe_insert('rotation_quaternion',frame=F(t))
# A folded paper boat, with the four-word instruction on a physical sail/note.
boat=empty('Paper boat delivery')
v=[(-.52,0,.18),(.52,0,.18),(-.31,-.22,.15),(.31,-.22,.15),(-.31,.22,.15),(.31,.22,.15),(0,0,-.11)]
mesh('Open folded paper hull',v,[(0,2,6),(2,3,6),(3,1,6),(1,5,6),(5,4,6),(4,0,6)],M['white'],boat)
mesh('Visible paper hull interior',[(-.49,0,.175),(.49,0,.175),(-.29,-.20,.145),(.29,-.20,.145),(-.29,.20,.145),(.29,.20,.145),(0,0,-.07)],[(0,6,2),(2,6,3),(3,6,1),(1,6,5),(5,6,4),(4,6,0)],M['paperfold'],boat)
mesh('Folded central paper triangle',[(-.23,0,.11),(.23,0,.11),(0,0,.44)],[(0,1,2)],M['white'],boat)
rod('Paper crease ridge',(0,0,.12),(0,0,.44),.009,M['paperfold'],boat)
rod('Tiny note support',(0,.035,.05),(0,.035,.77),.012,M['woodlight'],boat)
rod('Boat crease',(-.46,0,.125),(.46,0,.125),.009,M['paperfold'],boat)
cube('Attached four-word note',(0,-.025,.54),(.67,.024,.48),M['white'],boat,.012)
# Light wooden pin makes the message a diegetic object, not a generic overlay card.
cube('Tiny red delivery clip',(.28,-.045,.80),(.065,.045,.095),M['scarf'],boat,.012)
font=bpy.data.curves.new('TURN THE BEAM DOWN lettering','FONT');font.body='TURN\nTHE BEAM\nDOWN';font.align_x='CENTER';font.align_y='CENTER';font.size=.105;font.space_line=.9;font.extrude=.0006
note=bpy.data.objects.new('Ink on the delivered note',font);S.collection.objects.link(note);note.parent=boat;note.location=(0,-.041,.53);note.rotation_euler=(math.pi/2,0,0);font.materials.append(M['ink'])
for t,loc in [(0,(6,-2.0,3.3)),(9.8,(6,-2.0,3.3)),(10.5,(4,-2.1,2.4)),(11.5,(2.1,-2.1,1.8)),(12.8,(.98,-1.90,1.20)),(14,(.98,-1.90,1.16)),(17.4,(.98,-1.90,1.16)),(33,(.98,-1.90,1.16))]:key(boat,t,'location',loc)
for t in [0,9.8,10.5,11,11.5,12,12.8,13.5,14.5,15.5,16.5,17.5,33]:key(boat,t,'rotation_euler',(0,math.sin(t*4)*.045,math.sin(t*2)*.05))
# A real rail-top landing pad under the note/boat.
cube('Courier delivery rail',(1.0,-1.9,.99),(1.25,.34,.10),M['woodlight'],bevel=.025)
for x in [.5,1.5]:cube('Delivery rail post',(x,-1.9,.65),(.1,.12,.65),M['wood'],bevel=.012)
# Cloud curtains: opaque faceted volumes, animated apart to expose the world below.
cloudL=empty('West cloud curtain');cloudR=empty('East cloud curtain')
for x in [-15,-10,-5,0,5,10,15]:
 for y in [-10,-4,2,8,14,20,26]:
  pp=cloudL if x<1 else cloudR
  ico('Faceted cloud bank',(x+random.uniform(-.6,.6),y+random.uniform(-.5,.5),-3.8+random.uniform(-.35,.35)),(3.8+random.random(),3.3+random.random(),.85+random.random()*.35),M['cloudlight'] if random.random()<.4 else M['cloud'],pp,2)
for ob,direction in [(cloudL,-1),(cloudR,1)]:
 for t,xx in [(0,0),(21.4,0),(23,1.7*direction),(25,6.0*direction),(33,7.0*direction)]:key(ob,t,'location',(xx,0,0))
# Ocean facets and small animated wave motion.
N=42;vv=[]
for j in range(N+1):
 for i in range(N+1):x=(i/N-.5)*170;y=(j/N-.5)*170;vv.append((x,y,-12+.09*math.sin(x*.35)+.06*math.cos(y*.25)))
ff=[(j*(N+1)+i,j*(N+1)+i+1,(j+1)*(N+1)+i+1,(j+1)*(N+1)+i) for j in range(N) for i in range(N)]
water=mesh('Faceted hidden ocean',vv,ff,M['sea']);water.data.materials.append(M['sea2'])
for p in water.data.polygons:p.material_index=1 if random.random()<.23 else 0
wave=water.modifiers.new('Slow wind on the ocean','WAVE');wave.height=.09;wave.width=5;wave.speed=.045;wave.narrowness=.35;wave.use_x=True;wave.use_y=False
# Lower town stands in the ocean, not another generic astronaut/stock reveal.
island('Lower ocean town island',(1.2,14),3.8,-10.55,1.8)
for x,y,w,h in [(-.9,13.2,.85,1.0),(2.6,13.6,.85,.8),(.25,15.5,1.0,1.0),(2.4,15.4,.7,1.3),(-1.2,15,.7,.8)]:house('Town below cottage',(x,y,-10.5),w,.85,h,M['terracotta'] if x<1 else M['roof'])
cyl('Answering lighthouse',(1.0,14,-8.9),.44,3.4,M['plaster'],verts=8)
cyl('Lower lantern ring',(1.0,14,-7.12),.62,.16,M['darkmetal'],verts=8)
for i in range(6):
 a=i*math.tau/6;rod('Answer lantern strut',(1+.52*math.cos(a),14+.52*math.sin(a),-7.1),(1+.52*math.cos(a),14+.52*math.sin(a),-6.30),.024,M['gold'])
bpy.ops.mesh.primitive_cone_add(vertices=8,radius1=.70,radius2=.09,depth=.42,location=(1,14,-6.08));bpy.context.object.name='Lower beacon roof';bpy.context.object.data.materials.append(M['roof'])
answer=empty('Answering beacon emitter',(1,14,-6.7));answer.rotation_euler=(.71,0,math.pi-.075)
anslens=cyl('Blue answer lens',(0,.18,0),.25,.15,M['answer'],answer,12);anslens.rotation_euler[0]=math.pi/2
ansbeam,ansalpha=beam('Answer light rising to the courier',answer,(.30,.71,1.0),22,1.1,0)
for t,a in [(0,0),(26.8,0),(27.0,.0065),(27.25,.0018),(27.5,.0065),(33,.0065)]:ansalpha.default_value=a;ansalpha.keyframe_insert('default_value',frame=F(t))
for t,strength in [(0,.2),(26.8,.2),(27.0,9),(27.25,1.5),(27.5,9),(33,9)]:M['answer'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value=strength;M['answer'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].keyframe_insert('default_value',frame=F(t))

for ob in bpy.data.objects:
 if ob.type=='MESH' and 'Faceted cloud bank' in ob.name:
  for face in ob.data.polygons:face.use_smooth=True
for i in range(14):
 a=math.tau*i/14;x=5.0*math.cos(a);y=4.0*math.sin(a)
 puff=ico('Near rounded cloud layer',(x,y,-2.9), (1.9,1.55,.68), M['cloudlight'], cloudL if x<1 else cloudR,2)
 for face in puff.data.polygons:face.use_smooth=True
# The ocean is genuinely hidden in the opening, and revealed under the parting clouds.
for t,val in [(0,True),(21.5,True),(21.55,False),(33,False)]:
 water.hide_render=val;water.keyframe_insert('hide_render',frame=F(t))

# Native cinematic light: soft warm key, cool sky bounce, real contact shadows.
light('Warm last sun',(5,-8,13),(1.0,.66,.37),2600,5,target=(0,0,1))
light('Cool sky fill',(-7,-1,7),(.35,.57,1.0),850,8,target=(0,0,2))
light('Lantern rim',(1,3,8),(1,.48,.18),850,4,target=(0,0,4.7))
light('Lower sea-town moon fill',(-4,11,0),(.24,.47,.9),1900,8,target=(1,14,-9))
light('Lower windows warm bounce',(1,11,-7),(1,.50,.14),250,5,target=(1,14,-10))
# Far sky sun disc and receding island silhouettes.
ico('Pale low sun',(0,25,13),(2.4,1,2.4),mat('Sunset disc',(.91,.58,.29),1,0,.65),sub=3)
# No distant primitive cliff planes behind the hero island.
# A few wind-chime-like brass lantern details.
for x,y in [(-2.2,-1.1),(2.2,-1.1)]:
 rod('Lamp standard',(x,y,.35),(x,y,1.65),.035,M['darkmetal']);cube('Street lantern',(x,y,1.65),(.16,.16,.24),M['window'],bevel=.025)
# Eight deliberate shots. Camera movement, not a static image zoom.
shots=[
('01_establish',0,5,(10,-16,9),(8.5,-14.5,8),(0,0,1.7),(0,0,1.8),62,8),
('02_courier_walk',5,10,(2.5,-5.5,2.9),(2.0,-4.7,2.75),(-1.5,-1.5,1.35),(-.25,-1.5,1.35),55,5.6),
('03_boat_delivery',10,14,(2.6,-4.4,2.25),(2.0,-3.6,1.95),(1.2,-1.65,1.5),(.9,-1.65,1.5),60,5.6),
('04_the_note',14,17.5,(1.40,-3.85,1.72),(1.30,-3.70,1.72),(.98,-1.90,1.48),(.98,-1.90,1.48),48,8),
('05_turn_the_beacon',17.5,21.5,(3.3,-3.6,6.5),(2.7,-3.2,6.4),(0,-.1,5.25),(0,.1,5.22),48,6),
('06_clouds_part',21.5,25,(3.0,0.8,7.3),(2.8,2.0,6.0),(1,10,-3),(1,13,-6),32,9),
('07_town_below',25,29,(9.0,1.5,-5.1),(7.5,3.2,-5.4),(1,14,-8.8),(1,14,-8.6),48,9),
('08_the_answer',29,33,(18,-5,8),(20,-7,9),(.5,7,-1),(.6,7.5,-1),42,9)]
camrows=[]
for name,a,b,l1,l2,t1,t2,lens,fstop in shots:
 d=bpy.data.cameras.new(name);ca=bpy.data.objects.new(name,d);S.collection.objects.link(ca);d.lens=lens;d.sensor_width=36;d.sensor_fit='HORIZONTAL' if name in ['01_establish','03_boat_delivery','04_the_note','05_turn_the_beacon','06_clouds_part','07_town_below','08_the_answer'] else 'AUTO';d.clip_start=.05;d.clip_end=300;d.dof.use_dof=True;d.dof.aperture_fstop=fstop
 for tt,loc,tgt in [(a,l1,t1),(b,l2,t2)]:
  ca.location=loc;ca.rotation_euler=(Vector(tgt)-ca.location).to_track_quat('-Z','Y').to_euler();ca.keyframe_insert('location',frame=F(tt));ca.keyframe_insert('rotation_euler',frame=F(tt));d.dof.focus_distance=(Vector(tgt)-ca.location).length;d.dof.keyframe_insert('focus_distance',frame=F(tt))
 linear(ca);mark=S.timeline_markers.new(name,frame=F(a));mark.camera=ca;camrows.append({'shot':name,'start_seconds':a,'end_seconds':b,'start_frame':F(a),'end_frame':min(END,F(b)-1),'camera':ca.name,'lens_mm':lens,'purpose':name.split('_',1)[1]})
S.camera=bpy.data.objects[shots[0][0]]
# Restrained bloom is rendered from light, not text overlays.
S.use_nodes=True;nt=S.node_tree;nt.nodes.clear();rl=nt.nodes.new('CompositorNodeRLayers');gl=nt.nodes.new('CompositorNodeGlare');gl.glare_type='FOG_GLOW';gl.quality='LOW';gl.threshold=1.6;gl.mix=-.92;out=nt.nodes.new('CompositorNodeComposite');nt.links.new(rl.outputs['Image'],gl.inputs['Image']);nt.links.new(gl.outputs['Image'],out.inputs['Image'])

OLD=[0,5,10,14,17.5,21.5,25,29,33]
NEW=[0,3.7,6.7,9.7,13.8,15.8,19.7,22.7,28]
def remap(t):
 for i in range(len(OLD)-1):
  if t<=OLD[i+1]:return NEW[i]+(t-OLD[i])/(OLD[i+1]-OLD[i])*(NEW[i+1]-NEW[i])
 return NEW[-1]
for action in bpy.data.actions:
 for fc in action.fcurves:
  for k in fc.keyframe_points:
   for h in [k.co,k.handle_left,k.handle_right]:h.x=F(remap((h.x-1)/FPS))
for marker in S.timeline_markers:marker.frame=F(remap((marker.frame-1)/FPS))
for row in camrows:
 row['start_seconds']=remap(row['start_seconds']);row['end_seconds']=remap(row['end_seconds']);row['start_frame']=F(row['start_seconds']);row['end_frame']=F(row['end_seconds'])-1
END=round(28*FPS);S.frame_end=END
# Complete the cloud window before the narrator's 'far below' line.
for ob,direction in [(cloudL,-1),(cloudR,1)]:
 ob.animation_data_clear()
 for t,x in [(0,0),(15.75,0),(16.75,2.8*direction),(17.65,6.0*direction),(28,7.0*direction)]:key(ob,t,'location',(x,0,0))
# Answer precisely during the measured 20.68–22.00 second narration line.
ansalpha.id_data.animation_data_clear()
for t,a in [(0,0),(19.95,0),(20.08,.0065),(20.30,.0015),(20.55,.007),(20.90,.002),(21.20,.007),(28,.007)]:ansalpha.default_value=a;ansalpha.keyframe_insert('default_value',frame=F(t))
M['answer'].node_tree.animation_data_clear()
for t,v in [(0,.2),(19.95,.2),(20.08,9),(20.30,1.5),(20.55,9),(20.90,1.5),(21.20,9),(28,9)]:
 node=M['answer'].node_tree.nodes['Principled BSDF'];node.inputs['Emission Strength'].default_value=v;node.inputs['Emission Strength'].keyframe_insert('default_value',frame=F(t))

for ob in [boat]+list(boat.children_recursive):
 for t,hidden in [(0,True),(6.65,True),(6.7,False),(28,False)]:
  ob.hide_render=hidden;ob.keyframe_insert('hide_render',frame=F(t))

# Grounded story and provenance in machine-readable form.
manifest={'title':'The Downward Beacon','original_geometry':True,'external_assets':[],'character':'Young adult courier, amber jacket, vermilion scarf, navy trousers, teal satchel, dark swept hair.','note_text':'TURN THE BEAM DOWN','fps':FPS,'native_resolution':[o.width,o.height],'render_percentage':o.scale,'duration_seconds':28,'engine':S.render.engine,'samples':o.samples,'shots':camrows,'animation':['Articulated walking, head turns/blinks, scarf wind, boat arrival/bob, two-bone wheel gripping, gimbal down-tilt, cloud curtain separation, ocean wave modifier, answering beacon flash.'],'copyright':'All scene geometry, materials, animation and cameras created for this project. No Roblox/game/reference assets, copied plot, photos, textures or voice used.'}
(R/'camera-timing-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');S.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(R/'the-downward-beacon.blend'))
# Rendering records actual elapsed time for each output.
receipts=[]
def still(f,label,folder='stills'):
 outdir=R/folder;outdir.mkdir(exist_ok=True);S.frame_set(f);S.render.filepath=str(outdir/(label+'.png'));start=time.time();bpy.ops.render.render(write_still=True);r={'frame':f,'seconds':(f-1)/FPS,'path':S.render.filepath,'wall_seconds':round(time.time()-start,3),'resolution':[S.render.resolution_x*S.render.resolution_percentage//100,S.render.resolution_y*S.render.resolution_percentage//100],'engine':S.render.engine,'samples':o.samples};receipts.append(r);(R/'render-receipts.json').write_text(json.dumps(receipts,indent=2)+'\n');print('RENDER_RECEIPT',json.dumps(r),flush=True)
if o.stills:
 for t,n in [(1.5,'01-floating-town'),(12.6,'02-physical-note'),(21.3,'03-answering-town')]:still(F(t),n)
if o.audit:
 for t,n in [(1.5,'audit-01-opening'),(4.8,'audit-02-courier'),(10.0,'audit-03-note-start'),(13.5,'audit-04-note-end'),(14.6,'audit-05-crank'),(18.8,'audit-06-cloud-opening'),(21.2,'audit-07-clear-town'),(26.2,'audit-08-two-worlds')]:still(F(t),n,'audit-raw')
if o.motion:
 folder=R/'motion-test-frames';folder.mkdir(exist_ok=True)
 for f in range(F(4.5),F(5.5)):still(f,f'{f:05d}','motion-test-frames')
if o.full:
 folder=R/'frames';folder.mkdir(exist_ok=True)
 for f in range(o.start or 1,(o.end or END)+1):
  target=folder/f'{f:05d}.png'
  if not target.exists():still(f,f'{f:05d}','frames')
print('SCENE_READY',str(R/'the-downward-beacon.blend'),flush=True)
