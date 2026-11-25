#!/usr/bin/env python3
"""Prove the cue checker rejects corrupted bytes without touching the real asset."""
from contextlib import redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("sena_audio", HERE / "build.py")
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)
data, notice = generator.produce()

with TemporaryDirectory(prefix="yuga-sena-cue-") as tmp:
    root = Path(tmp)
    generator.OUTPUT = root / "vanara_sena.wav"
    generator.NOTICE = root / "notice.json"
    generator.OUTPUT.write_bytes(data)
    generator.NOTICE.write_text(json.dumps(notice, indent=2) + "\n")
    sys.argv = ["build.py", "--check"]
    with redirect_stdout(io.StringIO()):
        generator.main()
    altered = bytearray(data)
    altered[len(altered) // 2] ^= 1
    generator.OUTPUT.write_bytes(altered)
    try:
        generator.main()
    except ValueError:
        rejected_audio = True
    else:
        raise AssertionError("Corrupted WAV was accepted")
    generator.OUTPUT.write_bytes(data)
    generator.NOTICE.write_text("{}\n")
    try:
        generator.main()
    except ValueError:
        rejected_notice = True
    else:
        raise AssertionError("Corrupted notice was accepted")

result = {"passed": True, "correct_fixture_accepted": True,
          "corrupted_wav_rejected": rejected_audio,
          "corrupted_notice_rejected": rejected_notice,
          "scope": "Temporary copies only; no listener or live browser"}
report = HERE / "corruption-check.json"
report.write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
