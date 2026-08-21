# Submission index — claimtrace (Train Your Own Small Learning Model)

Each row names a deliverable from the brief, where it is, and the command that regenerates it.
Status: ✅ done · ⏳ running · ⛔ needs an action outside this repo.

## MVP

| Deliverable (brief) | Where | Regenerate | Status |
|---|---|---|---|
| Behavior Spec (1–2 sentences, falsifiable) | `BEHAVIOR_SPEC.md`; `ledger.BEHAVIOR_SPEC` | — | ✅ |
| Prompt-Ceiling Ablation report | `results/prompt-ceiling-ablation/REPORT.md` (table, per-shape, surviving failure mode, reliability bar); `table.md`; judged columns `judged_table.md`; transcripts `transcripts.jsonl`; judge output `judge_transcripts.jsonl` | `python3 metacog_precheck.py --out results/prompt-ceiling-ablation` then `python3 ablation_judge.py --transcripts results/prompt-ceiling-ablation/transcripts.jsonl --out results/prompt-ceiling-ablation` | ✅ |
| Eval harness: LLM-as-judge, behavioral check, base-vs-tuned | `eval.py` (judge: `JUDGE_PROMPT`, `judge()`), `ledger.py` (`check_turn`), `eval.py --base` | see next row | ✅ |
| One-command eval | `python3 eval.py --model <hf-repo-id or ckpt/q270/adapters> --base Qwen/Qwen3-1.7B --eval-set metacog_scenarios.jsonl --out <dir>` → `<dir>/table.md`, `<dir>/judge_transcripts.jsonl`, `<dir>/run.json` | same | ✅ |
| Full loop generate → train → eval on a smoke batch | `smoke.sh`; log `results/smoke-loop/log.txt` | `./smoke.sh` (`--skip-generate` reuses `data/smoke-v2`) | ✅ |
| First real dataset, generated and filtered | `data/dataset.jsonl` (300 conversations, 3,301 turns), `data/drop_report.json`, `data/generate.log`; spec `dataset_spec.md` | `python3 generate_dataset.py --n 300 --out data --workers 12` | ✅ |
| First real QLoRA training run | `results/train/q270/log.txt`, `lora_config.yaml`, `summary.json` (adapter sha256, checkpoints); adapters in `ckpt/q270/adapters/` (not in git) | `python3 train.py --n 270 --run-id q270` | ✅ done 22:20 CDT (500 optimizer steps, val loss 3.24 → 0.94, adapter sha256 `6a6af4f1ac8e…`); bf16 LoRA twin `n270`: `results/train/n270/` |
| First base-vs-tuned numbers + raw judge transcripts | QLoRA (run of record): `results/base-vs-tuned/` (table.md, judge_transcripts.jsonl, run.json, NOTES.md) — spec adherence 0.00 → 0.49, self-report→KNOWN 0.24 → 0.07, clean 0/41 → 20/41. bf16 LoRA twin: `results/base-vs-tuned-lora-bf16/` | eval command above | ✅ both |

## Verification requirements

| Requirement | Where | Status |
|---|---|---|
| Public model checkpoint on Hugging Face Hub + exact commit hash | `troysaved/claimtrace-qwen3-1.7b` @ `f6532284babb` (run `q236v2`, current run of record; `results/publish.json`); prior runs pinned: q270 `4de80c2a06ad`, n270 `b6f68ec27c1b` | ✅ |
| `eval.py --model <hf-repo-id> --eval-set <path>` | `eval.py` (root) | ✅ |
| Raw judge transcripts (score + reasoning per example) | `<dir>/judge_transcripts.jsonl` per eval run | ✅ |
| Staff held-out eval set | any JSONL in the schema in `README.md` "Eval set schema"; only `say` is required per turn | ✅ (schema) |
| Pinned versions | eval-code commit: `<dir>/run.json → eval_code_commit`; training commit + adapter sha256: `results/train/<run>/summary.json`; HF revision: `results/publish.json` | ✅ |
| Live comparison in demo | `python3 compare.py --tuned ckpt/q236v2/adapters "<turn 1>" ...`; or the Colab demo grader cell | ✅ tool; video ⛔ |
| Ablation reproducibility | `metacog_precheck.py --max-scenarios 1` (one cell); training logs `results/train/<run>/`; one point: `python3 train.py --n 33 --run-id q33` | ✅ |

## Early submission

| Deliverable | Where | Status |
|---|---|---|
| Failure mode diagnosed from MVP eval, resolved by a v2 dataset (not config) | Diagnosis: `results/base-vs-tuned/NOTES.md`; fix: `data/v2/` (265 convs, teacher kimi-k3, `dataset_spec.md` changelog v2→v3); config identical (diff `results/train/{q270,q236v2}/lora_config.yaml`) | ✅ unearned 15→1, self-report→KNOWN 0.07→0.00 |
| Updated base-vs-tuned numbers with delta + raw judge transcripts | `results/base-vs-tuned-v2/` (table.md, DELTA.md, NOTES.md, judge_transcripts.jsonl, run.json) | ✅ clean 20/41→33/41, spec adherence 0.49→0.80, robustness 0.69→0.83 |
| ≥2 points on the Data-Efficiency curve | `results/data-efficiency-curve/table.md`, `curve.png`, `sweep_summary.json`; per-N eval `q33/ q67/ q135/ q270→../base-vs-tuned`; training logs `results/train/q{33,67,135,270}/` | ✅ 4 points (N = 33/67/135/270, QLoRA, identical config) |
| Draft artifacts: dataset shape, checkpoint, in-progress Brainlift | `dataset_spec.md`; `results/train/<run>/summary.json`; `BRAINLIFT.md` | ✅ |

## Final submission

| Deliverable | Where | Status |
|---|---|---|
| Dataset published | `troysaved/claimtrace-ledger-dataset` @ `ef2f4a2bccba` (v2, `data/v2`; v1 pinned @ `af3b650835`) | ✅ |
| Model on HF Hub + running inference demo | model ✅ (above); demo: [`demo_colab.ipynb`](https://colab.research.google.com/github/troysatchell/claimtrace/blob/main/demo_colab.ipynb) (pinned revision, live prompts, mechanical checks); `space/` app remains for container hosting | ✅ |
| Eval harness + results, own set and staff set | `eval.py`; `results/base-vs-tuned/` | ⏳ staff set when provided |
| Full Data-Efficiency curve + justified minimum viable N | `results/data-efficiency-curve/table.md`, `curve.png`; `BRAINLIFT.md` "Minimum viable dataset size — N = 135" | ✅ 4 points; min viable N = 135 (N = 67 floor, N = 33 overfits) |
| Brainlift | `BRAINLIFT.md` (thesis, 5 evidence items incl. QLoRA run and data-efficiency curve, min viable N, v2 plan) | ✅ draft; v2-delta section pending |
| 3–5 minute demo video with a live grader prompt | link goes here | ⛔ |

## Stretch ladder (optional)

| Item | Where | Status |
|---|---|---|
| DPO preference tuning | pairs: `data/dpo/pairs.jsonl` (2,227 pairs, mechanical on-spec vs off-spec corruption; `build_dpo_pairs.py`); training: `train_dpo.py` (TRL, Colab/CUDA); eval: same `eval.py` command | 🟡 pairs + script ready; run needs a CUDA session |
| Adversarial / robustness eval | — | not attempted |
| Composed behavior | — | not attempted |

## Requirements audit

`audit/requirements/REPORT.md` — every requirement in the brief traced to file:line with a verdict;
`gaps.md` lists what is missing and the smallest change that closes it.
