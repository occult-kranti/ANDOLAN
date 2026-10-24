# Independent review of the publication auditor

The corrected root-authored auditor passes **12 distinct review checks** using
actual temporary Git commits and real loopback HTTP responses. This is a local
validator review, not an audit of the public website.

The original auditor `4c74d7b1…` accepted the valid control and correctly refused
a missing source field, wrong baseline pin, incomplete inventory, malformed
JSON syntax and altered delivered JavaScript. Five valid-JSON/non-object cases
instead raised `AttributeError` before saving the failed receipt: publication
arrays/null/strings and snapshot arrays/null. This was a failure-reporting defect;
it did not falsely accept changed static bytes.

Root added decoded-object/source guards and a full observed-commit check.
Against successor `b3f52784…`, the **unchanged original eleven-case probe** passes.
A separate extended run adds a scalar `snapshot.source` case, which also returns
a saved failed receipt. Its eleven repeated checks are not counted again.

- [Original source witness](auditor-original.py), [failed review](original-r1/report.json)
- [Unchanged probe](probe.py), [corrected review](successor-r1/report.json)
- [Extended probe](probe_source_scalar.py), [scalar-source review](successor-scalar-r1/report.json)
- [Exact hashes and retained artifact census](review.json)

The committed approved-file census, publisher-byte identity and delivered file
hash checks are coherent for the stated scope. The auditor checks browser entry
availability. It does not independently recover or compare the full assembled
browser baseline census; that remains the publisher receipt's responsibility.
Historical frozen publication auditors and their receipts remain untouched.
