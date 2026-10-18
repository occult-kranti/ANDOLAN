"""Exact separately approved r3 package identity; no runtime substitutions."""
import hashlib
import json
from pathlib import Path

SOURCE = 'f8dec5fa4f9bbd2d20c58f6102fb984d0b19a9f1'
EXPORTER = 'f64d4ed19fc9df9440321653fcc80df8c6e365ba7b6de0a29e2cfa9fa71bfeb3'
RUNTIME = 'dce0422d5a2ef2e00494a9b7689613d14bd1fcc4c07eac21c7e91721adcf730f'
ARCHIVE = '913e2b82b9a71977bf361349e225ae0295a9dd08f1e0a0a68d7b3b7d3df4426c'
PCK = 'f55b5417e38b6a5b46ff2b12ec22890509287f84ad1fe2fb62c87190c76a7197'
EXPORT_MANIFEST = 'c472ef5278b4c35b8226d654bbaf5c0061b98c00a4be20c7a3a1dbe8600adb54'
PACKAGE_MANIFEST = '6df86cc23505cbe6fc1a22d00e86cb9afc03c7733b69e0b068c40889d9c0ff36'
SELECTION = Path(__file__).with_name('expected-engine-selection.json')


def exact_selection(selection):
    """Includes exporter, runtime SHA, zero patches, source, build and proof pins."""
    if hashlib.sha256(SELECTION.read_bytes()).hexdigest() != 'ea1ad72422b657241150b1ae525536712c03dbec478dab659a6a41627376bb7a':
        return False
    expected = json.loads(SELECTION.read_text())
    return (selection == expected and
            selection['exporter']['sha256'] == EXPORTER and
            selection['linux_runtime']['sha256'] == RUNTIME and
            selection['linux_runtime']['provenance']['source_patches'] == 0 and
            selection['linux_runtime']['provenance']['target'] == 'template_debug')
