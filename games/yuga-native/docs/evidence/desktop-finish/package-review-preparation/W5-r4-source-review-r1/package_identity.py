"""Exact separately approved r4 archive identity; extracted patched runtime only."""
import hashlib
import json
from pathlib import Path
SOURCE = '96d5b9cd3114b9732f7dc80433b1ca0a1d4a9b12'
EXPORTER = 'f64d4ed19fc9df9440321653fcc80df8c6e365ba7b6de0a29e2cfa9fa71bfeb3'
RUNTIME = 'e69af4f6f07876a83e49a02a86928db00993f88594c05ae589e4021d6916d54e'
ARCHIVE = '27c36e5523643c647b245614721c0160b3d1548bf6da851d922886cffc180d0e'
PCK = 'b84ac0f4f1e70fbfc5366234729a9e97012e5664bd6a3a43bfb77fe61e7b6903'
EXPORT_MANIFEST = '4cb3316300092dcdb99016f3c0e6f024066df2f94999a3b7b4944247870aa4a7'
PACKAGE_MANIFEST = '01581b3d740097aa61bd35c3722a85dca1021dddb1766a2a28e1c1b53645417c'
SELECTION = Path(__file__).with_name('expected-engine-selection.json')

def approved_inputs_bound():
    return (isinstance(SOURCE,str) and len(SOURCE)==40 and all(c in '0123456789abcdef' for c in SOURCE) and
            all(isinstance(v,str) and len(v)==64 and all(c in '0123456789abcdef' for c in v) for v in [EXPORTER,RUNTIME,ARCHIVE,PCK,EXPORT_MANIFEST,PACKAGE_MANIFEST]))

def exact_selection(selection):
    if hashlib.sha256(SELECTION.read_bytes()).hexdigest() != '3c7ad7d93b40dc436ce80588a43fce7f920bb0d3416948a7b4f742df03bac38a': return False
    expected = json.loads(SELECTION.read_text())
    return (selection == expected and selection['exporter']['sha256'] == EXPORTER and
        selection['linux_runtime']['sha256'] == RUNTIME and
        selection['linux_runtime']['kind'] == 'patched-public-source-template-debug' and
        selection['linux_runtime']['provenance']['variant'] == 'pipeline-low-priority-v1' and
        selection['linux_runtime']['provenance']['source_patches'] == 1 and
        selection['linux_runtime']['provenance']['target'] == 'template_debug' and
        len(selection['linux_runtime']['provenance']['evidence']) == 11)
