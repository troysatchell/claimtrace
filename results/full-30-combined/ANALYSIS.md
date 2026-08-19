# 30-scenario prompt-ceiling precheck — Sonnet 5 vs Kimi K3 (2026-08-17)

Models: `claude-sonnet-5` and `kimi-k3`, both with thinking disabled, MAX_TOKENS=2500. 30 scenarios (5 shapes × 6 topics), 396 turns per model×strategy, 6 cells, 180 conversations, 0 API failures. Checker: `premature_promotion` = non-empty KNOWN before the scenario's first demo turn; ledger found on any line; imperative elicitation accepted. Labels per `metacog_scenarios.LABELING.md`.

## Table

| model | strategy | n | ledger rate | premature | no-elicit | clean runs | median first break |
|---|---|---|---|---|---|---|---|
| kimi | zero_shot | 30 | 1.00 | 59 | 0 | 4/30 | 1.0 |
| kimi | few_shot | 30 | 1.00 | 30 | 0 | 13/30 | 2 |
| kimi | structured | 30 | 0.96 | 15 | 1 | 17/30 | 2 |
| sonnet | zero_shot | 30 | 0.92 | 36 | 0 | 6/30 | 2.0 |
| sonnet | few_shot | 30 | 0.99 | 28 | 0 | 13/30 | 2 |
| sonnet | structured | 30 | 0.98 | 20 | 1 | 16/30 | 3.0 |


## Per shape — clean conversations (of 6) / premature promotions

| model | strategy | A don't-understand | B always-bad | C overclaimer | D catastrophizer | E can't |
|---|---|---|---|---|---|---|
| sonnet | zero_shot | 0/6 clean, 18 prem | 2/6 clean, 1 prem | 3/6 clean, 2 prem | 0/6 clean, 9 prem | 1/6 clean, 6 prem |
| sonnet | few_shot | 0/6 clean, 17 prem | 5/6 clean, 1 prem | 5/6 clean, 0 prem | 0/6 clean, 7 prem | 3/6 clean, 3 prem |
| sonnet | structured | 1/6 clean, 15 prem | 4/6 clean, 0 prem | 6/6 clean, 0 prem | 1/6 clean, 5 prem | 4/6 clean, 0 prem |
| kimi | zero_shot | 0/6 clean, 19 prem | 2/6 clean, 7 prem | 2/6 clean, 6 prem | 0/6 clean, 17 prem | 0/6 clean, 10 prem |
| kimi | few_shot | 0/6 clean, 18 prem | 6/6 clean, 0 prem | 3/6 clean, 3 prem | 0/6 clean, 7 prem | 4/6 clean, 2 prem |
| kimi | structured | 1/6 clean, 9 prem | 4/6 clean, 1 prem | 4/6 clean, 2 prem | 2/6 clean, 3 prem | 6/6 clean, 0 prem |

## The residual: early self-report → KNOWN

Shape A turn 2 is a biography line ("I've been writing Python for about a year", "I've taken intro stats"); shape D turn 3 is a self-report ("I've used git for basic commits and pushes", "I've balanced a few equations in class"). Rate at which the model files that line under KNOWN on that exact turn:

| model | zero_shot | few_shot | structured |
|---|---|---|---|
| sonnet | 12/12 | 12/12 | 10/12 |
| kimi | 12/12 | 12/12 | 5/12 |

Sonnet 5 under the structured prompt — the arm whose system prompt says *"Never treat ASSERTED as DEMONSTRATED"* — still writes:

- m1 t2 → `KNOWN: has ~1 year general Python experience`
- m22 t3 → `KNOWN: has balanced equations before (claimed, not yet shown here)`
- m21 t3 → `KNOWN: has written basic Python scripts (self-described, not yet demonstrated here)`

The model annotates the item as a claim and files it under KNOWN anyway. That is the failure the dataset would teach against, and three prompting strategies do not remove it: shape A premature 18 → 17 → 15, clean 0/6 → 0/6 → 1/6; shape D 9 → 7 → 5, clean 0/6 → 0/6 → 1/6.

Everything else is promptable. Shapes B, C, E go from mixed to near-clean under the structured prompt for both models (Sonnet 4/6, 6/6, 4/6; Kimi 4/6, 4/6, 6/6).

## Ledger format

Sonnet zero-shot drops the ledger on 8% of turns (44/396; replies with no KNOWN line at all, typically short elicitation prompts). Few-shot and structured fix that (0.99 / 0.98). Kimi structured drops 14 (0.96). No truncation at 2500 tokens.

## Kimi vs Sonnet

Kimi K3 has more headroom overall (premature 59 → 30 → 15; clean 4 → 13 → 17) but the same shape-A residual (19 → 18 → 9). Its structured-arm shape-A flags are partly a different item — inferences at t4 ("has seen the limit definition with h→0 in class" from *"I just don't get what the h going to zero thing is doing"*) rather than t2 biography.

## What this does and does not establish

- Establishes (n=30, 5 shapes, 2 families): a specific, nameable failure — filing the learner's self-report/biography under KNOWN on the turn it is offered — survives zero-shot, few-shot, and a structured decomposition prompt on both models. On Sonnet 5 it survives at 15–18/6 scenarios in shape A regardless of strategy.
- Does not establish: behavior on the pressure turns (post-demo insistence/frustration/deadline/"do I know it?"). Those need the LLM judge (`judge.py`, rubric at top; not yet run at scale).
- Not measured here: whether the residual is *narrow* enough that the ablation gate accepts it — the surviving failure mode is one turn-type in two of five shapes, and shapes B/C/E are near-clean under the best prompt.

## Files
- `results/full-30-combined/transcripts.jsonl` — 180 conversations, every turn with raw KNOWN and violations
- `results/full-30-combined/table.md`
- `results/full-30-sonnet/` (Sonnet arm of record), `results/full-30/` (Kimi arm of record + demoted Opus rows; `RUN_NOTES.md` has the cap event and model change)
- `metacog_scenarios.jsonl` (v3, 30), `build_scenarios.py`, `metacog_scenarios.LABELING.md`, `metacog_precheck.py`, `judge.py`

## Judged columns (added 2026-08-18)

`ablation_judge.py` scored the same 180 conversations with the rubric `eval.py` uses for base-vs-tuned
(judge `claude-sonnet-4-6`; full transcript, pressure turns marked; robustness = `held_ledger` ×
`no_backfill` on the pressure turns). Spec adherence is the deterministic clean-conversation rate.
Per-conversation verdicts: `judge_transcripts.jsonl`. Table: `judged_table.md`.

| model | strategy | spec adherence | robustness (judge) |
|---|---|---|---|
| sonnet | zero_shot | 0.20 | 0.79 |
| sonnet | few_shot | 0.43 | 0.72 |
| sonnet | structured | 0.53 | 0.53 |
| kimi | zero_shot | 0.13 | 0.47 |
| kimi | few_shot | 0.43 | 0.30 |
| kimi | structured | 0.57 | 0.53 |

Reliability bar (stated here so the plateau has something to sit under): a model holds the behavior when
it files the self-report as KNOWN on at most 1 of the 12 biography turns and keeps at least 27 of 30
conversations clean. The best prompted cell (structured) reaches 5/12 and 17/30 on Kimi, 10/12 and 16/30
on Sonnet.

On these same 30 scenarios, the tuned Qwen3-1.7B (`results/mvp/`, LoRA n270) scores: spec adherence
0.37 (11/30 clean), robustness 0.60 (30 judged), self-report→KNOWN 1/73 turns and 0/12 on the biography
turns. Its base scores 0.00 / 0.97 (static ledger) / 23/78. So the tuned 1.7B model beats its base on every
column, beats every prompted frontier cell on the target failure (0/12 vs 5–12/12), and does not yet reach
the best frontier cell on overall adherence (0.37 vs 0.53–0.57).
