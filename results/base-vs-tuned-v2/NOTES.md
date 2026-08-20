# Early submission: v2 data fix — run `q236v2` (QLoRA, v2/spec-v3 dataset)

Same model, config, eval set, harness, and judge as the MVP run of record (`results/base-vs-tuned/`,
run `q270`). The only change is the training data. Config proof: `results/train/q270/lora_config.yaml`
and `results/train/q236v2/lora_config.yaml` differ only in the data/adapter paths.

Command:

    python3 eval.py --model ckpt/q236v2/adapters --base Qwen/Qwen3-1.7B --eval-set metacog_scenarios.jsonl --out results/base-vs-tuned-v2

Eval-code commit `d9adae8` (`run.json`). Training: `data/v2/dataset.jsonl`, 265 conversations
(teacher kimi-k3, the v1 teacher; 236 train / 29 valid — the Moonshot quota died at 265 of the
300 target; the data-efficiency curve is flat over N=135–270, so the N gap vs q270's 270 is
within noise), 2,618 prefix rows, 500 optimizer steps, val loss 3.61 → 0.756, 85 min, adapter
sha256 `b6255e4963bc…` (`results/train/q236v2/summary.json`).

## Delta from MVP (same 41 scenarios, 498 turns; full delta table in `DELTA.md`)

| metric | base | MVP (q270) | v2 (q236v2) | Δ |
|---|---|---|---|---|
| clean conversations | 0/41 | 20/41 | **33/41** | +13 |
| spec adherence | 0.00 | 0.49 | **0.80** | +0.32 |
| self-report→KNOWN | 0.24 | 0.07 | **0.00** (0/96) | −0.07 |
| unearned KNOWN items | 45 | 15 | **1** | −14 |
| missed promotion | 0.95 | 0.12 | 0.10 | −0.02 |
| ledger rate | 1.00 | 0.95 | 1.00 | +0.05 |
| robustness (judge, 36 judged) | 0.94† | 0.69 | 0.83 | +0.14 |
| over-trigger (ordinary turns) | 0.00 | 0.04 | 0.15 | +0.11 |

† the base row is re-generated each eval; greedy decoding is identical, judge scores vary slightly
(0.97 in the MVP run).

## Each diagnosed failure mode → what the data change did

1. **Wrong-but-topical statements credited as KNOWN** (the headline diagnosis). v1 had no
   incorrect-attempt turns. v2 adds shape E (`wrong_attempt`, 461 training rows). Result:
   unearned KNOWN items 15 → 1 across 498 turns; eval shapes C/E self-report→KNOWN 0.17/0.12 → 0.00/0.00.
2. **Replies hitting the 512-token decode cap before the ledger line.** v2 caps prose at 120 words
   (filter drops >900 chars). Result: ledger rate 0.95 → 1.00 (no reply loses its ledger line to the cap); premature promotions 4 → 0.
3. **Verdict-turn prose over-crediting while the ledger held.** v2 restricts verdict prose to KNOWN
   items. Result: robustness (judged on exactly these pressure turns) 0.69 → 0.83.
4. **Jargon-gated promotion.** v2 adds a plain-language demonstration per topic. Missed promotion
   0.12 → 0.10.

## Residual failure mode (for Final)

Over-trigger rose 0.04 → 0.15 (14/96 ordinary turns): the model answers the ordinary question
correctly but appends a "quick check: …?" probe, which the mechanical no-diagnostic-question rule
flags. It is not withholding — the pure-ordinary control (shape G) is 5/5 clean, 0/30 over-trigger —
but it is off-spec tone on side questions inside mixed conversations. Likely cause: shape D fell to
9.8% of v2 rows while two probing shapes grew. Candidate v3 change: raise the ordinary share and
add ordinary turns immediately after demonstrations.

## In plain terms

The MVP model had learned "if the learner says something on-topic, write it in KNOWN". The v2
dataset showed it ~460 examples of on-topic statements that are *wrong* — where the tutor names
the error and the ledger does not move. That one addition removed nearly all unearned credit
(15 → 1) while keeping real demonstrations credited (90%), and the model now files self-reports
under CLAIMED perfectly (0 slips in 96 turns). 33 of 41 held-out conversations are now fully
clean, up from 20, with the base model still at 0.
