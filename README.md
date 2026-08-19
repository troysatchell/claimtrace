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
LLM judge. Everything here is re-runnable from the command line, on an Apple Silicon Mac
(`mlx_lm`) or a CUDA box (`transformers`), with the same commands.

Behavior Spec (two sentences): `BEHAVIOR_SPEC.md` · thesis and evidence: `BRAINLIFT.md` ·
MVP numbers and the format-vs-provenance analysis: `results/mvp/NOTES.md`.

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
ledger.py                the spec (BEHAVIOR_SPEC / SPEC) + parser + deterministic checks; single source of truth
build_scenarios.py       generates metacog_scenarios.jsonl — 41 scenarios in 7 shapes, per-turn flags
metacog_precheck.py      prompt-ceiling ablation (2 models × 3 strategies × 30 scenarios)
generate_dataset.py      distill multi-turn conversations from a frontier teacher; mechanical filter; drop report
train.py                 QLoRA on Qwen3-1.7B via mlx_lm.lora (data split, config, checkpoints, log); --sweep for the N curve
eval.py                  ONE command: base-vs-tuned table + per-example JSONL (+ judge); MLX or torch backend
sweep.py                 data-efficiency table + curve.png over the sweep runs
compare.py               live base-vs-tuned on one conversation (demo's grader-supplied prompt)
publish.py               fuse + push model and dataset to Hugging Face Hub; prints revision hashes
smoke.sh                 generate → train → eval on a 6-conversation batch (log in results/smoke-loop/)
run_pipeline_qlora.sh    train q270 → eval → sweep q135/q67/q33 → curve
judge.py                 standalone LLM-as-judge over any transcripts file
llm.py                   teacher/judge API routing (claude-* → Anthropic, kimi-* → Moonshot)
```

### Run it (Apple Silicon; the same commands work on a GPU box)

```bash
pip install -r requirements.txt            # mlx-lm on darwin/arm64; see comments for CUDA
export ANTHROPIC_API_KEY=... MOONSHOT_API_KEY=...

# 1. Prompt-ceiling ablation (any cell reproducible in isolation)
python3 metacog_precheck.py --models sonnet --strategies zero_shot --max-scenarios 1 --out results/one

# 2. Dataset (300 conversations; teacher pinned to claude-sonnet-4-6, --teacher overrides)
python3 generate_dataset.py --n 300 --out data --workers 12

# 3. Train (QLoRA: 4-bit base made on first use at ckpt/base-q4, LoRA r=16 on the last 16 blocks)
python3 train.py --n 270 --run-id q270                     # log: results/train/q270/log.txt
python3 train.py --sweep 135,67,33 --run-prefix q          # identical config, only N varies

# 4. Eval, base vs tuned, one command (table.md + judge_transcripts.jsonl + run.json)
python3 eval.py --model ckpt/q270/adapters --base Qwen/Qwen3-1.7B --eval-set metacog_scenarios.jsonl --out results/mvp-qlora
python3 eval.py --rejudge results/mvp-qlora --judge-model claude-sonnet-4-6   # judge saved transcripts only

# 5. Data-efficiency curve
python3 sweep.py --runs q270,q135,q67,q33 --base-results results/mvp-qlora --out results/sweep-qlora

# 6. Publish (needs `hf auth login`), then eval against the published revision
python3 publish.py --run q270 --user <hf-user>
python3 eval.py --model <hf-user>/claimtrace-qwen3-1.7b --base Qwen/Qwen3-1.7B --eval-set metacog_scenarios.jsonl

# Smoke test of the whole loop on 6 conversations (~5 min); live demo runner
./smoke.sh --skip-generate
python3 compare.py --tuned ckpt/q270/adapters "I've used git for years." "How do I see what commit I'm on?"
```

## Eval set schema (for a staff held-out set)

`--eval-set` takes any JSONL where each line is a scenario:

```json
{"id": "m1", "shape": "A", "topic": "recursion",
 "turns": [{"say": "<learner message>", "demo": false, "new": true, "pressure": false,
            "self_report": true, "ordinary": false}, ...]}
```

Only `say` is required. Flags drive the checks: `demo` — the learner demonstrated the item (KNOWN may
grow only here; missing it is `missed_promotion`); `pressure` — judged turns; `self_report` — the
learner describes their own background/ability (reported as self-report→KNOWN); `ordinary` — a plain
question (over-trigger control). Rules and history: `metacog_scenarios.LABELING.md`. The 41 scenarios
in `metacog_scenarios.jsonl` are never trained on; the training topics/sentences differ from them
(dataset_spec.md, "No eval leakage").

## Results so far

| artifact | where |
|---|---|
| Prompt-ceiling ablation (n=30, 2 families × 3 strategies) | `results/full-30-combined/ANALYSIS.md`, `table.md`, `transcripts.jsonl` |
| Dataset v2 (300 conversations, 3,301 turns) + drop report + generation log | `data/` |
| MVP base-vs-tuned, bf16 LoRA n270 (41 scenarios) + analysis | `results/mvp/table.md`, `results/mvp/NOTES.md`, `results/mvp/judge_transcripts.jsonl` |
| MVP base-vs-tuned, QLoRA q270 (configuration of record) | `results/mvp-qlora/` (in progress) |
| Training logs + checkpoint sha256s | `results/train/<run>/log.txt`, `summary.json`, `lora_config.yaml` |
| Data-efficiency sweep (N = 270/135/67/33) | `results/sweep-qlora/table.md`, `curve.png` (in progress) |
| Smoke loop log | `results/smoke-loop/log.txt` |
| Brainlift | `BRAINLIFT.md` |

Headline (bf16 LoRA n270, `results/mvp/NOTES.md`): clean conversations 0/41 → 20/41; self-report→KNOWN
0.24 → 0.01 (0/12 on the turns where the frontier's best prompt scored 10/12); hedged 1 → 0;
demonstrations credited 0.05 → 0.87; over-trigger control flat at 0.00 → 0.01. The base model holds the
ledger *format* on 100% of turns, so the delta is provenance, not formatting.

## Submission block (pinned versions)

- Eval code commit: see `results/<out>/run.json → eval_code_commit` (the tree that produced each table).
- Training commit + adapter sha256: `results/train/<run>/summary.json`.
- HF model repo + revision, dataset repo + revision: written to `results/publish.json` by `publish.py`
  — **not yet published** (this machine is not logged in to Hugging Face; run `hf auth login` then
  `python3 publish.py --run q270 --user <hf-user>`).
- LLM-judge column: empty in the current tables — the Anthropic key in `.env` is invalid and the
  Moonshot account ran out of balance after generation. `python3 eval.py --rejudge <dir> --judge-model <id>`
  fills it from the saved transcripts (greedy decoding; no regeneration).

## Provenance notes

- Ablation models pinned: `claude-sonnet-5`, `kimi-k3` (Moonshot), thinking disabled, MAX_TOKENS=2500.
- Teacher for distillation: pinned default `claude-sonnet-4-6`; **the shipped dataset was generated
  with `kimi-k3`** (`--teacher`, recorded in `data/drop_report.json`) because the Anthropic key was
  rejected. Judge: `eval.py` default `claude-sonnet-4-6`, `--judge-model` overrides and is recorded in `run.json`.
- Base model: `Qwen/Qwen3-1.7B` (thinking disabled via chat template). QLoRA = LoRA r=16/scale 20/dropout
  0.05 on the last 16 blocks over a 4-bit affine-quantized (group 64) copy of the base; bf16 LoRA on the
  unquantized base is `train.py --base Qwen/Qwen3-1.7B` (run `n270`).
- `mlx_lm --mask-prompt` computes loss on the last assistant turn only, so `train.py` expands each
  conversation into per-turn prefix rows; learner turns (the self-report strings) are never trained on.
- Decoding is greedy everywhere (`eval.py`, `compare.py`), so results are reproducible for a given
  model revision and eval-code commit.
- The requirements audit of the brief lives in `audit/` (inventory, traceability matrix, gaps).
