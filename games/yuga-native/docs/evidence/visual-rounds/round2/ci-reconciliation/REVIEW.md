# CI source-ancestry correction

GitHub Actions run39079055829 rejected source6046171 in the historical open-art input guard: that guard still required the current three hero GLBs to equal the pre-R2 tool inputs. Nine other authoring suites passed.

The original repair tool remains restricted to its exact historical source and shader hashes. The updated check verifies those retained bytes and requires the existing strict package provenance validator for later runtime stages. It does not accept arbitrary replacement GLBs or retarget the old repair helper. The corrected contract passes23 checks; the independent native authority/content catalog passes47 checks. Original failure logs and exact test reports are retained here. A fresh CI run is required before claiming whole-workflow success.
