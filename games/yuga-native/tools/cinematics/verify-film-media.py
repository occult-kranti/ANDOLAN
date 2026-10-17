#!/usr/bin/env python3
"""Independently inspect a completed film's timestamps and audio correspondence.

Requires ffprobe/ffmpeg, NumPy and SciPy. Never edits the media or source WAV.
This verifies encoded timing and waveform correspondence, not auditory quality.
"""
import argparse
import hashlib
import json
import math
import subprocess
import sys
import wave
from fractions import Fraction
from pathlib import Path

import numpy as np
from scipy.signal import correlate, correlation_lags

ROOT=Path(__file__).resolve().parents[2]
RATE=48000
FPS=24
DURATION=24
FRAMES=FPS*DURATION


def digest(path):
    h=hashlib.sha256()
    with path.open("rb") as stream:
        for part in iter(lambda:stream.read(1024*1024),b""):
            h.update(part)
    return h.hexdigest()


def run(command):
    return subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True,timeout=180).stdout


def require(condition, message):
    if not condition:
        raise ValueError(message)


def probe(path, entries, selector=None, frames=False):
    command=["ffprobe","-v","error","-threads","1"]
    if selector:command.extend(["-select_streams",selector])
    if frames:command.append("-show_frames")
    command.extend(["-show_entries",entries,"-of","json",str(path)])
    return json.loads(run(command))


def correlation_check(reference, decoded, maximum_lag=2400):
    reference=np.mean(reference,axis=1); decoded=np.mean(decoded,axis=1)
    reference=reference-np.mean(reference); decoded=decoded-np.mean(decoded)
    require(len(reference)==len(decoded),"Correlation inputs differ in length")
    values=correlate(decoded,reference,mode="full",method="fft")
    lags=correlation_lags(len(decoded),len(reference),mode="full")
    window=np.abs(lags)<=min(maximum_lag,len(reference)//4)
    lag=int(lags[window][np.argmax(values[window])])
    if lag>0:a,b=reference[:-lag],decoded[lag:]
    elif lag<0:a,b=reference[-lag:],decoded[:lag]
    else:a,b=reference,decoded
    energy_a=float(np.dot(a,a)); energy_b=float(np.dot(b,b))
    require(energy_a>1e-8 and energy_b>1e-8,"Missing/near-silent audio in comparison window")
    coefficient=float(np.dot(a,b)/math.sqrt(energy_a*energy_b))
    gain=float(np.dot(a,b)/energy_a)
    error=float(np.sqrt(np.mean((b-a*gain)**2)))
    require(abs(lag)<=1,"Encoded audio differs by more than one sample from source timing")
    require(coefficient>=.97,"Encoded audio does not closely match source waveform")
    require(.94<=gain<=1.06,"Encoded audio level differs materially from approved master")
    return {"estimated_offset_samples":lag,"estimated_offset_seconds":lag/RATE,
            "normalized_correlation":coefficient,"fitted_linear_gain":gain,"residual_rms_after_gain_fit":error,
            "thresholds":{"maximum_offset_samples":1,"minimum_correlation":.97,"gain_range":[.94,1.06]}}


def compare_capture(path, film_path, wav_path):
    report=json.loads(path.read_text())
    require(report.get("complete") is True and not report.get("failure"),"Capture report is incomplete")
    require(report.get("preview") is False,"A preview capture is not the complete film")
    require(report["frame_count"]==FRAMES and len(report["frames"])==FRAMES,"Capture does not contain 576 frames")
    require(report["sample_hz"]==FPS and report["duration_seconds"]==DURATION,"Capture rate/duration mismatch")
    for index,frame in enumerate(report["frames"]):
        require(abs(frame["t_seconds"]-index/FPS)<1e-6,"Capture time differs from absolute 24 Hz timeline")
        require(frame["width"]==1280 and frame["height"]==720,"Capture dimensions differ from 720p release")
        require(frame.get("diagnostics",{}).get("finite") is True,"Capture has a nonfinite state")
        png=path.parent/frame["file"]
        require(png.is_file() and digest(png)==frame["sha256"],"Capture PNG missing or changed")
    source=report["source_sha256"]
    for resource,file_path in [("res://assets/cinematics/confluence-duel.json",film_path),("res://assets/cinematics/audio/confluence-duel-mix.wav",wav_path)]:
        require(source.get(resource)==digest(file_path),"Capture source differs from approved film/audio")
    return {"path":str(path),"sha256":digest(path),"frames_hashed":FRAMES,"source_film_and_audio_match":True,
            "renderer":report.get("renderer"),"adapter":report.get("adapter"),"not_a_hardware_fps_measurement":True}


def verify(args):
    video=args.video.resolve(); wav=args.wav.resolve(); film_path=ROOT/"assets/cinematics/confluence-duel.json"
    initial=(video.stat().st_size,video.stat().st_mtime_ns)
    video_hash=digest(video); wav_hash=digest(wav)
    film=json.loads(film_path.read_text()); audio_manifest=json.loads((ROOT/"art/cinematics/audio-manifest.json").read_text())
    require(wav_hash==audio_manifest["track"]["sha256"],"Reference WAV differs from its approved manifest")
    streams=probe(video,"stream=index,codec_type,codec_name,width,height,sample_rate,channels,start_time,duration,nb_frames,avg_frame_rate,r_frame_rate:format=duration,start_time,format_name")
    video_streams=[s for s in streams["streams"] if s["codec_type"]=="video"]
    audio_streams=[s for s in streams["streams"] if s["codec_type"]=="audio"]
    require(len(video_streams)==1 and len(audio_streams)==1,"Expected exactly one video and one audio stream")
    v,a=video_streams[0],audio_streams[0]
    require((v["width"],v["height"])==(1280,720),"Expected actual 1280x720 encoded video")
    require(Fraction(v["avg_frame_rate"])==FPS and Fraction(v["r_frame_rate"])==FPS,"Video is not constant 24 fps")
    require(a["codec_name"]=="aac" and int(a["sample_rate"])==RATE and a["channels"]==2,"Expected 48 kHz stereo AAC delivery audio")
    for label,item in [("video",v),("audio",a),("container",streams["format"])]:
        require(abs(float(item["start_time"]))<1/RATE,label+" starts after/before timeline zero")
        require(abs(float(item["duration"])-DURATION)<1/RATE,label+" duration differs from 24 seconds")
    vf=probe(video,"frame=best_effort_timestamp_time,pkt_duration_time","v:0",True)["frames"]
    require(len(vf)==FRAMES,"Decoded frame count is not 576")
    video_errors=[abs(float(frame["best_effort_timestamp_time"])-i/FPS) for i,frame in enumerate(vf)]
    require(max(video_errors)<1e-5,"Video frame timestamps are irregular or shifted")
    af=probe(video,"frame=best_effort_timestamp_time,nb_samples,pkt_duration_time","a:0",True)["frames"]
    sample_cursor=0; audio_errors=[]
    for frame in af:
        audio_errors.append(abs(float(frame["best_effort_timestamp_time"])-sample_cursor/RATE))
        sample_cursor+=int(frame["nb_samples"])
    require(sample_cursor==DURATION*RATE,"AAC decoded sample count differs from source duration")
    require(audio_errors and max(audio_errors)<1e-5,"Audio frame timestamps are irregular or shifted")
    with wave.open(str(wav),"rb") as source:
        require((source.getframerate(),source.getnchannels(),source.getsampwidth(),source.getnframes())==(RATE,2,2,DURATION*RATE),"Reference master WAV format mismatch")
        reference=np.frombuffer(source.readframes(source.getnframes()),dtype="<i2").reshape(-1,2).astype(np.float64)/32767
    pcm=run(["ffmpeg","-v","error","-threads","1","-i",str(video),"-map","0:a:0","-f","s16le","-acodec","pcm_s16le","-ar",str(RATE),"-ac","2","-"])
    require(len(pcm)==DURATION*RATE*2*2,"Decoded audio byte count differs from 24 second stereo PCM")
    decoded=np.frombuffer(pcm,dtype="<i2").reshape(-1,2).astype(np.float64)/32767
    require(np.max(np.abs(decoded))<1,"Delivery AAC decodes to clipped PCM")
    whole=correlation_check(reference,decoded)
    cue_windows=[]
    for cue_id in ["audio-guard-block","audio-wave-release","audio-counter-hit","audio-resolve"]:
        cue=next(c for c in film["audio_cues"] if c["id"]==cue_id)
        start=round(max(0,cue["t_seconds"]-.15)*RATE)
        end=round(min(DURATION,cue["t_seconds"]+cue["duration_seconds"]+.15)*RATE)
        cue_windows.append({"id":cue_id,"start_sample":start,"end_sample_exclusive":end,
                            **correlation_check(reference[start:end],decoded[start:end])})
    capture=compare_capture(args.capture_report.resolve(),film_path,wav) if args.capture_report else None
    require(initial==(video.stat().st_size,video.stat().st_mtime_ns) and video_hash==digest(video),"Video changed during verification")
    require(wav_hash==digest(wav),"Reference WAV changed during verification")
    return {"schema_version":1,"passed":True,"scope":"Independent media structure, timestamps and numeric AAC/source-waveform correspondence; no listening review or commercial visual-quality claim",
            "script_sha256":digest(Path(__file__)),"video":{"path":str(video),"sha256":video_hash,"bytes":initial[0],"streams":streams},
            "reference_audio":{"path":str(wav),"sha256":wav_hash},"film_sha256":digest(film_path),
            "video_timing":{"frames":len(vf),"fps":FPS,"first_pts":float(vf[0]["best_effort_timestamp_time"]),"last_pts":float(vf[-1]["best_effort_timestamp_time"]),"maximum_timestamp_error_seconds":max(video_errors)},
            "audio_timing":{"decoded_frames":len(af),"decoded_sample_frames":sample_cursor,"sample_rate":RATE,"maximum_timestamp_error_seconds":max(audio_errors),"decoded_peak_linear":float(np.max(np.abs(decoded)))},
            "whole_track_correspondence":whole,"critical_cue_correspondence":cue_windows,"capture":capture,
            "tools":{"ffmpeg":run(["ffmpeg","-version"]).decode().splitlines()[0],"ffprobe":run(["ffprobe","-version"]).decode().splitlines()[0]},
            "auditory_audition":"Not performed. Numeric waveform comparison cannot judge artistic sound quality."}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video",type=Path,required=True)
    parser.add_argument("--wav",type=Path,default=ROOT/"assets/cinematics/audio/confluence-duel-mix.wav")
    parser.add_argument("--capture-report",type=Path,help="Optional completed 576-frame capture report; verifies every original PNG and source pins")
    parser.add_argument("--report",type=Path,default=ROOT/"tests/evidence/combat-film/media-release-check.json")
    args=parser.parse_args()
    try:
        result=verify(args)
    except Exception as error:
        result={"schema_version":1,"passed":False,"error":str(error),"scope":"Media timing/correspondence check; no auditory review"}
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({"passed":result["passed"],"report":str(args.report),"error":result.get("error")}))
    return 0 if result["passed"] else 1


if __name__=="__main__":
    sys.exit(main())
