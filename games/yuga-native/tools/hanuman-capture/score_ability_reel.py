"""Add the trial's authored release/impact cues to a silent native gameplay capture."""
import argparse
from fractions import Fraction
from hashlib import sha256
from io import BytesIO
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


def waveform(data):
    with wave.open(BytesIO(data)) as stream:
        if stream.getsampwidth() != 2:
            raise ValueError("Expected a PCM16 cue")
        samples = np.frombuffer(stream.readframes(stream.getnframes()),dtype="<i2")
        values = samples.astype(float).reshape(-1,stream.getnchannels()).mean(axis=1)/32768
        if stream.getframerate() == RATE:
            return values
        duration = len(values)/stream.getframerate()
        return np.interp(np.arange(round(RATE*duration))/RATE, np.arange(len(values))/stream.getframerate(), values)


def streams(path):
    return json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_streams", "-of", "json", str(path),
    ]))["streams"]


def verify_video(tracks, frames, fps, size):
    videos = [track for track in tracks if track["codec_type"] == "video"]
    if len(videos) != 1:
        raise ValueError("Expected exactly one video stream")
    video = videos[0]
    if (video.get("codec_name") != "h264" or int(video["nb_frames"]) != frames
            or Fraction(video["avg_frame_rate"]) != fps or Fraction(video["r_frame_rate"]) != fps
            or [video["width"], video["height"]] != size
            or abs(float(video["duration"]) - frames / fps) > .01
            or abs(float(video["start_time"])) > .001):
        raise ValueError("Video cadence, size or duration differs from the capture")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("capture", type=Path)
    p.add_argument("silent_video", type=Path)
    p.add_argument("output", type=Path)
    p.add_argument("--report", type=Path, required=True)
    p.add_argument("--encode-report", type=Path, help="encoder receipt, defaults to the input video's sibling JSON")
    args = p.parse_args()
    if args.output.resolve() == args.report.resolve() or args.output.exists() or args.report.exists():
        p.error("Choose fresh output and report paths")
    capture_bytes = args.capture.read_bytes()
    capture_hash = sha256(capture_bytes).hexdigest()
    capture = json.loads(capture_bytes)
    if not capture["complete"] or capture["audio_recorded"]:
        p.error("Use a completed silent native frame capture")
    profile_bytes = PROFILE.read_bytes()
    profile_hash = sha256(profile_bytes).hexdigest()
    source_hashes = capture["source_sha256"]
    if source_hashes.get("res://assets/design/hanuman-presentation.json") != profile_hash:
        raise ValueError("The presentation profile differs from the captured source")
    styles = json.loads(profile_bytes)
    fps = capture["fps"]
    frames = len(capture["frames"])
    if type(fps) is not int or not 8 <= fps <= 30 or not fps <= frames <= fps * 30:
        raise ValueError("Use a bounded fixed-cadence native capture")
    encode_report = args.encode_report or args.silent_video.with_suffix(".json")
    enc_bytes = encode_report.read_bytes()
    encoded = json.loads(enc_bytes)
    silent_hash = sha256(args.silent_video.read_bytes()).hexdigest()
    if (encoded.get("complete") is not True or encoded.get("render_receipt_sha256") != capture_hash
            or encoded.get("video_sha256") != silent_hash or encoded.get("frame_count") != frames):
        raise ValueError("Encoder receipt does not bind this capture and silent video")
    original_streams = streams(args.silent_video)
    verify_video(original_streams, frames, fps, capture["size"])
    if any(track["codec_type"] == "audio" for track in original_streams):
        raise ValueError("The encoded input already contains audio")
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
        file = (AUDIO / style[key]).resolve()
        cue_source = "res://assets/audio/" + file.relative_to(AUDIO.resolve()).as_posix()
        cue_bytes = file.read_bytes()
        cue_hash = sha256(cue_bytes).hexdigest()
        if source_hashes.get(cue_source) != cue_hash:
            raise ValueError("Cue differs from the captured source: " + cue_source)
        gain = style.get("impact_gain",1) if key == "impact_audio" else 1
        start = round(e["sample_frame"]*RATE/fps)
        if not 0 <= start < len(mix):
            raise ValueError("Event outside captured frames")
        cue = waveform(cue_bytes)*gain
        count = min(len(cue),len(mix)-start)
        mix[start:start+count] += cue[:count]
        events.append({"id":e["ability_id"],"event":e["kind"],"frame":e["sample_frame"],"start_sample":start,
                       "file":style[key],"gain":gain,"sha256":cue_hash})
    if {e["id"] for e in events if e["event"]=="release"} != set(styles) or not np.isfinite(mix).all():
        raise ValueError("Missing release or invalid samples")
    if np.max(np.abs(mix)) >= .96:
        raise ValueError("Mix exceeds available headroom")
    with TemporaryDirectory() as tmp:
        track = Path(tmp)/"cue-mix.wav"
        with wave.open(str(track),"wb") as w:
            w.setparams((1,2,RATE,len(mix),"NONE","not compressed"))
            w.writeframes(np.rint(mix*32767).astype("<i2").tobytes())
        subprocess.run(["ffmpeg","-v","error","-nostdin","-n","-i",str(args.silent_video),"-i",str(track),
                        "-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","aac","-b:a","96k",
                        "-movflags","+faststart",str(args.output)],check=True)
    mux_tracks = streams(args.output)
    verify_video(mux_tracks, frames, fps, capture["size"])
    audio = next(s for s in mux_tracks if s["codec_type"]=="audio")
    if abs(float(audio["duration"])-frames/fps) > 1/fps or abs(float(audio["start_time"])) > 1/fps:
        raise ValueError("Muxed video no longer matches the frame/time record")
    report={"scope":"Event-synchronized mono mix using original trial cues. Capture used a silent device. Spatial attenuation is omitted.",
            "frames":frames,"fps":fps,"sample_rate":RATE,"duration_s":frames/fps,"peak_linear":float(np.max(np.abs(mix))),
            "pre_mix_video_sha256":silent_hash,"encode_receipt_sha256":sha256(enc_bytes).hexdigest(),
            "capture_sha256":capture_hash,"presentation_profile_sha256":profile_hash,
            "score_script_sha256":sha256(Path(__file__).read_bytes()).hexdigest(),
            "output_sha256":sha256(args.output.read_bytes()).hexdigest(),"events":events}
    args.report.write_text(json.dumps(report,indent=2)+"\n")


if __name__ == "__main__":
    main()
