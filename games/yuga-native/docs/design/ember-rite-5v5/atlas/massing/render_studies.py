"""Build both review contact sheets from fresh GLB imports. Run with python3."""
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
ROWS = ("ayodhya", "kurukshetra", "lanka", "mandala")
WIDTH, HEIGHT = 740, 380


def render_objects(folder):
    import bpy
    from mathutils import Vector

    for key in ROWS:
        plan = json.loads((ROOT.parent / "maps" / f"{key}.json").read_text())
        for group in ("floor", "architecture"):
            name = key if group == "floor" else key+"-architecture"
            bpy.ops.wm.read_factory_settings(use_empty=True)
            bpy.ops.import_scene.gltf(filepath=str(ROOT / (name+".glb")))
            scene = bpy.context.scene
            points = [obj.matrix_world @ vertex.co for obj in scene.objects if obj.type == 'MESH'
                      for vertex in obj.data.vertices]
            bounds = [Vector([op(p[k] for p in points) for k in range(3)]) for op in (min,max)]
            target = (bounds[0]+bounds[1])*.5
            direction = Vector((.69,-.91,1.54))
            if group == "architecture":
                bearing = math.radians(plan["architecture"]["axis_deg"])
                forward = Vector((math.sin(bearing),math.cos(bearing),0))
                right = Vector((forward.y,-forward.x,0))
                angle = 1.23 if plan["architecture"]["form"]=="stepwell" else .70
                direction = .73*right-.97*forward+Vector((0,0,angle))
            camera_data = bpy.data.cameras.new("Study")
            camera = bpy.data.objects.new("Study",camera_data)
            scene.collection.objects.link(camera)
            camera.rotation_euler = (-direction).to_track_quat('-Z','Y').to_euler()
            orientation = camera.rotation_euler.to_matrix()
            view = [orientation.inverted() @ (p-target) for p in points]
            x0,x1 = min(p.x for p in view),max(p.x for p in view)
            y0,y1 = min(p.y for p in view),max(p.y for p in view)
            target += orientation @ Vector(((x0+x1)/2,(y0+y1)/2,0))
            camera.location = target + direction.normalized()*(bounds[1]-bounds[0]).length*2
            camera_data.type = 'ORTHO'
            camera_data.ortho_scale = max(x1-x0,(y1-y0)*WIDTH/HEIGHT)*1.10
            camera_data.clip_end = 1500
            scene.camera = camera
            scene.render.engine = 'BLENDER_WORKBENCH'
            scene.render.resolution_x,scene.render.resolution_y = WIDTH,HEIGHT
            scene.render.resolution_percentage = 100
            scene.view_settings.view_transform = 'Standard'
            shade = scene.display.shading
            shade.light,shade.color_type = 'STUDIO','MATERIAL'
            shade.show_shadows,shade.show_cavity = True,True
            shade.cavity_type = 'BOTH'
            shade.curvature_valley_factor = 1.05
            shade.curvature_ridge_factor = .5
            shade.show_specular_highlight = False
            shade.background_type = 'WORLD'
            scene.world = bpy.data.worlds.new("Backdrop")
            scene.world.color = (.65,.64,.57)
            scene.render.filepath = str(folder / (name+".png"))
            bpy.ops.render.render(write_still=True)


def contact_sheet(folder, group):
    from PIL import Image, ImageDraw, ImageFont

    canvas = Image.new("RGB",(WIDTH*2+6,2*(HEIGHT+69)+4),(247,244,235))
    draw = ImageDraw.Draw(canvas)
    typography = []
    for font,size in (("DejaVuSerif.ttf",23),("DejaVuSansMono.ttf",13)):
        try:
            typography.append(ImageFont.truetype(font,size))
        except OSError:
            typography.append(ImageFont.load_default())
    for i,key in enumerate(ROWS):
        plan = json.loads((ROOT.parent / "maps" / f"{key}.json").read_text())
        a = plan["architecture"]
        study = group == "architecture"
        name = key+"-architecture" if study else key
        x,y = (i%2)*(WIDTH+6),(i//2)*(HEIGHT+73)
        with Image.open(folder / (name+".png")) as capture:
            canvas.paste(capture.convert("RGB"),(x,y))
        title = a["name"] if study else plan["title"]
        if study:
            w,d = a["footprint"]
            info = f"{plan['title']}  /  {w:g} × {d:g} m  /  {a['opening']:g} m clear"
        else:
            info = f"{len(plan['nodes'])} rooms  /  {len(plan['links'])} connections  /  {len(plan['cover'])} cover pieces"
        draw.text((x+17,y+HEIGHT+5),title,font=typography[0],fill=(32,60,64))
        draw.text((x+18,y+HEIGHT+38),info,font=typography[1],fill=(74,91,86))
    output = "architecture-overview.jpg" if group == "architecture" else "overview.jpg"
    canvas.save(ROOT / output,quality=92,subsampling=0,optimize=True)


if __name__ == "__main__":
    if "--" in sys.argv:
        render_objects(Path(sys.argv[sys.argv.index("--")+1]))
    else:
        with tempfile.TemporaryDirectory() as destination:
            folder = Path(destination)
            subprocess.run(["blender","-b","--factory-startup","-t","1","--python-exit-code","1",
                            "--python",str(Path(__file__).resolve()),"--",destination],check=True)
            for group in ("floor","architecture"):
                contact_sheet(folder,group)
