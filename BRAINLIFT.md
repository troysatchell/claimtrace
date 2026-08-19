# Brainlift — claimtrace (in progress, 2026-08-18)

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

**4. Not yet shown.** The QLoRA run (the brief's configuration) is training; the LoRA row above is the bf16
comparison. The data-efficiency curve is not done.

## Minimum viable dataset size — pending

Sweep: N = 270 / 135 / 67 / 33 training conversations, nested subsets, identical config (500 optimizer
steps, effective batch 4). Log-2 spacing: the smallest point (~330 prefix rows, ≈5 epochs at the fixed
step budget) is where a 1.7B model would start to memorize conversations instead of the rule; the largest
point is everything we generated. The stated minimum viable N will be the smallest N whose spec adherence
and self-report→KNOWN rate are within noise of N=270. Source: `results/data-efficiency-curve/table.md`, `curve.png`.

## Failure modes → v2 data change (Early submission)

The tuned model credits wrong-but-topical statements ("I'd use an inner join for that" → KNOWN: inner
join) and situational facts. Cause: the dataset has no incorrect-attempt turns, so the model learned
"topical statement → KNOWN". Also, 7 broken scenarios are replies that hit the 512-token cap before the
ledger line, and the prose on the verdict turn over-credits. v2 dataset: add a `wrong_attempt` shape, add
plain-language demonstrations, add a brevity constraint, and make the verdict-turn prose list only KNOWN
items. Training config unchanged.

## What I believe now

The behavior lives in the data. The two hard parts were (a) stopping the teacher from making the frontier
mistake — solved by removing the judgment from its job, not by better instructions — and (b) making the
eval tell provenance from format, so a tuned model could not pass by copying or by withholding. Everything
after that was a button press.
