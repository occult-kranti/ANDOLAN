#!/usr/bin/env python3
"""Create source-bound, timestamped MP4 study frames without third-party Python packages.
This is reference evidence, never generated gameplay or a full-viewing claim.
"""
import argparse, hashlib, json, subprocess, time
from pathlib import Path

def run(argv):
    result = subprocess.run(argv, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return {'argv': argv, 'returncode': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('video', type=Path)
    p.add_argument('--output', required=True, type=Path)
    p.add_argument('--step', type=float, default=20)
    p.add_argument('--start', type=float, default=0)
    p.add_argument('--duration', type=float)
    a=p.parse_args()
    a.output.mkdir(parents=True, exist_ok=False)
    (a.output/'frames').mkdir()
    receipt={'input': str(a.video.resolve()),'sha256': hashlib.file_digest(a.video.open('rb'),'sha256').hexdigest(), 'sample_step_seconds':a.step,'sample_start_seconds':a.start,'sample_duration_seconds':a.duration,'timestamp_basis':'Original selected source frame PTS, source seek offset restored. Select takes first frame then first frame >= step after prior selected frame.','commands':[],'evidence_scope':'Timestamped sampled stills. No claim of uninterrupted viewing or audio listening.'}
    probe=run(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(a.video)])
    receipt['commands'].append(probe)
    receipt['probe']=json.loads(probe['stdout'])
    cmd=['ffmpeg','-hide_banner','-loglevel','error','-threads','2','-ss',str(a.start)]
    if a.duration is not None: cmd+=['-t',str(a.duration)]
    cmd+=['-i',str(a.video)]
    # Select source frames by original time; do not retime with fps (which hides source PTS).
    vf=f"select='isnan(prev_selected_t)+gte(t-prev_selected_t,{a.step})',setpts=PTS+{a.start}/TB,drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:text='%{{pts\\:hms}}':x=8:y=8:fontsize=20:fontcolor=white:box=1:boxcolor=black@0.8"
    cmd+=['-vf',vf,'-fps_mode','vfr',str(a.output/'frames'/'frame-%04d.png')]
    receipt['commands'].append(run(cmd))
    cmd=['ffmpeg','-hide_banner','-loglevel','error','-threads','2','-framerate','1','-i',str(a.output/'frames'/'frame-%04d.png'),'-vf','scale=320:180,tile=4x4:padding=4:margin=4:color=0x13191d','-q:v','2',str(a.output/'sheet-%02d.jpg')]
    receipt['commands'].append(run(cmd))
    receipt['frame_count']=len(list((a.output/'frames').glob('*.png')))
    receipt['sheets']=[str(f) for f in sorted(a.output.glob('sheet-*.jpg'))]
    receipt['artifacts']=[{'path':str(f.relative_to(a.output)),'bytes':f.stat().st_size,'sha256':hashlib.file_digest(f.open('rb'),'sha256').hexdigest()} for f in sorted(a.output.rglob('*')) if f.is_file()]
    (a.output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({'output':str(a.output),'frames':receipt['frame_count'],'sheets':len(receipt['sheets']),'returncodes':[c['returncode'] for c in receipt['commands']]}))
    if any(c['returncode'] for c in receipt['commands']): raise SystemExit(1)
if __name__=='__main__': main()
