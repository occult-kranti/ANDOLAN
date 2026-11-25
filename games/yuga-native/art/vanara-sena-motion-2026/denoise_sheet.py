"""Create a separate OIDN display contact sheet while preserving raw frames."""
import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
NATIVE = HERE.parents[1]
sys.path.insert(0,str(NATIVE / "tools/hanuman-art"))
from denoise import read_pfm, write_pfm

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument("--oidn",type=Path,required=True)
args=parser.parse_args()
source=HERE / "preview"
receipt=json.loads((source / "render-receipt.json").read_text())
frames=receipt["frames"]
indices=[0,4,6,10,16,26]
output=source / "denoised"
output.mkdir(exist_ok=True)

def sha(path):
    with path.open("rb") as stream: return hashlib.file_digest(stream,"sha256").hexdigest()

width,height=receipt["resolution"]
canvas=Image.new("RGB",(width*3,(height+26)*2),(12,20,22))
draw=ImageDraw.Draw(canvas)
entries=[]
with tempfile.TemporaryDirectory(prefix="yuga-sena-oidn-") as temp:
    input_pfm=Path(temp)/"input.pfm"
    output_pfm=Path(temp)/"output.pfm"
    for cell,index in enumerate(indices):
        item=frames[index]
        raw=source/item["file"]
        if sha(raw)!=item["sha256"]: raise ValueError(f"Raw frame changed: {raw}")
        with Image.open(raw) as image:
            data=np.asarray(image.convert("RGB"),dtype=np.float32)/255
        write_pfm(input_pfm,data)
        subprocess.run([str(args.oidn.resolve()),"--device","cpu","--threads","2","--affinity","0",
                        "--ldr",str(input_pfm),"--srgb","--output",str(output_pfm)],
                       check=True,stdout=subprocess.DEVNULL)
        filtered=read_pfm(output_pfm)
        if filtered.shape!=data.shape: raise ValueError("Denoiser changed image size")
        pic=Image.fromarray(np.rint(filtered.clip(0,1)*255).astype(np.uint8))
        path=output/item["file"]
        pic.save(path)
        canvas.paste(pic,((cell%3)*width,(cell//3)*(height+26)))
        draw.text(((cell%3)*width+8,(cell//3)*(height+26)+height+6),
                  f"frame {item['scene_frame']}   |   {item['seconds']:.2f}s",fill=(244,229,201))
        entries.append({"file":item["file"],"scene_frame":item["scene_frame"],
                        "raw_sha256":item["sha256"],"filtered_sha256":sha(path)})
sheet=source/"contact-sheet-denoised.png"
canvas.save(sheet)
report={"tool":"Intel Open Image Denoise CLI","tool_sha256":sha(args.oidn),"threads":2,
        "settings":"RT LDR sRGB; no albedo or normal auxiliary pass","frames":entries,
        "sheet":"contact-sheet-denoised.png","sheet_sha256":sha(sheet),
        "scope":"Display copies only; denoising can remove or invent fine detail. Original PNGs remain unchanged."}
(output/"receipt.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps({"result":"pass","frames":len(entries),"sheet_sha256":report["sheet_sha256"]},indent=2))
