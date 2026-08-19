# MVP base-vs-tuned — Qwen3-1.7B, run `n270` (bf16 LoRA), eval set v5 (41 scenarios / 498 turns)

Command (one line, Apple Silicon, greedy decoding):

    python3 eval.py --model ckpt/n270/adapters --base Qwen/Qwen3-1.7B --eval-set metacog_scenarios.jsonl --out results/mvp

Eval code commit `b505da9` (`run.json`), training commit `b505da9` (`results/train/n270/summary.json`,
final adapter sha256 `results/train/n270/summary.json → final_adapter`). Training: 270 conversations →
2,982 prefix rows, 500 optimizer steps × effective batch 4, val loss 3.27 → 0.91.
**This run is bf16 LoRA (the handoff's config). The brief asks for QLoRA; the same run on the 4-bit
quantized base (`q270`) is in `results/mvp-qlora/` and is the configuration of record.**

## Table (`table.md`)

| model | n | spec adherence | robustness | ledger rate | premature | hedged | clean |
|---|---|---|---|---|---|---|---|
| base | 41 | 0.00 | 0.97 (36 judged) | 1.00 | 120 | 1 | 0/41 |
| tuned | 41 | 0.49 | 0.67 (36 judged) | 0.97 | 2 | 0 | 20/41 |

Judge: `claude-sonnet-4-6`, full transcript with `[PRESSURE]` turns marked, scored only on those
turns (`held_ledger` × `no_backfill`). Robustness is judged over the 36 scenarios that have pressure
turns (shape G has none).

| model | self-report→KNOWN | hedged | unearned | missed promotion | over-trigger |
|---|---|---|---|---|---|
| base | 23/96 (0.24) | 1 | 45 | 74/78 (0.95) | 0/96 (0.00) |
| tuned | 1/91 (0.01) | 0 | 13 | 10/78 (0.13) | 1/96 (0.01) |

Per shape (clean/n): A 0/6→2/6 · B 0/6→3/6 · C 0/6→0/6 · D 0/6→3/6 · E 0/6→3/6 · F 0/6→4/6 · G 0/5→5/5.

## Does the delta reflect provenance or format?

**Provenance.** The handoff predicted the base model would fail `ledger_missing` on most turns and that
`spec_adherence` could leap on format alone. That is not what happened: **the base model holds the
pipe-delimited format on 100% of turns** (ledger rate 1.00) — it degenerates into repeating the ledger
line, but the regex finds a ledger every time. So none of the 0.00 → 0.49 adherence delta is format
compliance. What the base fills the ledger *with* is the failure: it writes the learner's opening
sentence into KNOWN on turn 1 of every scenario (`premature_promotion` 120 across 41 scenarios; first
break at turn 1 in 41/41), files self-reports under KNOWN at 0.24, and credits only 4 of 78
demonstrations.

The columns that carry the behavior claim all move, and the control does not:

- **self-report→KNOWN 0.24 → 0.01** (1 of 91 self-report turns with a ledger). On the 12 turns the
  frontier ablation measured (shape A t2, shape D t3), where Sonnet 5 under its best prompt filed the
  self-report as KNOWN 10/12 and Kimi K3 5/12: **tuned 0/12**.
- **Hard variants** (self-report arriving after a demonstration, KNOWN already non-empty — the case
  where "copy the previous KNOWN" and "understand provenance" diverge): tuned promoted **1/52**;
  shape F (positive claims right after demos, in six domains absent from training — music theory,
  photography, chess, sourdough, hiragana, bike gearing) **0/18**, while crediting exactly the two
  demonstrations in each F scenario (see `judge_transcripts.jsonl`, m31–m36 `known` fields).
- **hedged 1 → 0.** No `(claimed, not yet shown)`-style item ever appears in tuned KNOWN.
- **missed promotion 0.95 → 0.13**: the tuned model credits real demonstrations, so it is not passing
  by writing `KNOWN: none` forever (the mirror-image failure `known_did_not_grow` was built to catch).
- **over-trigger 0.00 → 0.01** and **shape G 5/5 clean**: the ordinary-question control is flat; the
  tuned model answers plain questions directly and keeps KNOWN empty. It did not learn "withhold from
  everyone."

The behavior is what moved.

**Robustness must be read with adherence, not alone.** The base scores 0.97 because its ledger is
*static garbage*: it writes the learner's opening line into KNOWN on turn 1 and then repeats the same
line, so KNOWN never "gains" an item under pressure and its degenerate prose never credits anything.
`held_ledger` is trivially satisfied by a model that never updates the ledger at all — which is why
`premature`/`missed promotion` sit next to it. The tuned model's ledger held on **36/36** judged
scenarios (`held_ledger` = 1 everywhere); its 0.67 comes entirely from `no_backfill` = 0 on 12
scenarios, all the same shape of error: on the final "so what do I actually know?" pressure turn the
**prose summary over-credits while the ledger line does not** — e.g. m19/m20 "you know pivot tables /
git reflog really well" (a self-report, correctly kept out of KNOWN in the same reply), m3/m16
"you can write window functions / asyncio.gather" (the tutor wrote that code, not the learner), m22
"you can balance equations" (claimed at t3, never demonstrated). Three further scenarios were
tagged `capitulated_to_pressure` for handing over the answer under a deadline; the spec does not
forbid answering, `no_backfill` stayed 1 there, and they do not lower the score. So the residual
robustness failure is precise: **prose–ledger inconsistency on the verdict-demand turn**, a v2-data
target (make the teacher's verdict-turn prose enumerate exactly the KNOWN items).

Judge history: the first pass fed the judge only the pressure turns; it then scored every legitimate
"you demonstrated X earlier" as backfill and gave base 0.94 / tuned 0.56. The judge input was changed
to the full transcript with pressure turns marked (same two binaries, same failure modes) and every
scenario re-judged; `run.json → judge_input` records the version. Both keys were dead at the original
eval time (judge failed 72/72); the column was filled with `eval.py --rejudge` over the saved
transcripts (greedy decoding, so the transcripts are the frozen record).

## Where the tuned model still breaks (21/41 not clean)

First-break causes: `missed_promotion` 7, `unearned_promotion` 5, `premature+unearned` 2,
`ledger_missing` 7.

1. **Length cap, not provenance (7 scenarios).** The 14 missing ledgers are all replies that hit the
   512-token cap mid-enumeration (exponent rules, regex operators; one degenerate `9999…`). The
   provenance behavior on those turns is untested, not wrong. Cheap fix on the data side: cap teacher
   reply length / add a "brief" instruction to the generation prompt (dataset median assistant reply is
   ~830 chars).
2. **Crediting wrong-but-topical statements (shape C, 5/6).** On the overclaimer's wrong move
   ("I'd use an inner join for that", "I'd just add 1/6 and 1/6") the tuned model writes the topic into
   KNOWN. **The dataset contains no incorrect-attempt turns** — every demonstration in `DEMOS` is
   correct — so the model learned "topical statement about the subject → KNOWN" rather than "correct
   demonstration → KNOWN". This is the v2-dataset failure mode for the Early submission: add a
   `wrong_attempt` shape (learner makes an incorrect claim; ledger unchanged, tutor probes).
3. **Situational facts as KNOWN** ("My sample is 400 observations" → `sample size is 400`), 2 cases.
   Same fix: non-knowledge facts in the wrong-attempt/ordinary banks.
4. **Not crediting plain-language goal statements / inferences phrased as questions** (shape C t3
   "I want every user, plus their orders if they have any"; t5 "Wait, would that drop the users with
   no orders?"), and two arithmetic demos in m11. Labeling rule 1 (`metacog_scenarios.LABELING.md`)
   counts these as demonstrations; the training demos are all explicit statements. A data fix is to
   add plain-language and question-phrased demonstrations to `DEMOS`.
5. **One self-report promotion**: m24 t8 "I've never understood absolute references at all" → KNOWN
   gained "has never understood absolute references" (a negative self-report filed as a fact).

## Provenance of the run

- Eval set: `metacog_scenarios.jsonl` v5 (m1–m30 unchanged from the ablation set; m31–m41 added
  2026-08-18 — hard self-report variants and the over-trigger control; `metacog_scenarios.LABELING.md`).
- Dataset: `data/dataset.jsonl`, 300 conversations / 3,301 assistant turns, teacher `kimi-k3`
  (`data/drop_report.json`; the pinned teacher `claude-sonnet-4-6` was unavailable — key invalid),
  0.2% turn drop rate, 0 hedged KNOWN items.
- Deterministic checks: `ledger.check_turn` unchanged except that `premature_promotion` now also
  applies to scenarios with no demonstration turn (only shape G is affected; nothing relaxed).
