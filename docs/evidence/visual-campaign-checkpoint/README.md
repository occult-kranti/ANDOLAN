# Verified source checkpoint

Runtime source commit: `09dac7220544374a471a11d953b67de20ab99d7d`.
`runtime-identity.json` verifies actual committed Git blobs against the final
R4 numerical and action-film manifests. Both 506-file scopes pass; all 505
shared runtime files agree. Export configuration and the authoring map are
the two explicitly different extra inputs. Three film helpers are checked
separately. `evidence-check.json` verifies all 6,244 archived evidence files.

Run the preserved verifier with `python3 docs/evidence/visual-campaign-checkpoint/verify-checkpoint.py --repo /workspace/ANDOLAN --commit FULL_SHA`.
This does not rerun engines or confer art, native online or GPU acceptance.
The adjacent publication receipt records current GitHub CI status.

[GitHub validation passed](https://github.com/occult-kranti/ANDOLAN/actions/runs/39071056853)
for that exact source, including Linux and Windows resource-pack export checks.
The API receipt is `ci.json`; Windows execution remains separately untested.
