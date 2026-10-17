"""Read original diagnostic PNGs; compare decoded title-label pixels, not previews."""
from pathlib import Path
import hashlib
import json
from PIL import Image

REPORT = Path(__file__).with_name('summary.json')
data = json.loads(REPORT.read_text())
hashes = set()
for shot in data['observed_images']:
    path = REPORT.parent / shot['archive_file']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == shot['file_pin']['sha256']
    with Image.open(path) as image:
        region = image.convert('RGB').crop(shot['label_roi_xyxy'])
        digest = hashlib.sha256(region.tobytes()).hexdigest()
        assert digest == shot['decoded_label_roi_rgb_sha256']
        count = sum(max(pixel) < 100 for pixel in region.get_flattened_data())
        assert count == shot['dark_pixels'] == 630
        hashes.add(digest)
assert len(data['observed_images']) == 12 and len(hashes) == 1
print(json.dumps({'passed': True, 'original_pngs': 12, 'identical_decoded_label_regions': 12,
                  'dark_text_pixels_each': 630, 'decoded_rgb_sha256': next(iter(hashes)),
                  'scope': 'Byte comparison against legible reference; not OCR or full-game UI acceptance.'}))
