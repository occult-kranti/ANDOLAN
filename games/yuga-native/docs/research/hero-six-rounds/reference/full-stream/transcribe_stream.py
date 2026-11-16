#!/usr/bin/env python3
"""Local full-input ASR; resulting text is machine evidence, not verified quotation."""
import argparse, dataclasses, hashlib, importlib.metadata, json, subprocess, time, wave
from pathlib import Path
from huggingface_hub import HfApi, snapshot_download
from faster_whisper import WhisperModel
import numpy as np

def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()

def main():
    p=argparse.ArgumentParser(); p.add_argument('audio',type=Path); p.add_argument('out',type=Path); p.add_argument('--model',default='Systran/faster-whisper-small.en'); p.add_argument('--revision'); p.add_argument('--threads',type=int,default=6)
    a=p.parse_args(); a.out.mkdir(parents=True,exist_ok=False); started=time.time()
    info=HfApi().model_info(a.model,revision=a.revision); revision=info.sha
    path=Path(snapshot_download(a.model,revision=revision,cache_dir='/tmp/yuga-hero-asr-models',allow_patterns=['config.json','model.bin','tokenizer.json','vocabulary.*','README.md']))
    receipt={'audio':str(a.audio.resolve()),'audio_sha256':sha(a.audio),'model':a.model,'revision':revision,'model_card_license':(info.card_data or {}).get('license'),'model_artifacts':[{'name':f.name,'sha256':sha(f),'bytes':f.stat().st_size} for f in sorted(path.iterdir()) if f.is_file()], 'versions':{name:importlib.metadata.version(name) for name in ['faster-whisper','ctranslate2','huggingface-hub','numpy','av','onnxruntime']},'configuration':{'device':'cpu','compute_type':'int8','cpu_threads':a.threads,'beam_size':3,'language':'en','vad_filter':True,'condition_on_previous_text':False,'word_timestamps':True},'status':'running','limits':'Machine ASR over full input with VAD; not human listening, verified quotations, or gameplay authority. Speech omissions, invented text and proper-name errors remain possible.'}
    (a.out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    model=WhisperModel(str(path),device='cpu',compute_type='int8',cpu_threads=a.threads,num_workers=1)
    # Input is our verified PCM WAV; avoid PyAV's version-dependent media API.
    with wave.open(str(a.audio),'rb') as wav:
        assert (wav.getnchannels(),wav.getsampwidth(),wav.getframerate())==(1,2,16000)
        samples=np.frombuffer(wav.readframes(wav.getnframes()),dtype='<i2').astype(np.float32)/32768.0
    segments,ti=model.transcribe(samples,language='en',beam_size=3,vad_filter=True,condition_on_previous_text=False,word_timestamps=True)
    count=0; last=0
    with (a.out/'segments.jsonl').open('w') as jf, (a.out/'transcript.txt').open('w') as tf:
        for s in segments:
            row=dataclasses.asdict(s); jf.write(json.dumps(row)+'\n'); jf.flush()
            tf.write(f'[{s.start:.3f} - {s.end:.3f}] {s.text.strip()}\n'); tf.flush()
            count+=1; last=s.end
            if count%25==0: print(json.dumps({'segments':count,'source_seconds':last,'elapsed_seconds':time.time()-started}),flush=True)
    receipt.update(status='completed',segment_count=count,last_segment_end_seconds=last,source_audio_duration=ti.duration,vad_duration=ti.duration_after_vad,language_probability=ti.language_probability,wall_seconds=time.time()-started)
    receipt['artifacts']=[{'name':f.name,'sha256':sha(f),'bytes':f.stat().st_size} for f in sorted(a.out.iterdir()) if f.is_file() and f.name!='receipt.json']
    (a.out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n'); print(json.dumps({'completed':True,'segments':count,'seconds':ti.duration,'wall_seconds':receipt['wall_seconds']}),flush=True)

if __name__=='__main__': main()
