# Exact-source remote CI acceptance

Both workflows passed for source
`02031d2c0132131a43ce55b2180527585f3306a7`:

| Workflow | Run | Actual completed steps |
| --- | --- | --- |
| Native foundation | [40057158770](https://github.com/occult-kranti/ANDOLAN/actions/runs/40057158770) | **42/42 success** |
| Native candidate | [40057158784](https://github.com/occult-kranti/ANDOLAN/actions/runs/40057158784) | **15/15 success** |

[completion.json](completion.json) pins the exact run/job IDs, attempt, source,
branch, every step result, timestamps and artifact metadata. The raw API
responses are retained. Intermediate foundation observations listed 41 steps;
GitHub added `Complete job` on completion. The final total is 42, not an estimate.

Only the **206,015-byte candidate evidence artifact** was downloaded. Its SHA-256
matches the API's recorded digest:
`45336dad7db6bfdfc7ffc47157fc9ebcec40c50a7526fb54ce5e61094ff6919c`.
The [download receipt](candidate-evidence/receipt.json) and [14-check evidence
review](candidate-evidence/verification.json) preserve the results and limits.

The evidence's exported source census matches committed Confluence, friendly
camera helper and garden source/assets. Its reported Linux and Windows PCKs
include the new compiled helper and garden, each with **558 entries and
77,892,680 bytes**, SHA-256
`6b93ecd7e56a1b7acadc483920e376dda5e20852a98c79f0241b5517521e073b`.
These are verified readings of CI-produced records, not fresh local downloads
or execution of those resource packs.

The foundation acceptance artifact is 13,053,394 bytes and was not downloaded.
The Linux and Windows game archives were not downloaded or executed here.
Their exact metadata and expiry dates remain in the completion receipt; the
candidate retains `built_candidate_requires_independent_qualification` status.

CI success does not establish public release acceptance, ordinary native input,
physical-GPU performance, listening, human game feel or commercial art quality.
W2 owns the current ordinary-input journey; root owns public delivery and the
combined acceptance decision. No runtime source was changed during this review.
