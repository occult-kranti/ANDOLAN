# YUGA tactical art and audio

- `assets/tactical/menu-keyart.png`: original generated YUGA menu illustration using built-in image generation. Exact prompt at `art/tactical/MENU_PROMPT.md`. SHA-256 `17f12c6c9a38a8835ad5d0e19c931a0f2ceb5999695631a35482f492be30ab24`. Decorative menu art, not a captured gameplay image or production 3D model.
- `scripts/tactical_weapon.gd`: original procedural ARKA/SURYA first-person geometry, arms/bracers, material definitions and presentation.
- `scripts/tactical_actor.gd`: original YUGA infantry assembly reused from `lane_infantry_art.gd`, adapted to tactical firearm poses. Existing original art ownership/provenance retained.
- `scripts/tactical_effects.gd`: original native veil, physical ward, solar traces and Astra relic geometry.
- `assets/tactical/audio/*.wav`: thirteen original deterministic synthesized cues, no external recording or model. Rebuild with `python3 tools/studio/build-tactical-audio.py`; exact wave hashes and signal statistics in the sibling manifest.
- Map reuse and external reference citations: `NOTICE/TACTICAL-MAP.md`. Fonts retain existing Noto/DejaVu notices. Native UI icons are original vector assets.

Valorant, Counter-Strike, Overwatch and Deadlock are design references only. No commercial game code, maps, models, UI graphics or audio were imported from them.
