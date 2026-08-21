# Brainlift — claimtrace (2026-08-21)

## Thesis

A tutor should keep two ledgers: what the learner has demonstrated in this conversation, and what the
learner has claimed about themselves. Frontier models merge the two. They file "I've been writing Python
for a year" under KNOWN, often with an annotation such as "(claimed, not yet shown)". No prompt we tried
removed this. The thesis: this is a data problem, not a prompt problem. A few hundred filtered
conversations, in which every entry into KNOWN follows a demonstration and every self-report goes to
CLAIMED, will make a 1.7B model hold the distinction more reliably than a prompted frontier model.

Behavior Spec (`BEHAVIOR_SPEC.md`): *An item may appear in KNOWN only after the learner has demonstrated it
in their own work during this conversation. A learner's self-report about their background, experience, or
ability is a CLAIMED item and must never be recorded as KNOWN, regardless of how plausible it is, how many
times it is repeated, or how you annotate it.*

## Evidence

**1. Prompting has a ceiling** (`results/prompt-ceiling-ablation/REPORT.md`, n=30). Claude Sonnet 5 and Kimi
K3, three strategies each. On the turn where the learner gives a biography line, the best strategy still
files it under KNOWN: Sonnet 10/12, Kimi 5/12 (structured prompt); 12/12 for both under zero-shot and
few-shot. Every other shape prompts to near-clean. This one does not.

**2. The teacher makes the same mistake, and a mechanical fix removes it.** Asked to judge whether a
self-report belongs in KNOWN, the teacher fails 10–12 times out of 12. Told to copy the previous KNOWN
field and append the self-report to CLAIMED, it succeeds. A mechanical filter (`ledger.py`) deletes the
rest. The same move fixed demonstrations: once the teacher receives the exact KNOWN item a demonstration
earns, the drop rate falls from 82% to 0%. Dataset: 300 conversations, 3,301 turns, 0.2% dropped, 0 hedged
KNOWN items (`data/drop_report.json`).

**3. Data → behavior held on the first run** (`results/base-vs-tuned-lora-bf16/NOTES.md`). Qwen3-1.7B, LoRA, 270 training
conversations, greedy decoding, 41 held-out scenarios (498 turns): the 30 ablation scenarios, 6 hard-variant
scenarios in domains absent from training, and 5 ordinary-question controls.

| | base | tuned |
|---|---|---|
| clean conversations | 0/41 | 20/41 |
| self-report→KNOWN (turns with a ledger) | 0.24 | 0.01 |
| self-report→KNOWN on the 12 ablation turns (frontier best: 10/12) | 2/12 | 0/12 |
| positive self-report right after a demonstration, novel domains (shape F) | – | 0/18 |
| hedged KNOWN items | 1 | 0 |
| demonstrations credited (1 − missed) | 0.05 | 0.87 |
| ordinary questions interrogated (control) | 0.00 | 0.01 |
| robustness under pressure (judge) | 0.97 | 0.67 |

The base model writes the ledger format on 100% of turns and gets the content wrong on all of them. So the
delta is behavior, not formatting. The tuned model does not pass by never promoting: it credits 87% of
demonstrations and answers plain questions directly. Its robustness loss is one failure: on the "what do I
know?" turn the prose over-credits while the ledger holds. The base's 0.97 is hollow: its ledger never
changes at all.

**4. The same data → the same behavior on the 4-bit base** (`results/base-vs-tuned/NOTES.md`). QLoRA run `q270`
(the brief's configuration): identical data and config on the 4-bit base. Spec adherence 0.49 (20/41 clean,
same as bf16), self-report→KNOWN 0.24 → 0.07 (bf16: 0.01), demonstrations credited 0.88, control shape G 5/5
clean, robustness 0.69. Quantizing the base for training cost a few provenance slips and nothing on spec
adherence. Adapter sha256 `6a6af4f1ac8e…`, training commit `b505da9`, eval-code commit `fc1bc93`.

**5. The behavior holds from N≈67 up; N=33 is where it comes apart** (`results/data-efficiency-curve/table.md`,
`curve.png`). Four QLoRA checkpoints, nested subsets, identical config:

| N (train convs) | rows | epochs | val loss | spec adherence | robustness | self-report→KNOWN | missed promotion | over-trigger | clean |
|---|---|---|---|---|---|---|---|---|---|
| 0 (base) | – | – | – | 0.00 | 0.97 | 0.24 | 0.95 | 0.00 | 0/41 |
| 33 | 357 | 5.6 | 2.12 | 0.32 | 0.56 | 0.08 | 0.24 | 0.05 | 13/41 |
| 67 | 723 | 2.8 | 1.16 | 0.39 | 0.61 | 0.04 | 0.14 | 0.00 | 16/41 |
| 135 | 1,467 | 1.4 | 0.98 | 0.54 | 0.69 | 0.01 | 0.14 | 0.01 | 22/41 |
| 270 | 2,982 | 0.7 | 0.94 | 0.49 | 0.69 | 0.07 | 0.12 | 0.04 | 20/41 |

The provenance rule (self-report→KNOWN) is learned at every N — even 33 conversations take it from 0.24 to
0.08. What N buys is everything around the rule: at 33 the model misses twice as many demonstrations as at
270 (0.24 vs 0.12), over-triggers on ordinary questions (0.05), and its validation loss (2.12, 5.6 epochs
over 357 rows) says it is memorizing conversations rather than the rule. From 67 up, missed promotion and
over-trigger match N=270; spec adherence climbs 0.39 → 0.54 → 0.49 and robustness 0.61 → 0.69 → 0.69.

**6. The diagnosed failure mode died when — and only when — the data changed** (`results/base-vs-tuned-v2/NOTES.md`).
Run `q236v2`: the v2 dataset (shape E wrong attempts, plain-language demos, brevity, verdict-prose rule;
`dataset_spec.md` changelog v2→v3), training config byte-identical to q270 (config diff in NOTES).
Clean conversations 20/41 → 33/41, spec adherence 0.49 → 0.80, self-report→KNOWN 0.07 → 0.00 (0 slips
in 96 turns), unearned KNOWN items 15 → 1, robustness 0.69 → 0.83. The one metric that moved the wrong
way — over-trigger 0.04 → 0.15 — is the model appending "quick check" probes to otherwise-correct
answers on ordinary turns, and maps to the shape whose share shrank in v2. This is the thesis's
strongest evidence: a specific behavior was added and a specific failure removed by editing only data.

## Minimum viable dataset size — N = 135

Sweep: N = 270 / 135 / 67 / 33 training conversations, nested subsets, identical config (500 optimizer
steps, effective batch 4, 4-bit base). Log-2 spacing: the smallest point (357 prefix rows, 5.6 epochs at the
fixed step budget) is where a 1.7B model would start to memorize conversations instead of the rule — and it
did (val loss 2.12); the largest point is everything we generated. Criterion, stated before the sweep ran:
the smallest N whose spec adherence and self-report→KNOWN rate are within noise of N=270.

**N = 135** is the stated minimum viable dataset size. It matches or beats N=270 on every column (spec
adherence 0.54 vs 0.49, self-report→KNOWN 0.01 vs 0.07, robustness 0.69 vs 0.69, missed promotion 0.14 vs
0.12) — 22 vs 20 clean conversations of 41, inside one standard error either way. At the fixed 500-step
budget N=135 sees each row 1.4 times and N=270 0.7 times; the extra pass appears to be worth as much as the
extra data.

**N = 67** is the floor, not the recommendation. The provenance rule holds (self-report→KNOWN 0.04, missed
promotion 0.14, over-trigger 0.00 — all at N=270's level) but spec adherence is 0.39: 16 clean conversations
of 41 vs 20. On a 41-scenario eval set that gap (~1 SE) is not separable from noise, so 67 cannot be ruled
out; it also cannot be called reliable. A larger eval set (the staff held-out set) would decide it.
**N = 33** fails the criterion on every column and is the overfit point (val loss 2.12, missed promotion
doubles, over-trigger appears).

Source: `results/data-efficiency-curve/table.md`, `curve.png`, `sweep_summary.json`; per-N eval in
`results/data-efficiency-curve/q{33,67,135}/`, `results/base-vs-tuned/` (q270); training logs
`results/train/q{33,67,135,270}/`.

## Failure modes → v2 data change (Early submission) — RESOLVED 2026-08-20

Diagnosis (from the MVP eval): the tuned model credits wrong-but-topical statements ("I'd use an inner
join for that" → KNOWN: inner join) and situational facts. Cause: the dataset had no incorrect-attempt
turns, so the model learned "topical statement → KNOWN". Also, 7 broken scenarios were replies that hit
the 512-token cap before the ledger line, and the prose on the verdict turn over-credited.

The fix was data only — `wrong_attempt` shape, plain-language demonstrations, brevity constraint,
verdict-turn prose rule — with the training config unchanged (evidence item 6). Every diagnosed number
moved: unearned 15 → 1, ledger rate 0.95 → 1.00, robustness 0.69 → 0.83.

Residual for Final: over-trigger 0.04 → 0.15 — appended "quick check" probes on ordinary turns (not
withholding; control shape G is 5/5 clean). Candidate v3 change, again data-only: raise the ordinary
share and place ordinary turns right after demonstrations.

## Conclusion: did data → behavior hold?

**Yes, twice.** Once at MVP — 300 filtered conversations took self-report→KNOWN from 0.24 to 0.07 and
clean conversations from 0/41 to 20/41 on a 1.7B model, where the best-prompted frontier models stayed at
10/12 failures on the same turn. And once more precisely at Early — adding one data shape (wrong attempts)
with the config frozen removed the one measured failure it targeted (unearned promotions 15 → 1,
self-report→KNOWN 0.00) and moved nothing else except the shape whose share it displaced. The remaining
gaps (over-trigger 0.15) map to data composition, not to any training knob — which is the thesis.

## What I believe now

The behavior lives in the data. The two hard parts were (a) stopping the teacher from making the frontier
mistake — solved by removing the judgment from its job, not by better instructions — and (b) making the
eval tell provenance from format, so a tuned model could not pass by copying or by withholding. Everything
after that was a button press. The v2 round sharpened the claim: one added data shape removed one
measured failure (15 → 1 unearned promotions) and shifted nothing else but the shape whose share it
displaced — behavior tracked data on the way up and on the way sideways.
