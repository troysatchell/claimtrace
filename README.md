# claimtrace

**Claim-provenance-constrained knowledge tracing.** A tutoring model keeps a ledger of what the learner
has demonstrated and what the learner has only claimed. An item never crosses that line because the learner
asserted it, repeated it, got frustrated, or demanded it.

Every tutor reply ends with one line:

```
KNOWN: <what the learner has demonstrated> | CLAIMED: <what they assert but have not shown> | UNCHECKED: <beliefs not yet probed>
```

Behavior Spec (two sentences): `BEHAVIOR_SPEC.md`. Thesis and evidence: `BRAINLIFT.md`. MVP numbers and
analysis: `results/mvp/NOTES.md`.

The repo covers the full arc of the "Train Your Own Small Learning Model" brief: prove a prompting ceiling
on frontier models, generate and filter a distilled dataset, QLoRA-tune a small open model, and compare
base vs tuned with a deterministic check plus an LLM judge. Every step is one command. The same commands
run on an Apple Silicon Mac (`mlx_lm`) and on a CUDA box (`transformers`).

## Finding 1: prompting has a ceiling (ablation, n=30)

Two frontier families × three prompting strategies × 30 scenarios (396 turns per cell), thinking disabled,
scored deterministically.

| model | strategy | ledger rate | premature promotions | clean conversations |
|---|---|---|---|---|
| claude-sonnet-5 | zero-shot | 0.92 | 36 | 6/30 |
| claude-sonnet-5 | few-shot | 0.99 | 28 | 13/30 |
| claude-sonnet-5 | structured | 0.98 | 20 | 16/30 |
| kimi-k3 | zero-shot | 1.00 | 59 | 4/30 |
| kimi-k3 | few-shot | 1.00 | 30 | 13/30 |
| kimi-k3 | structured | 0.96 | 15 | 17/30 |

The ceiling is specific. On the turn where the learner gives a self-report ("I've been writing Python for
about a year"), the model files it under KNOWN:

| self-report → KNOWN on that turn | zero-shot | few-shot | structured |
|---|---|---|---|
| claude-sonnet-5 | 12/12 | 12/12 | 10/12 |
| kimi-k3 | 12/12 | 12/12 | 5/12 |

It does this under a system prompt that says "Never treat ASSERTED as DEMONSTRATED", and it annotates the
item while filing it: `KNOWN: has balanced equations before (claimed, not yet shown here)`. Every other
shape prompts to near-clean. Report: `results/full-30-combined/ANALYSIS.md`. Transcripts:
`results/full-30-combined/transcripts.jsonl`. Judged columns (same rubric as `eval.py`):
`results/full-30-combined/judged_table.md`.

## Finding 2: the data removes it (MVP, base vs tuned)

Qwen3-1.7B, 270 training conversations, 41 held-out scenarios (498 turns), greedy decoding.
Full table and reading: `results/mvp/NOTES.md`.

| | base | tuned |
|---|---|---|
| clean conversations | 0/41 | 20/41 |
| self-report→KNOWN | 0.24 | 0.01 |
| self-report→KNOWN on the 12 ablation turns (frontier best 10/12) | 2/12 | 0/12 |
| hedged KNOWN items | 1 | 0 |
| demonstrations credited | 0.05 | 0.87 |
| ordinary questions interrogated (control) | 0.00 | 0.01 |
| robustness under pressure (judge) | 0.97 | 0.67 |

The base model writes the ledger format on 100% of turns, so the delta is provenance, not format. The base's
0.97 robustness is hollow: its ledger never changes. The tuned model's ledger held on 36/36 judged
scenarios; its 12 misses are prose that over-credits on the "what do I know?" turn.

## Files

```
ledger.py                spec (BEHAVIOR_SPEC / SPEC), ledger parser, deterministic checks
build_scenarios.py       writes metacog_scenarios.jsonl (41 scenarios, 7 shapes, per-turn flags)
metacog_precheck.py      prompt-ceiling ablation (2 models × 3 strategies × 30 scenarios)
ablation_judge.py        judges the ablation transcripts with the eval.py rubric
generate_dataset.py      distills conversations from a teacher; mechanical filter; drop report
train.py                 QLoRA via mlx_lm.lora: data split, config, checkpoints, log; --sweep for the N curve
eval.py                  one command: base-vs-tuned table + per-example JSONL + judge; MLX or torch
sweep.py                 data-efficiency table and curve.png
compare.py               live base-vs-tuned on one conversation (demo)
publish.py               fuse and push model + dataset to Hugging Face Hub; prints revision hashes
smoke.sh                 generate → train → eval on 6 conversations; log in results/smoke-loop/
run_pipeline_qlora.sh    train q270 → eval → sweep q135/q67/q33 → curve
judge.py                 standalone per-turn judge over a transcripts file
llm.py                   teacher/judge API routing (claude-* → Anthropic, kimi-* → Moonshot)
```

## Commands

```bash
pip install -r requirements.txt            # mlx-lm on darwin/arm64; see comments for CUDA
export ANTHROPIC_API_KEY=... MOONSHOT_API_KEY=...

# 1. Ablation, one cell
python3 metacog_precheck.py --models sonnet --strategies zero_shot --max-scenarios 1 --out results/one

# 2. Dataset (300 conversations; teacher default claude-sonnet-4-6; --teacher overrides)
python3 generate_dataset.py --n 300 --out data --workers 12

# 3. Train (QLoRA: 4-bit base at ckpt/base-q4, LoRA r=16 on the last 16 blocks)
python3 train.py --n 270 --run-id q270                     # log: results/train/q270/log.txt
python3 train.py --sweep 135,67,33 --run-prefix q          # identical config; only N varies

# 4. Eval, base vs tuned (table.md, judge_transcripts.jsonl, run.json)
python3 eval.py --model ckpt/q270/adapters --base Qwen/Qwen3-1.7B --eval-set metacog_scenarios.jsonl --out results/mvp-qlora
python3 eval.py --rejudge results/mvp-qlora --judge-model claude-sonnet-4-6   # judge saved transcripts only

# 5. Data-efficiency curve
python3 sweep.py --runs q270,q135,q67,q33 --base-results results/mvp-qlora --out results/sweep-qlora

# 6. Publish (needs `hf auth login`), then eval the published revision
python3 publish.py --run q270 --user <hf-user>
python3 eval.py --model <hf-user>/claimtrace-qwen3-1.7b --base Qwen/Qwen3-1.7B --eval-set metacog_scenarios.jsonl

# Smoke test of the whole loop (~5 min); live demo
./smoke.sh --skip-generate
python3 compare.py --tuned ckpt/q270/adapters "I've used git for years." "How do I see what commit I'm on?"
```

## Eval set schema (for a staff held-out set)

`--eval-set` takes a JSONL file. Each line is one scenario:

```json
{"id": "m1", "shape": "A", "topic": "recursion",
 "turns": [{"say": "<learner message>", "demo": false, "new": true, "pressure": false,
            "self_report": true, "ordinary": false}, ...]}
```

Only `say` is required. The flags drive the checks:

- `demo` — the learner demonstrated the item. KNOWN may grow only here; a miss is `missed_promotion`.
- `pressure` — the judge scores these turns.
- `self_report` — the learner describes their own background or ability. Reported as self-report→KNOWN.
- `ordinary` — a plain question. Reported as over-trigger.

Rules and history: `metacog_scenarios.LABELING.md`. The 41 scenarios are never trained on, and the training
sentences differ from them (`dataset_spec.md`, "No eval leakage").

## Results

| artifact | where |
|---|---|
| Ablation (n=30) | `results/full-30-combined/ANALYSIS.md`, `table.md`, `judged_table.md`, `transcripts.jsonl` |
| Dataset v2 (300 conversations) + drop report + generation log | `data/` |
| MVP base vs tuned, bf16 LoRA n270 | `results/mvp/table.md`, `NOTES.md`, `judge_transcripts.jsonl`, `run.json` |
| MVP base vs tuned, QLoRA q270 (configuration of record) | `results/mvp-qlora/` (in progress) |
| Training logs, configs, adapter sha256s | `results/train/<run>/log.txt`, `lora_config.yaml`, `summary.json` |
| Data-efficiency sweep (N = 270/135/67/33) | `results/sweep-qlora/table.md`, `curve.png` (in progress) |
| Smoke loop log | `results/smoke-loop/log.txt` |
| Requirements audit of the brief | `audit/requirements/REPORT.md` |

## Submission block

- Eval-code commit: `results/<out>/run.json → eval_code_commit`.
- Training commit and adapter sha256: `results/train/<run>/summary.json`.
- HF model repo and revision, dataset repo and revision: `results/publish.json`, written by `publish.py`.
  Not published yet: this machine is not logged in to Hugging Face. Run `hf auth login`, then
  `python3 publish.py --run q270 --user <hf-user>`.

## Provenance

- Ablation models: `claude-sonnet-5`, `kimi-k3`; thinking disabled; MAX_TOKENS 2500.
- Teacher: default `claude-sonnet-4-6`. The shipped dataset used `kimi-k3` (`--teacher`; recorded in
  `data/drop_report.json`) because the Anthropic key was rejected at generation time.
- Judge: `claude-sonnet-4-6` (`eval.py` default; `--judge-model` overrides; recorded in `run.json`).
- Base model: `Qwen/Qwen3-1.7B`, thinking disabled in the chat template. QLoRA: LoRA r=16, scale 20,
  dropout 0.05, last 16 blocks, over a 4-bit affine copy of the base (group 64). bf16 LoRA on the
  unquantized base is `train.py --base Qwen/Qwen3-1.7B` (run `n270`).
- `mlx_lm --mask-prompt` trains the last assistant turn only, so `train.py` expands each conversation into
  per-turn prefix rows. Learner turns are never trained on.
- Decoding is greedy in `eval.py` and `compare.py`. Results are reproducible for a model revision and an
  eval-code commit.
