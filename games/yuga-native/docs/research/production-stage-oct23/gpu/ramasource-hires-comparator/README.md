# One higher-resolution Rama comparator — provider quota blocked

The named question was whether the official model's 1024 resolution could reduce the preserved 512 candidate's pitted rear hair and softened relief. This was one bounded quality experiment, not a request to replace the canonical source or continue generating until something looked better.

Fresh official config and API info returned HTTP 200. Both advertise resolutions `512`, `1024` and `1536`, with `1024` the default. The request kept the original input hash `674077b910106cc718748530a1fa3fd4400ef959c2461b06060e41ff759c6872`, seed 71, eight sampling steps per stage and all guidance settings fixed. The intended export remained 100,000 target faces and 1024 texture size. **Only the generation resolution changed from 512 to 1024.** [The contract](comparison-contract.json) and [source diff](source-diff.patch) preserve that scope.

Session/upload/preprocessing completed. Exactly **one generation request** was submitted; the provider rejected event `ad111c290baa4eb7ba81c2b802da76fb` with the following message:

> You have exceeded your ZeroGPU quota (120s requested vs. 166s left). Try again in 23:51:35. Authenticate with a Hugging Face token for more quota - https://huggingface.co/settings/tokens

That is the provider's exact message, including its reported numbers; those numbers were not independently verified and are not a usable-resource measurement. The HTTP request returning 200 and the queue reporting `process_starts` do not establish successful GPU inference. The completed event has `success: false` and `title: ZeroGPU quota exceeded`, retained in the [actual receipt](run1/receipt.json).

**No export was submitted. No 1024 GLB was created. No quality comparison or improvement was established.** The local anonymous transport exited 1. There was no retry, login, token, paid API, alternate provider, quota workaround or general-purpose GPU allocation. The preserved [512 source and its prior evidence](../README.md) remain unchanged; its canonical GLB hash is still `0c9fe46baa0a2f6e5f9cdb9386aad1405f9f22470a729c2538142576981f5c0b`.

The next useful work is artist-controlled review/repair of the existing candidate. This attempted comparator earns no finished-art or game-completion credit. A future deliberately authorized run must inspect actual quota/access normally; this script is not an automatic retry task.

The [manifest](manifest.json), [metadata ledger](metadata-ledger.json), executed [script](trellis2_pipeline_once.py), source diff and `SHA256SUMS` retain the failure. `python3 verify.py` checks this handoff, preserved baseline and denied-event scope without network/GPU work.
