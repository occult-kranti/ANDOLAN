# Historical full-body study — binary evidence unavailable after recovery

The earlier full-body experiment was reported with animation library SHA-256
`276c210273e9524a4f13987e8940678e662be772245bbbb19cd32f83f216a3dc`.
That library, its intermediate target mesh and numerical reports were lost
when the cloud workspace was replaced. This directory contains historical notes
only; it must not be cited as a preserved or freshly verified binary archive.
The maintained reproduction entry point is `../reproduce_motion.py`.

Actual rendered review of the preceding full-body candidate
`cc5285a9f37d7985297f5c6b21a1006de6b5c3d6629fd15c4a84043bff439aae`
showed Rama's draw hand held behind his head while the bow arm swung across his
torso. The later full-body candidate retained that unsuitable upper-body mapping,
with a separately tested seam-velocity correction. Neither was promoted to
runtime. Passing finite-transform, bone-length and seam checks did not establish
a suitable weapon pose.

The maintained idle/run adaptation keeps useful source hip, spine and leg
motion, while retaining Rama's original bind/rest arms, hands and weapon fit.
Its fresh render still shows open fingers and stiff carry, so it is also
unpromoted. The firearm-derived aim pose remains a provisional reference study.

`reproduce_motion.py --full-body-study` can bake a new comparator against the
available restored hero. Set distinct `--output` and `--library` paths so it
cannot overwrite the current candidate. Such a new bake has its own hashes and
does not recreate the lost historical mesh or prove the old test results.
