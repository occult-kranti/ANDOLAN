#!/usr/bin/env python3
"""Original Rama action PCM: deterministic oscillators/noise, no external samples."""
import argparse
import hashlib
import io
import json
import math
from pathlib import Path
import random
import struct
import wave

ROOT = Path(__file__).resolve().parent
RATE = 48000
SEED = 202610170913
PEAK_CAP = .16
# These are original sound-design choices, not transcriptions or cultural claims.
SPECS = {
    "draw_kodanda": (.18, .105, "Short bow-fibre tension; low sympathetic-string color."),
    "draw_piercing_dawn": (.65, .13, "Rising sustained fibre tension, airy upper partials."),
    "draw_measured_step": (.10, .09, "A restrained friction pickup, no implied invulnerability."),
    "draw_guardian_circle": (.55, .12, "Soft paired modal tones open into a protective resonance."),
    "draw_dawn_volley": (.95, .135, "Long rising bow resonance with restrained electronic modulation."),
    "release_kodanda": (.34, .14, "Dry string snap followed by a short woody resonance."),
    "release_piercing_dawn": (.60, .15, "Sharper string attack and bright descending solar resonance."),
    "release_measured_step": (.32, .12, "Close airy sweep with a small wooden foot accent."),
    "release_guardian_circle": (.72, .14, "Rounded bell-like dyads with a soft plucked center."),
    "release_dawn_volley": (.30, .14, "One compact pulse; the existing authority receipts select three pulses."),
    "contact": (.16, .11, "Short woody target contact, intentionally distinct from confirmation."),
    "blocked": (.20, .10, "Duller cover contact without a success tone."),
    "confirm": (.10, .10, "Very short quiet two-part confirmation for an accepted damage receipt."),
    "threat": (.20, .13, "Local low-mid impact indicating accepted damage; no vocal content."),
    "cancel": (.12, .075, "Damped tension release, no successful attack accent."),
}

def env(t, duration, attack=.006, release=.035):
    return min(1., t / attack) * min(1., max(0., duration-t) / release)

def modal(t, frequency, decay=9., brightness=.25):
    return (math.sin(2*math.pi*frequency*t) + brightness*math.sin(2*math.pi*frequency*2.003*t)*math.exp(-6*t) + .09*math.sin(2*math.pi*frequency*3.013*t)*math.exp(-12*t)) * math.exp(-decay*t)

def synth(name, index):
    duration, peak, description = SPECS[name]
    count = round(RATE*duration)
    rng = random.Random(SEED+index)
    low = high = 0.
    values = []
    for n in range(count):
        t=n/RATE; u=t/duration
        raw=rng.uniform(-1., 1.)
        low += .18*(raw-low)
        high += .018*(low-high)
        fibre=low-high
        if name.startswith("draw_"):
            f={"draw_kodanda":196.,"draw_piercing_dawn":293.66,"draw_measured_step":147.,"draw_guardian_circle":220.,"draw_dawn_volley":261.63}[name]
            phase=2*math.pi*(f*t+70*t*t/(2*duration))
            value=(.30*fibre+.22*math.sin(phase)+.06*math.sin(2.007*phase))*(.18+.82*u)
            if name=="draw_guardian_circle":value+=.1*math.sin(2*math.pi*329.63*t)*math.sin(math.pi*u)
            if name=="draw_dawn_volley":value*=.9+.1*math.sin(2*math.pi*9*t)
        elif name=="release_kodanda":
            value=.85*fibre*math.exp(-75*t)+.35*modal(t,196.,13.)+.12*modal(t,587.33,24.)
        elif name=="release_piercing_dawn":
            value=.75*fibre*math.exp(-65*t)+.42*modal(t,293.66,7.)+.19*modal(t,440.,8.)
            value+=.09*math.sin(2*math.pi*(880*t-300*t*t))*math.exp(-10*t)
        elif name=="release_measured_step":
            value=.75*fibre*math.exp(-11*t)*math.sin(math.pi*u)+.25*modal(t,146.83,23.)
        elif name=="release_guardian_circle":
            value=.38*modal(t,220.,4.,.17)+.28*modal(t,329.63,5.,.15)+.1*modal(t,659.25,10.)
        elif name=="release_dawn_volley":
            value=.8*fibre*math.exp(-65*t)+.42*modal(t,261.63,14.)+.18*modal(t,392.,18.)
        elif name=="contact":value=.65*fibre*math.exp(-60*t)+.3*modal(t,174.61,27.)
        elif name=="blocked":value=.5*fibre*math.exp(-38*t)+.4*modal(t,130.81,30.,.5)
        elif name=="confirm":value=.45*modal(t,659.25,38.,.08)+.22*modal(t,987.77,42.,.04)
        elif name=="threat":value=.5*fibre*math.exp(-42*t)+.5*modal(t,98.,21.,.38)+.12*modal(t,196.,22.)
        elif name=="cancel":value=.4*fibre*math.exp(-38*t)+.24*modal(t,164.81,32.)
        else:raise ValueError(name)
        values.append(value*env(t,duration,.003 if not name.startswith("draw_") else .008,.028))
    magnitude=max(abs(x) for x in values)
    pcm=[round(x/magnitude*peak*32767) for x in values]
    pcm[0]=pcm[-1]=0
    output=io.BytesIO()
    with wave.open(output,'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(RATE)
        w.writeframes(struct.pack('<'+'h'*len(pcm),*pcm))
    stats={"bytes":len(output.getvalue()),"sha256":hashlib.sha256(output.getvalue()).hexdigest(),"frames":count,"duration_seconds":duration,"sample_rate":RATE,"channels":1,"bits_per_sample":16,"loop":False,"peak_linear":max(abs(x) for x in pcm)/32768.,"rms_linear":math.sqrt(sum(x*x for x in pcm)/count)/32768.,"mean_linear":sum(pcm)/count/32768.,"endpoints":[pcm[0],pcm[-1]],"seed":SEED+index,"description":description}
    return output.getvalue(), stats

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    parser.add_argument('--report',type=Path)
    args=parser.parse_args()
    files={};failures=[]
    for index,name in enumerate(SPECS):
        data,stats=synth(name,index);files[name+'.wav']=stats
        path=ROOT/'runtime'/(name+'.wav')
        if args.check:
            if not path.is_file() or path.read_bytes()!=data:failures.append(name+'.wav')
        else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    manifest={"schema":1,"origin":"Original deterministic oscillator and seeded filtered-noise synthesis; no external samples, voices, recordings or transcribed melodies.","scope":"One Rama action/counter sound set. Plucked/modal/bell colors are original abstractions, not historical instrument/raga/authenticity or psychological-effect claims.","generator_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),"rate":RATE,"voices_max":4,"spatial_voices":3,"local_feedback_voices":1,"gain_max_db":-18.,"peak_cap_linear":PEAK_CAP,"per_module_worst_case_amplitude":4*PEAK_CAP*10**(-18/20),"per_module_headroom_db":-20*math.log10(4*PEAK_CAP*10**(-18/20)),"mix_assumptions":"Only this four-voice module; slider<=1, no amplified buses/effects, positional maximum<=-18dB. Other subsystems are not included; integration must remove previous Rama playback and separately measure the whole mix.","pitch_range":[.988,1.012],"files":files}
    encoded=json.dumps(manifest,indent=2)+'\n'
    path=ROOT/'runtime/manifest.json'
    if args.check:
        if not path.is_file() or path.read_text()!=encoded:failures.append('manifest.json')
    else:path.write_text(encoded)
    passed=not failures and len({s['sha256'] for s in files.values()})==15 and all(s['peak_linear']<=PEAK_CAP and abs(s['mean_linear'])<.005 and s['endpoints']==[0,0] for s in files.values())
    report={"passed":passed,"mode":"check" if args.check else "generated","files":len(files),"failures":failures,"wav_bytes":sum(s['bytes'] for s in files.values()),"manifest_sha256":hashlib.sha256(encoded.encode()).hexdigest(),"module_amplitude_upper_bound":manifest['per_module_worst_case_amplitude'],"module_headroom_db":manifest['per_module_headroom_db'],"scope":"PCM reproducibility, finite duration/format/endpoints/peak/DC checks. Actual listening and dense-mix intelligibility UNRUN."}
    if args.report:args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report));return 0 if passed else 1
if __name__=='__main__':raise SystemExit(main())
