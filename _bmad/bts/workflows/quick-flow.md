# BTS Quick Flow

This workflow mirrors the spirit of BMAD Quick Flow, but for the BMAD Trading System (BTS).

1) `bmadts start`
2) `bmadts spec-wizard` (or edit `STRATEGY-SPEC.md` manually)
3) `bmadts gate` (Gate 1 -> LOGIC)
4) `bmadts logic-wizard` (or edit `LOGIC-MODEL.md`)
5) `bmadts gate` (Gate 2 -> CODE)
6) `bmadts code-wizard` (generate MT4/MT5/Pine skeletons)
7) `bmadts gate` (Gate 3 -> TEST)
8) `bmadts test-wizard` (or create `TEST-REPORT.md`)
9) `bmadts gate` (Gate 4 -> PROOF)
10) `bmadts proof` (edit `PROOF-CERTIFICATE.md`)
11) `bmadts gate` (finalize -> COMPLETE)
12) `bmadts export`

Tip: run `bmadts bmad-help` anytime.
