The MVP bundle (SLM-R34–R42) is present and re-runnable except for one item: **the full-size QLoRA
training run is not finished** (SLM-R41 PARTIAL — the completed n270 run is bf16 LoRA; the QLoRA run of
record `q270` started 20:25 CDT and its base-vs-tuned eval lands afterwards). The base-vs-tuned numbers
exist and carry the behavior claim (SLM-R6/R42: 0/41 → 20/41 clean; self-report→KNOWN 0.24 → 0.01;
base holds the ledger format on 100% of turns so the delta is provenance, not formatting), with full
per-example judge output. The hard blocker for the Verification Requirements is external: no
Hugging Face login on this machine, so no public checkpoint / revision hash (SLM-R23, R27, R47, R48). The ablation's LLM-judge column (SLM-R16/R17) is now computed with the eval.py rubric (`results/full-30-combined/judged_table.md`). Everything else that was MISSING at baseline
(harness, dataset, training, eval, JSONL, smoke loop, sweep tooling, Brainlift draft) now exists; 34 of
55 verdicts changed.
