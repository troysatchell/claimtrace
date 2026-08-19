# Requirements Audit — Trained_SLM (claimtrace)
**Commit:** 35b0b6cbd2f3 (dirty: results/pipeline-qlora.log, results/train/q270/log.txt — the in-progress QLoRA run) · **Date:** 2026-08-18T20:40:53-0500 · **Docs:** SLM (p.1–4) · **Mode:** compare `mvp` vs `matrix.baseline.json` (2026-08-17)

## Summary
- VERIFIED: 18
- IMPLEMENTED-UNVERIFIED: 7
- PARTIAL: 15
- MISSING: 7
- N/A: 7
- ASSUMED: 1

The MVP bundle (SLM-R34–R42) is present and re-runnable except for one item: **the full-size QLoRA
training run is not finished** (SLM-R41 PARTIAL — the completed n270 run is bf16 LoRA; the QLoRA run of
record `q270` started 20:25 CDT and its base-vs-tuned eval lands afterwards). The base-vs-tuned numbers
exist and carry the behavior claim (SLM-R6/R42: 0/41 → 20/41 clean; self-report→KNOWN 0.24 → 0.01;
base holds the ledger format on 100% of turns so the delta is provenance, not formatting), with full
per-example judge output. The two hard blockers for the Verification Requirements are external: no
Hugging Face login on this machine, so no public checkpoint / revision hash (SLM-R23, R27, R47, R48),
and the ablation's LLM-judge column (SLM-R16/R17) was never computed — the ablation table reports the
deterministic proxies, not the two named metrics. Everything else that was MISSING at baseline
(harness, dataset, training, eval, JSONL, smoke loop, sweep tooling, Brainlift draft) now exists; 34 of
55 verdicts changed.

## Coverage and limitations
- `verify.precheck` (the ablation) was NOT re-run in this sweep (API spend); SLM-R1, R11, R14, R29 lean on the 2026-08-17 run logs `results/full-30-run.log`, `results/full-30-sonnet-run.log`.
- Ticket dimension BLOCKED: `tickets.project` is null (the Linear team spans unrelated projects). Every row's ticket cell reads `BLOCKED` — never checked, not "checked, none".
- The judge column in `results/mvp` was filled by `eval.py --rejudge` after generation, with `claude-sonnet-4-6`, because both API keys were dead when the eval ran (Anthropic key invalid at the time, Moonshot account out of balance). Generation is greedy, so the transcripts are the frozen record; the judge input was changed from pressure-only excerpts to the full transcript with `[PRESSURE]` markers (recorded in `run.json → judge_input`).
- The smoke loop's *generate* step reused the committed 6-conversation batch (`data/smoke-v2`) for the same key reason; train and eval steps ran live.
- The dataset was generated with `kimi-k3` (`--teacher`), not the pinned `claude-sonnet-4-6`; recorded in `data/drop_report.json`.
- 7 rows are statically traced only (IMPLEMENTED-UNVERIFIED); 1 row (SLM-R7) remains ASSUMED pending the yes/no ruling in `interpretations.md`.
- No database or external state was written; the sweep ran read-only commands plus the training/eval/smoke jobs whose outputs are committed artifacts.

## Matrix
| ID | Requirement (short) | Ticket(s) | Evidence | Verdict |
|---|---|---|---|---|
| SLM-R1 | A well-prompted base model can't already do it reliably. | BLOCKED | results/full-30-combined/ANALYSIS.md:28, results/full-30-combined/ANALYSIS.md:57 | PARTIAL |
| SLM-R2 | Your first deliverable, before any code, is a falsifiable Behavior Spe… | BLOCKED | ledger.py:11, BEHAVIOR_SPEC.md:3, ledger.py:16, eval.py:37 | VERIFIED |
| SLM-R3 | Choose a specific learning or teaching behavior. | BLOCKED | BEHAVIOR_SPEC.md:3, build_scenarios.py:3 | IMPLEMENTED-UNVERIFIED |
| SLM-R4 | generate a distilled dataset that embodies it | BLOCKED | generate_dataset.py:246, generate_dataset.py:315, data/drop_report.json:5, data/generate.log:1 | VERIFIED |
| SLM-R5 | fine-tune a small open base model (QLoRA) to hold it | BLOCKED | train.py:46, train.py:191, train.py:199, results/smoke-loop/log.txt:4 | VERIFIED |
| SLM-R6 | prove — with numbers, not claims — that the tuned model beats the base… | BLOCKED | results/mvp/table.md:3, results/mvp/table.md:4, results/mvp/NOTES.md:31 | VERIFIED |
| SLM-R7 | One target, one context. No broad domains — diffuse data makes a mushy… | BLOCKED | BEHAVIOR_SPEC.md:3, generate_dataset.py:38 | ASSUMED |
| SLM-R8 | No training before the eval exists. Build the eval harness first, or y… | BLOCKED | results/train/n270/log.txt:1 | VERIFIED |
| SLM-R9 | A disappointing model is almost always a data problem. Don't tune hype… | BLOCKED | dataset_spec.md:5, BRAINLIFT.md:67 | N/A |
| SLM-R10 | Don't chase capability benchmarks. Measure your target behavior, not t… | BLOCKED | eval.py:346, eval.py:369 | VERIFIED |
| SLM-R11 | Before you write a line of fine-tuning code, prove (with numbers) that… | BLOCKED | results/full-30-combined/ANALYSIS.md:5, results/full-30-combined/ANALYSIS.md:28 | PARTIAL |
| SLM-R12 | This is presented live at your Architecture Defense, using the calenda… | BLOCKED | — | N/A |
| SLM-R13 | At least 2 frontier models from different model families. | BLOCKED | metacog_precheck.py:36, metacog_precheck.py:37 | VERIFIED |
| SLM-R14 | At least 3 prompting strategies per model: zero-shot, few-shot with in… | BLOCKED | metacog_precheck.py:85, metacog_precheck.py:86, metacog_precheck.py:87, results/full-30-combined/table.md:3 | IMPLEMENTED-UNVERIFIED |
| SLM-R15 | Minimum 30 scenarios per model × strategy combination | BLOCKED | metacog_precheck.py:287, results/full-30-combined/table.md:3 | VERIFIED |
| SLM-R16 | scored against your Behavior Spec using the same LLM-as-judge rubric y… | BLOCKED | eval.py:37, judge.py:36, metacog_precheck.py:214 | PARTIAL |
| SLM-R17 | A results table (mean Spec-adherence and Robustness per model × strate… | BLOCKED | results/full-30-combined/table.md:1 | PARTIAL |
| SLM-R18 | plus a short paragraph naming the specific failure mode that survives … | BLOCKED | results/full-30-combined/ANALYSIS.md:28, README.md:43 | IMPLEMENTED-UNVERIFIED |
| SLM-R19 | Train at least 4 checkpoints at different dataset sizes (e.g. a log-sp… | BLOCKED | train.py:310, BRAINLIFT.md:57, results/train/n270/summary.json:1, results/train/n135/summary.json:1 | PARTIAL |
| SLM-R20 | Evaluate every checkpoint on the same eval set (your own plus the staf… | BLOCKED | sweep.py:37, results/mvp/run.json:1 | PARTIAL |
| SLM-R21 | Report a performance-vs-N curve for at least Spec adherence and Robust… | BLOCKED | sweep.py:65, sweep.py:93 | PARTIAL |
| SLM-R22 | Identify and justify the smallest N that holds the behavior reliably —… | BLOCKED | BRAINLIFT.md:57 | PARTIAL |
| SLM-R23 | Pushed to Hugging Face Hub (public repo) with the exact commit hash re… | BLOCKED | publish.py:68, publish.py:73, README.md:146 | MISSING |
| SLM-R24 | `eval.py --model <hf-repo-id> --eval-set <path>` regenerates your full… | BLOCKED | eval.py:463, eval.py:464, eval.py:68 | VERIFIED |
| SLM-R25 | Full per-example LLM-as-judge output (score + reasoning) submitted as … | BLOCKED | eval.py:513, results/mvp/NOTES.md:20 | VERIFIED |
| SLM-R26 | At grading time, your eval harness will also be run against a scenario… | BLOCKED | eval.py:464, README.md:111 | IMPLEMENTED-UNVERIFIED |
| SLM-R27 | Exact HF model commit hash and exact eval-code commit hash included in… | BLOCKED | results/mvp/run.json:2, results/train/n270/summary.json:3, README.md:146 | PARTIAL |
| SLM-R28 | Part of your demo video must show a grader-supplied prompt run live ag… | BLOCKED | compare.py:20 | N/A |
| SLM-R29 | Prompt-Ceiling Ablation script and Data-Efficiency training logs inclu… | BLOCKED | metacog_precheck.py:287, README.md:86 | IMPLEMENTED-UNVERIFIED |
| SLM-R30 | Prompt-Ceiling Ablation script and Data-Efficiency training logs inclu… | BLOCKED | results/train/n270/log.txt:1, results/train/n270/lora_config.yaml:1, results/train/n270/summary.json:623 | VERIFIED |
| SLM-R31 | MVP — due Tuesday at midnight | BLOCKED | — | N/A |
| SLM-R32 | Early Submission — due Thursday at midnight | BLOCKED | — | N/A |
| SLM-R33 | Final Submission — due Sunday at noon | BLOCKED | — | N/A |
| SLM-R34 | Finalized Behavior Spec (falsifiable, one to two sentences). | BLOCKED | BEHAVIOR_SPEC.md:3, ledger.py:11 | VERIFIED |
| SLM-R35 | Completed Prompt-Ceiling Ablation report (see Required Ablations) — pr… | BLOCKED | results/full-30-combined/ANALYSIS.md:1 | IMPLEMENTED-UNVERIFIED |
| SLM-R36 | Eval harness built and committed: LLM-as-judge scoring, | BLOCKED | eval.py:209, eval.py:37 | VERIFIED |
| SLM-R37 | a behavioral check for your spec's specific failure mode, | BLOCKED | ledger.py:57, ledger.py:77, eval.py:268 | VERIFIED |
| SLM-R38 | and a base-vs-tuned comparison mechanism. | BLOCKED | eval.py:465, eval.py:381 | VERIFIED |
| SLM-R39 | Full loop — generate → train → eval — runs end to end, demonstrated on… | BLOCKED | smoke.sh:19, smoke.sh:22, results/smoke-loop/log.txt:1 | VERIFIED |
| SLM-R40 | First real dataset generated and filtered; | BLOCKED | data/drop_report.json:5, data/dataset.jsonl:1 | VERIFIED |
| SLM-R41 | first real QLoRA training run completed. | BLOCKED | results/train/n270/log.txt:1, results/train/n270/summary.json:623, results/smoke-loop/log.txt:4 | PARTIAL |
| SLM-R42 | First base-vs-tuned eval numbers submitted, using the format in Verifi… | BLOCKED | results/mvp/table.md:3, results/mvp/table.md:4, results/mvp/NOTES.md:13 | VERIFIED |
| SLM-R43 | At least one specific failure mode diagnosed from your MVP eval, and r… | BLOCKED | results/mvp/NOTES.md:84, BRAINLIFT.md:67 | PARTIAL |
| SLM-R44 | Updated base-vs-tuned eval numbers showing the delta from MVP, submitt… | BLOCKED | — | MISSING |
| SLM-R45 | At least 2 points on your Data-Efficiency curve (see Required Ablation… | BLOCKED | results/train/n135/summary.json:1, results/mvp/run.json:1 | PARTIAL |
| SLM-R46 | Draft versions of your final artifacts: dataset shape, model checkpoin… | BLOCKED | dataset_spec.md:46, results/train/n270/summary.json:623, BRAINLIFT.md:1 | IMPLEMENTED-UNVERIFIED |
| SLM-R47 | The dataset, published — this is your real artifact. | BLOCKED | publish.py:78 | MISSING |
| SLM-R48 | The model on Hugging Face Hub, public, plus a running inference demo. | BLOCKED | compare.py:20 | MISSING |
| SLM-R49 | Eval harness and results table — base vs. tuned, on your own eval set … | BLOCKED | results/mvp/table.md:3 | PARTIAL |
| SLM-R50 | Full Data-Efficiency curve (performance vs. dataset size) with a justi… | BLOCKED | sweep.py:93, BRAINLIFT.md:57 | PARTIAL |
| SLM-R51 | Brainlift — your behavior thesis, and whether data → behavior held, wi… | BLOCKED | BRAINLIFT.md:3, BRAINLIFT.md:19, BRAINLIFT.md:76 | PARTIAL |
| SLM-R52 | A 3–5 minute demo video showing the tuned model doing the thing the ba… | BLOCKED | — | N/A |
| SLM-R53 | DPO / preference tuning — build preference pairs (on-spec vs. off-spec… | BLOCKED | — | MISSING |
| SLM-R54 | Adversarial / robustness eval — a hard eval set built specifically to … | BLOCKED | — | MISSING |
| SLM-R55 | Composed behavior — instill a second, potentially competing constraint… | BLOCKED | — | MISSING |

## Gaps
- **SLM-R1 — PARTIAL**: Ablation completed at n=30 with numbers; the plateau is shown per model/strategy. Missing: an explicitly stated numeric reliability bar the plateau is compared against (ANALYSIS.md line 59 says this was 'not measured here'). Qwen3-1.7B base also fails outright (results/mvp/table.md line 3: 0/41 clean), which is the in-repo counterpart. *Suggested:* State the reliability bar in one line in ANALYSIS.md/BRAINLIFT.md (e.g. 'self-report→KNOWN ≤ 1/12 on the biography turn and ≥ 27/30 clean conversations') and show the best-prompt numbers against it.
- **SLM-R11 — PARTIAL**: Completed run with numbers, committed 2026-08-17 (before train.py existed). Missing: the stated reliability bar (same gap as SLM-R1). *Suggested:* Same as SLM-R1: one stated bar next to the table.
- **SLM-R16 — PARTIAL**: The ablation was scored deterministically (metacog_precheck.py); the base-vs-tuned run is judged by eval.py's rubric. Two rubric texts exist (eval.py JUDGE_PROMPT vs judge.py RUBRIC) and neither has been run over the ablation transcripts. Not the 'same LLM-as-judge rubric' across both. *Suggested:* Run eval.py's judge (or judge.py) over results/full-30-combined/transcripts.jsonl to add judged spec-adherence/robustness per model×strategy, and make judge.py import eval.py's JUDGE_PROMPT so one rubric exists.
- **SLM-R17 — PARTIAL**: Per model×strategy table exists but does not carry the two named metrics (mean Spec-adherence, Robustness). 'clean runs' is the deterministic adherence proxy; no robustness column. *Suggested:* Add spec_adherence and robustness columns computed by the judge (see SLM-R16) to the ablation table.
- **SLM-R19 — PARTIAL**: 2 of ≥4 checkpoints trained (bf16 LoRA n270, n135); QLoRA q270 training and q135/q67/q33 queued (run_pipeline_qlora_rest.sh) at sweep time. *Suggested:* Let run_pipeline_qlora_rest.sh finish (≈6 h); the four QLoRA runs land in results/train/q*/.
- **SLM-R20 — PARTIAL**: Only n270 evaluated so far; n135 trained not evaluated. Staff held-out set not yet available (schema documented, README.md line 111). *Suggested:* Ships when the sweep pipeline finishes; add the staff set path when provided.
- **SLM-R21 — PARTIAL**: Plotting code present; no curve produced yet. *Suggested:* Ships with the sweep (results/sweep-qlora/curve.png).
- **SLM-R22 — PARTIAL**: Criterion stated ('smallest N within noise of N=270 on spec adherence and self-report→KNOWN'); N not yet named. *Suggested:* Fill in from results/sweep-qlora/table.md.
- **SLM-R23 — MISSING**: publish.py is ready; this machine is not logged in to Hugging Face (`hf auth whoami` → Not logged in), so nothing is pushed. *Suggested:* `hf auth login` then `python3 publish.py --run q270 --user <hf-user>`; paste results/publish.json hashes into README.
- **SLM-R27 — PARTIAL**: Eval-code commit and training commit are recorded; the HF model revision hash does not exist yet (SLM-R23). *Suggested:* Ships with SLM-R23.
- **SLM-R41 — PARTIAL**: A full-size run is complete with log + checkpoint sha256, but it is bf16 LoRA; the full-size QLoRA run (q270) was training at sweep time (results/train/q270/log.txt). No HF revision yet (SLM-R23). *Suggested:* q270 finishes ≈22:05 CDT; then publish (SLM-R23) for the HF revision.
- **SLM-R43 — PARTIAL**: Diagnosis written; v2 dataset not generated yet (Early submission item). *Suggested:* Add a wrong_attempt shape (+ plain-language demos, brevity constraint) to generate_dataset.py, regenerate as data/v3, retrain with the identical config, diff configs.
- **SLM-R44 — MISSING**: Early-submission item; follows SLM-R43. *Suggested:* Re-run eval.py on the v2-trained adapter; report delta vs results/mvp-qlora.
- **SLM-R45 — PARTIAL**: Two Ns trained, one evaluated; sweep evals queued. *Suggested:* Ships with the sweep pipeline.
- **SLM-R47 — MISSING**: Not published; needs HF login. *Suggested:* Ships with publish.py (SLM-R23).
- **SLM-R48 — MISSING**: No public model, no hosted inference demo. *Suggested:* Publish (SLM-R23) then a minimal Space/Gradio wrapper around compare.py's backend, or a recorded local demo.
- **SLM-R49 — PARTIAL**: Own set done; staff held-out set not yet available. *Suggested:* Run eval.py with the staff set path when provided; schema documented (README.md line 111).
- **SLM-R50 — PARTIAL**: Pending the sweep. *Suggested:* Ships with the sweep pipeline + BRAINLIFT update.
- **SLM-R51 — PARTIAL**: Draft with thesis and MVP evidence; min-N and QLoRA/robustness updates pending. *Suggested:* Update after the sweep and q270 eval.
- **SLM-R53 — MISSING**: Stretch (optional): DPO not attempted. *Suggested:* Optional; not before Final-submission core items.
- **SLM-R54 — MISSING**: Stretch (optional): adversarial eval set not attempted. *Suggested:* Optional; not before Final-submission core items.
- **SLM-R55 — MISSING**: Stretch (optional): composed behavior not attempted. *Suggested:* Optional; not before Final-submission core items.

## Orphan tickets
None (ticket dimension BLOCKED).

## Blocked / assumed
- Ticket dimension: tickets.project is null: the Troysatchell team spans 8 unrelated projects and none is this repo (config comment); no scope to map against. Unblock: Create a Linear project for claimtrace and set tickets.project in audit/requirements.config.yaml.
- SLM-R7 ASSUMED — 'Context' means the 1:1 tutoring interaction, so multi-subject tutoring is one context (dataset_spec.md line 88 varies subject on purpose so the model learns the behavior, not the domain). (question: Is multi-subject tutoring acceptable as 'one context' (context = the 1:1 tutoring interaction, not a single subject)?)

## Delta (compare mode)
| ID | baseline verdict | now | evidence change |
|---|---|---|---|
| SLM-R2 | PARTIAL | VERIFIED | ledger.py:11, BEHAVIOR_SPEC.md:3, ledger.py:16 |
| SLM-R4 | MISSING | VERIFIED | generate_dataset.py:246, generate_dataset.py:315, data/drop_report.json:5 |
| SLM-R5 | MISSING | VERIFIED | train.py:46, train.py:191, train.py:199 |
| SLM-R6 | MISSING | VERIFIED | results/mvp/table.md:3, results/mvp/table.md:4, results/mvp/NOTES.md:31 |
| SLM-R8 | N/A | VERIFIED | results/train/n270/log.txt:1 |
| SLM-R10 | MISSING | VERIFIED | eval.py:346, eval.py:369 |
| SLM-R15 | PARTIAL | VERIFIED | metacog_precheck.py:287, results/full-30-combined/table.md:3 |
| SLM-R16 | MISSING | PARTIAL | eval.py:37, judge.py:36, metacog_precheck.py:214 |
| SLM-R18 | MISSING | IMPLEMENTED-UNVERIFIED | results/full-30-combined/ANALYSIS.md:28, README.md:43 |
| SLM-R19 | MISSING | PARTIAL | train.py:310, BRAINLIFT.md:57, results/train/n270/summary.json:1 |
| SLM-R20 | MISSING | PARTIAL | sweep.py:37, results/mvp/run.json:1 |
| SLM-R21 | MISSING | PARTIAL | sweep.py:65, sweep.py:93 |
| SLM-R22 | MISSING | PARTIAL | BRAINLIFT.md:57 |
| SLM-R24 | MISSING | VERIFIED | eval.py:463, eval.py:464, eval.py:68 |
| SLM-R25 | MISSING | VERIFIED | eval.py:513, results/mvp/NOTES.md:20 |
| SLM-R26 | MISSING | IMPLEMENTED-UNVERIFIED | eval.py:464, README.md:111 |
| SLM-R27 | MISSING | PARTIAL | results/mvp/run.json:2, results/train/n270/summary.json:3, README.md:146 |
| SLM-R29 | PARTIAL | IMPLEMENTED-UNVERIFIED | metacog_precheck.py:287, README.md:86 |
| SLM-R30 | MISSING | VERIFIED | results/train/n270/log.txt:1, results/train/n270/lora_config.yaml:1, results/train/n270/summary.json:623 |
| SLM-R34 | PARTIAL | VERIFIED | BEHAVIOR_SPEC.md:3, ledger.py:11 |
| SLM-R35 | MISSING | IMPLEMENTED-UNVERIFIED | results/full-30-combined/ANALYSIS.md:1 |
| SLM-R36 | MISSING | VERIFIED | eval.py:209, eval.py:37 |
| SLM-R37 | PARTIAL | VERIFIED | ledger.py:57, ledger.py:77, eval.py:268 |
| SLM-R38 | MISSING | VERIFIED | eval.py:465, eval.py:381 |
| SLM-R39 | MISSING | VERIFIED | smoke.sh:19, smoke.sh:22, results/smoke-loop/log.txt:1 |
| SLM-R40 | MISSING | VERIFIED | data/drop_report.json:5, data/dataset.jsonl:1 |
| SLM-R41 | MISSING | PARTIAL | results/train/n270/log.txt:1, results/train/n270/summary.json:623, results/smoke-loop/log.txt:4 |
| SLM-R42 | MISSING | VERIFIED | results/mvp/table.md:3, results/mvp/table.md:4, results/mvp/NOTES.md:13 |
| SLM-R43 | MISSING | PARTIAL | results/mvp/NOTES.md:84, BRAINLIFT.md:67 |
| SLM-R45 | MISSING | PARTIAL | results/train/n135/summary.json:1, results/mvp/run.json:1 |
| SLM-R46 | MISSING | IMPLEMENTED-UNVERIFIED | dataset_spec.md:46, results/train/n270/summary.json:623, BRAINLIFT.md:1 |
| SLM-R49 | MISSING | PARTIAL | results/mvp/table.md:3 |
| SLM-R50 | MISSING | PARTIAL | sweep.py:93, BRAINLIFT.md:57 |
| SLM-R51 | MISSING | PARTIAL | BRAINLIFT.md:3, BRAINLIFT.md:19, BRAINLIFT.md:76 |

## Verification performed
| Command | Result | Bears on |
|---|---|---|
| `verify.scenario_count` | scenarios 41 turns 498 | SLM-R15, SLM-R26 |
| `verify.precheck_compile` | compile-ok | SLM-R29 |
| `verify.probe_anthropic` | 200 | SLM-R13 |
| `verify.probe_kimi` | ['kimi-k3', 'kimi-k2.7-code-highspeed', 'kimi-k2.6', 'kimi-k2.7-code'] | SLM-R13 |
| `verify.precheck` | NOT RUN | SLM-R1, SLM-R11, SLM-R14, SLM-R29 |
| `python3 eval.py --model ckpt/n270/adapters --base Qwen/Qwen3-1.7B --eval-set metacog_scenarios.jsonl --out res` | exit 0 — results/mvp/table.md, judge_transcripts.jsonl (82 rows, 72 judged), run.json | SLM-R6, SLM-R10, SLM-R24, SLM-R25, SLM-R36, SLM-R37, SLM-R38, SLM-R42 |
| `python3 train.py --n 270 --run-id n270 (via run_pipeline.sh, 14:30-16:02 CDT)` | exit 0 — 10 checkpoints, val loss 3.27→0.91, results/train/n270/log.txt | SLM-R30, SLM-R41, SLM-R8 |
| `./smoke.sh --skip-generate` | exit 0 — results/smoke-loop/log.txt | SLM-R39, SLM-R5 |
| `git log --format='%h %ad %s' --date=iso -- eval.py ledger.py train.py | head -3` | 46d0b65 13:48 / 3210fd3 13:35 (2026-08-18) / 07eaf97 (2026-08-17) — all before the 14:30:18 training log | SLM-R8 |
| `python3 -c "import ledger; print(ledger.BEHAVIOR_SPEC.count('. ')+1)"` | 2 | SLM-R2, SLM-R34 |
| `wc -l data/dataset.jsonl` | 300 | SLM-R4, SLM-R40 |
| `hf auth whoami` | Error: Not logged in | SLM-R23, SLM-R27, SLM-R47, SLM-R48 |

Captured excerpts for VERIFIED rows:

**SLM-R2** — `python3 -c "import ledger; print(ledger.BEHAVIOR_SPEC.count('. ')+1)"`
```
2
```
**SLM-R4** — `wc -l data/dataset.jsonl; python3 -c "import json;print(json.load(open('data/drop_report.json'))['drops'])"`
```
300 data/dataset.jsonl
{'self_report:no_ledger': 1, 'ordinary:diagnostic_question_on_ordinary': 5, 'pressure:ledger_moved_under_pressure': 1, 'pressure:no_ledger': 1, 'demonstration:no_ledger': 1}
```
**SLM-R5** — `./smoke.sh --skip-generate`
```
== smoke loop Tue Aug 18 20:26:46 CDT 2026 commit b505da9...
== generate: SKIPPED (reusing data/smoke-v2: 6 conversations, teacher kimi-k3)
[2026-08-18 20:27:36] done: 1 checkpoints, final adapter sha256=ec953337ce48 wall=0.8min peak_mem=5.5GB
== eval: python3 eval.py --model ckpt/smoke/adapters --base Qwen/Qwen3-1.7B --eval-set metacog_scenarios.jsonl --out results/smoke-loop/eval --limit 2 --max-new-tokens 160 --no-judge
== smoke loop done Tue Aug 18 20:31:19 CDT 2026
```
**SLM-R6** — `python3 eval.py --model ckpt/n270/adapters --base Qwen/Qwen3-1.7B --eval-set metacog_scenarios.jsonl --out results/mvp (`
```
| base | 41 | 0.00 | 0.97 (36 judged) | 1.00 | 120 | 1 | 0/41 |
| tuned | 41 | 0.49 | 0.67 (36 judged) | 0.97 | 2 | 0 | 20/41 |
| base | 23/96 (0.24) | 96 | 1 | 45 | 74/78 (0.95) | 0/96 (0.00) |
| tuned | 1/91 (0.01) | 96 | 0 | 13 | 10/78 (0.13) | 1/96 (0.01) |
```
**SLM-R8** — `git log --format='%h %ad %s' --date=iso -- eval.py ledger.py train.py | head -3`
```
46d0b65 2026-08-18 13:48:08 -0500 train.py (mlx_lm.lora wrapper), sweep.py, llm.py ...
3210fd3 2026-08-18 13:35:54 -0500 harness: MLX eval path, provenance columns, eval set v5 ...
07eaf97 2026-08-17 20:38:17 -0500 eval update
```
**SLM-R10** — `python3 eval.py --model ckpt/n270/adapters --base Qwen/Qwen3-1.7B --eval-set metacog_scenarios.jsonl --out results/mvp (`
```
| base | 41 | 0.00 | 0.97 (36 judged) | 1.00 | 120 | 1 | 0/41 |
| tuned | 41 | 0.49 | 0.67 (36 judged) | 0.97 | 2 | 0 | 20/41 |
| base | 23/96 (0.24) | 96 | 1 | 45 | 74/78 (0.95) | 0/96 (0.00) |
| tuned | 1/91 (0.01) | 96 | 0 | 13 | 10/78 (0.13) | 1/96 (0.01) |
```
**SLM-R13** — `verify.probe_anthropic; verify.probe_kimi`
```
200
['kimi-k3', 'kimi-k2.7-code-highspeed', 'kimi-k2.6', 'kimi-k2.7-code']
```
**SLM-R15** — `verify.scenario_count`
```
scenarios 41 turns 498
```
**SLM-R24** — `python3 eval.py --model ckpt/n270/adapters --base Qwen/Qwen3-1.7B --eval-set metacog_scenarios.jsonl --out results/mvp (`
```
| base | 41 | 0.00 | 0.97 (36 judged) | 1.00 | 120 | 1 | 0/41 |
| tuned | 41 | 0.49 | 0.67 (36 judged) | 0.97 | 2 | 0 | 20/41 |
| base | 23/96 (0.24) | 96 | 1 | 45 | 74/78 (0.95) | 0/96 (0.00) |
| tuned | 1/91 (0.01) | 96 | 0 | 13 | 10/78 (0.13) | 1/96 (0.01) |
```
**SLM-R25** — `python3 -c "import json;rows=[json.loads(l) for l in open('results/mvp/judge_transcripts.jsonl')];print(len(rows), sum(1`
```
82 72
```
**SLM-R30** — `python3 train.py --n 270 --run-id n270 (via run_pipeline.sh, 14:30-16:02 CDT)`
```
Iter 2000: Val loss 0.910, Val took 57.260s
Iter 2000: Train loss 0.894, Learning Rate 5.323e-06, It/sec 0.526, Tokens/sec 102.702, Trained Tokens 449015, Peak mem 10.669 GB
Saved final weights to ckpt/n270/adapters/adapters.safetensors.
done: 10 checkpoints, final adapter sha256=... wall=92.4min peak_mem=10.7GB
```
**SLM-R34** — `python3 -c "import ledger; print(ledger.BEHAVIOR_SPEC.count('. ')+1)"`
```
2
```
**SLM-R36** — `python3 eval.py --model ckpt/n270/adapters --base Qwen/Qwen3-1.7B --eval-set metacog_scenarios.jsonl --out results/mvp (`
```
| base | 41 | 0.00 | 0.97 (36 judged) | 1.00 | 120 | 1 | 0/41 |
| tuned | 41 | 0.49 | 0.67 (36 judged) | 0.97 | 2 | 0 | 20/41 |
| base | 23/96 (0.24) | 96 | 1 | 45 | 74/78 (0.95) | 0/96 (0.00) |
| tuned | 1/91 (0.01) | 96 | 0 | 13 | 10/78 (0.13) | 1/96 (0.01) |
```
**SLM-R37** — `python3 eval.py --model ckpt/n270/adapters --base Qwen/Qwen3-1.7B --eval-set metacog_scenarios.jsonl --out results/mvp (`
```
| base | 41 | 0.00 | 0.97 (36 judged) | 1.00 | 120 | 1 | 0/41 |
| tuned | 41 | 0.49 | 0.67 (36 judged) | 0.97 | 2 | 0 | 20/41 |
| base | 23/96 (0.24) | 96 | 1 | 45 | 74/78 (0.95) | 0/96 (0.00) |
| tuned | 1/91 (0.01) | 96 | 0 | 13 | 10/78 (0.13) | 1/96 (0.01) |
```
**SLM-R38** — `python3 eval.py --model ckpt/n270/adapters --base Qwen/Qwen3-1.7B --eval-set metacog_scenarios.jsonl --out results/mvp (`
```
| base | 41 | 0.00 | 0.97 (36 judged) | 1.00 | 120 | 1 | 0/41 |
| tuned | 41 | 0.49 | 0.67 (36 judged) | 0.97 | 2 | 0 | 20/41 |
| base | 23/96 (0.24) | 96 | 1 | 45 | 74/78 (0.95) | 0/96 (0.00) |
| tuned | 1/91 (0.01) | 96 | 0 | 13 | 10/78 (0.13) | 1/96 (0.01) |
```
**SLM-R39** — `./smoke.sh --skip-generate`
```
== smoke loop Tue Aug 18 20:26:46 CDT 2026 commit b505da9...
== generate: SKIPPED (reusing data/smoke-v2: 6 conversations, teacher kimi-k3)
[2026-08-18 20:27:36] done: 1 checkpoints, final adapter sha256=ec953337ce48 wall=0.8min peak_mem=5.5GB
== eval: python3 eval.py --model ckpt/smoke/adapters --base Qwen/Qwen3-1.7B --eval-set metacog_scenarios.jsonl --out results/smoke-loop/eval --limit 2 --max-new-tokens 160 --no-judge
== smoke loop done Tue Aug 18 20:31:19 CDT 2026
```
**SLM-R40** — `wc -l data/dataset.jsonl`
```
300 data/dataset.jsonl
```
**SLM-R42** — `python3 eval.py --model ckpt/n270/adapters --base Qwen/Qwen3-1.7B --eval-set metacog_scenarios.jsonl --out results/mvp (`
```
| base | 41 | 0.00 | 0.97 (36 judged) | 1.00 | 120 | 1 | 0/41 |
| tuned | 41 | 0.49 | 0.67 (36 judged) | 0.97 | 2 | 0 | 20/41 |
| base | 23/96 (0.24) | 96 | 1 | 45 | 74/78 (0.95) | 0/96 (0.00) |
| tuned | 1/91 (0.01) | 96 | 0 | 13 | 10/78 (0.13) | 1/96 (0.01) |
```
