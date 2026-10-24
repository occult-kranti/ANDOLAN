#!/usr/bin/env python3
"""Two-case confirmation using the existing qualified HUD capture runner."""
from capture_hud import main

if __name__ == "__main__":
    raise SystemExit(main(driver_name="confirm_hud.gd", expected_samples=2, required_stages=("damage",)))
