"""Render the registered map in Cycles and compose three camera studies.

blender -b --factory-startup -t 2 --python-exit-code 1 --python src/light_study.py
Use -- --preview-dir /tmp/mandala-proof for a half-size lighting proof.
Blender builds without embedded Open Image Denoise can use its upstream CPU
tool (`oidnDenoise` on PATH or `--denoiser /path/to/oidnDenoise`). The shot
is denoised in scene-linear HDR before the AgX transform. Release used here:
https://github.com/RenderKit/oidn/releases/tag/v2.5.1
"""
import argparse
from dataclasses import dataclass
from math import radians
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory

import bpy
import _cycles
from mathutils import Vector


STUDIO = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Shot:
    name: str
    collection: str
    eye: tuple
    look: tuple
    lens: float
    aperture: float
    size: tuple
    title: str
    caption: str


# Local directions are measured in multiples of the focal object's largest span.
# The first shot lets the bell comb overlap the next terrace like a framing pier.
SHOTS = (
    Shot('ghat','artifact-bell-comb',(-3.23,-1.65,.33),(.53,-.29,.08),38,4.3,
         (1440,650),'Ghat Mandapa','Bell screen on the approach from the river'),
    Shot('ewer','rite-water-ewer',(2.57,-2.85,.78),(-.01,.00,.02),74,5.6,
         (713,448),'Water ewer','Patinated body, brass handle and rolled spout'),
    Shot('pavilion','architecture-quarter-turn-pavilion',(1.68,-2.30,.57),(0,0,.01),47,8.0,
         (713,448),'Quarter-turn Pavilion','The southern threshold from the market road'),
)


def aim(obj, target):
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()


def bounds(name):
    col=bpy.data.collections[name]
    corners=[o.matrix_world@Vector(corner) for o in col.all_objects if o.type=='MESH' for corner in o.bound_box]
    lo=Vector(tuple(min(corner[i] for corner in corners) for i in range(3)))
    hi=Vector(tuple(max(corner[i] for corner in corners) for i in range(3)))
    return (hi+lo)*.5,max(hi-lo)


def micro_surfaces():
    """Use world metres for stone pores and hammering, preserving packed PBR maps."""
    for material in bpy.data.materials:
        if not material.use_nodes:continue
        name=material.name.lower()
        tower_stone=name in ('stone','highlight','recess','plinth')
        if not (name.startswith('mandala / ') or tower_stone or name=='copper'):continue
        metal=any(x in name for x in ('patina','bronze','brass','copper'))
        stone=tower_stone or any(x in name for x in ('stone','granite','basalt','terracotta'))
        fabric=any(x in name for x in ('linen','saffron','madder','indigo','timber'))
        if not (metal or stone or fabric):continue
        graph=material.node_tree
        bs=next((n for n in graph.nodes if n.type=='BSDF_PRINCIPLED'),None)
        if bs is None or bs.inputs['Base Color'].is_linked:continue
        geometry=graph.nodes.new('ShaderNodeNewGeometry')
        rough=graph.nodes.new('ShaderNodeTexNoise');rough.noise_dimensions='3D'
        rough.inputs['Scale'].default_value=96 if metal else 48 if fabric else 35
        rough.inputs['Detail'].default_value=2
        graph.links.new(geometry.outputs['Position'],rough.inputs['Vector'])
        bump=graph.nodes.new('ShaderNodeBump');bump.inputs['Distance'].default_value=.001 if metal else .017 if stone else .006
        bump.inputs['Strength'].default_value=.16 if metal else .24
        graph.links.new(rough.outputs['Fac'],bump.inputs['Height']);graph.links.new(bump.outputs['Normal'],bs.inputs['Normal'])
        base=tuple(bs.inputs['Base Color'].default_value)
        grain=graph.nodes.new('ShaderNodeTexNoise');grain.inputs['Scale'].default_value=7 if metal else 3.8
        grain.inputs['Detail'].default_value=2
        graph.links.new(geometry.outputs['Position'],grain.inputs['Vector'])
        ramp=graph.nodes.new('ShaderNodeValToRGB');a,b=ramp.color_ramp.elements
        a.position=.16;b.position=.84
        a.color=tuple(v*.84 for v in base[:3])+(1,)
        b.color=tuple(min(1,v*1.10+.003) for v in base[:3])+(1,)
        graph.links.new(grain.outputs['Fac'],ramp.inputs['Fac']);graph.links.new(ramp.outputs['Color'],bs.inputs['Base Color'])


def add_light(scene,label,kind,color,power,source,look,width):
    data=bpy.data.lights.new(label,kind);data.energy=power;data.color=color
    if kind=='SUN':data.angle=radians(width)
    else:data.shape='DISK';data.size=width
    ob=bpy.data.objects.new(label,data);scene.collection.objects.link(ob);ob.location=source;aim(ob,look)
    return ob


def configure(scene,preview):
    scene.render.engine='CYCLES'
    scene.cycles.device='CPU';scene.cycles.samples=12 if preview else 48
    scene.cycles.use_adaptive_sampling=True;scene.cycles.adaptive_threshold=.095 if preview else .036
    scene.cycles.use_denoising=bool(_cycles.with_openimagedenoise);scene.cycles.max_bounces=6;scene.cycles.diffuse_bounces=3
    scene.cycles.glossy_bounces=3;scene.cycles.transparent_max_bounces=3
    scene.render.threads_mode='FIXED';scene.render.threads=2
    scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
    scene.render.film_transparent=False;scene.render.resolution_percentage=50 if preview else 100
    scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'
    scene.view_settings.exposure=.04
    for ob in scene.objects:
        if ob.type=='LIGHT':ob.hide_render=True
    scene.world=bpy.data.worlds.new('Mandala · blue monsoon sky');scene.world.use_nodes=True
    graph=scene.world.node_tree;bg=graph.nodes['Background']
    bg.inputs[0].default_value=(.46,.61,.79,1);bg.inputs[1].default_value=.46
    # A clear-sky horizon seen by the lens, with site bounce set independently.
    sky=graph.nodes.new('ShaderNodeTexSky');sky.sky_type='NISHITA';sky.sun_disc=False
    sky.sun_elevation=radians(33);sky.sun_rotation=radians(236);sky.dust_density=1.5
    horizon=graph.nodes.new('ShaderNodeBackground');horizon.inputs['Strength'].default_value=.12
    graph.links.new(sky.outputs['Color'],horizon.inputs['Color'])
    mix=graph.nodes.new('ShaderNodeMixShader');rays=graph.nodes.new('ShaderNodeLightPath')
    graph.links.new(rays.outputs['Is Camera Ray'],mix.inputs[0]);graph.links.new(bg.outputs[0],mix.inputs[1])
    graph.links.new(horizon.outputs[0],mix.inputs[2]);graph.links.new(mix.outputs[0],graph.nodes['World Output'].inputs['Surface'])
    add_light(scene,'Sunlight through the river gate','SUN',(1.,.81,.61),2.7,(-55,-85,65),(0,0,0),5.5)
    micro_surfaces()


def filtered_hdr(scene, path, denoiser):
    """Move unclamped, bottom-up RGB floats between Blender and OIDN's PFM IO."""
    import numpy as np
    exr=path.with_suffix('.exr');inp=path.with_suffix('.pfm');out=path.with_name(path.stem+'-clean.pfm')
    scene.render.image_settings.file_format='OPEN_EXR';scene.render.image_settings.color_depth='16'
    scene.render.filepath=str(exr);bpy.ops.render.render(write_still=True)
    image=bpy.data.images.load(str(exr));width,height=image.size
    rgba=np.empty(width*height*4,dtype=np.float32);image.pixels.foreach_get(rgba)
    with inp.open('wb') as handle:
        handle.write(f'PF\n{width} {height}\n-1.0\n'.encode());rgba.reshape(height,width,4)[:,:,:3].astype('<f4').tofile(handle)
    subprocess.run([denoiser,'-d','cpu','-f','RT','--hdr',str(inp),'-o',str(out),'--threads','2','--quality','high'],check=True)
    with out.open('rb') as handle:
        assert handle.readline().strip()==b'PF';assert handle.readline().split()==[str(width).encode(),str(height).encode()]
        endian='<f4' if float(handle.readline())<0 else '>f4';rgb=np.fromfile(handle,dtype=endian).reshape(height,width,3)
    rgba=rgba.reshape(height,width,4);rgba[:,:,:3]=rgb;rgba[:,:,3]=1
    image.pixels.foreach_set(rgba.ravel());image.update()
    scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_depth='8'
    image.save_render(str(path),scene=scene);bpy.data.images.remove(image)
    for intermediate in (exr,inp,out):intermediate.unlink()


def photograph(scene,shot,directory,denoiser):
    centre,span=bounds(shot.collection)
    target=centre+Vector(shot.look)*span
    camera_data=bpy.data.cameras.new(shot.name);camera_data.lens=shot.lens;camera_data.sensor_width=36
    camera=bpy.data.objects.new('Study camera · '+shot.title,camera_data);scene.collection.objects.link(camera)
    camera.location=centre+Vector(shot.eye)*span;aim(camera,target);scene.camera=camera
    camera_data.clip_start=.025;camera_data.clip_end=450
    camera_data.dof.use_dof=True;camera_data.dof.focus_distance=(camera.location-centre).length
    camera_data.dof.aperture_fstop=shot.aperture;camera_data.dof.aperture_blades=9
    fill=add_light(scene,'Reflected sky · '+shot.name,'AREA',(.68,.83,1.),max(3,15*span*span),
                   centre+Vector((.75,-.45,1.2))*span,centre,span*1.2)
    rim=add_light(scene,'Sunlit wall bounce · '+shot.name,'AREA',(1.,.77,.51),max(3,11*span*span),
                  centre+Vector((-.64,.52,.95))*span,centre,span*.74)
    scene.render.resolution_x,scene.render.resolution_y=shot.size
    path=directory/(shot.name+'.png')
    if not scene.cycles.use_denoising and denoiser:
        filtered_hdr(scene,path,denoiser)
    else:
        scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
    if not scene.cycles.use_denoising and not denoiser and shutil.which('ffmpeg'):
        cleaned=directory/(shot.name+'-clean.png')
        subprocess.run(['ffmpeg','-loglevel','error','-y','-threads','2','-filter_threads','2','-i',str(path),
                        '-vf','nlmeans=s=2.4:p=3:r=7','-frames:v','1',str(cleaned)],check=True)
        cleaned.replace(path)
    for obj in (fill,rim,camera):bpy.data.objects.remove(obj,do_unlink=True)


def typeface(size,title=False):
    from PIL import ImageFont
    for name in (('NotoSerif-Regular.ttf','DejaVuSerif.ttf') if title else ('NotoSans-Regular.ttf','DejaVuSans.ttf')):
        try:return ImageFont.truetype(name,size)
        except OSError:pass
    return ImageFont.load_default(size=size)


def assemble(directory,dest):
    from PIL import Image,ImageDraw
    images=[Image.open(directory/(shot.name+'.png')).convert('RGB') for shot in SHOTS]
    scale=images[0].width/1440
    def px(n):return round(n*scale)
    margin=px(20);gutter=px(14);bar=px(59)
    wide=images[0].width;lower_h=images[1].height
    paper=Image.new('RGB',(wide+2*margin,2*margin+images[0].height+lower_h+2*bar+gutter),(240,232,214))
    draw=ImageDraw.Draw(paper); top=margin
    slots=((margin,top),(margin,top+images[0].height+bar+gutter),
           (margin+images[1].width+gutter,top+images[0].height+bar+gutter))
    for shot,img,(left,upper) in zip(SHOTS,images,slots):
        paper.paste(img,(left,upper));baseline=upper+img.height+px(7)
        draw.text((left,baseline),shot.title,fill=(38,52,51),font=typeface(px(24),True))
        draw.text((left,baseline+px(31)),shot.caption,fill=(76,77,68),font=typeface(px(14)))
    dest.parent.mkdir(parents=True,exist_ok=True);paper.save(dest,'WEBP',quality=89,method=6)
    print('Cycles lighting study',dest,paper.size,flush=True)


def main():
    par=argparse.ArgumentParser(description=__doc__);par.add_argument('--preview-dir',type=Path)
    par.add_argument('--denoiser',default=shutil.which('oidnDenoise'))
    args=par.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(STUDIO/'mandala-rift.blend'))
    scene=bpy.context.scene;bpy.context.view_layer.update();configure(scene,bool(args.preview_dir))
    if args.preview_dir:
        directory=args.preview_dir;directory.mkdir(parents=True,exist_ok=True)
        for shot in SHOTS:photograph(scene,shot,directory,args.denoiser)
        assemble(directory,directory/'proof.webp')
    else:
        with TemporaryDirectory(prefix='mandala-lighting-') as tmp:
            directory=Path(tmp)
            for shot in SHOTS:photograph(scene,shot,directory,args.denoiser)
            assemble(directory,STUDIO/'lighting'/'study.webp')


if __name__=='__main__':main()
