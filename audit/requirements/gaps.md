# Requirements gaps — Trained_SLM (2026-08-17T18:15:20Z, commit none/not-git)

Ticket dimension was BLOCKED (no Linear project for this repo), so *every* gap below is unticketed by definition — none could be checked against a ticket. Stretch items (SLM-R53–R55) are optional per the brief and listed last.

## Unticketed requirements
### SLM-R1 — PARTIAL
- **Quote:** "A well-prompted base model can't already do it reliably."
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.1
- **Meaning in code:** The chosen target behavior is one that a prompted frontier model measurably fails to hold over a long conversation — evidenced by the Prompt-Ceiling Ablation numbers (SLM-R11) showing a plateau below the reliability bar.
- **What is missing:** No completed run and no stated reliability bar exist, so the 'hard test' is unproven. metacog_precheck.py is, by its own docstring (line 6: 'deterministic checks -- no LLM judge'), a cheap precursor to the ablation, and it is currently non-runnable: call() (lines 122-126) builds `fn` but never invokes or returns it, so every reply is None and all 30 conversations fail at parse_ledger before any API request is made (verify.precheck exit: 30/30 FAILED, empty table).
- **Suggested scope:** Fix call() so the precheck runs, add a stated reliability bar to the ablation report, run ≥30 scenarios per cell, and record whether the best strategy plateaus below the bar.

### SLM-R2 — PARTIAL
- **Quote:** "Your first deliverable, before any code, is a falsifiable Behavior Spec: one or two sentences a stranger could use to mark any model output pass/fail."
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.1
- **Meaning in code:** A standalone Behavior Spec text (README/BEHAVIOR_SPEC.md or a single named constant) of one or two sentences that yields a pass/fail for any single model output without further context.
- **What is missing:** SPEC (lines 38-44) is falsifiable but is a multi-sentence system prompt, not a one-or-two-sentence standalone spec; no spec document exists.
- **Suggested scope:** Write a standalone BEHAVIOR_SPEC.md (or README section) of one or two sentences a stranger can apply pass/fail to any single output; have SPEC, the judge rubric, and the generation prompt cite it.

### SLM-R4 — MISSING
- **Quote:** "generate a distilled dataset that embodies it"
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.1
- **Meaning in code:** A data-generation pipeline that calls a frontier teacher model with a generation prompt derived from the spec, then applies a quality filter, producing a training dataset file.
- **What is missing:** No implementing code found in code_roots.
- **Suggested scope:** Add a generate.py that prompts a frontier teacher with the spec-derived generation prompt, applies a programmatic quality filter (e.g. the score_turn checks), and writes a JSONL dataset with pre/post-filter counts.

### SLM-R5 — MISSING
- **Quote:** "fine-tune a small open base model (QLoRA) to hold it"
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.1
- **Meaning in code:** A QLoRA training script/config (Unsloth/TRL/PEFT/Axolotl) targeting a small open base model (≈0.6B–4B) that consumes the generated dataset.
- **What is missing:** No implementing code found in code_roots.
- **Suggested scope:** Add a train.py (Unsloth/TRL) loading a small Instruct base in 4-bit with LoRA adapters, consuming the generated dataset; commit the config.

### SLM-R6 — MISSING
- **Quote:** "prove — with numbers, not claims — that the tuned model beats the base model at your target behavior."
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.1
- **Meaning in code:** The harness produces a base-vs-tuned results table on the same eval set, with the tuned model scoring higher on the spec metric.
- **What is missing:** No implementing code found in code_roots.
- **Suggested scope:** Ships when eval.py (SLM-R24) exists: run it for base and tuned on the same eval set and commit the two-row results table.

### SLM-R10 — MISSING
- **Quote:** "Don't chase capability benchmarks. Measure your target behavior, not trivia accuracy."
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.2
- **Meaning in code:** The harness's metrics are spec adherence / robustness on target-behavior scenarios; no MMLU-style capability benchmark is used as the success metric.
- **What is missing:** No implementing code found in code_roots. No eval harness exists to trace metrics for. The precheck's deterministic metrics (score_turn, lines 155-170) are behavior-targeted, which is the intended direction.
- **Suggested scope:** Ships when the harness exists: define its metrics as spec adherence / robustness on target-behavior scenarios (the precheck's ledger_rate / unearned / no_elicit at metacog_precheck.py:155-170 are the right shape) and use no capability benchmark.

### SLM-R11 — PARTIAL
- **Quote:** "Before you write a line of fine-tuning code, prove (with numbers) that prompting has a real ceiling below your reliability bar."
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.2
- **Meaning in code:** A completed Prompt-Ceiling Ablation run (script + results) exists, with a stated reliability bar and numbers showing the best prompting strategy stays below it.
- **What is missing:** Script exists but produced no numbers. metacog_precheck.py is, by its own docstring (line 6: 'deterministic checks -- no LLM judge'), a cheap precursor to the ablation, and it is currently non-runnable: call() (lines 122-126) builds `fn` but never invokes or returns it, so every reply is None and all 30 conversations fail at parse_ledger before any API request is made (verify.precheck exit: 30/30 FAILED, empty table).
- **Suggested scope:** Fix call() (return fn(model_id, system, messages)), state the reliability bar, expand to ≥30 scenarios, run, and commit the numbers with the report.

### SLM-R15 — PARTIAL
- **Quote:** "Minimum 30 scenarios per model × strategy combination"
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.2
- **Meaning in code:** The ablation scenario set has ≥30 scenarios and every model×strategy cell is run over all of them.
- **What is missing:** verify.scenario_count → 5 scenarios; the brief's floor is 30 per model×strategy.
- **Suggested scope:** Add at least 25 more long tutoring scenarios in the same JSONL shape (id/topic/turns[say,demo,new]) to reach the 30-per-cell floor.

### SLM-R16 — MISSING
- **Quote:** "scored against your Behavior Spec using the same LLM-as-judge rubric you'll use later for base-vs-tuned comparison."
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.2
- **Meaning in code:** The ablation's per-turn/per-example score comes from an LLM-as-judge call using the same rubric module the base-vs-tuned harness imports (single shared judge implementation).
- **What is missing:** No implementing code found in code_roots. metacog_precheck.py is deterministic by design (line 6: 'no LLM judge'); there is no LLM-as-judge and no shared rubric module.
- **Suggested scope:** Create a shared judge module (rubric prompt derived from the Behavior Spec, returns score + reasoning) and import it from both the ablation script and eval.py so both use the identical rubric.

### SLM-R17 — PARTIAL
- **Quote:** "A results table (mean Spec-adherence and Robustness per model × strategy)"
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.2
- **Meaning in code:** The ablation emits a table with one row per model×strategy and columns for mean Spec-adherence and Robustness.
- **What is missing:** Per-model×strategy table exists but reports ledger-specific mechanical metrics, not the two named metrics; the captured run produced a header-only table (0 rows).
- **Suggested scope:** Add mean Spec-adherence and Robustness columns (per model×strategy) computed from the shared judge scores; keep the mechanical columns as extra diagnostics.

### SLM-R18 — MISSING
- **Quote:** "plus a short paragraph naming the specific failure mode that survives your best prompting attempt."
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.2
- **Meaning in code:** The ablation report contains a written paragraph naming the surviving failure mode.
- **What is missing:** No implementing code found in code_roots.
- **Suggested scope:** Add an ablation report (markdown) with a paragraph naming the failure mode that survives the best prompt, once the run produces numbers.

### SLM-R19 — MISSING
- **Quote:** "Train at least 4 checkpoints at different dataset sizes (e.g. a log-spaced sweep such as N, N/2, N/4, N/8 — choose and justify your own spacing)."
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.2
- **Meaning in code:** Training config/logs for ≥4 checkpoints at distinct dataset sizes, with the spacing choice justified in writing.
- **What is missing:** No implementing code found in code_roots.
- **Suggested scope:** Add a sweep config/script training ≥4 checkpoints at N, N/2, N/4, N/8 (or a justified alternative) and commit per-checkpoint logs.

### SLM-R20 — MISSING
- **Quote:** "Evaluate every checkpoint on the same eval set (your own plus the staff held-out set) using your existing harness — no new rubric needed."
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.2
- **Meaning in code:** Eval results for each checkpoint on the identical eval set, produced by the same harness (verify.eval), including a held-out set path.
- **What is missing:** No implementing code found in code_roots.
- **Suggested scope:** Ships when eval.py and the sweep exist: run eval.py per checkpoint on the same --eval-set (own + held-out) and commit results.

### SLM-R21 — MISSING
- **Quote:** "Report a performance-vs-N curve for at least Spec adherence and Robustness."
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.2
- **Meaning in code:** A curve (plot or table) of Spec adherence and Robustness vs dataset size N.
- **What is missing:** No implementing code found in code_roots.
- **Suggested scope:** Add a plot/table script producing Spec adherence and Robustness vs N from the per-checkpoint results.

### SLM-R22 — MISSING
- **Quote:** "Identify and justify the smallest N that holds the behavior reliably — this becomes your stated "minimum viable dataset size" in your Brainlift."
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.2
- **Meaning in code:** A stated minimum viable N with justification tied to the curve, recorded in the Brainlift.
- **What is missing:** No implementing code found in code_roots.
- **Suggested scope:** State and justify the minimum viable N in the Brainlift, citing the curve.

### SLM-R23 — MISSING
- **Quote:** "Pushed to Hugging Face Hub (public repo) with the exact commit hash referenced in your submission. Graders pull and run it themselves."
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.3
- **Meaning in code:** A public HF Hub model repo id and its exact commit hash appear in the submission (README/eval config); the model loads from that revision.
- **What is missing:** No implementing code found in code_roots.
- **Suggested scope:** Push the tuned model to a public HF repo and record repo id + commit hash in the README/eval config.

### SLM-R24 — MISSING
- **Quote:** "`eval.py --model <hf-repo-id> --eval-set <path>` regenerates your full results table from nothing. If it takes more than one command, it isn't verified."
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.3
- **Meaning in code:** An `eval.py` at repo root accepting `--model` and `--eval-set` that runs generation + judging + aggregation and writes the full results table in one invocation.
- **What is missing:** No implementing code found in code_roots. verify.eval NOT RUN — eval.py does not exist.
- **Suggested scope:** Add eval.py with --model and --eval-set that runs generation, judging, and aggregation in one command and writes the full results table.

### SLM-R25 — MISSING
- **Quote:** "Full per-example LLM-as-judge output (score + reasoning) submitted as a JSONL file — not just the aggregate score table."
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.3
- **Meaning in code:** The harness writes a JSONL of per-example judge records each carrying score and reasoning, alongside the aggregate table.
- **What is missing:** No implementing code found in code_roots.
- **Suggested scope:** Ships with eval.py: write per-example judge records (score + reasoning) to a JSONL next to the table. The precheck's transcripts.jsonl writer (metacog_precheck.py:238-240) is a starting shape but records mechanical violations, not judge output.

### SLM-R26 — MISSING
- **Quote:** "At grading time, your eval harness will also be run against a scenario set you never saw. This is graded — it's the primary check against overfitting your eval to your own training data."
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.3
- **Meaning in code:** The harness takes an arbitrary eval-set path (no hard-coded scenarios) and documents the input schema so a staff set can be dropped in.
- **What is missing:** No implementing code found in code_roots.
- **Suggested scope:** Ships with eval.py: load scenarios from the --eval-set path (no hard-coded set) and document the schema (the precheck's --scenarios loader at metacog_precheck.py:213/218 shows the pattern).

### SLM-R27 — MISSING
- **Quote:** "Exact HF model commit hash and exact eval-code commit hash included in your submission. Numbers must be reproducible against a specific, frozen state."
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.3
- **Meaning in code:** Submission doc records both the HF model revision hash and the eval-code git commit hash.
- **What is missing:** No implementing code found in code_roots.
- **Suggested scope:** Add a submission section to the README recording the HF model revision hash and the eval-code git commit hash (requires initializing git).

### SLM-R29 — PARTIAL
- **Quote:** "Prompt-Ceiling Ablation script and Data-Efficiency training logs included, so a grader can rerun at least one sample point from each ablation."
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.3
- **Meaning in code:** The Prompt-Ceiling Ablation script is in the repo and runnable end-to-end by a grader for at least one model×strategy×scenario point.
- **What is missing:** Script is present but a grader cannot rerun even one point: metacog_precheck.py is, by its own docstring (line 6: 'deterministic checks -- no LLM judge'), a cheap precursor to the ablation, and it is currently non-runnable: call() (lines 122-126) builds `fn` but never invokes or returns it, so every reply is None and all 30 conversations fail at parse_ledger before any API request is made (verify.precheck exit: 30/30 FAILED, empty table).
- **Suggested scope:** Make call() return fn(model_id, system, messages); then a grader can rerun a single cell. Consider adding --models/--strategies/--limit flags so one sample point is cheap to reproduce.

### SLM-R30 — MISSING
- **Quote:** "Prompt-Ceiling Ablation script and Data-Efficiency training logs included, so a grader can rerun at least one sample point from each ablation."
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.3
- **Meaning in code:** Data-Efficiency training logs (per-checkpoint) are included so a grader can rerun at least one N.
- **What is missing:** No implementing code found in code_roots.
- **Suggested scope:** Commit per-checkpoint training logs from the data-efficiency sweep with the config needed to reproduce one N.

### SLM-R34 — PARTIAL
- **Quote:** "Finalized Behavior Spec (falsifiable, one to two sentences)."
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.3
- **Meaning in code:** Same artifact as SLM-R2, in its finalized form at MVP: one to two sentences, falsifiable.
- **What is missing:** Same artifact as SLM-R2; not finalized as a standalone one-to-two-sentence spec.
- **Suggested scope:** Same as SLM-R2: a finalized ≤2-sentence standalone spec.

### SLM-R35 — MISSING
- **Quote:** "Completed Prompt-Ceiling Ablation report (see Required Ablations) — presented at Architecture Defense, submitted in full here."
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.3
- **Meaning in code:** A written ablation report (results table + failure-mode paragraph + method) committed in the repo.
- **What is missing:** No implementing code found in code_roots.
- **Suggested scope:** Add ABLATION_REPORT.md: method, results table (SLM-R17), surviving-failure-mode paragraph (SLM-R18), reliability bar.

### SLM-R36 — MISSING
- **Quote:** "Eval harness built and committed: LLM-as-judge scoring,"
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.3
- **Meaning in code:** Harness module implementing LLM-as-judge scoring of model outputs against the spec rubric.
- **What is missing:** No implementing code found in code_roots.
- **Suggested scope:** Add the LLM-as-judge scoring module to the harness (shared with the ablation per SLM-R16).

### SLM-R37 — PARTIAL
- **Quote:** "a behavioral check for your spec's specific failure mode,"
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.3
- **Meaning in code:** A deterministic/programmatic check in the harness that detects the spec's specific failure mode (independent of the LLM judge).
- **What is missing:** Behavioral checks for the spec's failure modes exist, but only inside the ablation precheck; no eval harness applies them to base/tuned model outputs.
- **Suggested scope:** Reuse score_turn/parse_ledger inside eval.py so every base/tuned example gets the behavioral check alongside the judge score.

### SLM-R38 — MISSING
- **Quote:** "and a base-vs-tuned comparison mechanism."
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.3
- **Meaning in code:** The harness can be pointed at both a base and a tuned model and emits a side-by-side comparison (delta) on the same eval set.
- **What is missing:** No implementing code found in code_roots.
- **Suggested scope:** Ships with eval.py: accept two --model values (or run twice) and emit a side-by-side delta table.

### SLM-R39 — MISSING
- **Quote:** "Full loop — generate → train → eval — runs end to end, demonstrated on a small smoke-test batch."
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.3
- **Meaning in code:** A documented smoke-test path (script/Makefile target) that runs generation, training, and eval end-to-end on a tiny batch, with a captured log.
- **What is missing:** No implementing code found in code_roots.
- **Suggested scope:** Add a smoke target (Makefile/script) chaining generate → train → eval on a tiny batch and commit its log.

### SLM-R40 — MISSING
- **Quote:** "First real dataset generated and filtered;"
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.3
- **Meaning in code:** A v1 dataset artifact produced by the generator with the quality filter applied (row counts before/after filter recorded).
- **What is missing:** No implementing code found in code_roots.
- **Suggested scope:** Ships when generate.py (SLM-R4) exists: commit the v1 dataset (or manifest) with pre/post-filter counts.

### SLM-R41 — MISSING
- **Quote:** "first real QLoRA training run completed."
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.3
- **Meaning in code:** A completed QLoRA training run producing an adapter/checkpoint, with its training log committed.
- **What is missing:** No implementing code found in code_roots.
- **Suggested scope:** Ships when train.py (SLM-R5) exists: run once and commit the training log + checkpoint reference.

### SLM-R42 — MISSING
- **Quote:** "First base-vs-tuned eval numbers submitted, using the format in Verification Requirements above."
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.3
- **Meaning in code:** A first results table (base vs tuned) plus raw judge JSONL, produced by `eval.py` per SLM-R24/R25.
- **What is missing:** No implementing code found in code_roots.
- **Suggested scope:** Ships when eval.py exists: commit the first base-vs-tuned table + judge JSONL.

### SLM-R43 — MISSING
- **Quote:** "At least one specific failure mode diagnosed from your MVP eval, and resolved via a data change (v2 dataset) — not a training-config change."
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.4
- **Meaning in code:** A v2 dataset exists with a written diagnosis of the MVP failure mode it targets; the training config is unchanged between v1 and v2 runs.
- **What is missing:** No implementing code found in code_roots.
- **Suggested scope:** After MVP: write a diagnosis note for one failure mode, produce a v2 dataset targeting it, retrain with the identical config.

### SLM-R44 — MISSING
- **Quote:** "Updated base-vs-tuned eval numbers showing the delta from MVP, submitted with raw judge transcripts."
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.4
- **Meaning in code:** A second results table with an explicit delta vs the MVP numbers, plus the corresponding judge JSONL.
- **What is missing:** No implementing code found in code_roots.
- **Suggested scope:** After MVP: commit an updated results table with an explicit delta column vs MVP, plus the judge JSONL.

### SLM-R45 — MISSING
- **Quote:** "At least 2 points on your Data-Efficiency curve (see Required Ablations), or a documented reason you're behind."
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.4
- **Meaning in code:** Eval results for ≥2 checkpoints at different N, or a written note explaining the delay.
- **What is missing:** No implementing code found in code_roots.
- **Suggested scope:** Two checkpoints at different N evaluated on the same set, or a dated note explaining the delay.

### SLM-R46 — MISSING
- **Quote:** "Draft versions of your final artifacts: dataset shape, model checkpoint, in-progress Brainlift."
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.4
- **Meaning in code:** Draft dataset schema/sample, a draft checkpoint reference, and an in-progress Brainlift document exist in the repo.
- **What is missing:** No implementing code found in code_roots.
- **Suggested scope:** Commit a dataset schema/sample, a draft checkpoint reference, and a BRAINLIFT.md stub.

### SLM-R47 — MISSING
- **Quote:** "The dataset, published — this is your real artifact."
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.4
- **Meaning in code:** The final dataset is published (HF Hub dataset repo or equivalent public location) and linked from the README.
- **What is missing:** No implementing code found in code_roots.
- **Suggested scope:** Publish the final dataset (HF Hub dataset repo) and link it from the README.

### SLM-R48 — MISSING
- **Quote:** "The model on Hugging Face Hub, public, plus a running inference demo."
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.4
- **Meaning in code:** Public HF model (SLM-R23) AND a running inference demo (HF Space / hosted endpoint / demo script) linked from the README.
- **What is missing:** No implementing code found in code_roots.
- **Suggested scope:** Public HF model (SLM-R23) plus a running inference demo (HF Space or hosted endpoint) linked from the README.

### SLM-R49 — MISSING
- **Quote:** "Eval harness and results table — base vs. tuned, on your own eval set and on the staff held-out set."
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.4
- **Meaning in code:** Final results table with base and tuned rows for both the own eval set and the staff held-out set, generated by the harness.
- **What is missing:** No implementing code found in code_roots.
- **Suggested scope:** Ships with eval.py: two results tables (own set, staff held-out set), each with base and tuned rows.

### SLM-R50 — MISSING
- **Quote:** "Full Data-Efficiency curve (performance vs. dataset size) with a justified minimum viable N."
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.4
- **Meaning in code:** The complete curve (SLM-R21) with ≥4 points and the justified minimum N (SLM-R22).
- **What is missing:** No implementing code found in code_roots.
- **Suggested scope:** Ships when SLM-R19–R22 ship: the ≥4-point curve with justified minimum N.

### SLM-R51 — MISSING
- **Quote:** "Brainlift — your behavior thesis, and whether data → behavior held, with evidence."
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.4
- **Meaning in code:** A Brainlift document stating the behavior thesis and the evidence-backed conclusion on whether data → behavior held.
- **What is missing:** No implementing code found in code_roots.
- **Suggested scope:** Add BRAINLIFT.md with the behavior thesis and the evidence-backed data → behavior conclusion.

## Stretch (optional) — no pass/fail weight
### SLM-R53 — MISSING
- **Quote:** "DPO / preference tuning — build preference pairs (on-spec vs. off-spec) and run DPO on top of your SFT model; measure the delta over SFT alone."
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.4
- **Meaning in code:** (Stretch — optional, not pass/fail.) A preference-pair dataset and a DPO training run on top of the SFT checkpoint, with a measured delta vs SFT.
- **What is missing:** No implementing code found in code_roots.
- **Suggested scope:** Optional stretch — no action required until the core arc is done: preference pairs + DPO run + delta vs SFT.

### SLM-R54 — MISSING
- **Quote:** "Adversarial / robustness eval — a hard eval set built specifically to break your behavior (jailbreak the tutor into giving answers, feed malformed input to the schema model); report robustness, not just clean-input performance."
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.4
- **Meaning in code:** (Stretch — optional, not pass/fail.) A separate adversarial eval set and a robustness column reported from it.
- **What is missing:** No implementing code found in code_roots.
- **Suggested scope:** Optional stretch — no action required until the core arc is done: adversarial eval set + robustness column.

### SLM-R55 — MISSING
- **Quote:** "Composed behavior — instill a second, potentially competing constraint and show the model holds both at once."
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.4
- **Meaning in code:** (Stretch — optional, not pass/fail.) A second constraint added to the spec/dataset with eval evidence that both hold simultaneously.
- **What is missing:** No implementing code found in code_roots.
- **Suggested scope:** Optional stretch — no action required until the core arc is done: second constraint + evidence both hold.

## Orphan tickets
- None checked — ticket dimension BLOCKED. Create a Linear project for this SLM work under Troysatchell, set tickets.project to its exact name in audit/requirements.config.yaml, and re-run.
