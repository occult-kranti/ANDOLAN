#!/usr/bin/env python3
"""Deterministic original synth cues; no external recordings or model weights."""
import hashlib
import json
import math
from pathlib import Path
import random
import struct
import wave

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / "games/yuga-native/assets/tactical/audio"
RATE = 48000
CUES = {"pistol":.30,"carbine":.24,"reload":.75,"step":.12,"buy":.24,"hit":.10,"veil":.85,"dash":.35,"ward":.65,"ultimate":1.0,"solar":.45,"objective":.75,"beep":.12}

def synth(cue, duration):
    rng = random.Random("yuga-tactical-v1:"+cue)
    previous = 0.0
    result = []
    for index in range(int(duration * RATE)):
        t = index / RATE
        p = t / duration
        noise = rng.uniform(-1, 1)
        previous = previous * .75 + noise * .25
        if cue in ("pistol", "carbine", "solar"):
            pitch = 92 if cue == "pistol" else (125 if cue == "carbine" else 185)
            attack = min(1, t/.001)
            value = attack * (.62*noise*math.exp(-t*95) + .55*math.sin(2*math.pi*pitch*t)*math.exp(-t*18) + .24*math.sin(2*math.pi*(1800*t-1100*t*t))*math.exp(-t*30))
        elif cue == "step":
            value = .55*previous*math.exp(-t*40) + .12*math.sin(t*2*math.pi*110)*math.exp(-t*60)
        elif cue == "reload":
            value = sum(.32*noise*math.exp(-(t-at)*70) for at in (.03,.28,.58) if t>=at)
        elif cue in ("buy","hit","beep","objective"):
            base = {"buy":660,"hit":1450,"beep":880,"objective":440}[cue]
            value = .3*(math.sin(t*2*math.pi*base)+.32*math.sin(t*2*math.pi*base*1.5))*math.sin(math.pi*p)**2
        else:
            base = {"veil":180,"dash":320,"ward":220,"ultimate":110}[cue]
            envelope = math.sin(math.pi*p)**1.5
            value = envelope*(.2*previous+.23*math.sin(2*math.pi*(base*t+base*.4*t*t))+.12*math.sin(2*math.pi*base*1.5*t))
        value *= min(1,t/.002,(duration-t)/.008)
        result.append(max(-.95,min(.95,value)))
    return result

def main():
    DEST.mkdir(parents=True,exist_ok=True)
    manifest={"schema":1,"origin":"Original deterministic YUGA synthesis; no external audio samples","sample_rate":RATE,"channels":1,"files":{}}
    for cue,duration in CUES.items():
        values=synth(cue,duration)
        path=DEST/(cue+".wav")
        with wave.open(str(path),"wb") as out:
            out.setparams((1,2,RATE,0,"NONE","not compressed"))
            out.writeframes(struct.pack("<"+"h"*len(values),*(round(x*32767) for x in values)))
        manifest["files"][path.name]={"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"samples":len(values),"duration_s":len(values)/RATE,"peak":max(abs(x) for x in values),"rms":math.sqrt(sum(x*x for x in values)/len(values))}
    (DEST/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print(json.dumps({"cues":len(CUES),"directory":str(DEST),"manifest_sha256":hashlib.sha256((DEST/"manifest.json").read_bytes()).hexdigest()}))

if __name__=="__main__": main()
