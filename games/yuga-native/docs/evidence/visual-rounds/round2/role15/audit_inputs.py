#!/usr/bin/env python3
"""Current review audit; initial implementation is preserved separately."""
import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).with_name("audit_final_inputs.py")), run_name="__main__")
