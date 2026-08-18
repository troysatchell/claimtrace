# Requirements Inventory — Trained_SLM

Source of truth for WHAT the brief requires. Extracted 2026-08-17 from
`Train_Your_Own_Small_Learning_Model.pdf` (doc ID `SLM`, sha256 `e4844d5f…5660b6`,
4 pages). Quotes are verbatim and verified against `source-SLM.md`. Your edits to
this file are authoritative over the extraction; IDs are stable and never reused.

Conventions used in **Meaning in code**: "harness" = the eval code that scores model
output against the Behavior Spec; "precheck" = `metacog_precheck.py`, the current
prompt-ceiling ablation script; "verify.X" = a label in
`audit/requirements.config.yaml`.

Not extracted (background/suggestions, not gradable): the *Background* section, the
*Why this is the gate* consequence paragraph (its obligation is SLM-R1/R11), the
*Stack Suggestions* section, and the *Submission Timeline* grid (its deadlines are
carried by SLM-R31–R33 which quote the section headers).

---

## SLM-R1
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.1
- **Quote:** "A well-prompted base model can't already do it reliably."
- **Meaning in code:** The chosen target behavior is one that a prompted frontier model measurably fails to hold over a long conversation — evidenced by the Prompt-Ceiling Ablation numbers (SLM-R11) showing a plateau below the reliability bar.
- **Type:** functional
- **Acceptance evidence:** verify.precheck — a completed run whose results table shows spec-adherence plateauing below the stated reliability bar for the best strategy on every model.
- **Status:** active

## SLM-R2
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.1
- **Quote:** "Your first deliverable, before any code, is a falsifiable Behavior Spec: one or two sentences a stranger could use to mark any model output pass/fail."
- **Meaning in code:** A standalone Behavior Spec text (README/BEHAVIOR_SPEC.md or a single named constant) of one or two sentences that yields a pass/fail for any single model output without further context.
- **Type:** functional
- **Acceptance evidence:** file:line of the spec text; the same text is what the harness's judge rubric and the data-generation prompt cite.
- **Status:** active

## SLM-R3
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.1
- **Quote:** "Choose a specific learning or teaching behavior."
- **Meaning in code:** The Behavior Spec and eval scenarios are about a tutoring/learning interaction behavior (not a general assistant task).
- **Type:** functional
- **Acceptance evidence:** file:line of the spec + scenario file showing a learning/teaching context.
- **Status:** active

## SLM-R4
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.1
- **Quote:** "generate a distilled dataset that embodies it"
- **Meaning in code:** A data-generation pipeline that calls a frontier teacher model with a generation prompt derived from the spec, then applies a quality filter, producing a training dataset file.
- **Type:** functional
- **Acceptance evidence:** file:line of the generation script + filter step; a produced dataset artifact (JSONL/parquet) in the repo or referenced by hash/URL.
- **Status:** active

## SLM-R5
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.1
- **Quote:** "fine-tune a small open base model (QLoRA) to hold it"
- **Meaning in code:** A QLoRA training script/config (Unsloth/TRL/PEFT/Axolotl) targeting a small open base model (≈0.6B–4B) that consumes the generated dataset.
- **Type:** functional
- **Acceptance evidence:** file:line of the training entrypoint and its QLoRA/LoRA config (4-bit load + LoRA adapters).
- **Status:** active

## SLM-R6
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.1
- **Quote:** "prove — with numbers, not claims — that the tuned model beats the base model at your target behavior."
- **Meaning in code:** The harness produces a base-vs-tuned results table on the same eval set, with the tuned model scoring higher on the spec metric.
- **Type:** functional
- **Acceptance evidence:** verify.eval — results table artifact with both base and tuned rows on the same eval set.
- **Status:** active

## SLM-R7
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.2
- **Quote:** "One target, one context. No broad domains — diffuse data makes a mushy model."
- **Meaning in code:** The spec, scenarios, and dataset are scoped to a single behavior in a single interaction context; the dataset generator does not mix unrelated tasks or contexts.
- **Type:** functional
- **Acceptance evidence:** file:line of the spec/scenario/generation-prompt scope; every scenario and dataset row shares the one target behavior and context.
- **Status:** active

## SLM-R8
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.2
- **Quote:** "No training before the eval exists. Build the eval harness first, or you have no way to know if you improved anything."
- **Meaning in code:** The eval harness commit predates the first training run (git history / training-log timestamps).
- **Type:** process
- **Acceptance evidence:** commit SHAs or timestamps showing harness before first training log; recorded in notes (no file:line form).
- **Status:** active

## SLM-R9
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.2
- **Quote:** "A disappointing model is almost always a data problem. Don't tune hyperparameters to fix bad data."
- **Meaning in code:** Iteration between checkpoints changes the dataset (v2, v3 …) rather than the training config; a changelog/README records data changes as the lever.
- **Type:** process
- **Acceptance evidence:** file:line of an iteration log or dataset version notes; training config unchanged across iterations (see SLM-R43).
- **Status:** active

## SLM-R10
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.2
- **Quote:** "Don't chase capability benchmarks. Measure your target behavior, not trivia accuracy."
- **Meaning in code:** The harness's metrics are spec adherence / robustness on target-behavior scenarios; no MMLU-style capability benchmark is used as the success metric.
- **Type:** functional
- **Acceptance evidence:** file:line of the harness's metric definitions.
- **Status:** active

## SLM-R11
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.2
- **Quote:** "Before you write a line of fine-tuning code, prove (with numbers) that prompting has a real ceiling below your reliability bar."
- **Meaning in code:** A completed Prompt-Ceiling Ablation run (script + results) exists, with a stated reliability bar and numbers showing the best prompting strategy stays below it.
- **Type:** functional
- **Acceptance evidence:** verify.precheck — green run producing a results table; a stated reliability bar in the report; the ablation results committed before any training code appears.
- **Status:** active

## SLM-R12
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.2
- **Quote:** "This is presented live at your Architecture Defense, using the calendar checkpoint already on the timeline."
- **Meaning in code:** The ablation report is presented at the Architecture Defense (timeline: "Defense (due 4 hrs after assignment)", p.3). Not code-traceable.
- **Type:** process
- **Acceptance evidence:** N/A for the code sweep — presentation event.
- **Status:** active

## SLM-R13
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.2
- **Quote:** "At least 2 frontier models from different model families."
- **Meaning in code:** The ablation script's model list contains ≥2 frontier models from different providers/families, each pinned to an exact API model id that resolves against the provider.
- **Type:** functional
- **Acceptance evidence:** file:line of the model list; verify.probe_anthropic + verify.probe_kimi confirm the pinned ids resolve.
- **Status:** active

## SLM-R14
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.2
- **Quote:** "At least 3 prompting strategies per model: zero-shot, few-shot with in-context examples, and a structured or chain-of-thought system prompt."
- **Meaning in code:** The ablation script defines and runs three strategies per model: zero-shot, few-shot (with in-context examples), and a structured/CoT system prompt.
- **Type:** functional
- **Acceptance evidence:** file:line of the strategy definitions and the model×strategy job loop.
- **Status:** active

## SLM-R15
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.2
- **Quote:** "Minimum 30 scenarios per model × strategy combination"
- **Meaning in code:** The ablation scenario set has ≥30 scenarios and every model×strategy cell is run over all of them.
- **Type:** functional
- **Acceptance evidence:** verify.scenario_count ≥ 30; file:line of the job loop iterating all scenarios per cell.
- **Status:** active

## SLM-R16
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.2
- **Quote:** "scored against your Behavior Spec using the same LLM-as-judge rubric you'll use later for base-vs-tuned comparison."
- **Meaning in code:** The ablation's per-turn/per-example score comes from an LLM-as-judge call using the same rubric module the base-vs-tuned harness imports (single shared judge implementation).
- **Type:** functional
- **Acceptance evidence:** file:line of the shared judge rubric and its import in both the ablation script and the harness.
- **Status:** active

## SLM-R17
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.2
- **Quote:** "A results table (mean Spec-adherence and Robustness per model × strategy)"
- **Meaning in code:** The ablation emits a table with one row per model×strategy and columns for mean Spec-adherence and Robustness.
- **Type:** functional
- **Acceptance evidence:** verify.precheck — table artifact with those two named metrics per model×strategy row.
- **Status:** active

## SLM-R18
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.2
- **Quote:** "plus a short paragraph naming the specific failure mode that survives your best prompting attempt."
- **Meaning in code:** The ablation report contains a written paragraph naming the surviving failure mode.
- **Type:** functional
- **Acceptance evidence:** file:line of the paragraph in the ablation report (markdown).
- **Status:** active

## SLM-R19
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.2
- **Quote:** "Train at least 4 checkpoints at different dataset sizes (e.g. a log-spaced sweep such as N, N/2, N/4, N/8 — choose and justify your own spacing)."
- **Meaning in code:** Training config/logs for ≥4 checkpoints at distinct dataset sizes, with the spacing choice justified in writing.
- **Type:** functional
- **Acceptance evidence:** file:line of the sweep config/logs listing ≥4 sizes; justification text.
- **Status:** active

## SLM-R20
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.2
- **Quote:** "Evaluate every checkpoint on the same eval set (your own plus the staff held-out set) using your existing harness — no new rubric needed."
- **Meaning in code:** Eval results for each checkpoint on the identical eval set, produced by the same harness (verify.eval), including a held-out set path.
- **Type:** functional
- **Acceptance evidence:** verify.eval run per checkpoint; per-checkpoint results artifacts referencing the same eval-set path.
- **Status:** active

## SLM-R21
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.2
- **Quote:** "Report a performance-vs-N curve for at least Spec adherence and Robustness."
- **Meaning in code:** A curve (plot or table) of Spec adherence and Robustness vs dataset size N.
- **Type:** functional
- **Acceptance evidence:** file:line of the curve artifact/plotting script.
- **Status:** active

## SLM-R22
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.2
- **Quote:** "Identify and justify the smallest N that holds the behavior reliably — this becomes your stated "minimum viable dataset size" in your Brainlift."
- **Meaning in code:** A stated minimum viable N with justification tied to the curve, recorded in the Brainlift.
- **Type:** functional
- **Acceptance evidence:** file:line in the Brainlift naming N and citing the curve.
- **Status:** active

## SLM-R23
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.3
- **Quote:** "Pushed to Hugging Face Hub (public repo) with the exact commit hash referenced in your submission. Graders pull and run it themselves."
- **Meaning in code:** A public HF Hub model repo id and its exact commit hash appear in the submission (README/eval config); the model loads from that revision.
- **Type:** functional
- **Acceptance evidence:** file:line of the HF repo id + commit hash; verify.eval loads it by revision.
- **Status:** active

## SLM-R24
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.3
- **Quote:** "`eval.py --model <hf-repo-id> --eval-set <path>` regenerates your full results table from nothing. If it takes more than one command, it isn't verified."
- **Meaning in code:** An `eval.py` at repo root accepting `--model` and `--eval-set` that runs generation + judging + aggregation and writes the full results table in one invocation.
- **Type:** functional
- **Acceptance evidence:** verify.eval — a single command produces the results table.
- **Status:** active

## SLM-R25
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.3
- **Quote:** "Full per-example LLM-as-judge output (score + reasoning) submitted as a JSONL file — not just the aggregate score table."
- **Meaning in code:** The harness writes a JSONL of per-example judge records each carrying score and reasoning, alongside the aggregate table.
- **Type:** functional
- **Acceptance evidence:** file:line of the JSONL writer; a produced transcripts JSONL with score+reasoning fields.
- **Status:** active

## SLM-R26
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.3
- **Quote:** "At grading time, your eval harness will also be run against a scenario set you never saw. This is graded — it's the primary check against overfitting your eval to your own training data."
- **Meaning in code:** The harness takes an arbitrary eval-set path (no hard-coded scenarios) and documents the input schema so a staff set can be dropped in.
- **Type:** functional
- **Acceptance evidence:** file:line of the `--eval-set` loader + schema doc.
- **Status:** active

## SLM-R27
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.3
- **Quote:** "Exact HF model commit hash and exact eval-code commit hash included in your submission. Numbers must be reproducible against a specific, frozen state."
- **Meaning in code:** Submission doc records both the HF model revision hash and the eval-code git commit hash.
- **Type:** process
- **Acceptance evidence:** file:line of the two hashes in README/submission notes.
- **Status:** active

## SLM-R28
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.3
- **Quote:** "Part of your demo video must show a grader-supplied prompt run live against base vs. tuned — not only pre-selected examples."
- **Meaning in code:** Demo video contains a live grader-supplied prompt run against base and tuned. (A single-prompt base-vs-tuned runner in the repo is what makes this demonstrable.)
- **Type:** process
- **Acceptance evidence:** video link in submission; N/A for the code sweep beyond the runner's existence.
- **Status:** active

## SLM-R29
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.3
- **Quote:** "Prompt-Ceiling Ablation script and Data-Efficiency training logs included, so a grader can rerun at least one sample point from each ablation."
- **Meaning in code:** The Prompt-Ceiling Ablation script is in the repo and runnable end-to-end by a grader for at least one model×strategy×scenario point.
- **Type:** functional
- **Acceptance evidence:** verify.precheck runs green for at least one cell.
- **Status:** active

## SLM-R30
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.3
- **Quote:** "Prompt-Ceiling Ablation script and Data-Efficiency training logs included, so a grader can rerun at least one sample point from each ablation."
- **Meaning in code:** Data-Efficiency training logs (per-checkpoint) are included so a grader can rerun at least one N.
- **Type:** functional
- **Acceptance evidence:** file:line of committed training logs + the config that reproduces one point.
- **Status:** active

## SLM-R31
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.3
- **Quote:** "MVP — due Tuesday at midnight"
- **Meaning in code:** Deadline for the MVP bundle (SLM-R34–R42). Not code-traceable.
- **Type:** process
- **Acceptance evidence:** N/A — calendar deadline.
- **Status:** active

## SLM-R32
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.3
- **Quote:** "Early Submission — due Thursday at midnight"
- **Meaning in code:** Deadline for the Early Submission bundle (SLM-R43–R46). Not code-traceable.
- **Type:** process
- **Acceptance evidence:** N/A — calendar deadline.
- **Status:** active

## SLM-R33
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.4
- **Quote:** "Final Submission — due Sunday at noon"
- **Meaning in code:** Deadline for the Final Submission bundle (SLM-R47–R52). Not code-traceable.
- **Type:** process
- **Acceptance evidence:** N/A — calendar deadline.
- **Status:** active

## SLM-R34
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.3
- **Quote:** "Finalized Behavior Spec (falsifiable, one to two sentences)."
- **Meaning in code:** Same artifact as SLM-R2, in its finalized form at MVP: one to two sentences, falsifiable.
- **Type:** functional
- **Acceptance evidence:** file:line of the finalized spec text (≤2 sentences).
- **Status:** active

## SLM-R35
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.3
- **Quote:** "Completed Prompt-Ceiling Ablation report (see Required Ablations) — presented at Architecture Defense, submitted in full here."
- **Meaning in code:** A written ablation report (results table + failure-mode paragraph + method) committed in the repo.
- **Type:** functional
- **Acceptance evidence:** file:line of the report document; it embeds/links the table from SLM-R17 and paragraph from SLM-R18.
- **Status:** active

## SLM-R36
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.3
- **Quote:** "Eval harness built and committed: LLM-as-judge scoring,"
- **Meaning in code:** Harness module implementing LLM-as-judge scoring of model outputs against the spec rubric.
- **Type:** functional
- **Acceptance evidence:** file:line of the judge call + rubric prompt; verify.eval exercises it.
- **Status:** active

## SLM-R37
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.3
- **Quote:** "a behavioral check for your spec's specific failure mode,"
- **Meaning in code:** A deterministic/programmatic check in the harness that detects the spec's specific failure mode (independent of the LLM judge).
- **Type:** functional
- **Acceptance evidence:** file:line of the check function and its use in the harness's per-example scoring.
- **Status:** active

## SLM-R38
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.3
- **Quote:** "and a base-vs-tuned comparison mechanism."
- **Meaning in code:** The harness can be pointed at both a base and a tuned model and emits a side-by-side comparison (delta) on the same eval set.
- **Type:** functional
- **Acceptance evidence:** file:line of the comparison/aggregation code; verify.eval run for base and tuned.
- **Status:** active

## SLM-R39
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.3
- **Quote:** "Full loop — generate → train → eval — runs end to end, demonstrated on a small smoke-test batch."
- **Meaning in code:** A documented smoke-test path (script/Makefile target) that runs generation, training, and eval end-to-end on a tiny batch, with a captured log.
- **Type:** functional
- **Acceptance evidence:** file:line of the smoke-test entrypoint + a committed run log.
- **Status:** active

## SLM-R40
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.3
- **Quote:** "First real dataset generated and filtered;"
- **Meaning in code:** A v1 dataset artifact produced by the generator with the quality filter applied (row counts before/after filter recorded).
- **Type:** functional
- **Acceptance evidence:** file:line of the dataset file or its manifest with pre/post-filter counts.
- **Status:** active

## SLM-R41
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.3
- **Quote:** "first real QLoRA training run completed."
- **Meaning in code:** A completed QLoRA training run producing an adapter/checkpoint, with its training log committed.
- **Type:** functional
- **Acceptance evidence:** file:line of the training log + checkpoint reference (HF revision).
- **Status:** active

## SLM-R42
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.3
- **Quote:** "First base-vs-tuned eval numbers submitted, using the format in Verification Requirements above."
- **Meaning in code:** A first results table (base vs tuned) plus raw judge JSONL, produced by `eval.py` per SLM-R24/R25.
- **Type:** functional
- **Acceptance evidence:** verify.eval — table + JSONL artifacts committed.
- **Status:** active

## SLM-R43
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.4
- **Quote:** "At least one specific failure mode diagnosed from your MVP eval, and resolved via a data change (v2 dataset) — not a training-config change."
- **Meaning in code:** A v2 dataset exists with a written diagnosis of the MVP failure mode it targets; the training config is unchanged between v1 and v2 runs.
- **Type:** functional
- **Acceptance evidence:** file:line of the diagnosis note + v2 dataset/manifest; diff of training configs is empty.
- **Status:** active

## SLM-R44
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.4
- **Quote:** "Updated base-vs-tuned eval numbers showing the delta from MVP, submitted with raw judge transcripts."
- **Meaning in code:** A second results table with an explicit delta vs the MVP numbers, plus the corresponding judge JSONL.
- **Type:** functional
- **Acceptance evidence:** file:line of the updated table + JSONL.
- **Status:** active

## SLM-R45
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.4
- **Quote:** "At least 2 points on your Data-Efficiency curve (see Required Ablations), or a documented reason you're behind."
- **Meaning in code:** Eval results for ≥2 checkpoints at different N, or a written note explaining the delay.
- **Type:** functional
- **Acceptance evidence:** file:line of the two data points (or the note).
- **Status:** active

## SLM-R46
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.4
- **Quote:** "Draft versions of your final artifacts: dataset shape, model checkpoint, in-progress Brainlift."
- **Meaning in code:** Draft dataset schema/sample, a draft checkpoint reference, and an in-progress Brainlift document exist in the repo.
- **Type:** functional
- **Acceptance evidence:** file:line of each of the three drafts.
- **Status:** active

## SLM-R47
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.4
- **Quote:** "The dataset, published — this is your real artifact."
- **Meaning in code:** The final dataset is published (HF Hub dataset repo or equivalent public location) and linked from the README.
- **Type:** functional
- **Acceptance evidence:** file:line of the public dataset link/id.
- **Status:** active

## SLM-R48
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.4
- **Quote:** "The model on Hugging Face Hub, public, plus a running inference demo."
- **Meaning in code:** Public HF model (SLM-R23) AND a running inference demo (HF Space / hosted endpoint / demo script) linked from the README.
- **Type:** functional
- **Acceptance evidence:** file:line of the demo link or demo entrypoint; the model link from SLM-R23.
- **Status:** active

## SLM-R49
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.4
- **Quote:** "Eval harness and results table — base vs. tuned, on your own eval set and on the staff held-out set."
- **Meaning in code:** Final results table with base and tuned rows for both the own eval set and the staff held-out set, generated by the harness.
- **Type:** functional
- **Acceptance evidence:** verify.eval — two table artifacts (own set, held-out set).
- **Status:** active

## SLM-R50
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.4
- **Quote:** "Full Data-Efficiency curve (performance vs. dataset size) with a justified minimum viable N."
- **Meaning in code:** The complete curve (SLM-R21) with ≥4 points and the justified minimum N (SLM-R22).
- **Type:** functional
- **Acceptance evidence:** file:line of the final curve artifact + justification.
- **Status:** active

## SLM-R51
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.4
- **Quote:** "Brainlift — your behavior thesis, and whether data → behavior held, with evidence."
- **Meaning in code:** A Brainlift document stating the behavior thesis and the evidence-backed conclusion on whether data → behavior held.
- **Type:** functional
- **Acceptance evidence:** file:line of the Brainlift document.
- **Status:** active

## SLM-R52
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.4
- **Quote:** "A 3–5 minute demo video showing the tuned model doing the thing the base model fails to do reliably, including one live, grader-supplied prompt."
- **Meaning in code:** A 3–5 minute video linked from the README, containing the live grader-supplied prompt segment (SLM-R28).
- **Type:** process
- **Acceptance evidence:** video link in submission; N/A for the code sweep.
- **Status:** active

## SLM-R53
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.4
- **Quote:** "DPO / preference tuning — build preference pairs (on-spec vs. off-spec) and run DPO on top of your SFT model; measure the delta over SFT alone."
- **Meaning in code:** (Stretch — optional, not pass/fail.) A preference-pair dataset and a DPO training run on top of the SFT checkpoint, with a measured delta vs SFT.
- **Type:** functional
- **Acceptance evidence:** file:line of the DPO pairs + run + delta table.
- **Status:** active

## SLM-R54
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.4
- **Quote:** "Adversarial / robustness eval — a hard eval set built specifically to break your behavior (jailbreak the tutor into giving answers, feed malformed input to the schema model); report robustness, not just clean-input performance."
- **Meaning in code:** (Stretch — optional, not pass/fail.) A separate adversarial eval set and a robustness column reported from it.
- **Type:** functional
- **Acceptance evidence:** file:line of the adversarial set + its results.
- **Status:** active

## SLM-R55
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.4
- **Quote:** "Composed behavior — instill a second, potentially competing constraint and show the model holds both at once."
- **Meaning in code:** (Stretch — optional, not pass/fail.) A second constraint added to the spec/dataset with eval evidence that both hold simultaneously.
- **Type:** functional
- **Acceptance evidence:** file:line of the composed spec + results.
- **Status:** active
