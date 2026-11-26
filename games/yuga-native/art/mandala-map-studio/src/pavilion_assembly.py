"""Film the registered Quarter-turn Pavilion's 62 original mesh parts in Blender.

Run with python3. --save-blend PATH also saves the keyed part and camera motion.
The checked-in inputs stay untouched. Blender 4.3, Pillow and FFmpeg are required.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile

STUDIO = Path(__file__).resolve().parents[1]
ATLAS = STUDIO.parents[1]/'docs/design/ember-rite-5v5/atlas'
MODEL = ATLAS/'massing/mandala-architecture.glb'
FPS, FRAMES = 16,128
CLIP_SIZE = (768,432)
CHAPTERS = ('foundations','piers','threshold','roof','crown')
COUNTS = (4,42,2,12,2)
PIER = ('bottom course','foot moulding','lower band','shaft','neck ring','capital','bearing')
PAPER = (247,243,231)
INK = (35,60,61)
MUTED = (76,94,90)
COPPER = (151,80,51)
RULE = (182,184,166)


def part_motion(name):
    """Return assembly membership, exploded displacement, and 1-based animation keys."""
    if name.startswith('Wing '):
        side=int(name.split()[1]); outer=name.endswith('inner return')
        return 'foundations',(side*(1.64 if outer else 1.05),0,.82 if outer else .12),(31,57),(68,83)
    if name.startswith('Pier '):
        _,station,finish=name.split(' ',2)
        side,bay=map(int,station.split('.'));k=PIER.index(finish)
        return 'piers',(side*1.36,(bay-1)*1.32,.67+k*.265),(27-k,52+k//2),(73+k*2,90+k*2)
    if name.startswith('Fold threshold inlay '):
        k=int(name.rsplit('.',1)[1]);return 'threshold',(-1.05+(.12 if k==2 else -.12),-.58,.31),(27,52),(79,98)
    if name.startswith('Course '):
        _,level,part=name.split(' ',2)
        level=int(level);k=('cornice','shadow','battered wall').index(part)
        return 'roof',(0,0,4.15+(level-1)*2.08+k*.23),(22-level*2,47-level*2),(88+level*4+k,101+level*4+k)
    if name in ('Crown saddle','Ridge crown'):
        top=int(name=='Ridge crown');return 'crown',(0,0,12.10+top*.86),(13-top,35-top),(108+top*2,121+top)
    raise ValueError(f'Unassigned pavilion mesh {name}')


def args():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=STUDIO/'assembly')
    p.add_argument('--save-blend',type=Path,help='Optional editable local animation scene')
    p.add_argument('--blender-work',type=Path,help=argparse.SUPPRESS)
    return p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else None)


def fitted_camera(scene,camera,objects,size,az,alt,padding=1.12):
    """Orthographic fit to real transformed mesh vertices, independent of part origins."""
    from mathutils import Vector
    az,alt=math.radians(az),math.radians(alt)
    direction=Vector((math.cos(az)*math.cos(alt),math.sin(az)*math.cos(alt),math.sin(alt)))
    rot=(-direction).to_track_quat('-Z','Y')
    inverse=rot.inverted()
    points=[inverse @ (o.matrix_world @ v.co) for o in objects for v in o.data.vertices]
    lo=Vector([min(v[k] for v in points) for k in range(3)])
    hi=Vector([max(v[k] for v in points) for k in range(3)])
    center=rot @ ((hi+lo)*.5)
    camera.location=center+direction*38
    camera.rotation_euler=rot.to_euler()
    aspect=size[0]/size[1]
    camera.data.ortho_scale=max((hi.x-lo.x)*max(1.,1/aspect),(hi.y-lo.y)*max(1.,aspect))*padding
    scene.render.resolution_x,scene.render.resolution_y=size
    return center


def render(work,save_blend):
    import bpy
    from bpy_extras.object_utils import world_to_camera_view
    from mathutils import Vector

    catalog=json.loads((STUDIO/'catalog.json').read_text())
    record=next(row for row in catalog['elements'] if row['id']=='architecture-quarter-turn-pavilion')
    if len(record['parts'])!=len(set(record['parts'])) or len(record['parts'])!=62:
        raise ValueError('The catalog must contain 62 distinct pavilion components')
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(MODEL))
    scene=bpy.context.scene
    scene.name='Quarter-turn Pavilion · Construction study'
    root,=[o for o in scene.objects if o.get('kind')=='district_architecture']
    if root.get('source_sha256')!=catalog['layout_sha256'] or root.get('room_id')!='pyramid_s':
        raise ValueError('Pavilion registration disagrees with the atlas')
    by_name={o.name:o for o in scene.objects if o.type=='MESH'}
    if by_name.keys()!=set(record['parts']):
        raise ValueError('The imported GLB inventory disagrees with the parts catalog')
    world_origin=root.matrix_world.copy()
    inverse=world_origin.inverted()
    objects=list(by_name.values());rest={o:o.location.copy() for o in objects}
    def center(o):
        points=[o.matrix_world@v.co for v in o.data.vertices]
        return Vector([(min(v[k] for v in points)+max(v[k] for v in points))*.5 for k in range(3)])
    def rounded(v): return [round(float(n),5) for n in v]
    parts=[]
    for name in record['parts']:
        obj=by_name[name];group,offset,opening,closing=part_motion(name)
        local=inverse@center(obj)
        parts.append(dict(name=name,group=group,material=obj.data.materials[0].name,rest_center_m=rounded(local),
                          exploded_offset_m=rounded(offset),open_frames=list(opening),close_frames=list(closing)))
        obj['assembly_group']=group
        # Translation in the imported pavilion parent's frame. Mesh vertices, materials,
        # original registration, orientation and scale remain their authored values.
        for f,amount in ((1,0),(opening[0],0),(opening[1],1),(closing[0],1),(closing[1],0),(FRAMES,0)):
            obj.location=rest[obj]+Vector(offset)*amount
            obj.keyframe_insert(data_path='location',frame=f,group='Assembly translation')
        for fcurve in obj.animation_data.action.fcurves:
            for key in fcurve.keyframe_points:
                key.interpolation='BEZIER';key.handle_left_type='AUTO_CLAMPED';key.handle_right_type='AUTO_CLAMPED'
    totals=Counter(p['group'] for p in parts)
    if tuple(totals[k] for k in CHAPTERS)!=COUNTS:
        raise ValueError(f'Pavilion groups disagree: {totals}')
    scene.frame_start=1;scene.frame_end=FRAMES;scene.render.fps=FPS
    scene.frame_set(1)
    corners=[inverse@(o.matrix_world@v.co) for o in objects for v in o.data.vertices]
    envelope=[max(p[k] for p in corners)-min(p[k] for p in corners) for k in range(3)]
    if any(abs(n-e)>.002 for n,e in zip(envelope,record['size_m'])):
        raise ValueError(f'Incorrect installed envelope {envelope}')
    manifest=dict(schema='yuga.pavilion-assembly.v1',title=record['title'],source_glb='../../../docs/design/ember-rite-5v5/atlas/massing/mandala-architecture.glb',
                  source_glb_sha256=hashlib.sha256(MODEL.read_bytes()).hexdigest(),source_layout_sha256=catalog['layout_sha256'],
                  frame_basis='1-based inclusive; Blender local axes +X east, +Y north, +Z up; metres',
                  source_origin_blender_xyz=rounded(world_origin.translation),installed_envelope_m=rounded(envelope),
                  clear_width_m=round(record['clear_width_m'],5),clear_height_m=round(record['clear_height_m'],5),fps=FPS,frames=FRAMES,
                  exploded_hold_frame=62,groups={k:totals[k] for k in CHAPTERS},parts=parts,
                  method='Original GLB geometry. Translation keys separate the named pieces, then restore every installed transform.',
                  source_notes=[{'title':s['title'],'href':s['href'] if s['href'].startswith('https://') else '../'+s['href']} for s in record['source_refs']])
    (work/'parts.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
    scene.render.engine='BLENDER_WORKBENCH';scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.image_settings.compression=8
    scene.render.film_transparent=True;scene.view_settings.view_transform='Standard';scene.view_settings.exposure=.53
    shade=scene.display.shading;shade.light='STUDIO';shade.studio_light='paint.sl';shade.color_type='MATERIAL'
    shade.show_shadows=True;shade.shadow_intensity=.32;shade.show_cavity=True;shade.cavity_type='BOTH'
    shade.curvature_ridge_factor=.55;shade.curvature_valley_factor=1.10;shade.show_specular_highlight=False
    scene.display.render_aa='FXAA'
    camera_data=bpy.data.cameras.new('Survey lens');camera_data.type='ORTHO';camera_data.clip_end=200
    camera=bpy.data.objects.new('Survey camera',camera_data);scene.collection.objects.link(camera);scene.camera=camera
    info={}
    def shot(name, frame, size, visible, targets, az,alt,pad,features):
        scene.frame_set(frame)
        for o in objects:o.hide_render=o.name not in visible
        fitted_camera(scene,camera,[by_name[n] for n in targets],size,az,alt,pad)
        bpy.context.view_layer.update()
        info[name]={}
        for tag,names in features.items():
            v=sum((center(by_name[n]) for n in names),Vector())/len(names)
            u=world_to_camera_view(scene,camera,v)
            info[name][tag]=[round(u.x*size[0],2),round((1-u.y)*size[1],2)]
        scene.render.filepath=str(work/(name+'.png'));bpy.ops.render.render(write_still=True)
    all_names=list(by_name)
    shot('exploded',62,(585,650),all_names,all_names,-63,13,1.08,
         {'crown':['Ridge crown'],'roof':['Course 3 cornice'],'piers':['Pier 1.0 neck ring'],
          'foundations':['Wing 1 inner return'],'threshold':['Fold threshold inlay 1.1','Fold threshold inlay 1.2']})
    shot('installed',1,(608,245),all_names,all_names,-63,22,1.09,{})
    pier=['Pier -1.0 '+k for k in PIER]
    shot('pier',62,(245,303),pier,pier,-65,15,1.10,{k:[n] for k,n in zip(PIER,pier)})
    mark=['Fold threshold inlay 1.1','Fold threshold inlay 1.2']
    shot('mark',1,(245,105),mark+['Wing -1 plinth'],mark,-84,5,1.54,{})
    (work/'anchors.json').write_text(json.dumps(info))
    for obj in objects:obj.hide_render=False
    # The moving camera is keyed as well so an optional .blend reproduces the film.
    # Keep the whole building registered in world space, including the settled wings.
    clean=(CLIP_SIZE[0],CLIP_SIZE[1]-80)
    for f in range(1,FRAMES+1):
        scene.frame_set(f)
        t=(f-1)/(FRAMES-1)
        az=-67+23*(3*t*t-2*t**3)
        fitted_camera(scene,camera,objects,clean,az,15+3*math.sin(math.pi*t),1.09)
        camera.keyframe_insert(data_path='location',frame=f)
        camera.keyframe_insert(data_path='rotation_euler',frame=f)
        camera_data.keyframe_insert(data_path='ortho_scale',frame=f)
    for f,tag in ((1,'Installed'),(12,'Separate'),(58,'Exploded'),(68,'Assemble'),(122,'Registered')):
        scene.timeline_markers.new(tag,frame=f)
    scene.frame_set(FRAMES)
    if any((o.location-rest[o]).length>.00001 for o in objects):
        raise ValueError('The installed pose did not close')
    scene.frame_set(62)
    for part in parts:
        obj=by_name[part['name']]
        error=obj.location-rest[obj]-Vector(part['exploded_offset_m'])
        if error.length>.00002:
            raise ValueError(f"The hold pose disagrees for {part['name']}")
    scene.frame_set(1)
    if save_blend:
        save_blend.parent.mkdir(parents=True,exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(save_blend))
    scene.render.filepath=str(work/'image-')
    bpy.ops.render.render(animation=True)


def letterface(n,role='sans'):
    from PIL import ImageFont
    families={'sans':'DejaVuSans.ttf','serif':'DejaVuSerif.ttf','mono':'DejaVuSansMono.ttf'}
    try:
        return ImageFont.truetype(families[role],n)
    except OSError:
        return ImageFont.load_default(size=n)


def paste_render(canvas,file,position):
    from PIL import Image
    with Image.open(file) as original:
        layer=original.convert('RGBA')
        canvas.paste(layer,position,layer.getchannel('A'))


def plate(work):
    from PIL import Image,ImageDraw
    main=Image.new('RGB',(1600,1060),PAPER);d=ImageDraw.Draw(main)
    anchors=json.loads((work/'anchors.json').read_text())
    def text(x,y,s,size=17,role='sans',color=INK,anchor='lt'):
        d.text((x,y),s,fill=color,font=letterface(size,role),anchor=anchor)
    def marker(x,y):
        d.ellipse((x-3,y-3,x+3,y+3),fill=COPPER,outline=PAPER,width=1)
    d.rectangle((0,0,1600,8),fill=INK)
    text(43,31,'YUGA  /  MANDALA RIFT',16,'mono',MUTED)
    text(1556,31,'SOUTH PYRAMID  /  CONSTRUCTION STUDY',16,'mono',MUTED,'rt')
    text(40,61,'Quarter-turn Pavilion',51,'serif')
    text(1556,83,'10 × 8 m at the sill    /    9 m high',20,'mono',INK,'rt')
    d.line((43,133,1557,133),fill=INK,width=2)
    d.line((915,154,915,869),fill=RULE,width=1)
    text(44,157,'Exploded axonometric',27,'serif')
    text(44,194,'62 named meshes',15,'mono',MUTED)
    loc=(48,212)
    paste_render(main,work/'exploded.png',loc)
    groups={'crown':('Crown','Saddle and ridge cap'), 'roof':('Four roof courses','Cornice, shadow band,', 'battered wall per tier'),
            'piers':('Six piers','Three per flank,','seven pieces per pier'),
            'foundations':('Two wings','Two plinths, two returns'), 'threshold':('Threshold inlay','Two joined strips')}
    mark_y={k:anchors['exploded'][k][1]+loc[1] for k in groups}
    ys=[]
    for k in sorted(groups,key=mark_y.get):
        top=max(mark_y[k]-16,ys[-1]+71 if ys else 231)
        ys.append(top)
    if ys[-1]>805:
        excess=ys[-1]-805
        ys=[y-excess for y in ys]
    for k,ly in zip(sorted(groups,key=mark_y.get),ys):
        ax=anchors['exploded'][k][0]+loc[0];ay=mark_y[k];x=651
        if k=='threshold':
            leader=[(ax,ay),(ax-9,ay+16),(ax-9,858),(613,858),(625,ly+9),(x-10,ly+9)]
        else:
            leader=[(ax,ay),(min(615,max(ax+14,ax+(615-ax)*.80)),ay),(625,ly+9),(x-10,ly+9)]
        d.line(leader,fill=(139,118,93),width=1)
        marker(ax,ay)
        text(x,ly,groups[k][0],20,'serif')
        for j,s in enumerate(groups[k][1:]):text(x,ly+26+j*18,s,14,'sans',MUTED)
    text(947,157,'As installed',27,'serif')
    paste_render(main,work/'installed.png',(944,197))
    text(947,454,'5.00 m clear width   /   4.23 m headroom',19,'mono')
    text(947,484,'The passage runs north from the south threshold.',16,'sans',MUTED)
    d.line((943,517,1557,517),fill=RULE,width=1)
    text(947,537,'One pier, seven pieces',25,'serif')
    pos=(951,570)
    paste_render(main,work/'pier.png',pos)
    prev=578
    for part in reversed(PIER):
        a=[v+inc for v,inc in zip(anchors['pier'][part],pos)]
        y=max(prev,a[1]);prev=y+25
        d.line([(a[0],a[1]),(1173,a[1]),(1202,y),(1229,y)],fill=(139,118,93),width=1)
        marker(*a)
        text(1244,y-8,part.capitalize(),18)
    d.line((43,888,1557,888),fill=INK,width=2)
    text(44,909,'Threshold detail',19,'serif')
    paste_render(main,work/'mark.png',(37,942))
    text(315,938,'The southern fold',22,'serif')
    text(315,974,'A pale V on the west plinth identifies the South Pyramid mouth.',17,'sans',MUTED)
    text(315,1003,'The paired north fold uses two horizontal bars.',16,'sans',MUTED)
    d.line((1038,922,1038,1021),fill=RULE,width=1)
    text(1060,938,'Map registration',22,'serif')
    text(1060,974,'28 m east, 32 m south of the plan origin.',16,'sans',MUTED)
    text(1060,1003,'M1 · Chola temple profiles informed the stepped roof.',15,'sans',MUTED)
    main.save(work/'pavilion.webp',format='WEBP',quality=94,method=6)


def encode(work):
    from PIL import Image,ImageDraw
    w,h=CLIP_SIZE
    command=['ffmpeg','-nostdin','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-video_size',f'{w}x{h}',
             '-framerate',str(FPS),'-i','pipe:0','-an','-c:v','libx264','-preset','fast','-threads','1',
             '-crf','20','-pix_fmt','yuv420p','-movflags','+faststart',str(work/'pavilion.mp4')]
    faces={'heading':letterface(20,'serif'),'phase':letterface(13,'mono'),'caption':letterface(14)}
    with subprocess.Popen(command,stdin=subprocess.PIPE) as ff:
        for f in range(1,FRAMES+1):
            canvas=Image.new('RGB',(w,h),PAPER);d=ImageDraw.Draw(canvas)
            paste_render(canvas,work/f'image-{f:04}.png',(0,37))
            d.text((21,13),'Quarter-turn Pavilion',font=faces['heading'],fill=INK,anchor='lt')
            d.text((w-21,17),'MANDALA RIFT  /  SOUTH PYRAMID',font=faces['phase'],fill=MUTED,anchor='rt')
            d.line((21,36,w-21,36),fill=RULE)
            d.line((21,h-41,w-21,h-41),fill=RULE)
            if f<13:
                label='Installed';detail='5.00 m clear passage'
            elif f<58:
                label='Separate the parts';detail='Six piers carry four stepped roof courses'
            elif f<68:
                label='Exploded assembly';detail='4 wing pieces  /  42 pier pieces  /  2 inlays  /  12 roof pieces  /  2 crown pieces'
            elif f<91:
                label='Set the wings';detail='Plinths, returns and six pier stacks'
            elif f<104:
                label='Close the piers';detail='Capitals and bearings meet the lower cornice'
            elif f<122:
                label='Seat the roof';detail='Four courses, then the saddle and ridge cap'
            else:
                label='Installed';detail='All 62 parts restored to the registered pose'
            d.text((21,h-32),label,font=faces['phase'],fill=COPPER,anchor='lt')
            d.text((w-21,h-32),detail,font=faces['caption'],fill=INK,anchor='rt')
            d.line((21,h-10,21+(w-42)*(f-1)/(FRAMES-1),h-10),fill=COPPER,width=2)
            ff.stdin.write(canvas.tobytes())
        ff.stdin.close()
        if ff.wait():raise RuntimeError('FFmpeg failed to encode the pavilion film')


def publish(work,destination):
    import shutil
    from PIL import Image
    plate(work);encode(work)
    with Image.open(work/'pavilion.webp') as im:
        assert im.size==(1600,1060) and im.format=='WEBP'
    stream=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries',
             'stream=codec_name,pix_fmt,width,height,nb_read_frames,r_frame_rate','-of','json',str(work/'pavilion.mp4')]))['streams'][0]
    if (stream['codec_name'],stream['pix_fmt'],stream['width'],stream['height'],int(stream['nb_read_frames']),stream['r_frame_rate'])!=('h264','yuv420p',*CLIP_SIZE,FRAMES,f'{FPS}/1'):
        raise RuntimeError(f'Unexpected video stream: {stream}')
    destination.mkdir(parents=True,exist_ok=True)
    for name in ('parts.json','pavilion.webp','pavilion.mp4'):
        with tempfile.NamedTemporaryFile(dir=destination,delete=False) as temp:
            with (work/name).open('rb') as src:shutil.copyfileobj(src,temp)
        Path(temp.name).replace(destination/name)


if __name__=='__main__':
    import os
    options=args()
    if options.blender_work:
        render(options.blender_work,options.save_blend)
    else:
        with tempfile.TemporaryDirectory() as temporary:
            work=Path(temporary)
            command=['blender','-b','--factory-startup','-t','1','--python-exit-code','1','--python',str(Path(__file__).resolve()),'--','--blender-work',str(work)]
            if options.save_blend:command+=['--save-blend',str(options.save_blend.resolve())]
            subprocess.run(command,check=True,env={**os.environ,'LP_NUM_THREADS':'1','OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1'})
            publish(work,options.output)
