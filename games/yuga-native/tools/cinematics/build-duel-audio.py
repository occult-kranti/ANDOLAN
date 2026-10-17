#!/usr/bin/env python3
"""Synthesize an original, sample-aligned score and cues for Confluence.

Python3 + NumPy + SciPy; no downloaded samples, voices, music, or game audio.
Every run reads the film contract before producing any audio. The native viewer
seeks one baked mix; it must never spawn another cue player during a seek.
"""
import argparse
import array
import hashlib
import json
import math
import sys
import wave
from pathlib import Path

try:
    import numpy as np
    import scipy
    from scipy.signal import butter, sosfilt
except ModuleNotFoundError:
    np = scipy = None

ROOT = Path(__file__).resolve().parents[2]
FILM = ROOT / "assets/cinematics/confluence-duel.json"
OUT = ROOT / "assets/cinematics/audio"
MANIFEST = ROOT / "art/cinematics/audio-manifest.json"
RATE = 48000
SEED = 20261017
KINDS = {"bow_draw", "bow_release", "guard_block", "wave_charge", "wave_release", "evade", "counter_hit", "resolve"}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{label} must be finite numeric seconds")
    return float(value)


def validate_film(film):
    duration = number(film.get("duration_seconds"), "duration_seconds")
    if duration != 24:
        raise ValueError("This original score is authored for the 24 second duel")
    cues = film.get("audio_cues")
    if not isinstance(cues, list) or not cues:
        raise ValueError("audio_cues must be a nonempty list")
    ids = set()
    for cue in cues:
        cue_id = cue.get("id")
        if not isinstance(cue_id, str) or not cue_id.startswith("audio-") or not all(c.isalnum() or c == "-" for c in cue_id) or cue_id in ids:
            raise ValueError("Every audio cue needs a unique filename-safe audio-* id")
        ids.add(cue_id)
        start = number(cue.get("t_seconds"), cue_id + " start")
        length = number(cue.get("duration_seconds"), cue_id + " duration")
        if start < 0 or length < .04 or start + length > duration:
            raise ValueError(f"Cue outside film bounds: {cue_id}")
        if cue.get("kind") not in KINDS or cue.get("actor_id") not in {"rama", "ravana"}:
            raise ValueError(f"Unknown audio kind or actor: {cue_id}")
        if abs(start * RATE - round(start * RATE)) > .000001 or abs(length * RATE - round(length * RATE)) > .000001:
            raise ValueError("Cue time must map exactly to a 48 kHz sample")
    return duration, cues


def fade(n, attack=.006, release=.035):
    envelope = np.ones(n, dtype=np.float64)
    a = min(round(attack * RATE), n // 2)
    r = min(round(release * RATE), n // 2)
    if a:
        envelope[:a] = np.sin(np.linspace(0, math.pi / 2, a)) ** 2
    if r:
        envelope[-r:] = np.sin(np.linspace(math.pi / 2, 0, r)) ** 2
    envelope[0] = envelope[-1] = 0
    return envelope


def colored_noise(n, rng, low=100, high=5000):
    noise = rng.standard_normal(n)
    filtered = sosfilt(butter(2, [low, high], btype="bandpass", fs=RATE, output="sos"), noise)
    return filtered / max(float(np.sqrt(np.mean(filtered ** 2))), .00001)


def stereo(mono, pan=0):
    return np.stack((mono * math.sqrt((1-pan)/2), mono * math.sqrt((1+pan)/2)), axis=1)


def cue_sound(kind, seconds, seed):
    n = round(seconds * RATE)
    t = np.arange(n, dtype=np.float64) / RATE
    u = t / seconds
    rng = np.random.default_rng(seed)
    noise = colored_noise(n, rng)
    if kind == "bow_draw":
        # Friction and intermittent wooden creak, rather than a pitched UI beep.
        creak = np.sin(math.tau*(145*t+24*t*t)) + .3*np.sin(math.tau*403*t)
        texture = colored_noise(n, rng, 250, 2400)
        pulses = (.32+.68*np.sin(math.tau*(3.2*t+2*t*t))**4)
        signal = (.035*creak + .035*texture)*pulses*(.4+.6*u)
    elif kind == "bow_release":
        twang = sum(w*np.sin(math.tau*f*t-5*(1-np.exp(-t*35))) for f,w in [(185,1),(369,.34),(591,.12)])
        signal = .26*twang*np.exp(-t*20) + .10*noise*np.exp(-t*65)
    elif kind == "guard_block":
        signal = sum(w*np.sin(math.tau*f*t)*np.exp(-t*d) for f,w,d in [(387,.22,9),(637,.14,12),(1031,.095,15),(1729,.045,22)])
        signal += .13*noise*np.exp(-t*75)
    elif kind == "wave_charge":
        phase = math.tau*(53*t+30*t*t/seconds)
        texture = colored_noise(n, rng, 150, 1800)
        signal = (.10*np.sin(phase)+.042*np.sin(phase*1.51)+.035*texture)*(u**.85)*(.86+.14*np.sin(math.tau*7*t))
    elif kind == "wave_release":
        phase = math.tau*(140*t-48*t*t/seconds)
        signal = (.20*np.sin(phase)+.14*colored_noise(n,rng,80,3300))*np.exp(-u*3.2)
    elif kind == "evade":
        # Two soft cloth/air swells with no tonal success chime.
        swells = np.exp(-((u-.22)/.15)**2)+.6*np.exp(-((u-.56)/.18)**2)
        signal = .12*colored_noise(n,rng,450,4700)*swells
    elif kind == "counter_hit":
        thud = np.sin(math.tau*(115*t-32*t*t/seconds))*np.exp(-t*14)
        ring = .16*np.sin(math.tau*294*t)*np.exp(-t*11)+.08*np.sin(math.tau*487*t)*np.exp(-t*15)
        signal = .32*thud+ring+.15*noise*np.exp(-t*55)
    elif kind == "resolve":
        # A low, gently resolving harmonic bloom; no borrowed melody.
        signal = sum(w*np.sin(math.tau*f*t+p) for f,w,p in [(146.832,.07,0),(220,.04,.2),(293.665,.025,.4)])
        signal *= np.sin(np.clip(u,0,1)*math.pi)**1.3
    else:
        raise ValueError(kind)
    signal = sosfilt(butter(2, 35, btype="highpass", fs=RATE, output="sos"), signal)
    signal *= fade(n, .002 if kind in {"bow_release","guard_block","counter_hit"} else .018, min(.1,seconds*.17))
    if not np.isfinite(signal).all():
        raise ValueError("Nonfinite synthesis")
    return signal


def score(n, cues):
    t = np.arange(n,dtype=np.float64)/RATE
    rng = np.random.default_rng(SEED)
    base = np.zeros(n,dtype=np.float64)
    # Original fifth-based drone, sparse plucked notes and membrane-like taps.
    # Indian-inspired atmosphere, not a claim to perform a traditional raga.
    for frequency,amount,phase in [(73.416,.018,.1),(146.832,.010,.8),(110,.010,1.4),(220,.004,.3)]:
        base += amount*np.sin(math.tau*frequency*t+.009*np.sin(math.tau*.12*t)+phase)
    base *= .82+.18*np.sin(math.tau*.08*t)
    base += .0018*colored_noise(n,rng,80,1100)
    for start,freq,length in [(1.0,293.665,2.4),(5.2,261.626,2.1),(11.0,220,2.8),(17.5,293.665,3.2),(20.5,440,2.8)]:
        a=round(start*RATE); count=min(round(length*RATE),n-a)
        q=np.arange(count)/RATE
        pluck=(np.sin(math.tau*freq*q)+.3*np.sin(math.tau*freq*2.001*q)+.1*np.sin(math.tau*freq*3*q))*.012*np.exp(-q*2)
        base[a:a+count]+=pluck*fade(count,.008,.2)
    for start,amount in [(1.0,.025),(3.4,.020),(6.4,.030),(10.5,.025),(12.0,.020),(14.0,.025),(18.2,.025)]:
        a=round(start*RATE); count=round(.4*RATE); q=np.arange(count)/RATE
        drum=amount*np.sin(math.tau*(83*q+1.5*(1-np.exp(-q*40))))*np.exp(-q*13)
        base[a:a+count]+=drum*fade(count,.002,.05)
    # Reserve space for semantic cue onsets with smooth pre/post ducking.
    duck=np.ones(n)
    for cue in cues:
        start=cue["t_seconds"]; end=start+cue["duration_seconds"]
        envelope=np.minimum(np.clip((t-(start-.12))/.12,0,1),np.clip(((end+.25)-t)/.25,0,1))
        duck=np.minimum(duck,1-.48*envelope)
    base*=duck*fade(n,.65,1.2)
    wide=stereo(base)
    # Quiet short reflections preserve a stable center for important effects.
    for delay,amount,channel in [(.081,.13,0),(.127,.11,1),(.223,.055,0)]:
        shift=round(delay*RATE)
        wide[shift:,channel]+=base[:-shift]*amount
    wide*=fade(n,.10,.75)[:,None]
    return wide


def pcm16(samples):
    if not np.isfinite(samples).all() or np.max(np.abs(samples))>=1:
        raise ValueError("PCM would clip or contain nonfinite samples")
    return np.rint(samples*32767).astype("<i2")


def save_wav(path, samples):
    encoded=pcm16(samples)
    channels=1 if samples.ndim==1 else samples.shape[1]
    with wave.open(str(path),"wb") as out:
        out.setnchannels(channels); out.setsampwidth(2); out.setframerate(RATE)
        out.writeframes(encoded.tobytes())
    with wave.open(str(path),"rb") as restored:
        assert restored.getframerate()==RATE and restored.getnchannels()==channels
        assert restored.getnframes()==len(samples) and restored.getsampwidth()==2
        decoded=np.frombuffer(restored.readframes(restored.getnframes()),dtype="<i2")
    assert np.max(np.abs(decoded.astype(np.int32)))<32767
    return {"path":str(path.relative_to(ROOT)),"sha256":sha(path.read_bytes()),"bytes":path.stat().st_size,
            "sample_rate":RATE,"channels":channels,"sample_frames":len(samples),"duration_seconds":len(samples)/RATE,
            "peak_linear":float(np.max(np.abs(samples))),"rms_linear":float(np.sqrt(np.mean(samples**2))),
            "zero_first_last_sample":bool(np.all(encoded[0]==0) and np.all(encoded[-1]==0))}


def negative_checks(film):
    import copy
    checks=[]
    mutations=[("duplicate_id",lambda f:f["audio_cues"].append(copy.deepcopy(f["audio_cues"][0]))),
               ("negative_start",lambda f:f["audio_cues"][0].update(t_seconds=-.1)),
               ("overrun",lambda f:f["audio_cues"][0].update(duration_seconds=24)),
               ("unknown_kind",lambda f:f["audio_cues"][0].update(kind="downloaded_music")),
               ("nonfinite_time",lambda f:f["audio_cues"][0].update(t_seconds=float("nan"))),
               ("path_id",lambda f:f["audio_cues"][0].update(id="audio-../../elsewhere")),
               ("unknown_actor",lambda f:f["audio_cues"][0].update(actor_id="missing")),
               ("fractional_sample",lambda f:f["audio_cues"][0].update(t_seconds=.000001))]
    for name,mutate in mutations:
        candidate=copy.deepcopy(film); mutate(candidate)
        try:
            validate_film(candidate)
        except ValueError:
            checks.append({"case":name,"rejected":True})
        else:
            raise RuntimeError("Negative fixture accepted: "+name)
    return checks


def check_assets(film, film_bytes, cues):
    """Read committed PCM and hashes using only Python's standard library."""
    manifest=json.loads(MANIFEST.read_text())
    if manifest["film_sha256"]!=sha(film_bytes) or manifest["source_sha256"]!=sha(Path(__file__).read_bytes()):
        raise ValueError("Audio manifest source pins are stale; rebuild after contract/source changes")
    by_id={c["id"]:c for c in manifest["cues"]}
    if set(by_id)!={c["id"] for c in cues}:
        raise ValueError("Audio event IDs differ from film")
    descriptors=[manifest["track"]]
    for cue in cues:
        item=by_id[cue["id"]]
        if any(item.get(k)!=v for k,v in cue.items()):
            raise ValueError("Cue metadata differs from film")
        if item["start_sample"]!=round(cue["t_seconds"]*RATE) or item["end_sample_exclusive"]!=round((cue["t_seconds"]+cue["duration_seconds"])*RATE):
            raise ValueError("Cue samples differ from contract")
        if item["clip"]["sample_frames"]!=round(cue["duration_seconds"]*RATE):
            raise ValueError("Cue PCM duration differs from contract")
        if item["best_alignment_sample_offset"]!=0:
            raise ValueError("Cue PCM timing check did not pass")
        descriptors.append(item["clip"])
    for item in descriptors:
        path=(ROOT/item["path"]).resolve()
        if not path.is_relative_to(OUT.resolve()) or sha(path.read_bytes())!=item["sha256"] or path.stat().st_size!=item["bytes"]:
            raise ValueError("Audio asset path/hash mismatch")
        with wave.open(str(path),"rb") as stream:
            if (stream.getframerate(),stream.getnchannels(),stream.getsampwidth(),stream.getnframes())!=(RATE,item["channels"],2,item["sample_frames"]):
                raise ValueError("Audio PCM header mismatch")
            raw=stream.readframes(stream.getnframes())
            if len(raw)!=stream.getnframes()*stream.getnchannels()*stream.getsampwidth():
                raise ValueError("Truncated PCM payload despite declared WAV frame count")
            data=array.array("h",raw)
            if sys.byteorder!="little": data.byteswap()
        if max(abs(x) for x in data)>=32767 or any(data[:item["channels"]]) or any(data[-item["channels"]:]):
            raise ValueError("Audio clips or has nonzero edges")
        if item is manifest["track"]:
            if item["sample_frames"]!=1152000 or item["channels"]!=2 or max(abs(x) for x in data)>round(.721*32767):
                raise ValueError("Master duration/format/headroom mismatch")
            if any(data[:960]) or any(data[-960:]):
                raise ValueError("Master silence padding missing")
    print(json.dumps({"passed":True,"assets":len(descriptors),"cues":len(cues),"duration_seconds":24,"sample_rate":RATE,
                      "master_sha256":manifest["track"]["sha256"],"headroom_db":manifest["tests"]["headroom_db"]}))


def check_asset_mutations(film, film_bytes, cues):
    """Exercise saved-file rejection gates on isolated temporary copies only."""
    import copy
    import shutil
    import struct
    import tempfile
    global ROOT, OUT, MANIFEST
    original_root,original_out,original_manifest=ROOT,OUT,MANIFEST
    base=json.loads(MANIFEST.read_text())
    original_wav=(ROOT/base["track"]["path"]).read_bytes()
    results=[]
    try:
        with tempfile.TemporaryDirectory(prefix="yuga-audio-negative-") as temporary:
            ROOT=Path(temporary); OUT=ROOT/"assets/cinematics/audio"; MANIFEST=ROOT/"art/cinematics/audio-manifest.json"
            shutil.copytree(original_out,OUT,ignore=shutil.ignore_patterns("*.import"))
            MANIFEST.parent.mkdir(parents=True)
            master=ROOT/base["track"]["path"]
            for name in ["stale_source_pin","one_sample_cue_shift","truncated_pcm","nonzero_edge","clipped_sample","wrong_channels"]:
                manifest=copy.deepcopy(base); data=bytearray(original_wav)
                if name=="stale_source_pin": manifest["film_sha256"]="0"*64
                elif name=="one_sample_cue_shift": manifest["cues"][0]["start_sample"]+=1
                elif name=="truncated_pcm": data=data[:-8]
                elif name=="nonzero_edge": struct.pack_into("<h",data,44,100)
                elif name=="clipped_sample": struct.pack_into("<h",data,44+RATE*4,32767)
                elif name=="wrong_channels": struct.pack_into("<H",data,22,1)
                # Update byte/hash fields to exercise structural checks past integrity.
                manifest["track"]["sha256"]=sha(data); manifest["track"]["bytes"]=len(data)
                master.write_bytes(data); MANIFEST.write_text(json.dumps(manifest))
                try:
                    check_assets(film,film_bytes,cues)
                except (ValueError,EOFError) as error:
                    results.append({"case":name,"rejected":True,"reason":str(error)})
                else:
                    raise RuntimeError("Saved-file negative fixture accepted: "+name)
    finally:
        ROOT,OUT,MANIFEST=original_root,original_out,original_manifest
    if (ROOT/base["track"]["path"]).read_bytes()!=original_wav:
        raise RuntimeError("Frozen master changed during temporary-copy tests")
    print(json.dumps({"passed":True,"cases":results,"frozen_assets_modified":False}))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only",action="store_true",help="Validate film and rejection fixtures without writing audio")
    parser.add_argument("--check",action="store_true",help="Validate existing committed audio, source pins and PCM with standard-library checks; no writes")
    parser.add_argument("--check-fixtures",action="store_true",help="Run saved-file corruption fixtures on temporary copies; frozen assets remain untouched")
    args=parser.parse_args()
    film_bytes=FILM.read_bytes(); film=json.loads(film_bytes)
    duration,cues=validate_film(film)
    rejection_checks=negative_checks(film)
    if args.check_fixtures:
        check_asset_mutations(film,film_bytes,cues); return
    if args.check:
        check_assets(film,film_bytes,cues); return
    if args.check_only:
        print(json.dumps({"passed":True,"cues":len(cues),"negative_cases":len(rejection_checks)})); return
    if np is None or scipy is None:
        raise SystemExit("Synthesis requires NumPy and SciPy; --check and --check-only use only the standard library")
    n=round(duration*RATE)
    music=score(n,cues)
    mix=music.copy()
    cue_data=[]
    for cue in cues:
        seed=SEED+int(sha(cue["id"].encode())[:8],16)
        mono=cue_sound(cue["kind"],cue["duration_seconds"],seed)
        pan=-.18 if cue["actor_id"]=="rama" else .18
        start=round(cue["t_seconds"]*RATE); end=start+len(mono)
        mixed=stereo(mono,pan)
        mix[start:end]+=mixed
        cue_data.append((cue,mono,pan,start,end,seed))
    peak=float(np.max(np.abs(mix)))
    gain=.72/peak
    # One linear gain preserves transients; no clipping limiter or nonlinear saturation.
    mix*=gain
    assert np.isfinite(mix).all() and np.max(np.abs(mix))<=.720001
    # Force 10 ms true silence only at the outer film edges, with 30 ms adjacent fades.
    pad=round(.01*RATE); edge=round(.03*RATE)
    mix[:pad]=0; mix[-pad:]=0
    mix[pad:pad+edge]*=np.sin(np.linspace(0,math.pi/2,edge))[:,None]**2
    mix[-pad-edge:-pad]*=np.sin(np.linspace(math.pi/2,0,edge))[:,None]**2
    OUT.mkdir(parents=True,exist_ok=True); MANIFEST.parent.mkdir(parents=True,exist_ok=True)
    track=save_wav(OUT/"confluence-duel-mix.wav",mix)
    with wave.open(str(OUT/"confluence-duel-mix.wav"),"rb") as saved:
        actual_pcm=np.frombuffer(saved.readframes(saved.getnframes()),dtype="<i2").reshape(-1,2).astype(np.float64)/32767
    metadata=[]
    for cue,mono,pan,start,end,seed in cue_data:
        clip=save_wav(OUT/(cue["id"]+".wav"),mono*gain)
        active=np.flatnonzero(np.abs(mono*gain)>1/32767)
        # Check timing against decoded saved PCM, remove other known stems, and
        # compare neighboring sample offsets. A one-sample routing error fails.
        background=music[start:end].copy()*gain
        for other,other_mono,other_pan,other_start,other_end,other_seed in cue_data:
            if other["id"]==cue["id"]:
                continue
            a=max(start,other_start); b=min(end,other_end)
            if a<b:
                background[a-start:b-start]+=stereo(other_mono[a-other_start:b-other_start],other_pan)*gain
        isolated=actual_pcm[start:end]-background
        expected=stereo(mono,pan)*gain
        errors={"0":float(np.sqrt(np.mean((isolated-expected)**2))),
                "-1":float(np.sqrt(np.mean((isolated[1:]-expected[:-1])**2))),
                "+1":float(np.sqrt(np.mean((isolated[:-1]-expected[1:])**2)))}
        assert errors["0"]<.5/32767 and min(errors,key=errors.get)=="0", "Saved PCM cue onset shifted"
        metadata.append({**cue,"start_sample":start,"end_sample_exclusive":end,
                         "first_audible_sample":start+int(active[0]),"last_audible_sample":start+int(active[-1]),
                         "pan":pan,"seed":seed,"clip":clip,
                         "saved_pcm_alignment_rms_by_sample_offset":errors,"best_alignment_sample_offset":0})
        assert end-start==clip["sample_frames"]
        assert start<=start+active[0]<end and start<=start+active[-1]<end
    assert np.max(np.abs(mix[:pad]))==0 and np.max(np.abs(mix[-pad:]))==0
    document={"schema_version":1,"id":"confluence-original-audio","provenance":"Original deterministic mathematical synthesis; no downloaded recordings, voices, commercial game sounds or copyrighted music samples",
              "film_path":str(FILM.relative_to(ROOT)),"film_sha256":sha(film_bytes),
              "source_path":str(Path(__file__).resolve().relative_to(ROOT)),"source_sha256":sha(Path(__file__).read_bytes()),
              "tools":{"numpy":np.__version__,"scipy":scipy.__version__,"python":"stdlib wave PCM encoder"},
              "seed":SEED,"master_linear_gain":gain,"master_peak_target":.72,
              "track":track,"cues":metadata,
              "score":"Original fifth-based low drone, sparse plucked tones and soft membrane percussion; music smoothly ducks48percent under cues",
              "silence_padding_samples_per_edge":pad,"encoding":"48kHz16bit little-endian PCM; stereo master, mono individual cues; no loop metadata",
              "tests":{"exact_duration":track["sample_frames"]==1152000,"finite_pcm_source":True,"no_clipping":True,
                       "headroom_db":float(-20*math.log10(track["peak_linear"])),"outer_silence_passed":True,
                       "saved_pcm_cue_alignment":True,"one_sample_shift_negative_checks":len(cues)*2,
                       "validated_cues":len(cues),"negative_contract_cases":rejection_checks},
              "review":{"status":"numerically_validated_original_synthesis","listening_review":"Human audition and audiovisual timing review remain required; waveform checks do not establish sound quality"},
              "playback_contract":"One nonlooping AudioStreamPlayer. Seek/restart with play(absolute_seconds), pause with stream_paused, stop at24s. Capture mutes nativeaudio; mux this exact WAV. Do not spawn cue players on seek."}
    MANIFEST.write_text(json.dumps(document,indent=2)+"\n")
    print(json.dumps({"passed":True,"frames":track["sample_frames"],"duration":duration,"peak":track["peak_linear"],"headroom_db":document["tests"]["headroom_db"],"cues":len(cues),"sha256":track["sha256"]}))


if __name__=="__main__":
    main()
