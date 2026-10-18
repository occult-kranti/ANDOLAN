# Current Volley fixture maintenance

The unchanged17-check fixture reproduces **16/17 locally** on accepted motion5023: only its obsolete8c377 content-hash readiness condition fails. All16 other behavior/source-stability checks pass. Replacing that literal with the live Script's expected resource path, Resource identity and loaded-source SHA binding yields **17/17**, clean logs and exit0. Every original readiness/behavior predicate and tolerance remains unchanged; no effects or runtime code changed.

Both runs use the official f64 Godot4.6.3 binary through the existing catalog, warmup200 and fixed60Hz. All nonfixture source/import pins are identical between runs and stable within each run. Every recorded gameplay-script byte matches b4d; the16 other assertion results are identical. Exact fixture snapshots, reports, timelines, events and logs are preserved.

CI39113365079 on b4d reports the Volley suite failed;17 is its total check count. The remote assertion artifact could not be retrieved: the managed HTTP redirect to the Azure artifact host returned403. The archived failed-step log does not identify an assertion. This report therefore distinguishes the authorized local reproduction from the unavailable remote assertion detail and does not claim a new whole-CI pass.

The maintained suite now admits reviewed current motion without a perpetually stale content literal, while requiring that the actual instance is the expected resource and that its loaded source equals the reported current hash. Historical source-specific8c reports in the original W5 packet are unchanged. Existing motion26/27 limits, current art limits, raster, audible quality and human feel remain separate.
