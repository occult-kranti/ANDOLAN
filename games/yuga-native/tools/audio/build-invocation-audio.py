#!/usr/bin/env python3
"""Original short invocation cues; deterministic stdlib synthesis, no samples."""
import argparse
import hashlib
import io
import json
import math
from pathlib import Path
import struct
import wave

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / 'assets/audio/invocations'
RATE = 48000
# Frequency, partial mix, falloff and modulation are original sound-design choices.
PROFILES = {
 'rama': (392, [1,.28,.08], 6, .012),
 'ravana': (146.83, [1,.55,.31,.15], 4, .032),
 'arjuna': (523.25, [1,.14,.35], 8, .008),
 'duryodhana': (174.61, [1,.46,.07], 11, .025),
 'hanuman': (220, [1,.08,.22,.04], 5, .06),
 'karna': (659.25, [1,.33,.19], 7, .018),
 'bhima': (110, [1,.65,.11], 12, .04),
 'meghnad': (196, [1,.21,.5,.13], 4, .08),
 'sita': (440, [1,.06,.04,.12], 3, .006),
 'draupadi': (349.23, [1,.4,.17,.26], 6, .05),
 'subhadra': (587.33, [1,.11,.3], 5, .01),
 'hidimbi': (164.81, [1,.2,.4,.06], 9, .045),
 'chitrangada': (466.16, [1,.34,.1], 6, .022),
 'ulupi': (293.66, [1,.09,.21,.1], 3, .07),
}

def synth(kind, profile=None):
    duration = .24 if kind == 'windup' else .16 if kind == 'cancel' else .48
    count = round(RATE * duration)
    values = []
    for n in range(count):
        t=n/RATE; u=n/(count-1)
        attack=min(1., t/.012)
        tail=min(1., (duration-t)/.025)
        if kind == 'release':
            freq, partials, decay, vibrato = profile
            phase=2*math.pi*freq*t + vibrato*math.sin(2*math.pi*7*t)
            tone=sum(weight*math.sin((i+1)*phase + i*.19*math.sin(2*math.pi*3*t)) for i,weight in enumerate(partials))/sum(partials)
            value=.23*attack*tail*math.exp(-decay*t)*tone
        else:
            freq=240 if kind=='windup' else 380
            chirp=180 if kind=='windup' else -200
            phase=2*math.pi*(freq*t+chirp*t*t/(2*duration))
            value=.16*attack*tail*(1-u)*(.8*math.sin(phase)+.2*math.sin(2.01*phase))
        values.append(max(-32767,min(32767,round(value*32767))))
    stream=io.BytesIO()
    with wave.open(stream,'wb') as wav:
        wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(RATE)
        wav.writeframes(struct.pack('<'+'h'*len(values),*values))
    return stream.getvalue(), {'duration_seconds':count/RATE,'frames':count,'peak':max(abs(x) for x in values)/32768,'rms':math.sqrt(sum(x*x for x in values)/count)/32768,'sample_rate':RATE,'channels':1,'bits_per_sample':16}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');parser.add_argument('--report',type=Path);args=parser.parse_args()
    cues={'windup.wav':synth('windup'),'cancel.wav':synth('cancel')}
    cues.update({hero+'-release.wav':synth('release',spec) for hero,spec in PROFILES.items()})
    manifest={'schema':1,'origin':'Original deterministic mathematical synthesis; no external samples, melodies or voice recordings.','scope':'Short invocation UI/combat cues; no music, mythology authenticity or auditory quality claim.','generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'voices_max':3,'files':{}}
    failures=[]
    for name,(data,stats) in cues.items():
        manifest['files'][name]=dict(stats,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data))
        if args.check:
            if not (OUTPUT/name).is_file() or (OUTPUT/name).read_bytes()!=data: failures.append(name)
        else:
            OUTPUT.mkdir(parents=True,exist_ok=True);(OUTPUT/name).write_bytes(data)
    manifest['heroes']={hero:{'release_file':hero+'-release.wav','fundamental_hz':p[0],'partials':p[1],'decay_per_second':p[2],'phase_modulation':p[3]} for hero,p in PROFILES.items()}
    encoded=json.dumps(manifest,indent=2)+'\n'
    if args.check:
        if not (OUTPUT/'manifest.json').is_file() or (OUTPUT/'manifest.json').read_text()!=encoded: failures.append('manifest.json')
    else: (OUTPUT/'manifest.json').write_text(encoded)
    # All three allowed simultaneous voices remain below full scale even at maximum volume.
    budget=max(v['peak'] for v in manifest['files'].values())*3
    passed=not failures and budget<1 and len({v['sha256'] for v in manifest['files'].values()})==16
    report={'passed':passed,'files':16,'failures':failures,'sum_of_three_maximum_peaks':budget,'mode':'check' if args.check else 'generated','manifest_sha256':hashlib.sha256(encoded.encode()).hexdigest(),'scope':'PCM structural/reproducibility/peak checks. No listening review.'}
    if args.report: args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report));return 0 if passed else 1

if __name__=='__main__': raise SystemExit(main())
