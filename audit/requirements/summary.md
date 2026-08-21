# Requirements audit summary — compare `early-sub` (2026-08-20, commit 909ac76a3a85)

31 VERIFIED · 10 IMPLEMENTED-UNVERIFIED · 4 PARTIAL · 3 MISSING · 6 N/A · 1 ASSUMED

Every Early-submission requirement (SLM-R43–R46) is VERIFIED: the v2 dataset (`data/v2`, 265 convs,
teacher kimi-k3) resolves the diagnosed failure mode with a byte-identical training config (unearned
15→1, self-report→KNOWN 0.00, clean 20/41→33/41), the MVP delta regenerates from the run.json pair,
and the raw judge JSONL is complete. The data-efficiency bundle (R19–R22, R45, R50) is VERIFIED with
min viable N = 135. One regression: the published HF dataset/model are v1/q270 while the artifact of
record is now v2/q236v2 (SLM-R47 PARTIAL; note on R23) — one publish command fixes both. Remaining
PARTIALs are externally blocked (staff set, demo hosting); MISSINGs are the three optional stretch
items. Full detail: REPORT.md; deltas vs after-mvp in its Delta section.

**Addendum (2026-08-20 19:25 CDT):** the R47/R23 regression flagged above is closed — q236v2 model
(rev `f6532284babb`) and v2 dataset (rev `ef2f4a2bccba`) published to HF; README/SUBMISSION updated.
Verified in `results/publish.json`. R47 → VERIFIED at next compare run.
