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
| First real QLoRA training run | `results/train/q270/log.txt`, `lora_config.yaml`, `summary.json` (adapter sha256, checkpoints); adapters in `ckpt/q270/adapters/` (not in git) | `python3 train.py --n 270 --run-id q270` | ⏳ training (bf16 LoRA run `n270` complete: `results/train/n270/`) |
| First base-vs-tuned numbers + raw judge transcripts | QLoRA: `results/base-vs-tuned/` (table.md, judge_transcripts.jsonl, run.json, NOTES.md). bf16 LoRA: `results/base-vs-tuned-lora-bf16/` | eval command above | ⏳ QLoRA eval follows training; LoRA ✅ |

## Verification requirements

| Requirement | Where | Status |
|---|---|---|
| Public model checkpoint on Hugging Face Hub + exact commit hash | `troysaved/claimtrace-qwen3-1.7b` @ `b6f68ec27c1b` (`results/publish.json`; run `n270`) | ✅ n270; re-publish `q270` when its eval lands (`python3 publish.py --run q270 --user troysaved`) |
| `eval.py --model <hf-repo-id> --eval-set <path>` | `eval.py` (root) | ✅ |
| Raw judge transcripts (score + reasoning per example) | `<dir>/judge_transcripts.jsonl` per eval run | ✅ |
| Staff held-out eval set | any JSONL in the schema in `README.md` "Eval set schema"; only `say` is required per turn | ✅ (schema) |
| Pinned versions | eval-code commit: `<dir>/run.json → eval_code_commit`; training commit + adapter sha256: `results/train/<run>/summary.json`; HF revision: `results/publish.json` | ✅ |
| Live comparison in demo | `python3 compare.py --tuned ckpt/q270/adapters "<turn 1>" "<turn 2>" ...` | ✅ tool; video ⛔ |
| Ablation reproducibility | `metacog_precheck.py --max-scenarios 1` (one cell); training logs `results/train/<run>/`; one point: `python3 train.py --n 33 --run-id q33` | ✅ |

## Early submission

| Deliverable | Where | Status |
|---|---|---|
| Failure mode diagnosed from MVP eval, resolved by a v2 dataset (not config) | Diagnosis: `results/base-vs-tuned-lora-bf16/NOTES.md` "Where the tuned model still breaks"; plan: `BRAINLIFT.md` "Failure modes → v2 data change" | ⏳ v2 dataset not generated |
| Updated base-vs-tuned numbers with delta + raw judge transcripts | — | ⏳ |
| ≥2 points on the Data-Efficiency curve | `results/data-efficiency-curve/table.md` | ⏳ sweep queued after q270 |
| Draft artifacts: dataset shape, checkpoint, in-progress Brainlift | `dataset_spec.md`; `results/train/<run>/summary.json`; `BRAINLIFT.md` | ✅ |

## Final submission

| Deliverable | Where | Status |
|---|---|---|
| Dataset published | `troysaved/claimtrace-ledger-dataset` @ `af3b650835` (`results/publish.json`) | ✅ |
| Model on HF Hub + running inference demo | model ✅ (above); demo app `space/` (Gradio + Dockerfile, mirrors `compare.py`) | ⏳ hosting: HF Space needs PRO, or Railway/Render via `space/Dockerfile` |
| Eval harness + results, own set and staff set | `eval.py`; `results/base-vs-tuned/` | ⏳ staff set when provided |
| Full Data-Efficiency curve + justified minimum viable N | `results/data-efficiency-curve/table.md`, `curve.png`; `BRAINLIFT.md` "Minimum viable dataset size" | ⏳ |
| Brainlift | `BRAINLIFT.md` | ✅ draft |
| 3–5 minute demo video with a live grader prompt | link goes here | ⛔ |

## Requirements audit

`audit/requirements/REPORT.md` — every requirement in the brief traced to file:line with a verdict;
`gaps.md` lists what is missing and the smallest change that closes it.
