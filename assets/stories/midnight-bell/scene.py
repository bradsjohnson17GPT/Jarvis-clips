"""Midnight Bell: project-owned courier; all station/robot geometry is original.

Build: blender -b -t 2 --python midnight_bell.py -- --stills
Only representative stills are authorized by default. No full-render entry point.
"""
import bpy,math,json,hashlib,sys,time,argparse,subprocess
from pathlib import Path
from mathutils import Vector,Matrix,Euler,Quaternion
SOURCE_DIR=Path(__file__).resolve().parent
PROJECT_ROOT=next(p for p in SOURCE_DIR.parents if (p/'AGENTS.md').exists() and (p/'stories').is_dir())
R=SOURCE_DIR
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path);ap.add_argument('--stills',action='store_true');ap.add_argument('--frames',nargs='*',type=float);o=ap.parse_args(args)
R=o.output or PROJECT_ROOT/'work/preproduction/midnight-bell/staging'
R.mkdir(parents=True,exist_ok=True)
FPS=24;DURATION=28.228;END=math.ceil(DURATION*FPS)
def F(t):return min(END,round(t*FPS)+1)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
S=bpy.context.scene;S.render.engine='CYCLES';S.cycles.device='CPU';S.cycles.samples=4;S.cycles.use_denoising=False;S.cycles.max_bounces=3;S.cycles.diffuse_bounces=1;S.cycles.glossy_bounces=1;S.cycles.transparent_max_bounces=3;S.cycles.use_adaptive_sampling=True;S.cycles.adaptive_threshold=.12
S.render.resolution_x=720;S.render.resolution_y=1280;S.render.resolution_percentage=100;S.render.fps=FPS;S.frame_start=1;S.frame_end=END;S.render.threads_mode='FIXED';S.render.threads=2;S.render.use_persistent_data=True;S.render.image_settings.file_format='PNG';S.render.film_transparent=False
S.view_settings.view_transform='AgX';S.view_settings.look='AgX - Medium High Contrast';S.view_settings.exposure=.3
S.world.use_nodes=True;bg=S.world.node_tree.nodes['Background'];bg.inputs['Color'].default_value=(.025,.045,.09,1);bg.inputs['Strength'].default_value=.3

def mat(n,c,rough=.6,metal=0,emit=0):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);m.use_nodes=True;p=m.node_tree.nodes['Principled BSDF'];p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
 if emit:p.inputs['Emission Color'].default_value=(*c,1);p.inputs['Emission Strength'].default_value=emit
 return m
M={'slate':mat('Station | midnight slate',(.07,.115,.17)), 'wall':mat('Station | faded petrol plaster',(.14,.25,.27)), 'walllight':mat('Station | cream brick edges',(.54,.49,.37)), 'timber':mat('Station | chestnut timber',(.17,.075,.035)), 'wood':mat('Station | worn honey edges',(.34,.18,.07)), 'floor':mat('Station | blue-grey platform',(.21,.27,.30)), 'tile':mat('Station | warm floor tiles',(.28,.29,.25)), 'dark':mat('Station | forged dark iron',(.035,.055,.07),.36,.55), 'steel':mat('Robot | brushed pewter',(.37,.47,.50),.32,.7), 'brass':mat('Bell | mellow brass',(.59,.33,.075),.3,.62), 'cream':mat('Robot | warm ceramic tool lid',(.65,.62,.48),.42), 'teal':mat('Robot | petrol-blue toolbox enamel',(.035,.23,.27),.38,.2), 'orange':mat('Robot | copper safety stripe',(.84,.28,.045),.45), 'rubber':mat('Robot | matte caster rubber',(.018,.025,.03),.8), 'led':mat('Robot | single cyan LED face',(.14,.72,.8),.28,0,3), 'battery':mat('Robot | charge segments',(.1,.8,.38),.35,0,2), 'red':mat('Robot | low-charge warning',(.9,.06,.018),.4,0,2), 'glass':mat('Station | midnight blue panes',(.025,.055,.12),.25,.15), 'lamp':mat('Station | warm glass lamps',(.98,.46,.13),.35,0,4), 'paper':mat('Station | ivory sign enamel',(.78,.73,.58)), 'ink':mat('Station | sign lettering',(.035,.055,.075)), 'white':mat('Station | clock ticks',(.82,.78,.62))}
def empty(n,loc=(0,0,0),p=None):
 a=bpy.data.objects.new(n,None);S.collection.objects.link(a);a.location=loc;a.parent=p;return a
def cube(n,loc,size,ma,p=None,bevel=.025):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);a=bpy.context.object;a.name=n;a.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);a.parent=p;a.data.materials.append(ma)
 if bevel:
  b=a.modifiers.new('Soft machined edges','BEVEL');b.width=bevel;b.segments=2;a.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL')
 return a
def cyl(n,loc,rad,depth,ma,p=None,vertices=16):
 bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=rad,depth=depth,location=loc);a=bpy.context.object;a.name=n;a.parent=p;a.data.materials.append(ma);b=a.modifiers.new('Turned edge highlights','BEVEL');b.width=min(.018,rad*.1);b.segments=2;a.modifiers.new('Weighted cylinder normals','WEIGHTED_NORMAL');return a
def uv(n,loc,size,ma,p=None):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=1,location=loc);a=bpy.context.object;a.name=n;a.scale=size;a.parent=p;a.data.materials.append(ma)
 for f in a.data.polygons:f.use_smooth=True
 return a
def rod(n,a,b,r,ma,p=None):
 aa=Vector(a);bb=Vector(b);ob=cyl(n,(aa+bb)/2,r,(bb-aa).length,ma,p,12);ob.rotation_euler=(bb-aa).to_track_quat('Z','Y').to_euler();return ob
def text(n,body,loc,size,ma,p=None,align='CENTER'):
 d=bpy.data.curves.new(n,'FONT');d.body=body;d.align_x=align;d.align_y='CENTER';d.size=size;d.extrude=.0005;a=bpy.data.objects.new(n,d);S.collection.objects.link(a);a.location=loc;a.rotation_euler=(math.pi/2,0,0);a.parent=p;d.materials.append(ma);return a
def key(ob,t,prop,value):setattr(ob,prop,value);ob.keyframe_insert(data_path=prop,frame=F(t))
def linear(ob):
 if ob.animation_data and ob.animation_data.action:
  for fc in ob.animation_data.action.fcurves:
   for k in fc.keyframe_points:k.interpolation='LINEAR'
def emission(ma,t,v):
 s=ma.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'];s.default_value=v;s.keyframe_insert('default_value',frame=F(t))
def light(n,loc,color,power,size,target):
 d=bpy.data.lights.new(n,'AREA');d.energy=power;d.color=color;d.shape='DISK';d.size=size;a=bpy.data.objects.new(n,d);S.collection.objects.link(a);a.location=loc;a.rotation_euler=(Vector(target)-a.location).to_track_quat('-Z','Y').to_euler();return a
def cable(n,points,ma,radius=.027):
 d=bpy.data.curves.new(n,'CURVE');d.dimensions='3D';d.resolution_u=12;d.bevel_depth=radius;d.bevel_resolution=2;sp=d.splines.new('BEZIER');sp.bezier_points.add(len(points)-1)
 for p,co in zip(sp.bezier_points,points):p.co=co;p.handle_left_type='AUTO';p.handle_right_type='AUTO'
 a=bpy.data.objects.new(n,d);S.collection.objects.link(a);d.materials.append(ma);return a,sp

# Enclosed original station: carved timber canopy, tiled floor, service pit, waiting room.
cube('Deep service-bay floor',(0,.7,-.09),(12,7,.18),M['floor'],bevel=.03)
for i in range(-13,14):
 x=i*.4
 for j in range(5):
  y=-.2+j*.55
  if -.05<x<2.85 and y<1.7:continue
  cube('Individual platform paving',(x,y,1.02),(.385,.53,.13),M['tile'],bevel=.012)
for x,w in [(-2.65,5.1),(4.15,2.5)]:cube('Platform front blue fascia',(x,-.50,.49),(w,.18,.96),M['wall'],bevel=.025)
cube('Service pit back wall',(1.4,1.68,.49),(2.85,.16,1.0),M['slate'])
cube('Station waiting-room plaster',(0,2.62,2.55),(11,.22,3.2),M['wall'],bevel=.04)
cube('Waiting-room lower timber sill',(0,2.46,1.35),(11,.20,.18),M['timber'])
for z in [1.65,1.9,2.15]:
 for j in range(-12,13):cube('Plaster brick reveal',(j*.46+(z==1.9)*.22,2.494,z),(.43,.018,.024),M['walllight'],bevel=.003)
for x in [-4,-2.8,3.1,4.3]:
 cube('Tall midnight window',(x,2.46,2.80),(.90,.06,1.65),M['glass'],bevel=.025)
 for xx in [x-.48,x+.48]:cube('Window timber upright',(xx,2.40,2.8),(.065,.11,1.78),M['timber'])
 for zz in [1.92,2.8,3.68]:cube('Window cross rail',(x,2.40,zz),(1.01,.11,.06),M['timber'])
 cube('Warm window sill',(x,2.32,1.90),(1.12,.30,.09),M['wood'])
for x in [-4.8,-1.8,2.95,4.8]:
 cube('Canopy fluted square column',(x,-.38,2.75),(.16,.19,3.6),M['timber'])
 cube('Canopy column foot',(x,-.38,1.19),(.28,.31,.30),M['dark'])
 rod('Diagonal canopy brace',(x,-.38,3.6),(x+.55,-.38,4.35),.07,M['wood'])
cube('Canopy front lintel',(0,-.38,4.42),(11,.24,.22),M['wood'])
cube('Canopy roof interior',(0,1.18,4.58),(11,3.8,.18),M['timber'])
for x in range(-5,6):cube('Visible roof rafter',(x,1.18,4.42),(.09,3.45,.15),M['wood'])
for x in [-3.8,-.6,3.5]:
 rod('Suspended station lamp stalk',(x,1.15,4.4),(x,1.15,3.8),.025,M['dark'])
 lamp=cyl('Station lamp shade',(x,1.15,3.78),.27,.10,M['dark'])
 uv('Station lamp glowing underside',(x,1.15,3.71),(.21,.21,.07),M['lamp'])
 light('Warm hanging practical',(x,1.13,3.55),(1,.56,.22),95,1.0,(x,.3,1.3))
for x in [-3.4,3.8]:
 for xx in [x-.65,x+.65]:cube('Waiting bench leg',(xx,1.9,1.30),(.09,.35,.5),M['dark'])
 for y in [1.78,1.96,2.14]:cube('Waiting bench seat slat',(x,y,1.56),(1.6,.15,.08),M['wood'])
 for z in [1.85,2.05]:cube('Waiting bench back slat',(x,2.19,z),(1.6,.07,.13),M['timber'])
# Distant tracks and an unambiguously empty platform, no borrowed train insert.
for x in [-.72,.72]:rod('Empty rail line',(x,-7,.02),(x+8,-20,.02),.04,M['steel'])
for k in range(10):
 y=-7-k*1.25;x=k*.77;sl=cube('Railway sleeper',(x,y,-.04),(2.4,.18,.11),M['timber']);sl.rotation_euler[2]=-.45
cube('Station sign enamel',(-.75,2.38,3.55),(2.15,.07,.46),M['paper'],bevel=.04)
text('Original station name','NORTH QUAY',(-.75,2.33,3.55),.22,M['ink'])
cube('Last train notice',(-.83,2.38,2.80),(1.5,.055,.48),M['paper'])
text('Last train notice type','LAST TRAIN 21:05',(-.83,2.34,2.80),.12,M['ink'])
# Analog midnight clock, visible above the hook and in station reaction geography.
clock=empty('Midnight station clock',(1.72,2.30,2.92));disc=cyl('Clock brass rim',(0,0,0),.47,.075,M['brass'],clock,32);disc.rotation_euler[0]=math.pi/2
face=cyl('Clock enamel face',(0,-.047,0),.42,.026,M['paper'],clock,32);face.rotation_euler[0]=math.pi/2
for i in range(12):
 a=i*math.tau/12;tick=cube('Clock hour mark',(.35*math.sin(a),-.068,.35*math.cos(a)),(.022,.012,.065),M['ink'],clock,.002);tick.rotation_euler[1]=a
rod('Clock minute hand',(0,-.085,0),(0,-.085,.30),.012,M['ink'],clock);rod('Clock hour hand',(0,-.10,0),(0,-.10,.22),.022,M['ink'],clock);uv('Clock central pin',(0,-.115,0),(.03,.018,.03),M['brass'],clock)
# Maintenance cover opens around an actual hinge, establishing the cavity's position.
hatch=empty('Maintenance hatch hinge',(1.40,1.43,1.10))
cube('Liftable intact maintenance lid',(0,-.91,0),(2.78,1.78,.08),M['slate'],hatch,.025)
for x in [-1.12,1.12]:cube('Hatch brass edge strip',(x,-.91,-.05),(.055,1.78,.025),M['brass'],hatch,.01)
rod('Hatch pull grip',(-.25,-1.62,.08),(.25,-1.62,.08),.035,M['steel'],hatch)
for t,v in [(0,0),(8.35,0),(9.25,-1.44),(28.228,-1.44)]:key(hatch,t,'rotation_euler',(v,0,0))
for i in range(4):cube('Service access step',(-.70-i*.27,.30,1.0-i*.25),(.32,.65,.17),M['floor'],bevel=.02)

# Bell is a real lathed open shell, swung by impact, with a visible clapper.
bellroot=empty('Physical bell swing',(2.05,.42,.88))
profile=[(0,.10),(-.06,.11),(-.10,.15),(-.20,.17),(-.31,.23),(-.36,.29),(-.40,.30),(-.41,.26),(-.34,.22),(-.23,.14),(-.12,.12),(-.07,.08)]
verts=[];N=32
for z,r in profile:
 for i in range(N):a=i*math.tau/N;verts.append((r*math.cos(a),r*math.sin(a),z))
faces=[]
for j in range(len(profile)-1):
 for i in range(N):faces.append((j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i))
d=bpy.data.meshes.new('Original bell lathe');d.from_pydata(verts,[],faces);d.materials.append(M['brass']);ob=bpy.data.objects.new('Open brass bell shell',d);S.collection.objects.link(ob);ob.parent=bellroot
for p in d.polygons:p.use_smooth=True
rod('Bell inner clapper stem',(0,0,-.02),(0,0,-.30),.02,M['dark'],bellroot);uv('Bell clapper',(0,0,-.31),(.055,.055,.07),M['steel'],bellroot)
rod('Bell horizontal mounting rail',(1.65,.42,.94),(2.48,.42,.94),.04,M['dark']);rod('Bell mounting foot',(2.48,.42,.03),(2.48,.42,.94),.05,M['dark'])
impacts=[.68,1.12,1.56,6.75,7.20,7.65,10.2,10.75,11.3,12.0,12.55,14.0,22.6,23.05,23.5]
for t in [0,28.228]:key(bellroot,t,'rotation_euler',(0,0,0))
for t in impacts:
 for dt,a in [(-.055,0),(0,0),(.055,-.14),(.15,.10),(.27,-.055),(.39,0)]:key(bellroot,max(0,t+dt),'rotation_euler',(0,a,0))

# Distinct original tool-cart robot: four casters, toolbox handle, ONE continuous LED face.
bot=empty('Original toolbox maintenance robot',(.94,.55,.04))
cube('Robot petrol enamel toolbox',(0,0,.44),(.88,.68,.60),M['teal'],bot,.09)
cube('Robot cream tool lid',(0,0,.775),(.94,.73,.12),M['cream'],bot,.04)
cube('Robot copper bumper',(0,-.355,.23),(.82,.07,.09),M['orange'],bot,.025)
cube('Robot single dark face panel',(0,-.353,.51),(.61,.035,.24),M['dark'],bot,.045)
faceled=cube('ONE cyan LED face ribbon',(0,-.377,.525),(.40,.018,.052),M['led'],bot,.022)
for x in [-.21,.21]:rod('Toolbox carry handle upright',(x,.02,.83),(x,.02,1.00),.03,M['dark'],bot)
rod('Toolbox carry handle',(-.21,.02,1.00),(.21,.02,1.00),.03,M['dark'],bot)
for x in [-.37,.37]:
 for y in [-.24,.24]:
  wheel=cyl('Four independent caster tires',(x,y,.13),.13,.13,M['rubber'],bot,20);wheel.rotation_euler[1]=math.pi/2
  hub=cyl('Caster steel hub',(x+(.073 if x>0 else -.073),y,.13),.055,.018,M['steel'],bot,16);hub.rotation_euler[1]=math.pi/2
  cube('Caster bracket',(x,y,.235),(.10,.12,.14),M['dark'],bot,.015)
for x in [-.30,.30]:cube('Toolbox lid latch',(x,-.39,.75),(.07,.04,.13),M['steel'],bot,.012)
text('Tool cart serial','M-07',(.26,-.394,.30),.075,M['cream'],bot)
battery=[]
for i in range(4):
 b=cube('Battery bar segment '+str(i),(-.35,-.381,.35+i*.075),(.055,.018,.053),M['red'] if i==0 else M['battery'],bot,.009);battery.append(b)
 for t,scale in [(0,1 if i==0 else .01),(13.5,1 if i==0 else .01),(15.6,.01),(19.94,.01),(20.06,1),(28.228,1)]:key(b,t,'scale',(1,1,scale))
for t,v in [(0,2.8),(13.5,2.8),(15.6,0),(19.93,0),(20.05,4.0),(28.228,4.0)]:emission(M['led'],t,v)
for t,col in [(0,(.14,.72,.8,1)),(13.5,(.14,.72,.8,1)),(15.6,(.003,.012,.015,1)),(19.93,(.003,.012,.015,1)),(20.05,(.14,.72,.8,1)),(28.228,(.14,.72,.8,1))]:
 node=M['led'].node_tree.nodes['Principled BSDF'].inputs['Base Color'];node.default_value=col;node.keyframe_insert('default_value',frame=F(t))
for b in battery[1:]:
 for t,v in [(0,True),(20.0,True),(20.06,False),(28.228,False)]:b.hide_render=v;b.keyframe_insert('hide_render',frame=F(t))
for t,v in [(0,2),(13.7,2),(15.6,.015),(19.93,.015),(20.05,3),(28.228,3)]:emission(M['red'],t,v)
for t,col in [(0,(.9,.06,.018,1)),(19.94,(.9,.06,.018,1)),(20.05,(.10,.8,.38,1)),(28.228,(.10,.8,.38,1))]:
 for name in ['Base Color','Emission Color']:
  node=M['red'].node_tree.nodes['Principled BSDF'].inputs[name];node.default_value=col;node.keyframe_insert('default_value',frame=F(t))
for t,rot in [(0,(0,0,0)),(13.8,(0,0,0)),(15.6,(.05,-.04,0)),(19.95,(.05,-.04,0)),(20.15,(0,0,0)),(28.228,(0,0,0))]:key(bot,t,'rotation_euler',rot)
# Two articulated tool arms; robot's right arm carries a physical open-ended wrench.
rs=empty('Robot wrench shoulder',(.48,.03,.65),bot);rs.rotation_mode='QUATERNION'
cyl('Robot shoulder joint',(0,0,0),.08,.13,M['steel'],rs)
cube('Robot upper tool arm',(0,0,-.135),(.105,.12,.27),M['teal'],rs,.02)
re=empty('Robot wrench elbow',(0,0,-.27),rs);re.rotation_mode='QUATERNION'
uv('Robot elbow joint',(0,0,0),(.075,.075,.075),M['steel'],re)
cube('Robot forearm',(0,0,-.13),(.085,.10,.26),M['steel'],re,.018)
wrist=empty('Wrench-gripping tool wrist',(0,0,-.29),re)
cube('Robot two-prong gripper',(0,0,-.015),(.14,.12,.07),M['dark'],wrist,.015)
rod('Real wrench shaft',(0,0,-.02),(0,0,-.24),.028,M['steel'],wrist)
cube('Wrench open jaw bridge',(0,0,-.265),(.13,.045,.045),M['steel'],wrist,.01)
for x in [-.058,.058]:cube('Wrench open jaw prong',(x,0,-.307),(.035,.045,.10),M['steel'],wrist,.007)
left=empty('Robot greeting shoulder',(-.48,.03,.70),bot);cube('Robot greeting arm',(0,0,-.17),(.10,.12,.34),M['teal'],left,.02);uv('Robot greeting hand',(0,0,-.38),(.09,.055,.065),M['steel'],left)
def solve(sh,el,A,T,l1=.30,l2=.335,pref=Vector((-.5,-.4,-.3)),t=0):
 D=T-A;dd=max(.08,min(l1+l2-.005,D.length));di=D.normalized();a=(l1*l1-l2*l2+dd*dd)/(2*dd);h=math.sqrt(max(0,l1*l1-a*a));per=(pref-di*pref.dot(di)).normalized();E=A+di*a+per*h;q=Vector((0,0,-1)).rotation_difference((E-A).normalized());qq=Vector((0,0,-1)).rotation_difference((T-E).normalized());key(sh,t,'rotation_quaternion',q);key(el,t,'rotation_quaternion',q.inverted()@qq)
# The arm grip advances right toward the bell; wrench tip follows its forearm axis.
# Solve the effective forearm plus wrench length to the jaw tip; the tool is rigid in the gripper.
for t in [0,28.228]:solve(rs,re,Vector((.48,.03,.65)),Vector((.67,-.28,.40)),.27,.647,Vector((0,-1,-.25)),t)
for t in impacts:
 if t>15 and t<22:continue
 for dt,T in [(-.20,(.67,-.28,.40)),(-.055,(.78,-.18,.44)),(0,(.82,-.13,.45)),(.13,(.70,-.26,.40)),(.36,(.67,-.28,.40))]:solve(rs,re,Vector((.48,.03,.65)),Vector(T),.27,.647,Vector((0,-1,-.3)),max(0,t+dt))
for t,T in [(15.15,(.67,-.28,.40)),(15.7,(.50,-.28,.15)),(19.95,(.50,-.28,.15)),(20.25,(.67,-.28,.40)),(21.8,(.67,-.28,.40))]:solve(rs,re,Vector((.48,.03,.65)),Vector(T),.27,.647,Vector((0,-1,-.3)),t)
for t,a in [(0,0),(23.9,0),(24.4,-2.75),(24.75,-3.1),(25.1,-2.7),(25.5,-3.05),(26,-2.7),(26.6,-3.1),(27.3,-2.75),(28.228,-2.75)]:key(left,t,'rotation_euler',(a,0,-.25 if t>24 else 0))
# Conceal the cause only during the hook/investigation; it remains original animated geometry.
for a in [bot]+list(bot.children_recursive):
 for t,v in [(0,True),(9.20,True),(9.3,False),(28.228,False)]:a.hide_render=v;a.keyframe_insert('hide_render',frame=F(t))

# Battery visibility overrides cause concealment: inactive segments stay fully off.
for b in battery[1:]:
 for t,v in [(0,True),(9.3,True),(20.0,True),(20.06,False),(28.228,False)]:b.hide_render=v;b.keyframe_insert('hide_render',frame=F(t))

# Intact wall charger, visible unbroken cable, seated connector and charge cause/effect.
cube('Charger structural mounting panel',(-1.08,1.67,.53),(.77,.10,1.07),M['slate'],bevel=.025)
cube('Wall maintenance charger',(-1.08,1.55,.65),(.50,.15,.46),M['cream'],bevel=.035)
cube('Charger dark face',(-1.08,1.46,.65),(.35,.03,.29),M['dark'],bevel=.02)
cube('Charger green power lamp',(-1.18,1.43,.72),(.065,.018,.065),M['battery'],bevel=.012)
text('Charger label','24V',(-1.02,1.425,.61),.065,M['white'])
port=cyl('Robot intact charger socket',(.56,.158,.66),.07,.045,M['dark']);port.rotation_euler[0]=math.pi/2
# The independent world-space socket follows the same reveal as the robot.
for t,v in [(0,True),(9.20,True),(9.3,False),(28.228,False)]:port.hide_render=v;port.keyframe_insert('hide_render',frame=F(t))
plug=empty('Charger connector in courier hand',(.40,-.26,.53))
cube('Intact insulated charger grip',(0,-.03,0),(.105,.18,.105),M['orange'],plug,.025)
pin=cyl('Short recessed metal plug',(0,.08,0),.035,.06,M['steel'],plug);pin.rotation_euler[0]=math.pi/2
plugkeys=[(0,(.40,-.26,.53)),(18.2,(.40,-.26,.53)),(18.95,(.46,-.12,.60)),(19.70,(.56,.08,.66)),(19.94,(.56,.105,.66)),(28.228,(.56,.105,.66))]
for t,p in plugkeys:key(plug,t,'location',p)
wire,sp=cable('Continuous intact charging cable',[(-1.08,1.45,.52),(-1.10,.63,.12),(-.70,-.28,.07),(.10,-.45,.09),(.40,-.36,.53)],M['rubber'],.024)
# Introduce the charger lead with the hand-held plug in the rescue shot.
for t,v in [(0,True),(17.7,True),(17.8,False),(28.228,False)]:wire.hide_render=v;wire.keyframe_insert('hide_render',frame=F(t))
for t,p in plugkeys:
 bp=sp.bezier_points[-1];bp.co=(p[0],p[1]-.12,p[2]);bp.keyframe_insert('co',frame=F(t))
for a in [plug]+list(plug.children_recursive):
 for t,v in [(0,True),(17.7,True),(17.8,False),(28.228,False)]:a.hide_render=v;a.keyframe_insert('hide_render',frame=F(t))

# Append ONLY the original project-owned courier hierarchy, clearing previous story motion.
source=PROJECT_ROOT/'assets/stories/downward-beacon/scene.blend'
with bpy.data.libraries.load(str(source),link=False) as (src,dst):dst.objects=src.objects
loaded=[a for a in dst.objects if a];char=next(a for a in loaded if a.name=='Courier master');keep={char,*char.children_recursive}
for a in loaded:
 if a in keep:S.collection.objects.link(a);a.animation_data_clear()
 else:bpy.data.objects.remove(a,do_unlink=True)
char.location=(0,0,0);char.rotation_euler=(0,0,0);char.scale=(1,1,1)
neck=next(a for a in keep if a.name.startswith('Expressive neck'));neck.rotation_euler=(0,0,0)
limbs={}
for side,n in [(-1,'Left hip'),(1,'Right hip')]:
 hip=next(a for a in keep if a.name==n);knee=next(a for a in hip.children if a.name.startswith('Knee'));hip.rotation_euler=(0,0,0);knee.rotation_euler=(0,0,0);limbs['leg'+str(side)]=(hip,knee)
 sh=next(a for a in keep if a.name=='Shoulder '+str(side));el=next(a for a in sh.children if a.name.startswith('Elbow'));sh.rotation_mode='QUATERNION';el.rotation_mode='QUATERNION';sh.rotation_quaternion=Quaternion();el.rotation_quaternion=Quaternion();limbs['arm'+str(side)]=(sh,el)
eyes=[a for a in keep if a.name in ['Eye -1','Eye 1']];scarf=next(a for a in keep if a.name.startswith('Scarf tail hinge'))
travel=[(0,(-2.25,.75,1.02),1.55),(2.65,(-2.25,.75,1.02),1.55),(5.7,(-1.35,.75,1.02),1.55),(8.2,(-.45,.85,1.02),1.35),(9.3,(-.45,.85,1.02),1.35),(10.0,(-1.4,.25,.6),1.0),(12.0,(-1.25,-.1,-.06),1.0),(16.0,(-.35,-.12,-.06),1.6),(17.8,(.05,-.05,-.30),math.pi),(20.6,(.05,-.05,-.30),math.pi),(21.3,(-1.55,-.35,-.06),1.55),(24.5,(.0,-.30,-.06),2.0),(28.228,(.0,-.30,-.06),2.0)]
for t,p,rz in travel:key(char,t,'location',p);key(char,t,'rotation_euler',(0,0,rz))
linear(char)
for f in range(1,END+1,3):
 t=(f-1)/FPS;walk=1 if (3.2<t<8.0 or 9.5<t<16.0 or 21.3<t<24.3) else 0;phase=t*math.tau*1.05;crouch=max(0,min(1,(t-16.3)/1.3)) if t<20.7 else max(0,1-(t-20.7)/.5)
 for side in [-1,1]:
  hip,knee=limbs['leg'+str(side)];key(hip,t,'rotation_euler',(-.95*crouch+side*.28*math.sin(phase)*walk,0,0));key(knee,t,'rotation_euler',(1.4*crouch+max(0,-side*math.sin(phase))*.35*walk,0,0))
  if 16.5<t<21.2 or (side==1 and 2.7<=t<=5.6) or (side==-1 and t>=24.1):continue
  sh,el=limbs['arm'+str(side)];key(sh,t,'rotation_quaternion',Euler((-side*.25*math.sin(phase)*walk,0,side*.05)).to_quaternion());key(el,t,'rotation_quaternion',Euler((-.12,0,0)).to_quaternion())
# Listening hand, head turns and a purposeful kneeling connection.
sh,el=limbs['arm1']
for t,target in [(2.7,(.34,-.04,.76)),(3.5,(.28,-.02,1.72)),(4.5,(.28,-.02,1.72)),(5.5,(.34,-.04,.76))]:solve(sh,el,Vector((.34,0,1.36)),Vector(target),.30,.335,Vector((.7,-.3,0)),t)
for t,rot in [(0,(0,0,0)),(3.1,(0,0,-.25)),(3.7,(-.10,0,.30)),(5.5,(.06,0,.08)),(7.0,(.24,0,-.15)),(8.8,(.35,0,-.15)),(13.0,(.25,0,.1)),(16.3,(.3,0,.10)),(19.8,(.3,0,.08)),(21.3,(0,0,0)),(24.0,(0,0,-.35)),(25.3,(0,0,-.35)),(28.228,(0,0,-.3))]:key(neck,t,'rotation_euler',rot)
Ci=(Matrix.Translation((.05,-.05,-.30))@Matrix.Rotation(math.pi,4,'Z')).inverted()
for t,p in [(16.6,(.37,-.29,.52)),(17.8,(.40,-.26,.53)),(18.2,(.40,-.26,.53)),(18.95,(.46,-.12,.60)),(19.7,(.56,.08,.66)),(19.94,(.56,.105,.66)),(20.3,(.48,-.08,.56)),(20.65,(.37,-.25,.50))]:
 sh,el=limbs['arm-1'];solve(sh,el,Vector((-.34,0,1.36)),Ci@Vector((p[0]-.08,p[1]-.12,p[2]+.02)),.30,.335,Vector((-.6,-.4,-.3)),t)
# The return wave is real joint motion, not a repeated still.
sh,el=limbs['arm-1']
for t,a in [(24.2,0),(25.25,-2.05),(25.65,-2.3),(26.1,-1.95),(26.5,-2.3),(27,-1.95),(27.5,-2.22),(28.228,-2.05)]:key(sh,t,'rotation_quaternion',Euler((a,0,.20)).to_quaternion());key(el,t,'rotation_quaternion',Euler((-.6 if a else -.12,0,0)).to_quaternion())
for t in [0,2,4,6,8,10,12,14,16,18,20,22,24,26,28.228]:key(scarf,t,'rotation_euler',(math.sin(t*1.7)*.035,0,math.sin(t*1.5)*.06))
for eye in eyes:
 for t,scale in [(0,1),(4.9,1),(5.0,.12),(5.12,1),(15.7,1),(15.8,.12),(15.92,1),(25.0,1),(25.1,.12),(25.22,1),(28.228,1)]:key(eye,t,'scale',(1,1,scale))

# Warm/cool modeled light. Dawn is a clear editorial cut, not hours passing continuously.
night=light('Blue platform night fill',(1,-3.2,4.3),(.23,.43,1.0),340,5,(.6,.5,1.2))
light('Service-bay warm practical',(1.1,1.2,1.0),(1,.55,.21),75,1.7,(1.2,.1,.3))
light('Robot face cool edge',(.6,-1.3,1.6),(.25,.73,1),75,2.3,(1,.55,.4))
dawn=light('Dawn through station opening',(-3.0,-4.0,3.7),(1,.63,.30),0,4,(.5,.6,1.2))
for t,power in [(0,0),(21.25,0),(21.3,1150),(28.228,1150)]:dawn.data.energy=power;dawn.data.keyframe_insert('energy',frame=F(t))
for t,power in [(0,340),(21.25,340),(21.3,120),(28.228,120)]:night.data.energy=power;night.data.keyframe_insert('energy',frame=F(t))
for t,c,strength in [(0,(.025,.045,.09,1),.3),(21.25,(.025,.045,.09,1),.3),(21.3,(.20,.24,.31,1),.65),(28.228,(.20,.24,.31,1),.65)]:bg.inputs['Color'].default_value=c;bg.inputs['Color'].keyframe_insert('default_value',frame=F(t));bg.inputs['Strength'].default_value=strength;bg.inputs['Strength'].keyframe_insert('default_value',frame=F(t))

# Deliberate portrait cameras: action fills the image; no empty-sky establishing shot.
shots=[
 ('01_midnight_bell',0,2.7,(2.13,-2.80,1.25),(2.10,-2.60,1.24),(2.0,.45,1.32),(2.0,.45,1.32),50,'Bell sways; midnight clock in receding station background.'),
 ('02_listening',2.7,5.7,(-.75,-1.7,2.65),(-.65,-1.45,2.64),(-1.95,.76,2.25),(-1.43,.76,2.26),50,'Listening hand/head reaction, empty bench and last-train sign.'),
 ('03_hatch_investigation',5.7,9.3,(1.7,-1.55,3.65),(1.95,-1.15,3.15),(.0,.70,1.45),(.85,.65,1.02),42,'Courier approaches; real maintenance lid opens to reveal the bay.'),
 ('04_robot_cause',9.3,13.4,(3.15,-1.66,1.02),(2.96,-1.53,.98),(1.40,.40,.61),(1.42,.40,.60),55,'Original tool cart and actual wrench-to-bell impact share the image.'),
 ('05_low_battery',13.4,16.1,(1.22,-1.05,.85),(1.19,-.99,.83),(.86,.20,.56),(.86,.20,.53),55,'Single LED face and battery segments visibly dim; wrench arm weakens.'),
 ('06_call_for_help',16.1,18.35,(2.85,-2.05,1.78),(2.72,-1.92,1.72),(.67,.25,1.0),(.65,.22,.95),48,'Courier crouches beside robot and takes intact charger lead.'),
 ('07_charge_connection',18.35,21.3,(1.18,-.90,.32),(1.12,-.82,.34),(.56,.16,.65),(.56,.16,.65),52,'Plug physically seats before four battery lights and LED recover.'),
 ('08_dawn_callback',21.3,24.6,(3.1,-2.85,2.42),(2.95,-2.58,2.31),(.45,.70,1.18),(.55,.65,1.20),45,'Warm dawn; same bell/robot, connected cable, courier returns.'),
 ('09_wave_back',24.6,DURATION,(2.36,-1.87,1.75),(2.22,-1.70,1.70),(.35,.25,1.05),(.37,.25,1.08),40,'Robot greeting and courier return wave in a close two-shot.')]
rows=[]
for n,a,b,l1,l2,t1,t2,lens,purpose in shots:
 d=bpy.data.cameras.new(n);cam=bpy.data.objects.new(n,d);S.collection.objects.link(cam);d.lens=lens;d.sensor_width=36;d.sensor_fit='HORIZONTAL';d.clip_start=.03;d.clip_end=100;d.dof.use_dof=False
 for t,loc,target in [(a,l1,t1),(b,l2,t2)]:cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.keyframe_insert('location',frame=F(t));cam.keyframe_insert('rotation_euler',frame=F(t))
 linear(cam);marker=S.timeline_markers.new(n,frame=F(a));marker.camera=cam;rows.append({'shot':n,'start_seconds':a,'end_seconds':b,'start_frame':F(a),'end_frame':END if b==DURATION else F(b)-1,'camera':n,'purpose':purpose})
S.camera=bpy.data.objects[shots[0][0]]
S.use_nodes=True;nt=S.node_tree;nt.nodes.clear();rl=nt.nodes.new('CompositorNodeRLayers');gl=nt.nodes.new('CompositorNodeGlare');gl.glare_type='FOG_GLOW';gl.quality='LOW';gl.threshold=1.7;gl.mix=-.96;comp=nt.nodes.new('CompositorNodeComposite');nt.links.new(rl.outputs['Image'],gl.inputs['Image']);nt.links.new(gl.outputs['Image'],comp.inputs['Image'])
S.frame_set(1);blend=R/'midnight-bell.blend';bpy.ops.wm.save_as_mainfile(filepath=str(blend))
plan={'title':'Midnight Bell','status':'representative_frames_only_not_full_rendered','original_geometry':['Entire station, clock, bell, hatch, robot/toolbox/wheels, charger, cable, wrench, environment, cameras and animation authored here.'],'project_owned_reuse':{'courier_blend':str(source),'courier_blend_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'only_hierarchy':'Courier master and its children; previous story animation removed.'},'external_geometry_assets':[],'copyrighted_designs_imported':False,'narration_path':str(PROJECT_ROOT.parent/'quality-reset-2026-11-16/midnight-bell-audio/narration-paced.wav'),'narration_sha256':'22bc37f7aafbdebbafe2295fbccc9faca92820065522a5ff175250f72f0064dd','narration_duration_seconds':DURATION,'authored_fps':FPS,'frame_count':END,'frame_quantized_picture_duration_seconds':END/FPS,'native_resolution':[720,1280],'engine':'Cycles CPU','samples':4,'threads':2,'denoiser':'Reviewed standalone Open Image Denoise2.5.1 RT LDR/sRGB high, same-size images.','shots':rows,'physical_bell_impact_seconds':impacts,'critical_actions':{'hatch_opens':[8.35,9.25],'low_battery_dims':[13.5,15.6],'plug_travel':[18.95,19.94],'charger_seated':19.94,'battery_recovers':20.05,'dawn_cut':21.3,'robot_wave':[24.4,27.3],'courier_wave':[25.25,28.228]},'render_authorization':'Only representative stills. Full render requires parent inspection; no full-render entry point in this script.'}
(R/'motion-and-camera-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
receipts=[]
def render(t,label):
 raw=R/'review-raw';clean=R/'review-clean';raw.mkdir(exist_ok=True);clean.mkdir(exist_ok=True);S.frame_set(F(t));S.render.filepath=str(raw/(label+'.png'));start=time.time();bpy.ops.render.render(write_still=True);elapsed=time.time()-start;start=time.time();subprocess.run(['/usr/bin/env','python3',str(SOURCE_DIR/'denoise_frames.py'),S.render.filepath,'--out',str(clean)],check=True);receipts.append({'seconds':t,'source_frame':F(t),'raw_path':S.render.filepath,'denoised_path':str(clean/(label+'.png')),'render_seconds':round(elapsed,3),'denoise_seconds':round(time.time()-start,3),'sha256':hashlib.sha256((clean/(label+'.png')).read_bytes()).hexdigest()});(R/'representative-render-receipts.json').write_text(json.dumps(receipts,indent=2)+'\n');print('REPRESENTATIVE_FRAME_READY',json.dumps(receipts[-1]),flush=True)
if o.stills:
 for t,n in [(1.20,'01-midnight-hook'),(11.3,'02-robot-cause'),(19.95,'03-connection'),(26.15,'04-dawn-wave')]:render(t,n)
if o.frames:
 for t in o.frames:render(t,'frame-'+str(t).replace('.','-'))
print('SCENE_AND_PLAN_READY',str(blend),flush=True)
