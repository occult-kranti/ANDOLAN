"""Verify the rendered source-frame hashes and decode the authored preview."""
import hashlib
import json
import subprocess
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
PREVIEW = HERE / "preview"
receipt = json.loads((PREVIEW / "render-receipt.json").read_text())


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


scene = HERE / "vanara-sena-study.blend"
assert sha(scene) == receipt["scene_sha256"]
frames = receipt["frames"]
assert len(frames) == 31 and frames[0]["scene_frame"] == 1 and frames[-1]["scene_frame"] == 91
assert {19, 79} <= {item["scene_frame"] for item in frames}
for item in frames:
    path = PREVIEW / item["file"]
    assert sha(path) == item["sha256"], item["file"]
    with Image.open(path) as im:
        assert list(im.size) == receipt["resolution"] and im.mode == "RGB"
movie = PREVIEW / receipt["movie"]
assert sha(movie) == receipt["movie_sha256"]
probe = subprocess.run([
    "ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames",
    "-show_entries", "stream=width,height,avg_frame_rate,nb_read_frames,duration,codec_name",
    "-of", "json", str(movie)
], check=True, text=True, capture_output=True)
video = json.loads(probe.stdout)["streams"][0]
assert int(video["nb_read_frames"]) == len(frames)
assert [video["width"],video["height"]] == receipt["resolution"]
md5 = subprocess.run(["ffmpeg", "-v", "error", "-threads", "1", "-i", str(movie),
                      "-f", "framemd5", "-"], check=True, text=True, capture_output=True)
rows = [line for line in md5.stdout.splitlines() if line and not line.startswith("#")]
hashes = [line.rsplit(",",1)[-1].strip() for line in rows]
assert len(hashes) == len(frames) and len(set(hashes)) > 10
report = {"result":"pass","scene_sha256":receipt["scene_sha256"],"video":video,
          "raw_frames_verified":len(frames),"distinct_decoded_frames":len(set(hashes)),
          "contact_sheet_sha256":sha(PREVIEW / "contact-sheet.png"),
          "scope":"Hash, timing, dimensions and full video decode only; does not establish artistic quality, true motion contact or runtime integration."}
(PREVIEW / "media-verification.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps(report,indent=2))
