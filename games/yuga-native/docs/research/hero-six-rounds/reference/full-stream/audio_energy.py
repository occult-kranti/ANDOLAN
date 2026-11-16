#!/usr/bin/env python3
"""Energy index of full decoded audio: not a speech/SFX recognition claim."""
import wave, numpy as np, json, hashlib
from pathlib import Path
base=Path(__file__).resolve().parent
for name in ['gameplay','ults']:
    path=base/name/'speech-16k-mono.wav'
    with wave.open(str(path),'rb') as wav:
        assert (wav.getnchannels(),wav.getsampwidth(),wav.getframerate())==(1,2,16000)
        samples=np.frombuffer(wav.readframes(wav.getnframes()),dtype='<i2').astype(np.float32)/32768
    levels=[]
    for i in range(0,len(samples),16000):
        q=samples[i:i+16000]; rms=float(np.sqrt(np.mean(q*q)))
        levels.append({'start_seconds':i/16000,'rms_dbfs':round(float(20*np.log10(max(rms,1e-10))),3),'peak':float(abs(q).max())})
    with path.open('rb') as f: digest=hashlib.file_digest(f,'sha256').hexdigest()
    result={'input_sha256':digest,'seconds':len(samples)/16000,'one_second_windows':len(levels),'below_minus_60_dbfs_windows':int(sum(x['rms_dbfs']<-60 for x in levels)),'below_minus_40_dbfs_windows':int(sum(x['rms_dbfs']<-40 for x in levels)),'median_rms_dbfs':float(np.median([x['rms_dbfs'] for x in levels])),'windows':levels,'limits':'Signal energy only; not listening, speech recognition or SFX classification.'}
    (base/name/'audio-energy.json').write_text(json.dumps(result,indent=2)+'\n')
    print(name,{k:v for k,v in result.items() if k not in ['windows','input_sha256','limits']})
