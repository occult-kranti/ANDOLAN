"""Render the saved Sena Blender animation as bounded CPU preview frames and film."""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import bpy
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--scene",type=Path,default=HERE / "vanara-sena-study.blend")
parser.add_argument("--output",type=Path,default=HERE / "preview")
parser.add_argument("--samples",type=int,default=3)
parser.add_argument("--width",type=int,default=480)
parser.add_argument("--step",type=int,default=3)
args = parser.parse_args(sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else [])
if not 1 <= args.samples <= 64 or not 160 <= args.width <= 1920 or args.width % 2 or args.step not in (1,2,3,5,6):
    raise ValueError("Invalid bounded render settings")
args.output.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(args.scene.resolve()),load_ui=False)
scene = bpy.context.scene
scene.render.engine="CYCLES"
scene.cycles.device="CPU"
scene.cycles.samples=args.samples
scene.render.threads_mode="FIXED"
scene.render.threads=2
scene.render.resolution_x=args.width
scene.render.resolution_y=2*round(args.width*9/32)
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.render.image_settings.color_mode="RGB"
scene.render.use_persistent_data=True
frames=list(range(scene.frame_start,scene.frame_end+1,args.step))
files=[]
for index,frame in enumerate(frames):
    scene.frame_set(frame)
    filename=f"frame-{index+1:03}.png"
    path=args.output / filename
    scene.render.filepath=str(path.resolve())
    bpy.ops.render.render(write_still=True)
    with path.open("rb") as stream:
        sha=hashlib.file_digest(stream,"sha256").hexdigest()
    files.append({"file":filename,"scene_frame":frame,"seconds":round((frame-1)/scene.render.fps,4),"sha256":sha})

# Keep the raw output; temporal denoising is applied only to the MP4 presentation.
fps=scene.render.fps / args.step
movie=args.output / "vanara-sena-preview.mp4"
subprocess.run(["ffmpeg","-v","error","-y","-threads","2","-filter_threads","2",
                "-framerate",str(fps),"-i",str(args.output / "frame-%03d.png"),
                "-vf","hqdn3d=2:1:3:2","-c:v","libx264","-crf","19","-pix_fmt","yuv420p",
                "-movflags","+faststart",str(movie)],check=True)
indices=[0,min(len(files)-1,round(12/args.step)),min(len(files)-1,round(18/args.step)),
         min(len(files)-1,round(30/args.step)),min(len(files)-1,round(48/args.step)),
         min(len(files)-1,round(78/args.step))]
canvas=Image.new("RGB",(args.width*3,(scene.render.resolution_y+26)*2),(12,20,22))
draw=ImageDraw.Draw(canvas)
for cell,index in enumerate(indices):
    source=files[index]
    with Image.open(args.output/source["file"]) as im:
        canvas.paste(im.convert("RGB"),((cell%3)*args.width,(cell//3)*(scene.render.resolution_y+26)))
    draw.text(((cell%3)*args.width+8,(cell//3)*(scene.render.resolution_y+26)+scene.render.resolution_y+6),
              f"frame {source['scene_frame']}   |   {source['seconds']:.2f}s",fill=(244,229,201))
sheet=args.output/"contact-sheet.png"
canvas.save(sheet)
with args.scene.open("rb") as stream: scene_sha=hashlib.file_digest(stream,"sha256").hexdigest()
with movie.open("rb") as stream: movie_sha=hashlib.file_digest(stream,"sha256").hexdigest()
receipt={"scene_sha256":scene_sha,"renderer":"Blender Cycles CPU","blender":bpy.app.version_string,
         "samples_per_frame":args.samples,"resolution":[scene.render.resolution_x,scene.render.resolution_y],
         "sampling":"every %d scene frames"%args.step,"video_fps":fps,"frames":files,
         "movie":"vanara-sena-preview.mp4","movie_sha256":movie_sha,
         "postprocess":"ffmpeg hqdn3d on MP4 only; PNG frames are unfiltered",
         "limits":"Low-sample offline study with no audio; not a gameplay capture, human review or GPU benchmark."}
(args.output/"render-receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
print(json.dumps({"result":"pass","frames":len(files),"fps":fps,"movie_sha256":movie_sha},indent=2))
