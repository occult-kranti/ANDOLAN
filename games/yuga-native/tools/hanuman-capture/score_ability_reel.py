"""Add the trial's authored release/impact cues to a silent native gameplay capture."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import wave

import numpy as np


NATIVE = Path(__file__).resolve().parents[2]
PROFILE = NATIVE / "assets/design/hanuman-presentation.json"
AUDIO = NATIVE / "assets/audio"
RATE = 24000


def waveform(path):
    with wave.open(str(path)) as stream:
        if stream.getsampwidth() != 2:
            raise ValueError(f"Expected PCM16: {path}")
        samples = np.frombuffer(stream.readframes(stream.getnframes()),dtype="<i2")
        values = samples.astype(float).reshape(-1,stream.getnchannels()).mean(axis=1)/32768
        if stream.getframerate() == RATE:
            return values
        duration = len(values)/stream.getframerate()
        return np.interp(np.arange(round(RATE*duration))/RATE, np.arange(len(values))/stream.getframerate(), values)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("capture", type=Path)
    p.add_argument("silent_video", type=Path)
    p.add_argument("output", type=Path)
    p.add_argument("--report", type=Path, required=True)
    args = p.parse_args()
    if args.output.exists() or args.report.exists():
        p.error("Choose fresh output and report paths")
    capture = json.loads(args.capture.read_text())
    if not capture["complete"] or capture["audio_recorded"]:
        p.error("Use a completed silent native frame capture")
    styles = json.loads(PROFILE.read_text())
    fps = capture["fps"]
    frames = len(capture["frames"])
    mix = np.zeros(round(frames*RATE/fps))
    events = []
    for e in capture["events"]:
        if e["kind"] not in ("release","impact"):
            continue
        style = styles[e["ability_id"]]
        key = "impact_audio" if e["kind"] == "impact" else "audio"
        if key not in style:
            continue
        if e["ability_id"] == "vajra_kavacha" and key == "impact_audio":
            if not any("shield" in hit.get("effects",[]) for hit in e["receipts"]):
                continue
        file = AUDIO / style[key]
        gain = style.get("impact_gain",1) if key == "impact_audio" else 1
        start = round(e["sample_frame"]*RATE/fps)
        if not 0 <= start < len(mix):
            raise ValueError("Event outside captured frames")
        cue = waveform(file)*gain
        count = min(len(cue),len(mix)-start)
        mix[start:start+count] += cue[:count]
        events.append({"id":e["ability_id"],"event":e["kind"],"frame":e["sample_frame"],"start_sample":start,
                       "file":style[key],"gain":gain,"sha256":sha256(file.read_bytes()).hexdigest()})
    if {e["id"] for e in events if e["event"]=="release"} != set(styles) or not np.isfinite(mix).all():
        raise ValueError("Missing release or invalid samples")
    if np.max(np.abs(mix)) >= .96:
        raise ValueError("Mix exceeds available headroom")
    with TemporaryDirectory() as tmp:
        track = Path(tmp)/"cue-mix.wav"
        with wave.open(str(track),"wb") as w:
            w.setparams((1,2,RATE,len(mix),"NONE","not compressed"))
            w.writeframes(np.rint(mix*32767).astype("<i2").tobytes())
        subprocess.run(["ffmpeg","-v","error","-nostdin","-i",str(args.silent_video),"-i",str(track),
                        "-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","aac","-b:a","96k",
                        "-movflags","+faststart",str(args.output)],check=True)
    streams = json.loads(subprocess.check_output(["ffprobe","-v","error","-show_streams","-of","json",str(args.output)]))["streams"]
    video = next(s for s in streams if s["codec_type"]=="video")
    audio = next(s for s in streams if s["codec_type"]=="audio")
    if int(video["nb_frames"])!=frames or abs(float(audio["duration"])-frames/fps) > 1/fps:
        raise ValueError("Muxed video no longer matches the frame/time record")
    report={"scope":"Event-synchronized mono mix using original trial cues. Capture used a silent device. Spatial attenuation is omitted.",
            "frames":frames,"fps":fps,"sample_rate":RATE,"duration_s":frames/fps,"peak_linear":float(np.max(np.abs(mix))),
            "pre_mix_video_sha256":sha256(args.silent_video.read_bytes()).hexdigest(),
            "capture_sha256":sha256(args.capture.read_bytes()).hexdigest(),"output_sha256":sha256(args.output.read_bytes()).hexdigest(),"events":events}
    args.report.write_text(json.dumps(report,indent=2)+"\n")


if __name__ == "__main__":
    main()
