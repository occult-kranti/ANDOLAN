# User-supplied animation and technical brief

Received 25 November 2026. The text below is retained as **user-supplied planning input**. It is not evidence that capture, coaching, engine integration, budgets, formulas, lore checks or completed abilities exist. Empty headings and underscore operators are preserved because their missing meaning must be resolved before implementation.

---

# DHARMIC COMBAT CODEX v2.0 — ANIMATED SCRIPT & TECH DESIGN DOCUMENT

_Production-Grade Breakdown | Unreal Engine 5 / Unity 6 Compatible_

_Authenticity Source: Valmiki Ramayana, Vyasa Mahabharata, Devi Mahatmya, Vishnu Purana_

## I. ANIMATION PIPELINE & STATE MACHINE ARCHITECTURE

*Core Principle:* All animations are rooted in _Kalaripayattu + Bharatanatyam_ motion capture + hand-keyed divine flourishes. 60fps base, 24fps for cinematic ultimates.

*State Machine Hierarchy:*

*Blend Tree Rules:*
- Divine abilities blend at 0.15s using _root motion override_
- Karmic break = 0.5s stagger with 30° camera tilt + desaturation shader

## II. HANUMAN — MARUTI TECHNICAL BREAKDOWN

*Skeletal Setup:* 78 bones. Tail = 12-bone physics chain with 0.8 spring stiffness. Fur = Niagara cloth sim.

### A. Sanjeevani Dharma Leap — Full Animation Breakdown
*IK Setup:* Left hand IK to mountain prop. Right foot IK to ground on landing.

*Camera:* 0.4s slow-mo at frame 50 + 15° Dutch angle on impact.

*Damage Formula:* `150 + (TargetMaxHP _ 0.15) _ (1 + Dharma/100)`

### B. Gada Bharata — Weapon Animation Layering

*Weapon:* 2.8m golden mace with 4-bone chain + physics drag 0.6.

*Divine Property:* Gada emits _Saffron Light_ that only damages Rakshasa/Asura tags. Deals 50% reduced damage to humans/animals.

## III. ARJUNA — GANDIVADHARI TECHNICAL BREAKDOWN

*Skeletal Setup:* 62 bones. Bowstring = 8-bone cable sim with 0.95 tension. Quiver = particle spawner.

### A. Pashupatastra Marking — Projectile Logic

*Arrow Blueprint:*

*Animation Breakdown — Gandiva Draw:*
- *Frame 0–18:* Left hand draws string. _Dhanur Mudra_ hand pose. String tension = 0 → 1.0
- *Frame 19–24:* Arrow nocks with golden light. _Anjali Mudra_ for 6f
- *Frame 25–30:* Release. String snap = Niagara particle burst + sound crack
- *Frame 31–40:* Recovery. Arjuna shifts weight to back foot

*Auto-Curve Logic:* Arrow uses `SeekBehavior` with 120° turn rate + 800u/s speed. Only seeks targets with “KarmaMark” tag.

### B. Brahmashira — Cinematic Ultimate

*12-Second Cinematic Sequence:*

*Karmic HP Cost Calculation:*

## IV. KALI — MAHAKALI TECHNICAL BREAKDOWN

*Skeletal Setup:* 94 bones. 4 arms = 4 independent IK chains. Hair = 16-bone physics chain.

### A. Maha Tandava — Procedural Dance System

*Animation:* Motion-capped Bharatanatyam _Tandava_ + hand-keyed 4-arm coordination.

*Blending:* All 4 arms run on separate Animation Layers with 0.1s blend-in.

*Skull Garland Stack System:*

*Visual:* 5 skulls materialize on necklace, each skull glowing red when stack consumed.

### B. Yama’s Nectar — Execution Animation

*Instant Kill Logic:*

*Frame Data:* 48f animation. Active frames 24–32. During frames 20–40 Kali is intangible.

## V. RAMA — MARYADA PURUSHOTTAMA TECHNICAL BREAKDOWN

*Skeletal Setup:* 64 bones. Bow = rigidbody with cloth quiver. Cape = 24-bone cloth sim.

### A. Alignment Detection System
*Visual Feedback:* Target gets colored aura — Red=Evil, Yellow=Neutral, White=Good, Blue=Innocent.

### B. Kodanda Shot — Alignment-Based Damage

*Animation Layers:*
- *Base:* Draw animation 24f
- *Layer 1 [Evil]:* Arrow glows white-blue + emits Sanskrit shloka audio
- *Layer 2 [Innocent]:* Arrow dissolves into lotus petals + Rama plays “Shame” animation

*Damage Calculation:*

## VI. KRISHNA — YOGESHWARA TECHNICAL BREAKDOWN

*Skeletal Setup:* 68 bones. Peacock feather = 6-bone physics. Flute = held prop with finger IK.

### A. Maya Illusion System

*Mirror Image AI:*

*Spawn Pattern:* 2 images spawn at 120° and 240° relative to Krishna’s facing.

### B. Vishwaroopa — Shader & VFX Breakdown

*Post-Process Effect:*
- *Chromatic Aberration:* 0.15 intensity
- *Screen Distortion:* Sine wave with 2.5 amplitude
- *Color Shift:* RGB channels separate by 8px
- *Vignette:* 0.8 intensity + golden tint

*Cosmic Form Mesh:* Krishna mesh swaps to 3-head + 4-arm + cosmic background material with moving stars.

*Stun Recovery Animation:*

## VII. KARMIC RESONANCE — COMBO SYSTEM

*Combo Detection:*

*Rama Setu Bridge:*
- *Mesh:* Stone blocks floating with water ripple shader
- *Physics:* Walkable surface with 0.5 friction
- *Duration:* 8s + 2s fade-out with stone crumble VFX

## VIII. PERFORMANCE & OPTIMIZATION

*LOD Strategy:*
- *LOD0:* 60k triangles + 4k textures [0–5m]
- *LOD1:* 25k triangles + 2k textures [5–15m]
- *LOD2:* 8k triangles + 1k textures [15m+]

*Niagara VFX Pooling:*
- Sanjeevani particles: Pool size 200, lifetime 3s
- Pashupatastra arrows: Pool size 50, lifetime 5s
- Kali skulls: Pool size 30, lifetime 6s

*Memory Budget:* 450MB for all 5 heroes + VFX + animations.

## IX. AUTHENTICITY CHECKLIST

## X. QA TESTING MATRIX

*PRODUCTION NOTES:*
- All voice lines recorded with Sanskrit phonetic coach
- Motion capture done with Kalaripayattu master from Kerala
- VFX reference: Ajanta Ellora cave paintings + miniature paintings

*The Goal:* When player uses _Brahmashira_, they don’t just feel power — they feel the _weight of dharma_ on their shoulders.

Want me to draft the _Mahishasura Boss Phase System_ with phase transitions tied to Devi Mahatmya Chapter 3?
