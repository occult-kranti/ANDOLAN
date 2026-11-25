"""Package only the local offline world candidate for visual and input checks."""
import hashlib
import json
import sys
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

candidate = Path(sys.argv[1] if len(sys.argv) > 1 else '/tmp/yuga-ghat-candidate')
html = (candidate / 'yuga-rust.html').read_bytes()
result = json.loads((candidate / 'build.json').read_text())
if hashlib.sha256(html).hexdigest() != result['candidate_html_sha256']:
    raise ValueError('Candidate HTML differs from its receipt')
notice = ("""YUGA Ghat Coast candidate

Offline review copy with the released combat authority.
""" + result.get('scope','Six scenic rock faces outside the actor bounds.') + """
Source: Rock Face 01 by Dario Barresi, https://polyhaven.com/a/rock_face_01
License: CC0, https://polyhaven.com/license
Open yuga-rust.html in a WebGL2 desktop browser. Multiplayer is outside this
candidate's verification. The studied rocks are visual and beyond actor bounds.
""").encode()
with ZipFile(candidate / 'yuga-rust-confluence.zip', 'w') as output:
    for filename, data in [('yuga-rust.html', html), ('PLAY.txt', notice),
                           ('build.json', json.dumps(result, indent=2).encode())]:
        output.writestr(ZipInfo(filename), data, compress_type=ZIP_DEFLATED, compresslevel=7)
print(candidate / 'yuga-rust-confluence.zip')
