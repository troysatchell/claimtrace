# Requirements gaps — Trained_SLM (2026-08-18T22:20:44-0500, commit fc1bc9345cdb)

> **Update 2026-08-19 (after commit 9015412, sweep complete):** the QLoRA sweep finished 10:31 CDT with all four
> points trained and evaluated. This closes SLM-R19, R20 (own set), R21, R45, R50 and names min viable N
> (SLM-R22: N = 135, `BRAINLIFT.md`); SLM-R42 now has the QLoRA row (`results/base-vs-tuned/`). Still open:
> SLM-R43/R44 (v2 dataset + delta), R48 (hosted demo), R49/R20 staff held-out set, R51 v2 update, and the
> stretch items. Current status per deliverable: `SUBMISSION.md`. The verdicts below are as of fc1bc93.

## Unticketed requirements (ticket dimension BLOCKED — every gap is unticketed)

### SLM-R19 — PARTIAL
- **Quote:** "Train at least 4 checkpoints at different dataset sizes (e.g. a log-spaced sweep such as N, N/2, N/4, N/8 — choose and justify your own spacing)."
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.2
- **Meaning in code:** Training config/logs for ≥4 checkpoints at distinct dataset sizes, with the spacing choice justified in writing.
- **What is missing:** 2 of ≥4 checkpoints trained (bf16 LoRA n270, n135); QLoRA q270 training and q135/q67/q33 queued (run_pipeline_qlora_rest.sh) at sweep time.
- **Suggested scope:** Let run_pipeline_qlora_rest.sh finish (≈6 h); the four QLoRA runs land in results/train/q*/.

### SLM-R20 — PARTIAL
- **Quote:** "Evaluate every checkpoint on the same eval set (your own plus the staff held-out set) using your existing harness — no new rubric needed."
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.2
- **Meaning in code:** Eval results for each checkpoint on the identical eval set, produced by the same harness (verify.eval), including a held-out set path.
- **What is missing:** Only n270 evaluated so far; n135 trained not evaluated. Staff held-out set not yet available (schema documented, README.md line 111).
- **Suggested scope:** Ships when the sweep pipeline finishes; add the staff set path when provided.

### SLM-R21 — PARTIAL
- **Quote:** "Report a performance-vs-N curve for at least Spec adherence and Robustness."
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.2
- **Meaning in code:** A curve (plot or table) of Spec adherence and Robustness vs dataset size N.
- **What is missing:** Plotting code present; no curve produced yet.
- **Suggested scope:** Ships with the sweep (results/data-efficiency-curve/curve.png).

### SLM-R22 — PARTIAL
- **Quote:** "Identify and justify the smallest N that holds the behavior reliably — this becomes your stated "minimum viable dataset size" in your Brainlift."
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.2
- **Meaning in code:** A stated minimum viable N with justification tied to the curve, recorded in the Brainlift.
- **What is missing:** Criterion stated ('smallest N within noise of N=270 on spec adherence and self-report→KNOWN'); N not yet named.
- **Suggested scope:** Fill in from results/data-efficiency-curve/table.md.

### SLM-R43 — PARTIAL
- **Quote:** "At least one specific failure mode diagnosed from your MVP eval, and resolved via a data change (v2 dataset) — not a training-config change."
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.4
- **Meaning in code:** A v2 dataset exists with a written diagnosis of the MVP failure mode it targets; the training config is unchanged between v1 and v2 runs.
- **What is missing:** Diagnosis written; v2 dataset not generated yet (Early submission item).
- **Suggested scope:** Add a wrong_attempt shape (+ plain-language demos, brevity constraint) to generate_dataset.py, regenerate as data/v3, retrain with the identical config, diff configs.

### SLM-R44 — MISSING
- **Quote:** "Updated base-vs-tuned eval numbers showing the delta from MVP, submitted with raw judge transcripts."
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.4
- **Meaning in code:** A second results table with an explicit delta vs the MVP numbers, plus the corresponding judge JSONL.
- **What is missing:** Early-submission item; follows SLM-R43.
- **Suggested scope:** Re-run eval.py on the v2-trained adapter; report delta vs results/base-vs-tuned.

### SLM-R45 — PARTIAL
- **Quote:** "At least 2 points on your Data-Efficiency curve (see Required Ablations), or a documented reason you're behind."
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.4
- **Meaning in code:** Eval results for ≥2 checkpoints at different N, or a written note explaining the delay.
- **What is missing:** Two Ns trained, one evaluated; sweep evals queued.
- **Suggested scope:** Ships with the sweep pipeline.

### SLM-R48 — PARTIAL
- **Quote:** "The model on Hugging Face Hub, public, plus a running inference demo."
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.4
- **Meaning in code:** Public HF model (SLM-R23) AND a running inference demo (HF Space / hosted endpoint / demo script) linked from the README.
- **What is missing:** Model is public on the Hub. The inference-demo app exists (space/) but is not hosted yet: HF gates Gradio Spaces on cpu-basic behind PRO (create returned 402); container hosting (Railway/Render) needs an account decision.
- **Suggested scope:** Host space/ (HF PRO Space, or Railway via space/Dockerfile) and link the URL from README + SUBMISSION.md.

### SLM-R49 — PARTIAL
- **Quote:** "Eval harness and results table — base vs. tuned, on your own eval set and on the staff held-out set."
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.4
- **Meaning in code:** Final results table with base and tuned rows for both the own eval set and the staff held-out set, generated by the harness.
- **What is missing:** Own set done; staff held-out set not yet available.
- **Suggested scope:** Run eval.py with the staff set path when provided; schema documented (README.md line 111).

### SLM-R50 — PARTIAL
- **Quote:** "Full Data-Efficiency curve (performance vs. dataset size) with a justified minimum viable N."
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.4
- **Meaning in code:** The complete curve (SLM-R21) with ≥4 points and the justified minimum N (SLM-R22).
- **What is missing:** Pending the sweep.
- **Suggested scope:** Ships with the sweep pipeline + BRAINLIFT update.

### SLM-R51 — PARTIAL
- **Quote:** "Brainlift — your behavior thesis, and whether data → behavior held, with evidence."
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.4
- **Meaning in code:** A Brainlift document stating the behavior thesis and the evidence-backed conclusion on whether data → behavior held.
- **What is missing:** Draft with thesis and MVP evidence; min-N and QLoRA/robustness updates pending.
- **Suggested scope:** Update after the sweep and q270 eval.

### SLM-R53 — MISSING
- **Quote:** "DPO / preference tuning — build preference pairs (on-spec vs. off-spec) and run DPO on top of your SFT model; measure the delta over SFT alone."
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.4
- **Meaning in code:** (Stretch — optional, not pass/fail.) A preference-pair dataset and a DPO training run on top of the SFT checkpoint, with a measured delta vs SFT.
- **What is missing:** Stretch (optional): DPO not attempted.
- **Suggested scope:** Optional; not before Final-submission core items.

### SLM-R54 — MISSING
- **Quote:** "Adversarial / robustness eval — a hard eval set built specifically to break your behavior (jailbreak the tutor into giving answers, feed malformed input to the schema model); report robustness, not just clean-input performance."
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.4
- **Meaning in code:** (Stretch — optional, not pass/fail.) A separate adversarial eval set and a robustness column reported from it.
- **What is missing:** Stretch (optional): adversarial eval set not attempted.
- **Suggested scope:** Optional; not before Final-submission core items.

### SLM-R55 — MISSING
- **Quote:** "Composed behavior — instill a second, potentially competing constraint and show the model holds both at once."
- **Source:** Train_Your_Own_Small_Learning_Model.pdf, p.4
- **Meaning in code:** (Stretch — optional, not pass/fail.) A second constraint added to the spec/dataset with eval evidence that both hold simultaneously.
- **What is missing:** Stretch (optional): composed behavior not attempted.
- **Suggested scope:** Optional; not before Final-submission core items.

## Orphan tickets
- None (ticket dimension BLOCKED: no Linear project scoped to this repo).
