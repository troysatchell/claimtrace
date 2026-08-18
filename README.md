# claimtrace

**Claim-provenance-constrained knowledge tracing.** A tutoring model that keeps a running
ledger of what the learner has *demonstrated* versus what they have merely *claimed* — and
never lets an item cross that line because the learner asserted it, repeated it, got
frustrated, or demanded it.

Every tutor reply ends with one line:

```
KNOWN: <what the learner has demonstrated> | CLAIMED: <what they assert but have not shown> | UNCHECKED: <beliefs not yet probed>
```

The behavior spec (`ledger.py`): an item may appear in KNOWN only after the learner has
demonstrated it in their own work during this conversation. A self-report about background,
experience, or ability is CLAIMED and is never recorded as KNOWN — regardless of how
plausible it is, how often it is repeated, or how the tutor annotates it.

This repo is the full arc for the "Train Your Own Small Learning Model" brief: prove a
prompting ceiling on frontier models, generate and filter a distilled dataset, QLoRA-tune a
small open model, and evaluate base-vs-tuned with a deterministic behavioral check plus an
LLM judge. Everything here is re-runnable from the command line.

## The finding so far (prompt-ceiling ablation, n=30)

Two frontier families × three prompting strategies × 30 long tutoring scenarios (5 shapes,
396 turns per cell), scored deterministically. Both models run with thinking **disabled** so
the ablation measures plain prompting.

| model | strategy | ledger rate | premature promotions | clean conversations |
|---|---|---|---|---|
| claude-sonnet-5 | zero-shot | 0.92 | 36 | 6/30 |
| claude-sonnet-5 | few-shot | 0.99 | 28 | 13/30 |
| claude-sonnet-5 | structured | 0.98 | 20 | 16/30 |
| kimi-k3 | zero-shot | 1.00 | 59 | 4/30 |
| kimi-k3 | few-shot | 1.00 | 30 | 13/30 |
| kimi-k3 | structured | 0.96 | 15 | 17/30 |

The top line looks like headroom. The ceiling is underneath it, and it is specific: on the
turn where the learner offers a self-report (*"I've been writing Python for about a year"*,
*"I've used git for basic commits and pushes"*), the model files it under KNOWN —

| self-report → KNOWN on that turn | zero-shot | few-shot | structured |
|---|---|---|---|
| claude-sonnet-5 | 12/12 | 12/12 | 10/12 |
| kimi-k3 | 12/12 | 12/12 | 5/12 |

— even under a system prompt that says *"Never treat ASSERTED as DEMONSTRATED"*, and even
while annotating the item as a claim: `KNOWN: has balanced equations before (claimed, not
yet shown here)`. Three prompting strategies do not remove it. Every other shape prompts to
near-clean. That surviving failure is what the dataset teaches against.

Full write-up with per-shape breakdown: `results/full-30-combined/ANALYSIS.md`. Every turn
of every conversation, with the raw KNOWN field and violations, is in
`results/full-30-combined/transcripts.jsonl`.

## Pipeline

```
metacog_precheck.py      prompt-ceiling ablation (2 models × 3 strategies × N scenarios), deterministic checks
build_scenarios.py       generates metacog_scenarios.jsonl — 30 scenarios in 5 shapes, labeled (demo / new / pressure)
ledger.py                the spec + parser + checks; single source of truth imported by the pipeline
generate_dataset.py      distill from a frontier teacher, mechanical filter (delete, never repair), drop report
train_qlora.py           QLoRA on Qwen3-1.7B-Instruct via Unsloth; --n truncates with a fixed seed for the data-efficiency curve
eval.py                  one command: base-vs-tuned table + per-example judge JSONL
judge.py                 LLM-as-judge over full transcripts (per-turn verdicts + reasoning), same rubric for ablation and base-vs-tuned
```

### Run it

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=... MOONSHOT_API_KEY=...

# 1. Prompt-ceiling ablation (any cell reproducible in isolation)
python3 metacog_precheck.py --out results/run                       # everything
python3 metacog_precheck.py --models sonnet --strategies zero_shot --max-scenarios 1 --out results/one   # one point

# 2. Dataset
python3 generate_dataset.py --n 300 --out data/                     # writes dataset.jsonl + drop_report.json

# 3. Train (GPU box — Unsloth needs CUDA), four checkpoints for the curve
for N in 300 150 75 40; do python3 train_qlora.py --data data/dataset.jsonl --n $N --out ckpt/n$N; done

# 4. Eval, base vs tuned, one command
python3 eval.py --model ckpt/n300 --eval-set metacog_scenarios.jsonl --base unsloth/Qwen3-1.7B-Instruct

# 5. Judge over any transcripts file (pressure turns are where the deterministic checks are blind)
python3 judge.py --transcripts results/run/transcripts.jsonl --out results/run/
```

## Scenarios and labels

`metacog_scenarios.jsonl` — 30 scenarios, 12–15 turns each, five shapes:

| shape | opening move | n |
|---|---|---|
| A | "I want to learn X but I don't understand it at all" (biography at t2) | 6 |
| B | "I've always been bad at X" | 6 |
| C | overclaimer: "I already know X, skip it" | 6 |
| D | catastrophizer: "I'd have to understand everything first" | 6 |
| E | "I can't do this, I don't know X" | 6 |

Each turn carries three flags — `demo` (learner demonstrates knowledge in their own words),
`new` (opens a topic/problem; tutor must elicit before explaining), `pressure` (insists,
repeats, cites a deadline, is frustrated, demands an answer or verdict; no new
demonstration). Rules and history in `metacog_scenarios.LABELING.md`. The scenarios are
generated by `build_scenarios.py`; earlier label versions are kept as `.v1/.v2/.v3.jsonl`.

## Deterministic checks (`ledger.py` / `metacog_precheck.py`)

- `ledger_missing` — no `KNOWN | CLAIMED | UNCHECKED` line anywhere in the reply
- `premature_promotion` — non-empty KNOWN before the scenario's first `demo` turn
- `unearned_promotion` — KNOWN grew on a non-demo turn (`ledger.py`, dataset filter)
- `hedged_known` — a KNOWN item carrying a hedge token (`claimed`, `self-described`, `not yet
  demonstrated`, …): the signature frontier failure
- `explained_without_eliciting` — on a `new` turn, no question or imperative ask

The precheck's history matters: its first version measured its own harness (truncation,
ledger placement, a comma-split set-diff that flagged rewording). Those bugs and the fixes
are recorded in `results/full/` → `results/full-v2/` → `results/full-30-combined/`.

## Status

- Ablation: done at n=30 for Sonnet 5 and Kimi K3 (above). Earlier 5-scenario runs used
  Opus 5 and are kept under `results/full*` for reference.
- Dataset: `generate_dataset.py` smoke-tested at n=30 (`data/smoke/`); self-report drop rate
  0%, demonstration rows dropped 9/11 (`known_did_not_grow`) — see `data/smoke/drop_report.json`.
- Training / eval: not yet run — needs a CUDA box. Base-vs-tuned table pending.
- Judge: built and smoke-tested (`results/full-v2/judge-smoke/`); not yet run at scale.

## Provenance notes

- Ablation models pinned: `claude-sonnet-5`, `kimi-k3` (Moonshot). Both are thinking
  models by default; thinking is disabled in `metacog_precheck.py` so the comparison is plain
  prompting on both families. `MAX_TOKENS=2500`.
- Teacher for distillation: `claude-sonnet-4-6`. Judge: `claude-opus-5` by default
  (a different model from the one under test); `--judge-model` overrides.
- The requirements audit of the brief lives in `audit/` (55 extracted requirements,
  traceability matrix, gaps).
