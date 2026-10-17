#!/usr/bin/env python3
"""Original deterministic traversal audio; no recordings or borrowed melodies.

NumPy synthesis only. --check regenerates bytes in memory and verifies committed
assets, manifest, PCM headroom, discontinuity and cue distinction. Runtime mix
bound is conservative: six simultaneous full-amplitude cues plus music.
"""
import argparse
import hashlib
import io
import json
import math
from pathlib import Path
import wave

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "assets/audio/traversal"
MANIFEST = ROOT / "art/audio/traversal-audio-manifest.json"
NOTICE = ROOT / "NOTICE/TRAVERSAL-AUDIO-PROVENANCE.json"
RATE = 24000
SEED = 2026101707
TEMPO = 96
BEATS = 32
DURATION = BEATS * 60 / TEMPO
CUES = {"grapple_lock": .24, "grapple_release": .28, "flight_start": .48,
        "flight_exhaust": .40, "flight_recharge": .56, "minion_hit": .16, "coin": .36}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def hz(semitone):
    return 440.0 * 2 ** ((50 + semitone - 69) / 12)  # D3 reference, 12-TET


def envelope(n, attack=.004, release=.04):
    result = np.ones(n)
    a, r = min(round(attack * RATE), n // 2), min(round(release * RATE), n // 2)
    result[:a] = np.sin(np.linspace(0, math.pi / 2, a)) ** 2
    result[-r:] = np.sin(np.linspace(math.pi / 2, 0, r)) ** 2
    result[0] = result[-1] = 0
    return result


def pluck(frequency, duration, strength=.8):
    t = np.arange(round(duration * RATE)) / RATE
    result = np.zeros_like(t)
    # Harmonic decay makes the bright attack recede faster than the fundamental.
    for harmonic in range(1, 8):
        result += (np.sin(math.tau * frequency * harmonic * t + .06 * harmonic)
                   * np.exp(-t * (2.2 + .65 * harmonic)) / harmonic ** 1.35)
    return result * envelope(len(t), .003, .07) * strength


def membrane(frequency, duration, rng, bright=False):
    t = np.arange(round(duration * RATE)) / RATE
    phase = math.tau * (frequency * t + 1.7 * (1 - np.exp(-35 * t)))
    result = np.sin(phase) * np.exp(-16 * t)
    result += .30 * np.sin(phase * 2.13) * np.exp(-26 * t)
    if bright:
        noise = rng.standard_normal(len(t))
        noise = noise - np.roll(noise, 1)
        result += .12 * noise * np.exp(-60 * t)
    return result * envelope(len(t), .002, .035)


def stereo(mono, pan=0):
    return np.stack((mono * math.sqrt((1-pan)/2), mono * math.sqrt((1+pan)/2)), axis=1)


def add_circular(target, source, start):
    """Wrap event tails so the loop is a periodic mix, without an end fade/gap."""
    indices = (np.arange(len(source)) + round(start * RATE)) % len(target)
    np.add.at(target, indices, source)


def music():
    n = round(DURATION * RATE)
    t = np.arange(n) / RATE
    rng = np.random.default_rng(SEED)
    result = np.zeros((n, 2))
    # Quantize drone oscillators to integer cycles per complete loop (<0.4 cents
    # pitch deviation). Notes are envelopes with circularly wrapped tails.
    for semitone, amplitude, pan in [(0,.12,-.15), (7,.065,.18), (-12,.08,0)]:
        f = round(hz(semitone) * DURATION) / DURATION
        drone = amplitude * np.sin(math.tau*f*t + .11)
        drone += amplitude*.16*np.sin(math.tau*f*2*t+.3)
        drone *= .88+.12*np.cos(math.tau*t/DURATION)
        result += stereo(drone,pan)
    beat = 60 / TEMPO
    # Two original sparse pentatonic phrases. This is not a named raga or a
    # transcription: raga identity cannot be reduced to pitch membership.
    phrase = [(0,0),(2.5,7),(5,4),(7.5,2),(10,9),(12.5,7),(14,4),
              (16,0),(18.5,4),(21,7),(23.5,12),(26,9),(28.5,7),(30,2)]
    for i,(at,note) in enumerate(phrase):
        add_circular(result,stereo(pluck(hz(note+12),2.2,.17),-.32 if i%2 else .32),at*beat)
    for b in range(BEATS):
        # A sixteen-beat grouping, four groups of four, repeated with accents.
        accent = .12 if b%16==0 else (.085 if b%4==0 else .040)
        drum = membrane(102 if b%4==0 else 176,.36,rng,bright=b%2==1)
        add_circular(result,stereo(drum*accent, -.2 if b%2 else .2),b*beat)
        # Restrained pulse and electronic bass below the plucked-register melody.
        kick=membrane(48,.24,rng)*(.065 if b%2==0 else .025)
        add_circular(result,stereo(kick),b*beat)
        if b%4 in (1,3):
            hat_t=np.arange(round(.055*RATE))/RATE
            hat=rng.standard_normal(len(hat_t))
            hat=(hat-np.roll(hat,1))*.008*np.exp(-70*hat_t)*envelope(len(hat_t),.002,.015)
            add_circular(result,stereo(hat,.25), (b+.5)*beat)
    result *= .16 / np.max(np.abs(result))
    return result


def cue(kind, duration, index):
    t=np.arange(round(duration*RATE))/RATE
    u=t/duration
    rng=np.random.default_rng(SEED+index+1)
    noise=rng.standard_normal(len(t))
    noise=(noise+np.roll(noise,1)+np.roll(noise,2))/3
    if kind=="grapple_lock":
        result=(np.sin(math.tau*(630*t+600*t*t))+.35*np.sin(math.tau*1570*t))*np.exp(-12*t)
    elif kind=="grapple_release":
        result=.55*noise*np.exp(-13*t)+.35*np.sin(math.tau*(390*t-450*t*t))*np.exp(-18*t)
    elif kind=="flight_start":
        result=(.65*noise+.45*np.sin(math.tau*(100*t+160*t*t)))*np.sin(math.pi*u)**1.4
    elif kind=="flight_exhaust":
        result=np.sin(math.tau*(220*t-180*t*t))*np.exp(-3*t)*(.55+.45*np.cos(math.tau*7*t))
    elif kind=="flight_recharge":
        result=np.zeros_like(t)
        for at,f in [(0,440),(.15,660),(.30,880)]:
            a=round(at*RATE); p=pluck(f,duration-at,.5); result[a:a+len(p)]+=p
    elif kind=="minion_hit":
        result=membrane(125,duration,rng,True)+.25*noise*np.exp(-60*t)
    elif kind=="coin":
        result=(np.sin(math.tau*1175*t)+.3*np.sin(math.tau*2350*t))*np.exp(-16*t)
        a=round(.09*RATE); q=t[:-a]
        result[a:]+=.65*np.sin(math.tau*1480*q)*np.exp(-24*q)*envelope(len(q),.002,.025)
    else:
        raise ValueError(kind)
    result*=envelope(len(t), .004, .045)
    return result * (.18/np.max(np.abs(result)))


def encode(samples):
    if not np.isfinite(samples).all() or np.max(np.abs(samples))>=1:
        raise ValueError("Nonfinite or clipped audio")
    pcm=np.rint(samples*32767).astype('<i2')
    output=io.BytesIO()
    with wave.open(output,'wb') as f:
        f.setnchannels(2 if samples.ndim==2 else 1); f.setsampwidth(2)
        f.setframerate(RATE); f.writeframes(pcm.tobytes())
    return output.getvalue(),pcm


def build():
    sources={"lane-procession-loop":music()}
    sources.update({kind:cue(kind,duration,i) for i,(kind,duration) in enumerate(CUES.items())})
    records=[]; encoded={}
    for name,samples in sources.items():
        data,pcm=encode(samples); encoded[name]=data
        seam=float(np.max(np.abs(pcm[0].astype(float)-pcm[-1].astype(float)))/32767)
        difference=np.max(np.abs(np.diff(pcm.astype(float),axis=0)),axis=1) if pcm.ndim==2 else np.abs(np.diff(pcm.astype(float)))
        p99=float(np.quantile(difference,.99)/32767)
        records.append({"asset":f"assets/audio/traversal/{name}.wav","kind":name,"sha256":digest(data),"bytes":len(data),
          "sample_rate":RATE,"channels":2 if samples.ndim==2 else 1,"sample_frames":len(pcm),"duration_seconds":len(pcm)/RATE,
          "peak_linear":round(float(np.max(np.abs(pcm.astype(float)))/32767),12),"rms_linear":round(float(np.sqrt(np.mean((pcm.astype(float)/32767)**2))),12),
          "seam_step_linear":round(seam,12),"within_clip_difference_p99":round(p99,12),"endpoint_zero":bool(np.all(pcm[0]==0) and np.all(pcm[-1]==0))})
    loop=records[0]
    if loop['seam_step_linear']>loop['within_clip_difference_p99']:
        raise ValueError("Loop seam exceeds normal waveform transitions")
    if len({x['sha256'] for x in records})!=len(records):raise ValueError("Cue duplication")
    if not all(x['endpoint_zero'] for x in records[1:]):raise ValueError("Cue endpoint click risk")
    # AudioStreamPlayer3D unit_size 1, max_db -6 prevents positional gain above
    # the chosen cue gain; six players maximum, mono PCM <.181, music <.161.
    mix_bound=6*.181*10**(-6/20)+.161*10**(-20/20)
    if mix_bound>=.60:raise ValueError("Insufficient worst-case headroom")
    return encoded,{"schema":1,"title":"Lantern Procession — original traversal music and cues","license":"CC0-1.0",
      "source":str(Path(__file__).relative_to(ROOT)),"source_sha256":digest(Path(__file__).read_bytes()),
      "seed":SEED,"numpy_version":np.__version__,"sample_rate":RATE,"tempo_bpm":TEMPO,"loop_beats":BEATS,
      "music_math":{"reference":"D3; 440 * 2 ** ((MIDI - 69) / 12)","phrase_semitones":[0,2,4,7,9,12],
        "rhythm":"32 beats: two 16-beat cycles grouped 4+4+4+4; original accents", "loop":"integer-cycle drone and circularly wrapped event tails",
        "scope":"Modal, plucked-string, drone and membrane inspiration; not an authentic raga/tala performance or copied recording"},
      "mix":{"music_gain_db":-20,"cue_gain_db":-6,"max_cue_players":6,"conservative_amplitude_bound":mix_bound,
        "minimum_headroom_db":-20*math.log10(mix_bound),"scope":"This subsystem at volume1, all six cue peaks aligned; other scene buses must be budgeted separately"},
      "assets":records}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');parser.add_argument('--report',type=Path)
    args=parser.parse_args();encoded,manifest=build()
    expected=json.dumps(manifest,indent=2)+'\n'
    if args.check:
        if not MANIFEST.exists() or json.loads(MANIFEST.read_text())!=manifest:raise ValueError('Stale audio manifest; regenerate')
        for name,data in encoded.items():
            if (OUT/(name+'.wav')).read_bytes()!=data:raise ValueError('Changed audio bytes: '+name)
            settings=(OUT/(name+'.wav.import')).read_text()
            for required in ['compress/mode=0','edit/trim=false','edit/normalize=false','force/8_bit=false','force/mono=false','force/max_rate=false']:
                if required not in settings.splitlines():raise ValueError('Unsafe or lossy Godot import setting: '+name+' '+required)
        if json.loads(NOTICE.read_text())!=manifest:raise ValueError('Stale exported provenance notice')
    else:
        OUT.mkdir(parents=True,exist_ok=True);MANIFEST.parent.mkdir(parents=True,exist_ok=True)
        for name,data in encoded.items():(OUT/(name+'.wav')).write_bytes(data)
        MANIFEST.write_text(expected);NOTICE.write_text(expected)
    report={"passed":True,"mode":"check" if args.check else "generate","assets":len(encoded),
            "source_sha256":manifest['source_sha256'],"total_wav_bytes":sum(len(v) for v in encoded.values()),
            "loop":manifest['assets'][0],"mix":manifest['mix'],"all_cues_zero_endpoints":True,
            "all_assets_distinct_and_deterministic":True,"limitations":"Numerical PCM verification; no human listening or physiological-benefit claim"}
    if args.report:args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
