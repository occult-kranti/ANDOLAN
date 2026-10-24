#!/usr/bin/env python3
"""Confirm the atlas repair through the existing qualified native capture runner."""
from capture_hud import main

if __name__ == "__main__":
    raise SystemExit(main(driver_name="confirm_atlas_repair.gd", expected_samples=4, required_stages=("damage",)))
