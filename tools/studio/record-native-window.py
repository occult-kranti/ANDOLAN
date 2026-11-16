#!/usr/bin/env python3
"""Record an owned X11 window through timestamped, unmodified screen PNGs.

This is wall-clock screen sampling, not an engine frame or GPU benchmark.
"""
import argparse, hashlib, json, subprocess, time
from pathlib import Path
from PIL import ImageGrab
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--display',required=True)
p.add_argument('--output',type=Path,required=True)
p.add_argument('--seconds',type=float,default=30)
p.add_argument('--fps',type=int,default=10)
a=p.parse_args()
if not a.output.is_absolute() or a.output.exists() or not 1<=a.fps<=15 or not 1<=a.seconds<=120:p.error('Fresh absolute output; 1–15 samples/s and 1–120 seconds required')
a.output.mkdir(parents=True)
start=time.monotonic();wall=time.time();frames=[]
while time.monotonic()-start<a.seconds:
 now=time.monotonic(); name=f'frame-{len(frames):05d}.png'; im=ImageGrab.grab(xdisplay=a.display);im.save(a.output/name,compress_level=1)
 frames.append({'file':name,'time_s':now-start,'unix_s':time.time(),'sha256':hashlib.sha256((a.output/name).read_bytes()).hexdigest(),'width':im.width,'height':im.height})
 deadline=start+len(frames)/a.fps
 time.sleep(max(0,deadline-time.monotonic()))
duration=time.monotonic()-start
lines=[]
for i,row in enumerate(frames):
 lines += ["file '"+row['file']+"'",'duration '+str((frames[i+1]['time_s'] if i+1<len(frames) else duration)-row['time_s'])]
lines += ["file '"+frames[-1]['file']+"'"]
(a.output/'frames.txt').write_text('\n'.join(lines)+'\n')
command=['ffmpeg','-hide_banner','-loglevel','error','-nostdin','-n','-f','concat','-safe','0','-i',str(a.output/'frames.txt'),'-t',str(duration),'-fps_mode','vfr','-an','-c:v','libx264','-threads','2','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(a.output/'window-input.mp4')]
subprocess.run(command,check=True,timeout=120)
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(a.output/'window-input.mp4')]))
report={'complete':True,'display':a.display,'wall_start_unix_s':wall,'duration_s':duration,'requested_samples_per_s':a.fps,'samples':frames,'encode_command':command,'probe':probe,'video_sha256':hashlib.sha256((a.output/'window-input.mp4').read_bytes()).hexdigest(),'scope':'Unmodified X11 screen samples of ordinary OS input, with actual wall-clock intervals. Silent VFR screen video; no state injection, engine-frame-count or physical-GPU claim.'}
(a.output/'recording.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'complete':True,'frames':len(frames),'seconds':duration,'output':str(a.output)}))
