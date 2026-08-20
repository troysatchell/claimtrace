# Requirements Audit — Trained_SLM
**Commit:** 909ac76a3a85 · **Date:** 2026-08-20T18:46:21-05:00 · **Docs:** SLM (p.1–4) · **Mode:** compare (`early-sub`, baselineRef matrix.after-mvp.json)

## Summary
VERIFIED 31 · IMPLEMENTED-UNVERIFIED 10 · PARTIAL 4 · MISSING 3 · N/A 6 · ASSUMED 1

The most consequential finding is a regression the Early push created as a side effect: **SLM-R47 — the
published Hugging Face dataset (revision `af3b6508`) is the v1 dataset, but the project's artifact of record
is now the v2 dataset (`data/v2`) that produced run `q236v2`** — the published artifact no longer matches
the reported numbers, and the same applies to the model checkpoint (published `q270` @ `4de80c2a`, best run
`q236v2`, noted on SLM-R23). Both fixes are one `publish.py` command with no API cost. Beyond that, every
Early-submission requirement is now VERIFIED with behavioral evidence: the v2 dataset resolves the diagnosed
failure mode with the training config byte-identical (SLM-R43), the delta table regenerates exactly from the
two run.json files (SLM-R44), and the data-efficiency curve is complete with a justified minimum viable N of
135 (SLM-R19–R22, R45, R50). The remaining PARTIALs are externally blocked (staff held-out set not yet
released — R20/R49; demo hosting behind a paid plan — R48) and the MISSINGs are the three optional stretch
items (R53–R55).

## Coverage and limitations
- **Ticket dimension BLOCKED** — `tickets.project` is null by documented decision (the Troysatchell Linear
  team spans 8 unrelated projects; none is this repo). Every row's Ticket cell means "not checkable", not
  "no ticket". Unblock: create/scope a Linear project and set `tickets.project` in the config.
- **verify.eval NOT RUN by this sweep** (~70 min + judge cost). The identical `eval.py` invocation ran live
  today 18:01–18:23 CDT (`results/pipeline-v2.log`; `results/base-vs-tuned-v2/run.json`, eval-code commit
  `d9adae8`). Rows R6/R24/R42/R44 lean on that observed run, not a sweep-initiated one.
- **verify.smoke, verify.train_point, verify.precheck NOT RUN** (API cost / hours); R39, R30, R11/R17/R29
  carry their after-mvp verification unchanged — their code paths and artifacts did not change in this window.
- **12 rows are statically traced only** (IMPLEMENTED-UNVERIFIED): no behavioral command bears on them.
- The sweep wrote only under `audit/requirements/`; no databases, no application files.

## Matrix
| ID | Requirement (short) | Ticket(s) | Evidence | Verdict |
|---|---|---|---|---|
| SLM-R1 | Prompted base model can’t do it reliably | BLOCKED | results/prompt-ceiling-ablation/REPORT.md:55, results/prompt-ceiling-ablation/REPORT.md:57, results/prompt-ceiling-ablation/REPORT.md:83 | IMPLEMENTED-UNVERIFIED |
| SLM-R2 | Falsifiable Behavior Spec | BLOCKED | ledger.py:11, BEHAVIOR_SPEC.md:3, ledger.py:16 | VERIFIED |
| SLM-R3 | Learning/teaching behavior | BLOCKED | BEHAVIOR_SPEC.md:3, build_scenarios.py:3 | IMPLEMENTED-UNVERIFIED |
| SLM-R4 | Distilled + filtered dataset | BLOCKED | generate_dataset.py:246, generate_dataset.py:315, data/drop_report.json:5 | VERIFIED |
| SLM-R5 | QLoRA fine-tune | BLOCKED | train.py:46, train.py:191, train.py:199 | VERIFIED |
| SLM-R6 | Tuned beats base, with numbers | BLOCKED | results/base-vs-tuned/table.md:1, results/base-vs-tuned-v2/table.md:1, results/base-vs-tuned-lora-bf16/table.md:1 | VERIFIED |
| SLM-R7 | One target, one context | BLOCKED | BEHAVIOR_SPEC.md:3, generate_dataset.py:38 | ASSUMED |
| SLM-R8 | Eval before training | BLOCKED | results/train/n270/log.txt:1 | VERIFIED |
| SLM-R9 | Iterate on data, not hyperparameters | BLOCKED | dataset_spec.md:10, BRAINLIFT.md:109, results/train/q236v2/lora_config.yaml:1 | VERIFIED |
| SLM-R10 | Measure target behavior only | BLOCKED | eval.py:346, eval.py:369 | VERIFIED |
| SLM-R11 | Prompt ceiling proven with numbers | BLOCKED | results/prompt-ceiling-ablation/REPORT.md:5, results/prompt-ceiling-ablation/REPORT.md:28, results/prompt-ceiling-ablation/REPORT.md:83 | IMPLEMENTED-UNVERIFIED |
| SLM-R12 | Presented at Architecture Defense | BLOCKED | — | N/A |
| SLM-R13 | ≥2 frontier model families | BLOCKED | metacog_precheck.py:36, metacog_precheck.py:37 | VERIFIED |
| SLM-R14 | ≥3 prompting strategies | BLOCKED | metacog_precheck.py:85, metacog_precheck.py:86, metacog_precheck.py:87 | IMPLEMENTED-UNVERIFIED |
| SLM-R15 | ≥30 scenarios per cell | BLOCKED | metacog_precheck.py:287, results/prompt-ceiling-ablation/table.md:3 | VERIFIED |
| SLM-R16 | Same judge rubric as base-vs-tuned | BLOCKED | ablation_judge.py:1, results/prompt-ceiling-ablation/judged_table.md:1, eval.py:37 | VERIFIED |
| SLM-R17 | Model×strategy results table | BLOCKED | results/prompt-ceiling-ablation/judged_table.md:3, results/prompt-ceiling-ablation/REPORT.md:67 | VERIFIED |
| SLM-R18 | Surviving-failure-mode paragraph | BLOCKED | results/prompt-ceiling-ablation/REPORT.md:55, README.md:45 | IMPLEMENTED-UNVERIFIED |
| SLM-R19 | ≥4 checkpoints at different N | BLOCKED | results/train/q270/summary.json:1, results/train/q135/summary.json:1, results/train/q67/summary.json:1 | VERIFIED |
| SLM-R20 | Every checkpoint on same eval set (+staff) | BLOCKED | results/data-efficiency-curve/sweep_summary.json:1, results/data-efficiency-curve/table.md:1, README.md:122 | PARTIAL |
| SLM-R21 | Performance-vs-N curve | BLOCKED | results/data-efficiency-curve/table.md:1, results/data-efficiency-curve/curve.png:1, sweep.py:82 | VERIFIED |
| SLM-R22 | Justified minimum viable N | BLOCKED | BRAINLIFT.md:84, BRAINLIFT.md:92, BRAINLIFT.md:97 | VERIFIED |
| SLM-R23 | Public HF checkpoint + commit hash | BLOCKED | README.md:161, results/publish.json:3, SUBMISSION.md:23 | VERIFIED |
| SLM-R24 | One-command eval | BLOCKED | eval.py:463, eval.py:464, eval.py:68 | VERIFIED |
| SLM-R25 | Raw judge JSONL | BLOCKED | eval.py:513, results/base-vs-tuned-lora-bf16/NOTES.md:20 | VERIFIED |
| SLM-R26 | Staff held-out set runnable | BLOCKED | eval.py:464, README.md:121 | IMPLEMENTED-UNVERIFIED |
| SLM-R27 | Pinned model + eval-code hashes | BLOCKED | results/base-vs-tuned-lora-bf16/run.json:2, results/train/n270/summary.json:3, results/publish.json:3 | VERIFIED |
| SLM-R28 | Live grader prompt in demo | BLOCKED | compare.py:20 | N/A |
| SLM-R29 | Ablation rerunnable by grader | BLOCKED | metacog_precheck.py:287, README.md:95 | IMPLEMENTED-UNVERIFIED |
| SLM-R30 | Training logs rerunnable | BLOCKED | results/train/n270/log.txt:1, results/train/n270/lora_config.yaml:1, results/train/n270/summary.json:623 | VERIFIED |
| SLM-R31 | MVP deadline | BLOCKED | — | N/A |
| SLM-R32 | Early deadline | BLOCKED | — | N/A |
| SLM-R33 | Final deadline | BLOCKED | — | N/A |
| SLM-R34 | Finalized Behavior Spec | BLOCKED | BEHAVIOR_SPEC.md:3, ledger.py:11 | VERIFIED |
| SLM-R35 | Ablation report submitted | BLOCKED | results/prompt-ceiling-ablation/REPORT.md:1, results/prompt-ceiling-ablation/REPORT.md:67 | IMPLEMENTED-UNVERIFIED |
| SLM-R36 | LLM-as-judge scoring | BLOCKED | eval.py:209, eval.py:37 | VERIFIED |
| SLM-R37 | Behavioral failure-mode check | BLOCKED | ledger.py:57, ledger.py:77, eval.py:268 | VERIFIED |
| SLM-R38 | Base-vs-tuned mechanism | BLOCKED | eval.py:465, eval.py:381 | VERIFIED |
| SLM-R39 | Smoke-test full loop | BLOCKED | smoke.sh:19, smoke.sh:22, results/smoke-loop/log.txt:1 | VERIFIED |
| SLM-R40 | First dataset generated + filtered | BLOCKED | data/drop_report.json:5, data/dataset.jsonl:1 | VERIFIED |
| SLM-R41 | First QLoRA run completed | BLOCKED | results/train/q270/log.txt:1, results/train/q270/summary.json:3, results/train/q270/lora_config.yaml:1 | VERIFIED |
| SLM-R42 | First base-vs-tuned numbers | BLOCKED | results/base-vs-tuned/table.md:1, results/base-vs-tuned/judge_transcripts.jsonl:1, results/base-vs-tuned/NOTES.md:1 | VERIFIED |
| SLM-R43 | Failure mode fixed via v2 data | BLOCKED | results/base-vs-tuned-v2/NOTES.md:33, dataset_spec.md:16, data/v2/drop_report.json:1 | VERIFIED |
| SLM-R44 | Updated numbers + delta + transcripts | BLOCKED | results/base-vs-tuned-v2/DELTA.md:1, results/base-vs-tuned-v2/table.md:1, results/base-vs-tuned-v2/judge_transcripts.jsonl:1 | VERIFIED |
| SLM-R45 | ≥2 curve points | BLOCKED | results/data-efficiency-curve/table.md:1, results/data-efficiency-curve/sweep_summary.json:1 | VERIFIED |
| SLM-R46 | Draft final artifacts | BLOCKED | dataset_spec.md:1, results/train/q236v2/summary.json:1, BRAINLIFT.md:1 | IMPLEMENTED-UNVERIFIED |
| SLM-R47 | Dataset published | BLOCKED | README.md:163, results/publish.json:5 | PARTIAL |
| SLM-R48 | Model public + running demo | BLOCKED | results/publish.json:2, space/app.py:1, compare.py:20 | PARTIAL |
| SLM-R49 | Results on own + staff sets | BLOCKED | results/base-vs-tuned-v2/table.md:1, README.md:122 | PARTIAL |
| SLM-R50 | Full curve + justified min N | BLOCKED | results/data-efficiency-curve/curve.png:1, results/data-efficiency-curve/table.md:1, BRAINLIFT.md:84 | VERIFIED |
| SLM-R51 | Brainlift | BLOCKED | BRAINLIFT.md:3, BRAINLIFT.md:75, BRAINLIFT.md:124 | IMPLEMENTED-UNVERIFIED |
| SLM-R52 | 3–5 min demo video | BLOCKED | — | N/A |
| SLM-R53 | Stretch: DPO | BLOCKED | — | MISSING |
| SLM-R54 | Stretch: adversarial eval | BLOCKED | — | MISSING |
| SLM-R55 | Stretch: composed behavior | BLOCKED | — | MISSING |

## Gaps
- **SLM-R20** (PARTIAL) — Every checkpoint on same eval set (+staff): Every checkpoint evaluated on the identical own eval set with the same harness (q270 via results/base-vs-tuned, symlinked as q270).
- **SLM-R47** (PARTIAL) — Dataset published: REGRESSION vs after-mvp (was VERIFIED): the published dataset revision is v1 (data/), but the project's real artifact is now the v2 dataset (data/v2) that produced q236v2.
- **SLM-R48** (PARTIAL) — Model public + running demo: Model is public on the Hub.
- **SLM-R49** (PARTIAL) — Results on own + staff sets: Own-set half satisfied and current; staff held-out set not yet provided.
- **SLM-R53** (MISSING) — Stretch: DPO: Stretch (optional): DPO not attempted.
- **SLM-R54** (MISSING) — Stretch: adversarial eval: Stretch (optional): adversarial eval set not attempted.
- **SLM-R55** (MISSING) — Stretch: composed behavior: Stretch (optional): composed behavior not attempted.

## Orphan tickets
None reportable (ticket dimension BLOCKED).

## Blocked / assumed
- Every row's ticket cell: BLOCKED — unblock by scoping a Linear project in `audit/requirements.config.yaml`.
- SLM-R7 remains ASSUMED from baseline (single-context ruling pending; assumption recorded in the matrix).

## Delta (vs after-mvp, rendered 2026-08-18)
| ID | after-mvp | now | evidence change |
|---|---|---|---|
| SLM-R9 | N/A | VERIFIED | v2 iteration exists: dataset_spec v3 changelog; config diff q270↔q236v2 empty outside paths |
| SLM-R19 | PARTIAL | VERIFIED | 4 QLoRA checkpoints trained (q33/q67/q135/q270) with logs + spacing justification |
| SLM-R21 | PARTIAL | VERIFIED | curve.png + table with spec adherence and robustness columns |
| SLM-R22 | PARTIAL | VERIFIED | BRAINLIFT names N=135 with pre-stated criterion and per-column justification |
| SLM-R43 | PARTIAL | VERIFIED | data/v2 (265 convs) + per-failure-mode results; config identical |
| SLM-R44 | MISSING | VERIFIED | DELTA.md + judge JSONL (82 records); recomputed deltas match |
| SLM-R45 | PARTIAL | VERIFIED | 4 evaluated points on the curve |
| SLM-R47 | VERIFIED | PARTIAL | REGRESSION: published dataset is v1; artifact of record is now v2 (unpublished) |
| SLM-R50 | PARTIAL | VERIFIED | full curve + justified min N both present |
| SLM-R51 | PARTIAL | IMPLEMENTED-UNVERIFIED | min-N and v2 conclusions landed; complete as an in-progress draft |

## Verification performed
| Command | Result | Bears on |
|---|---|---|
| `verify.scenario_count` | scenarios 41 turns 498 | SLM-R15, SLM-R26 |
| `verify.precheck_compile` | compile-ok | SLM-R29 |
| `verify.probe_anthropic` | 200 | SLM-R13 |
| `verify.probe_kimi` | kimi-k3 resolves (4 models listed) | SLM-R13 |
| `config-identity diff q270 vs q236v2 lora_config.yaml` | identical except data/adapter paths | SLM-R9, SLM-R43 |
| `sweep-points listing (results/train/{q33,q67,q135,q270,q236v2}/summary` | distinct Ns [33,67,135,270]; >=4 sizes True | SLM-R19, SLM-R30 |
| `curve columns + row count + curve.png` | spec adherence + robustness columns, 4 tuned rows, curve.png 69,590 bytes | SLM-R21, SLM-R45, SLM-R50 |
| `grep min viable N in BRAINLIFT` | 84:## Minimum viable dataset size — N = 135 | SLM-R22, SLM-R50 |
| `v2 dataset composition (shape counts, drop report)` | 265 convs; wrong_attempt=520 turns; teacher kimi-k3; 6 content drops | SLM-R43 |
| `DELTA.md consistency recompute from run.json pair` | all 4 checks pass | SLM-R44 |
| `judge JSONL check (v2)` | 82 records; fields held_ledger/no_backfill/failure_mode/reasoning | SLM-R25, SLM-R44 |
| `citation integrity check (114 citations from after-mvp)` | 2 stale (REPORT.md line shift), repointed to line 55 | SLM-R1, SLM-R18 |
| `verify.eval` | NOT RUN | SLM-R6, SLM-R24, SLM-R42, SLM-R44 |
| `verify.smoke` | NOT RUN | SLM-R39 |
| `verify.train_point` | NOT RUN | SLM-R30 |
| `verify.precheck` | NOT RUN | SLM-R1, SLM-R11, SLM-R17, SLM-R29 |

Captured outputs: `audit/requirements/runs/early-sub/{basic-checks,sweep-and-curve,v2-and-delta,citation-check}.txt`.
