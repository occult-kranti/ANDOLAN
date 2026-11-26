"""Build neutral EN/HI timing reads for the listening desk with eSpeak NG and SoX."""

import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory


CAST_SHEET = Path(__file__).resolve().parents[2] / "docs/design/ember-rite-5v5/audio/hero-voice-lines.csv"
ANNOUNCEMENTS = {
    "ignite": "vo.announcer.ritual.kindled",
    "quench": "vo.announcer.ritual.quenched",
}


def capture(args):
    return subprocess.check_output(args, text=True).strip()


def build(folder, synth, sox, voice_data):
    folder.mkdir(parents=True, exist_ok=True)
    espeak = [synth] + ([f"--path={voice_data}"] if voice_data else [])
    entries = {}
    with CAST_SHEET.open(encoding="utf-8", newline="") as cast:
        lines = {row["cue_id"]: row for row in csv.DictReader(cast)}
    with TemporaryDirectory() as temp:
        source = Path(temp) / "read.wav"
        for event, cue in ANNOUNCEMENTS.items():
            for locale in ("en", "hi"):
                line = lines[cue][locale]
                voice = {"hi": "hi", "en": "en-gb"}[locale]
                target = folder / f"{event}-{locale}.wav"
                subprocess.run(
                    [
                        *espeak,
                        "-v",
                        voice,
                        "-s",
                        "157",
                        "-p",
                        "43",
                        "-b",
                        "1",
                        "-w",
                        source,
                        "--stdin",
                    ],
                    input=line + "\n",
                    text=True,
                    check=True,
                )
                subprocess.run(
                    [
                        sox,
                        "-R",
                        "-D",
                        source,
                        "-b",
                        "16",
                        target,
                        "rate",
                        "-v",
                        "24000",
                        "highpass",
                        "50",
                        "gain",
                        "-n",
                        "-8",
                        "pad",
                        ".03",
                        ".06",
                    ],
                    check=True,
                )
                samples = int(capture([sox, "--i", "-s", target]))
                if (
                    int(capture([sox, "--i", "-c", target])) != 1
                    or not 12000 < samples < 100000
                ):
                    raise ValueError(
                        f"Unexpected read length or channel count for {target.name}"
                    )
                entries[target.name] = {
                    "event": event,
                    "locale": locale,
                    "text": line,
                    "voice": voice,
                    "sample_rate": 24000,
                    "samples": samples,
                    "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                }
    report = {
        "purpose": "Actor-neutral scratch announcements for timing and bilingual copy review",
        "clips": entries,
    }
    (folder / "lines.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path(__file__).parent / "voice-guide"
    )
    parser.add_argument("--espeak", default="espeak-ng")
    parser.add_argument("--sox", default="sox")
    parser.add_argument(
        "--voice-data",
        type=Path,
        help="Optional parent of espeak-ng-data for a portable installation",
    )
    args = parser.parse_args()
    build(args.output, args.espeak, args.sox, args.voice_data)
