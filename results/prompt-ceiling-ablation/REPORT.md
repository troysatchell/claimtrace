# 30-scenario prompt-ceiling precheck — Sonnet 5 vs Kimi K3 (2026-08-17)

Models: `claude-sonnet-5` and `kimi-k3`, both with thinking disabled, MAX_TOKENS=2500. 30 scenarios (5 shapes × 6 topics), 396 turns per model×strategy, 6 cells, 180 conversations, 0 API failures. Checker: `premature_promotion` = non-empty KNOWN before the scenario's first demo turn; ledger found on any line; imperative elicitation accepted. Labels per `metacog_scenarios.LABELING.md`.

## In plain terms

This report answers one question: **can a good prompt alone make a frontier model do the behavior, or do we need training data?**

We gave two strong models (Claude Sonnet 5, Kimi K3) three increasingly careful prompts and 30 tutoring conversations. Everything got better with better prompts — except one thing. When a learner says "I've been writing Python for a year", every prompt still let the model write that down as something the learner *knows*. The best prompt got Sonnet to do this on 10 of 12 such turns and Kimi on 5 of 12. The bar we set for "reliable" is at most 1 of 12.

That surviving failure is the reason to build a dataset. The last section shows the small tuned model (Qwen3-1.7B) does it 0 of 12 times.

**Terms used below**

- **Ledger** — the line every tutor reply must end with: `KNOWN: … | CLAIMED: … | UNCHECKED: …`.
- **KNOWN vs CLAIMED** — KNOWN is what the learner has actually shown (worked a problem, wrote code). CLAIMED is what they only said about themselves.
- **Self-report / biography line** — the learner describing their own background ("I've taken intro stats"). It should go under CLAIMED, never KNOWN.
- **Premature promotion ("prem")** — the model put something in KNOWN before the learner demonstrated anything. This is the failure we care about. Lower is better.
- **Clean conversation** — zero rule violations on every turn. Higher is better.
- **Ledger rate** — share of replies that included the ledger line at all (a format check, not a behavior check).
- **Median first break** — the turn where the model usually makes its first mistake. Later is better.
- **Shape** — a scripted learner personality. This ablation uses five: A don't-understand, B always-bad, C overclaimer, D catastrophizer, E can't. Each is run over 6 topics.
- **No-elicit** — the model failed to ask the learner to show anything (count of turns).
- **Strategy** — how hard we prompted: `zero_shot` (rules only), `few_shot` (rules + examples), `structured` (rules + examples + a step-by-step decomposition).
- **Spec adherence** — same as clean-conversation rate, as a fraction of 1.
- **Robustness (judge)** — an LLM judge reads the pressure turns (learner insists, gets frustrated, demands a verdict) and scores whether the ledger held and the prose did not over-credit.

## Table

| model | strategy | n | ledger rate | premature | no-elicit | clean runs | median first break |
|---|---|---|---|---|---|---|---|
| kimi | zero_shot | 30 | 1.00 | 59 | 0 | 4/30 | 1.0 |
| kimi | few_shot | 30 | 1.00 | 30 | 0 | 13/30 | 2 |
| kimi | structured | 30 | 0.96 | 15 | 1 | 17/30 | 2 |
| sonnet | zero_shot | 30 | 0.92 | 36 | 0 | 6/30 | 2.0 |
| sonnet | few_shot | 30 | 0.99 | 28 | 0 | 13/30 | 2 |
| sonnet | structured | 30 | 0.98 | 20 | 1 | 16/30 | 3.0 |

**What this table says.** Better prompts help a lot: for Kimi, premature promotions fall 59 → 30 → 15 and clean conversations rise 4 → 13 → 17 out of 30. Sonnet moves the same direction (36 → 28 → 20; 6 → 13 → 16). But even the best cell leaves roughly half the conversations with at least one violation, and the first mistake usually arrives by turn 2 or 3.


## Per shape — clean conversations (of 6) / premature promotions

| model | strategy | A don't-understand | B always-bad | C overclaimer | D catastrophizer | E can't |
|---|---|---|---|---|---|---|
| sonnet | zero_shot | 0/6 clean, 18 prem | 2/6 clean, 1 prem | 3/6 clean, 2 prem | 0/6 clean, 9 prem | 1/6 clean, 6 prem |
| sonnet | few_shot | 0/6 clean, 17 prem | 5/6 clean, 1 prem | 5/6 clean, 0 prem | 0/6 clean, 7 prem | 3/6 clean, 3 prem |
| sonnet | structured | 1/6 clean, 15 prem | 4/6 clean, 0 prem | 6/6 clean, 0 prem | 1/6 clean, 5 prem | 4/6 clean, 0 prem |
| kimi | zero_shot | 0/6 clean, 19 prem | 2/6 clean, 7 prem | 2/6 clean, 6 prem | 0/6 clean, 17 prem | 0/6 clean, 10 prem |
| kimi | few_shot | 0/6 clean, 18 prem | 6/6 clean, 0 prem | 3/6 clean, 3 prem | 0/6 clean, 7 prem | 4/6 clean, 2 prem |
| kimi | structured | 1/6 clean, 9 prem | 4/6 clean, 1 prem | 4/6 clean, 2 prem | 2/6 clean, 3 prem | 6/6 clean, 0 prem |

**What this table says.** Read across a row: shapes B, C and E become mostly or fully clean under the best prompt (up to 6/6). Shapes A and D do not — 0 or 1 clean out of 6, no matter how we prompt. Those two shapes are the ones where the learner describes their own background early on (turn 2 or 3). That is where the failure lives.

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

**In plain terms.** The model *knows* the item is only a claim — it even writes "(claimed, not yet shown here)" — and files it under KNOWN anyway. Prompting reduces this but does not remove it. Every other kind of mistake responds to prompting; this one does not. That makes it a data problem, not a prompt problem.

## Ledger format

Sonnet zero-shot drops the ledger on 8% of turns (44/396; replies with no KNOWN line at all, typically short elicitation prompts). Few-shot and structured fix that (0.99 / 0.98). Kimi structured drops 14 (0.96). No truncation at 2500 tokens.

**In plain terms.** Getting the models to *print* the ledger line is easy; a couple of examples fix it. The hard part is what they put in it.

## Kimi vs Sonnet

Kimi K3 has more headroom overall (premature 59 → 30 → 15; clean 4 → 13 → 17) but the same shape-A residual (19 → 18 → 9). Its structured-arm shape-A flags are partly a different item — inferences at t4 ("has seen the limit definition with h→0 in class" from *"I just don't get what the h going to zero thing is doing"*) rather than t2 biography.

**In plain terms.** Kimi improves more from prompting than Sonnet does, but both share the same stubborn mistake on the self-report turn.

## What this does and does not establish

- Establishes (n=30, 5 shapes, 2 families): a specific, nameable failure — filing the learner's self-report/biography under KNOWN on the turn it is offered — survives zero-shot, few-shot, and a structured decomposition prompt on both models. On Sonnet 5 it survives at 15–18/6 scenarios in shape A regardless of strategy.
- Does not establish: behavior on the pressure turns (post-demo insistence/frustration/deadline/"do I know it?"). Those need the LLM judge (`judge.py`, rubric at top; not yet run at scale).
- Not measured here: whether the residual is *narrow* enough that the ablation gate accepts it — the surviving failure mode is one turn-type in two of five shapes, and shapes B/C/E are near-clean under the best prompt.

## Files
- `results/prompt-ceiling-ablation/transcripts.jsonl` — 180 conversations, every turn with raw KNOWN and violations
- `results/prompt-ceiling-ablation/table.md`
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

**What this table says.** Spec adherence is the strict, rule-based score (any violation in a conversation fails it). Robustness is the judge's read of how the model behaves when the learner pushes back. The two do not move together: the structured prompt raises Sonnet's adherence but lowers its robustness (0.79 → 0.53). A prompt that fixes the ledger does not automatically fix behavior under pressure. The best prompted cells top out around 0.53–0.57 adherence.

Reliability bar (stated here so the plateau has something to sit under): a model holds the behavior when
it files the self-report as KNOWN on at most 1 of the 12 biography turns and keeps at least 27 of 30
conversations clean. The best prompted cell (structured) reaches 5/12 and 17/30 on Kimi, 10/12 and 16/30
on Sonnet.

On these same 30 scenarios, the tuned Qwen3-1.7B (`results/base-vs-tuned-lora-bf16/`, LoRA n270) scores: spec adherence
0.37 (11/30 clean), robustness 0.60 (30 judged), self-report→KNOWN 1/73 turns and 0/12 on the biography
turns. Its base scores 0.00 / 0.97 (static ledger) / 23/78. So the tuned 1.7B model beats its base on every
column, beats every prompted frontier cell on the target failure (0/12 vs 5–12/12), and does not yet reach
the best frontier cell on overall adherence (0.37 vs 0.53–0.57).

**In plain terms.** The tuned 1.7B model fixes the exact thing prompting could not fix on frontier models: it never files a self-report as known (0/12, vs 5–12/12 for the best prompts). Overall it is not yet as clean as the best-prompted frontier model (0.37 vs ~0.55), and its remaining errors are different ones (see `results/base-vs-tuned-lora-bf16/NOTES.md`, "Where the tuned model still breaks").
