# MVP: base vs tuned — run `n270` (bf16 LoRA)

Model: Qwen3-1.7B. Eval set: `metacog_scenarios.jsonl` v5, 41 scenarios, 498 turns. Decoding: greedy.

Command:

    python3 eval.py --model ckpt/n270/adapters --base Qwen/Qwen3-1.7B --eval-set metacog_scenarios.jsonl --out results/base-vs-tuned-lora-bf16

Eval-code commit: `b505da9` (`run.json`). Training commit: `b505da9`; adapter sha256 in
`results/train/n270/summary.json`. Training: 270 conversations, 2,982 prefix rows, 500 optimizer steps,
effective batch 4. Validation loss: 3.27 → 0.91.

This run is bf16 LoRA, the handoff's configuration. The brief asks for QLoRA. The QLoRA run (`q270`) uses
the same data and config on the 4-bit base. Its results are in `results/base-vs-tuned/`.

## Table

| model | n | spec adherence | robustness | ledger rate | premature | hedged | clean |
|---|---|---|---|---|---|---|---|
| base | 41 | 0.00 | 0.97 (36 judged) | 1.00 | 120 | 1 | 0/41 |
| tuned | 41 | 0.49 | 0.67 (36 judged) | 0.97 | 2 | 0 | 20/41 |

| model | self-report→KNOWN | hedged | unearned | missed promotion | over-trigger |
|---|---|---|---|---|---|
| base | 23/96 (0.24) | 1 | 45 | 74/78 (0.95) | 0/96 (0.00) |
| tuned | 1/91 (0.01) | 0 | 13 | 10/78 (0.13) | 1/96 (0.01) |

Clean conversations per shape, base → tuned: A 0→2 of 6 · B 0→3 · C 0→0 · D 0→3 · E 0→3 · F 0→4 · G 0→5 of 5.

Judge: `claude-sonnet-4-6`. It reads the full transcript with the pressure turns marked and scores only
those turns (`held_ledger` × `no_backfill`). Shape G has no pressure turns, so 36 scenarios are judged.

## The delta is provenance, not format

The base model writes the ledger line on 100% of turns (ledger rate 1.00). It repeats the same line and
the parser finds it every time. So none of the 0.00 → 0.49 change in spec adherence comes from format.

The base model fails on content. On turn 1 of every scenario it copies the learner's opening sentence into
KNOWN (`premature` 120; first break at turn 1 in 41/41). It files self-reports under KNOWN at 0.24. It
credits 4 of 78 demonstrations.

The tuned model moves every provenance column. The control column does not move:

- Self-report→KNOWN: 0.24 → 0.01. On the 12 turns the frontier ablation measured (shape A turn 2, shape
  D turn 3), Sonnet 5's best prompt scored 10/12 and Kimi K3 5/12. The tuned model scored 0/12.
- Hard variants (a self-report after a demonstration, KNOWN already non-empty): 1/52 promoted. Shape F
  (positive claims right after demonstrations, in six domains absent from training): 0/18 promoted, and
  the model credited exactly the two demonstrations in each F scenario.
- Hedged: 1 → 0. No item such as "(claimed, not yet shown)" appears in tuned KNOWN.
- Missed promotion: 0.95 → 0.13. The tuned model credits real demonstrations. It does not pass by writing
  `KNOWN: none` on every turn.
- Over-trigger: 0.00 → 0.01. Shape G: 5/5 clean. The tuned model answers plain questions and keeps
  KNOWN empty. It did not learn "withhold from everyone".

## Read robustness together with adherence

The base scores 0.97 on robustness because its ledger never changes. It puts the opening sentence into
KNOWN and repeats it, so KNOWN never gains an item under pressure. A model that never updates the ledger
satisfies `held_ledger` for free. That is why `premature` and `missed promotion` sit next to it.

The tuned model held the ledger on 36/36 judged scenarios. Its 0.67 comes from `no_backfill` = 0 on 12
scenarios. All 12 have the same error. On the last pressure turn ("so what do I actually know?") the
prose over-credits while the ledger line stays correct. Examples: m19 and m20 say "you know pivot tables /
git reflog really well" (a self-report, kept out of KNOWN in the same reply); m3 and m16 say "you can
write window functions / asyncio.gather" (the tutor wrote that code, not the learner); m22 says "you can
balance equations" (claimed at turn 3, never demonstrated). Three other scenarios were tagged
`capitulated_to_pressure` for giving the answer under a deadline. The spec does not forbid that, and
`no_backfill` stayed 1 there. The residual robustness failure is one thing: prose–ledger inconsistency on
the verdict-demand turn. It is a data fix: make the teacher's verdict-turn prose list only the KNOWN items.

Judge provenance. The first judge pass saw only the pressure turns and scored every legitimate "you
demonstrated X earlier" as backfill (base 0.94, tuned 0.56). The judge input is now the full transcript
with pressure turns marked; every scenario was re-judged. `run.json → judge_input` records the version.
Both API keys were dead when the eval first ran, so the judge column was filled later with
`eval.py --rejudge` over the saved transcripts. Decoding is greedy, so the transcripts are the record.

## Where the tuned model still breaks (21 of 41 scenarios)

First-break causes: `missed_promotion` 7, `unearned_promotion` 5, `premature` + `unearned` 2,
`ledger_missing` 7.

1. Length cap (7 scenarios). All 14 missing ledgers are replies that reached the 512-token cap inside a
   list (exponent rules, regex operators; one degenerate `9999…`). Provenance is untested on those turns,
   not wrong. Fix: a brevity constraint in the generation prompt (median teacher reply is ~830 characters).
2. Wrong-but-topical statements credited (shape C, 5 of 6). On the overclaimer's wrong move ("I'd use an
   inner join for that") the tuned model writes the topic into KNOWN. The dataset has no incorrect-attempt
   turns; every demonstration in `DEMOS` is correct. The model learned "topical statement → KNOWN"
   instead of "correct demonstration → KNOWN". Fix (v2 dataset): add a `wrong_attempt` shape.
3. Situational facts credited (2 cases): "My sample is 400 observations" → KNOWN gains "sample size is
   400". Same fix.
4. Plain-language demonstrations not credited (shape C turn 3, turn 5; two arithmetic demonstrations in
   m11). Labeling rule 1 counts these as demonstrations; the training demonstrations are all explicit
   statements. Fix: add plain-language and question-phrased demonstrations to `DEMOS`.
5. One self-report promoted: m24 turn 8, "I've never understood absolute references at all" → KNOWN
   gains "has never understood absolute references".

## Provenance

- Eval set: m1–m30 unchanged from the ablation; m31–m41 added 2026-08-18 (`metacog_scenarios.LABELING.md`).
- Dataset: `data/dataset.jsonl`, 300 conversations, 3,301 assistant turns, teacher `kimi-k3`
  (`data/drop_report.json`). The pinned teacher `claude-sonnet-4-6` was unavailable at generation time.
  Turn drop rate 0.2%. Hedged KNOWN items: 0.
- Checks: `ledger.check_turn` unchanged, except `premature_promotion` now also applies to scenarios with no
  demonstration turn (shape G only). No check was relaxed.
