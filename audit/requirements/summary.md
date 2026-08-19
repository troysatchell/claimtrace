The MVP bundle (SLM-R34–R42) is present and re-runnable except for one item: **the full-size QLoRA
training run is not finished** (SLM-R41 PARTIAL — the completed n270 run is bf16 LoRA; the QLoRA run of
record `q270` started 20:25 CDT and its base-vs-tuned eval lands afterwards). The base-vs-tuned numbers
exist and carry the behavior claim (SLM-R6/R42: 0/41 → 20/41 clean; self-report→KNOWN 0.24 → 0.01;
base holds the ledger format on 100% of turns so the delta is provenance, not formatting), with full
per-example judge output. The model and dataset are now public on the Hugging Face Hub with recorded revisions
(SLM-R23, R27, R47 VERIFIED; `results/publish.json`, run n270 — q270 to follow). The hosted inference demo
(SLM-R48) is built (`space/`) but not yet deployed: HF gates Gradio Spaces behind PRO, so hosting is an account decision. The ablation's LLM-judge column (SLM-R16/R17) is now computed with the eval.py rubric (`results/prompt-ceiling-ablation/judged_table.md`). Everything else that was MISSING at baseline
(harness, dataset, training, eval, JSONL, smoke loop, sweep tooling, Brainlift draft) now exists; 34 of
55 verdicts changed.
