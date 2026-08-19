# Base vs tuned — run `q270` (QLoRA, run of record)

Model: Qwen3-1.7B, 4-bit base (`ckpt/base-q4`), LoRA rank 16 on 16 layers. Eval set: `metacog_scenarios.jsonl`
v5, 41 scenarios, 498 turns. Decoding: greedy, 512 new tokens. Judge: `claude-sonnet-4-6`.

Command:

    python3 eval.py --model ckpt/q270/adapters --base Qwen/Qwen3-1.7B --eval-set metacog_scenarios.jsonl --out results/base-vs-tuned

Eval-code commit: `fc1bc93` (`run.json → eval_code_commit`). Training commit: `b505da9`; adapter sha256
`6a6af4f1ac8e…` (`results/train/q270/summary.json`). Training: 270 conversations, 2,982 prefix rows, 500
optimizer steps, effective batch 4, 0.67 epochs, 1 h 54 min, 7.8 GB peak. Validation loss: 3.24 → 0.94.

This is the brief's configuration (QLoRA). The bf16 LoRA twin `n270` — same data, same config, unquantized
base — is in `results/base-vs-tuned-lora-bf16/` and carried the MVP numbers.

## Numbers

| | base | tuned (q270) | tuned (n270, bf16) |
|---|---|---|---|
| clean conversations | 0/41 | 20/41 | 20/41 |
| spec adherence | 0.00 | 0.49 | 0.49 |
| self-report→KNOWN (turns with a ledger) | 23/96 (0.24) | 6/89 (0.07) | 1/91 (0.01) |
| missed promotion | 74/78 (0.95) | 9/76 (0.12) | 10/78 (0.13) |
| over-trigger (shape D/G control) | 0/96 (0.00) | 4/96 (0.04) | 1/96 (0.01) |
| hedged KNOWN items | 1 | 0 | 0 |
| robustness under pressure (judge, 36 judged) | 0.97 | 0.69 | 0.67 |

Full table with the per-shape breakdown: `table.md`. Per-example judge output: `judge_transcripts.jsonl`.

## In plain terms

Same rulebook, same 41 scripted learners, for both models. The rule: write something under KNOWN only after
the learner has shown it in their own work; a self-report stays under CLAIMED.

- **Base model:** prints the ledger line on every turn, and on the first turn of nearly every conversation
  copies the learner's biography line into KNOWN. 0 of 41 conversations clean. It credits almost no
  demonstrations either (misses 95%): the ledger never changes, which is why its "robustness" is 0.97 — it
  holds a ledger that was wrong from turn one.
- **Tuned model (4-bit QLoRA):** keeps self-reports out of KNOWN (6 slips in 89 turns, down from 23 in 96),
  credits real demonstrations (misses 12% instead of 95%), and still answers ordinary questions normally
  (control shape G: 5/5 clean, over-trigger 0.04). 20 of 41 conversations clean.

The number to quote: **self-report → KNOWN went from 0.24 to 0.07** on the 4-bit base (0.01 on the bf16
twin). Quantizing the base for training cost nothing on spec adherence (0.49 both) and a few provenance
slips; the behavior the dataset was built to teach moved the same way in both runs.

## Where the tuned model still breaks

Same failure modes as the bf16 run (`results/base-vs-tuned-lora-bf16/NOTES.md`): it credits wrong-but-topical
statements as demonstrations (shape C, 2/12 self-report→KNOWN; shape E, 2/17), and on the verdict turn the
prose over-credits while the ledger holds. Both are data gaps — no incorrect-attempt turns in the training
set — and are the target of the v2 dataset (`BRAINLIFT.md`, "Failure modes → v2 data change").
