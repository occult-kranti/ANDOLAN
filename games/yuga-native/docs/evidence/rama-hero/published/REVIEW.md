# Published Rama hero preview

[Download the native preview](https://github.com/occult-kranti/ANDOLAN/releases/tag/yuga-rama-hero-2026-10-17).

The public tag resolves to clean package source `9eb6323ef20d8f10436a893ffcd434096686247a`. Full native foundation CI [39036000777](https://github.com/occult-kranti/ANDOLAN/actions/runs/39036000777) passed on that exact commit. This is a manual prerelease backed by those checks, not a run of an older tag-triggered release workflow.

All seven public assets were downloaded without authentication and matched both the frozen local upload manifest and GitHub's server SHA-256 digests. Both ZIPs passed CRC and every manifest payload hash; all 350 PCK entries passed integrity checks. Their game pack is identical to the exact Linux package used for the current actual-input smoke. The downloaded Linux engine also matches that reviewed binary. Both public MP4s fully decoded without error. `public-verification.json`, the verifier, expected hashes and publication metadata are retained here.

The actual Linux smoke is [recorded separately](../window/960x600-r3/REVIEW.md); downloaded-byte equivalence is not a claim that another input run occurred in the download directory. Windows was packaged and validated but remains unexecuted. The final [gameplay recording](../gameplay/REVIEW.md) and [independent review](../qa/final-review/gameplay-r3-review.json) retain their own exact source and review scopes.

The release is an offline single-hero preview. Art, secondary cloth/hair and facial expression remain below the concept target. Native online play, full-roster production, human balance/feel/listening review and physical-GPU performance remain open. Video frame rates describe sampled simulation, not measured real-time rendering. The immutable release source precedes this documentation/evidence commit; runtime files were not changed during final publication.

After verification, [cleanup](cleanup/receipt.json) removed 2,199,999,121 bytes of obsolete duplicate package files whose source commits are ancestors of the published tag. Their manifests and regeneration instructions remain. Current R3 and public downloads, source/art and capture evidence remain available. The downloaded local credential copy was removed without recording its value or hash.
