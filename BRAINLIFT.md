# Brainlift — claimtrace (in progress; updated 2026-08-18)

## Behavior thesis

A tutor should keep two ledgers, not one: what the learner has **demonstrated** in this conversation
and what the learner has merely **claimed** about themselves. Frontier models collapse the two —
they file "I've been writing Python for a year" under KNOWN, often while annotating it as a claim
(`KNOWN: has balanced equations before (claimed, not yet shown here)`) — and no prompt we tried
removes it. The thesis: **this is a data problem, not a prompt problem** — a few hundred filtered
conversations in which every promotion into KNOWN is earned by a demonstration, and every
self-report is copied into CLAIMED, will make a 1.7B model hold the distinction more reliably than a
prompted frontier model does.

Behavior Spec (`BEHAVIOR_SPEC.md`, two sentences): *An item may appear in KNOWN only after the learner
has demonstrated it in their own work during this conversation. A learner's self-report about their
background, experience, or ability is a CLAIMED item and must never be recorded as KNOWN, regardless
of how plausible it is, how many times it is repeated, or how you annotate it.*

## Evidence, in order

**1. Prompting has a ceiling (Ablation 1, n=30, `results/full-30-combined/ANALYSIS.md`).**
Claude Sonnet 5 and Kimi K3 × zero-shot / few-shot / structured. Best strategy still files the
learner's biography under KNOWN on the turn it is offered: Sonnet 10/12, Kimi 5/12 (structured);
12/12 for both under zero- and few-shot. Every other shape prompts to near-clean; this one does not.

**2. The teacher has the same failure, and the fix is mechanical.** Asked to *judge* whether a
self-report belongs in KNOWN, the teacher fails 10–12/12; asked to *copy* the previous KNOWN
byte-for-byte and append to CLAIMED, it succeeds, and a mechanical filter (`ledger.py`) deletes the
rest. The same move fixed under-promotion on demonstrations (drop rate 82% → 0% once the teacher was
handed the exact KNOWN item each demonstration earns). Dataset: 300 conversations / 3,301 turns,
0.2% dropped, 0 hedged KNOWN items (`data/drop_report.json`).

**3. Data → behavior held on the first real run (`results/mvp/NOTES.md`).** Qwen3-1.7B, LoRA,
270 training conversations, greedy eval on 41 held-out scenarios (498 turns; the 30 ablation
scenarios plus 6 hard-variant scenarios in domains absent from training and 5 ordinary-only
controls):

| | base | tuned |
|---|---|---|
| clean conversations | 0/41 | 20/41 |
| self-report → KNOWN (turns with a ledger) | 0.24 | **0.01** |
| self-report → KNOWN on the 12 ablation turns (frontier best: 10/12) | 2/12 | **0/12** |
| positive self-report right after a demo, novel domains (shape F) | – | **0/18** |
| hedged KNOWN items | 1 | 0 |
| demonstrations credited (1 − missed) | 0.05 | 0.87 |
| ordinary questions interrogated (over-trigger control) | 0.00 | 0.01 |

The base model holds the *format* perfectly (ledger on 100% of turns) and the *provenance* not at
all, so the delta is behavior, not formatting. The tuned model does not pass by never promoting: it
credits 87% of demonstrations and answers plain questions directly.

**4. What is not yet shown.** Robustness under pressure (the LLM-judge column) — both judge keys were
dead at eval time; the transcripts are saved and `eval.py --rejudge` fills the column without
regeneration. QLoRA (the brief's configuration) is training now; the LoRA row above is the bf16
comparison and will be reported next to it.

## Minimum viable dataset size — pending the curve

Data-efficiency sweep at N = 270 / 135 / 67 / 33 training conversations (nested subsets, identical
config: 500 optimizer steps × effective batch 4; `train.py --sweep`, `sweep.py`,
`results/sweep-qlora/`). Log-2 spacing was chosen because the smallest point (~330 prefix rows,
≈5 epochs at the fixed step budget) is where a 1.7B model would start memorizing conversations
rather than the rule, and the largest is everything we generated. The stated minimum viable N will
be the smallest N whose spec adherence and self-report→KNOWN rate are within noise of the N=270 run
on this eval set — to be filled in from `results/sweep-qlora/table.md` and `curve.png`.

## Failure modes diagnosed from the MVP eval → v2 data change (planned, Early submission)

The tuned model credits **wrong-but-topical statements** ("I'd use an inner join for that" → KNOWN:
inner join) and situational facts. Cause: the dataset has no incorrect-attempt turns — every
demonstration it saw was correct — so it learned "topical statement → KNOWN". v2 dataset: add a
`wrong_attempt` shape (ledger unchanged, tutor probes) and plain-language / question-phrased
demonstrations; training config unchanged. Second, length: 7 broken scenarios are replies that hit
the 512-token cap before the ledger line — a generation-prompt brevity constraint, also data-side.

## What I believe now

The behavior lives in the data. The two hardest parts were (a) getting the *teacher* to stop making
the frontier mistake — solved not by better instructions but by removing the judgment from its job —
and (b) making the eval able to tell provenance from format, so a tuned model could not pass by
copying or by withholding. Everything downstream of that was a button press.
