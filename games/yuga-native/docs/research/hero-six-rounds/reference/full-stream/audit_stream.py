#!/usr/bin/env python3
"""Decode every frame, retain full-resolution hashes and low-resolution activity index.
Machine coverage is distinct from human visual review. No game-state inference.
"""
import argparse, csv, hashlib, json, subprocess, time
from fractions import Fraction
from pathlib import Path
import numpy as np

def sha(path):
    with path.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()

def main():
    p=argparse.ArgumentParser(); p.add_argument('video',type=Path); p.add_argument('out',type=Path)
    a=p.parse_args(); a.out.mkdir(parents=True, exist_ok=False); started=time.time()
    probe_cmd=['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(a.video)]
    probe=json.loads(subprocess.check_output(probe_cmd)); stream=next(s for s in probe['streams'] if s['codec_type']=='video')
    cmd=['ffmpeg','-hide_banner','-v','error','-xerror','-threads','2','-filter_threads','1','-i',str(a.video),
         '-map','0:v:0','-c:v','rawvideo','-pix_fmt','yuv420p','-fps_mode','passthrough','-f','framemd5',str(a.out/'full-resolution.framemd5'),
         '-map','0:v:0','-vf','scale=160:90,format=gray','-pix_fmt','gray','-fps_mode','passthrough','-f','rawvideo','pipe:1',
         '-map','0:a:0','-ac','1','-ar','16000','-c:a','pcm_s16le',str(a.out/'speech-16k-mono.wav')]
    rows=[]; prior=None; priorhist=None
    with (a.out/'decode.stderr').open('wb') as err:
        proc=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=err)
        while True:
            raw=proc.stdout.read(160*90)
            if not raw: break
            if len(raw)!=160*90: raise RuntimeError('Partial decoded frame')
            frame=np.frombuffer(raw,dtype=np.uint8).reshape((90,160)).astype(np.int16)
            hist=np.bincount((frame//16).reshape(-1),minlength=16)/(160*90)
            diff=np.abs(frame-prior) if prior is not None else np.zeros_like(frame)
            hist_delta=float(np.abs(hist-priorhist).sum()/2) if priorhist is not None else 0.0
            rows.append([len(rows),float(frame.mean()),float(diff.mean()),float(diff[9:72,16:144].mean()),hist_delta])
            prior=frame; priorhist=hist
        code=proc.wait()
    hashrows=[]; timebase=None
    for line in (a.out/'full-resolution.framemd5').read_text().splitlines():
        if line.startswith('#tb 0:'): timebase=Fraction(line.split(':',1)[1].strip())
        elif line and not line.startswith('#'):
            parts=[p.strip() for p in line.split(',')]; hashrows.append((int(parts[2]),int(parts[3]),parts[-1]))
    expected=int(stream['nb_frames']); count=len(rows)
    with (a.out/'every-frame-activity.csv').open('w',newline='') as f:
        w=csv.writer(f); w.writerow(['frame_index_zero','source_pts_seconds','luma_mean','frame_delta_mean_0_255','central_delta_mean_0_255','histogram_total_variation_0_1','scene_candidate'])
        for row, (pts,duration,digest) in zip(rows,hashrows):
            w.writerow([row[0],f'{float(pts*timebase):.6f}',*[f'{n:.6f}' for n in row[1:]],int(row[2]>=20 and row[4]>=.15)])
    buckets={}
    for row, (pts,duration,digest) in zip(rows,hashrows):
        sec=float(pts*timebase); b=int(sec//5)*5
        item=buckets.setdefault(b,{'start_seconds':b,'end_seconds':b+5,'frames':0,'central_delta_sum':0.,'max_central_delta':0.,'peak_time_seconds':sec,'scene_candidates':[]})
        item['frames']+=1; item['central_delta_sum']+=row[3]
        if row[3]>item['max_central_delta']: item['max_central_delta']=row[3]; item['peak_time_seconds']=sec
        if row[2]>=20 and row[4]>=.15: item['scene_candidates'].append(sec)
    for b in buckets.values(): b['mean_central_delta']=b.pop('central_delta_sum')/b['frames']
    (a.out/'five-second-activity.json').write_text(json.dumps(list(buckets.values()),indent=2)+'\n')
    receipt={'input':str(a.video.resolve()),'input_sha256':sha(a.video),'probe_command':probe_cmd,'probe':probe,'decode_command':cmd,'decode_exit':code,'decoded_frame_count':count,'full_resolution_hash_count':len(hashrows),'metadata_frame_count':expected,'counts_match':count==len(hashrows)==expected,'first_pts_seconds':float(hashrows[0][0]*timebase),'last_pts_seconds':float(hashrows[-1][0]*timebase),'wall_seconds':time.time()-started,'ffmpeg_version':subprocess.check_output(['ffmpeg','-version'],text=True).splitlines()[0],'analysis_resolution':[160,90],'limits':'All frames decoded and hashed, not all frames personally inspected. Delta includes camera motion, animation, effects and edits; scene candidates are heuristic, not semantic gameplay events. Audio extracted only, not listened to or transcribed by this script.'}
    receipt['artifacts']=[{'path':f.name,'bytes':f.stat().st_size,'sha256':sha(f)} for f in sorted(a.out.iterdir()) if f.is_file()]
    (a.out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({k:receipt[k] for k in ['input','decode_exit','decoded_frame_count','full_resolution_hash_count','counts_match','wall_seconds']}),flush=True)
    if code or not receipt['counts_match']: raise SystemExit(1)

if __name__=='__main__': main()
