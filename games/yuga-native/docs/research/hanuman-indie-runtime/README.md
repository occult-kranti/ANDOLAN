# Hanuman practice court render checks

Run Godot 4.6.3 from the repository root with `godot --path games/yuga-native`. Choose **Hanuman → Begin Hanuman Trial → Begin practice**. Vault to see the footprint fade. Use the rear sweep or Mountain Pulse to see the ground field advance across the accepted area.

| Review | Result | Open |
| --- | --- | --- |
| Contact shadow | The matched 960 × 540 Forward+ capture localized the additional darkening beneath the feet. Both the directional-shadow and fallback settings passed 12 headless checks each. | [With contact](shadow-contact.png) · [Control](shadow-control.png) · [Pixel measurement, inputs and tests](shadow-verification.json) |
| Ground effects | A shared clock drives three reusable tiles. Time advances without re-uploading the texture. The native disk and sector, pause, cancellation, capacity, expiry and reset tests passed. | [Mountain Pulse in practice](ground-mountain.png) · [23 headless checks and 24 Forward+ checks](ground-verification.json) |
| Normal launcher and controls | An X11 input driver selected Hanuman, entered practice, moved, used all five abilities, paused, returned to title, and quit with exit code zero. The archive contains 20 original screens and 23 JSON files, including the input sequence and all five impact or movement receipts. | [Download the complete input run](ordinary-input.zip) · [Driver](../../../tools/hanuman-capture/ordinary.py) |

ZIP SHA-256 is `fd02117eb6d2a51ccc29a5379f5975914acf84d53d6ed1db417d120200780a49`. These captures used Vulkan software rendering in the cloud. The physical Steam Deck comparison remains open. [Handheld measurement protocol](../HANUMAN_INDIE_RENDER_TECHNIQUES.md#measure-the-actual-renderer)
