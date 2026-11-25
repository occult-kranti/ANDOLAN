"""Apply optional Open Image Denoise to Blender PNGs without altering originals.

Needs numpy, Pillow and the official oidnDenoise tool; pass its absolute path.
RGB channels are passed as display-encoded (sRGB) floating-point PFM; the
denoised presentation file is separate from the unmodified Cycles evidence.
"""
from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image


def write_pfm(path: Path, data: np.ndarray) -> None:
    rows, columns, channels = data.shape
    if channels != 3:
        raise ValueError('Only RGB images are supported')
    with path.open('wb') as f:
        f.write(f'PF\n{columns} {rows}\n-1.0\n'.encode('ascii'))
        np.flipud(data).astype('<f4').tofile(f)


def read_pfm(path: Path) -> np.ndarray:
    with path.open('rb') as f:
        if f.readline().strip() != b'PF':
            raise ValueError('OIDN did not produce an RGB PFM')
        width,height = map(int,f.readline().split())
        scale = float(f.readline())
        endian = '<' if scale < 0 else '>'
        values = np.fromfile(f, dtype=endian+'f4').reshape(height,width,3)
    if not np.isfinite(values).all():
        raise ValueError('OIDN returned non-finite RGB values')
    return np.flipud(values)*abs(scale)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--oidn', type=Path, required=True)
    parser.add_argument('source', type=Path, nargs='+')
    args = parser.parse_args()
    for path in args.source:
        output = path.with_name(path.stem+'-denoised.png')
        if output.exists():
            raise FileExistsError(output)
        with Image.open(path) as source:
            values = np.asarray(source.convert('RGB'), np.float32)/255
        with tempfile.TemporaryDirectory(prefix='yuga-oidn-') as work:
            inp,out = Path(work)/'in.pfm',Path(work)/'out.pfm'
            write_pfm(inp,values)
            subprocess.run([str(args.oidn.resolve()),'--device','cpu','--threads','2',
                            '--affinity','0','--ldr',str(inp),'--srgb','--output',str(out)],
                           check=True, timeout=80)
            filtered=read_pfm(out)
        if filtered.shape != values.shape:
            raise ValueError('OIDN changed render dimensions')
        rgb=np.round(filtered.clip(0,1)*255).astype(np.uint8)
        Image.fromarray(rgb).save(output)
        print(output)


if __name__=='__main__':
    main()
