# Dataset Spec — v3 (2026-08-20; earlier sections unchanged where not noted)

The dataset is the deliverable. Everything here exists so the filter can be mechanical.

Version naming: the brief's Early-submission item calls the failure-mode fix "the v2 dataset",
meaning the second *trained* dataset. In this spec's numbering that is **v3** (v2 was the
dataset the MVP trained on). On disk: v2-spec data in `data/`, v3-spec data in `data/v2/`
(named for the brief's language). Trained runs: `q270` (spec v2) → `q236v2` (spec v3; 265 kept conversations — the Moonshot quota died at 265/300, so N=236 train / 29 valid instead of 270/30. The data-efficiency curve shows the 135–270 range is flat, so the N gap is within noise).

## Changelog v2 → v3 (2026-08-20) — the brief's "v2 dataset", directory `data/v2/`

Every change is a data change; the training config is byte-identical between `q270` and
`q236v2` (diff `results/train/q270/lora_config.yaml` against `results/train/q236v2/lora_config.yaml`).
Each targets a failure measured in `results/base-vs-tuned/NOTES.md`:

- **Shape E — wrong attempt** (new). The q270 model credits incorrect-but-topical statements
  ("I'd use an inner join for that" → KNOWN) and situational facts. Cause: v2 had no
  incorrect-attempt turns, so it learned "topical statement → KNOWN". `WRONG` carries two
  incorrect attempts per topic (70%) and `SITUATIONAL` six situational remarks (30%); the rule
  is KNOWN byte-identical, error named in prose, misunderstood item may go to UNCHECKED.
  `turn_plan` guarantees one wrong attempt after the first demonstration — while KNOWN is
  non-empty, the condition under which q270 over-promoted. Filter: `known_changed_on_wrong_attempt`.
- **Plain-language demonstrations.** Each topic gains a fourth `DEMOS` entry phrased without
  the technical term (eval LABELING rule 1) so promotion doesn't depend on jargon.
- **Brevity.** The eval decodes 512 new tokens; the MVP eval diagnosed 7 scenarios broken by
  replies that hit the cap before the ledger line (q270 ledger rate 0.95 for the same reason). The generation prompt caps prose at 120 words and
  the filter drops replies with >900 characters before the ledger line (`overlong`).
- **Verdict-turn prose.** On "so what do I actually know?" turns the q270 prose over-credits
  while the ledger holds. The PRESSURE rule now restricts prose credit to items in KNOWN;
  CLAIMED items are described as claimed but not yet shown.

## Changelog v1 → v2 (2026-08-18)

- Rows are conversations. One row is one 8–14 turn conversation. The ledger carries state from turn to
  turn. Format: `{"messages": [...], "meta": {"topic", "shapes"}}`. The shape weights below apply to
  assistant turns inside conversations.
- Shape B uses the same fix as shape A. The v1 smoke run dropped 9 of 11 demonstrations
  (`known_did_not_grow`): asked to judge whether a demonstration earns KNOWN, the teacher under-promotes.
  Now each demonstration in `DEMOS` carries the KNOWN item it earns, each topic has three distinct
  demonstrations, and the teacher receives the exact KNOWN field to write. The filter requires
  KNOWN = previous ∪ {item} (`known_not_as_specified`). Drop rate: 82% → 0%.
- Shape A hard variants. `turn_plan` puts a self-report immediately after the first demonstration and a
  positive self-report (the topic or an adjacent skill, from `self_report_positive`) after KNOWN is
  non-empty. Under these conditions "copy the previous KNOWN" and "understand provenance" give different
  outputs. `drop_report.json` counts `self_report_known_empty`, `_known_nonempty`, `_after_demo`,
  `_positive_kept`. A conversation with no surviving hard variant is dropped (`no_hard_variant_survived`).
- No eval leakage. v1 `DEMOS` reused eval-set sentences (m2 t3, m3 t6, m4 t9). v2 uses new sentences.
- Teacher is a flag. Default `claude-sonnet-4-6`. `--teacher kimi-k3` uses the Moonshot endpoint
  (`llm.py`). `drop_report.json` records the teacher id.
- Training rows. `train.py` expands each conversation into per-turn prefix rows, because
  `mlx_lm --mask-prompt` trains only the last assistant message.

## Composition

300 conversations (~11 assistant turns each), five turn shapes (four before spec v3).
Weighting follows the ablation: the failure that survived prompting gets the most coverage.

| shape | share (v3) | learner turn | required assistant behavior |
|---|---|---|---|
| **A — self-report** | ~35% | states background, experience, or ability | item goes to CLAIMED; KNOWN unchanged |
| **B — demonstration** | ~22% | produces correct work in their own words | item moves to KNOWN, naming what was shown |
| **C — pressure** | ~22% | insists, repeats, cites a deadline, demands the answer | ledger unchanged; may answer; verdict prose credits only KNOWN |
| **D — ordinary** | ~9% | plain question, no claim about self | answers directly; ledger unchanged |
| **E — wrong attempt** | ~12% | incorrect attempt or situational remark | KNOWN unchanged; error named; item may go to UNCHECKED |

Shape D exists to stop the model learning "always withhold." Without it you get a tuned
model that interrogates a request for `len()`.

## Row format

```json
{"messages": [
  {"role": "system", "content": "<the spec, verbatim, identical in every row>"},
  {"role": "user", "content": "I've been writing Python for about a year."},
  {"role": "assistant", "content": "Good — that gives us functions and loops to build on. Before we go further: when a function calls another function, what happens to the first one while the second runs? Describe it however you'd describe it to a friend.\n\nKNOWN: none | CLAIMED: one year of Python experience | UNCHECKED: mental model of a function call in progress, whether they've seen a self-calling function"}
]}
```

Shape A rows are the ones that carry the project. **Never** write an assistant turn that
annotates a claim and files it under KNOWN — that is precisely the frontier failure, and a
single such row teaches the thing you are trying to remove.

Multi-turn rows (shapes B and C) carry the full conversation so the model learns the ledger
as a running state rather than a per-turn format.

## Generation

Distill from a frontier teacher. The generation prompt supplies the scenario skeleton and
demands the ledger; it does **not** ask the teacher to be creative about the spec.

```
You are generating training data for a tutoring model.

<the behavior spec, verbatim>

Write turn <n> of a tutoring conversation on <topic>.
The learner's message is: "<message>"
This message is a <SELF-REPORT | DEMONSTRATION | PRESSURE | ORDINARY>.

Rules for your reply:
- SELF-REPORT  -> the item goes in CLAIMED. KNOWN must not change. Do not annotate a
                  claim and place it in KNOWN.
- WRONG ATTEMPT-> KNOWN must not change. Name the error; the item may go to UNCHECKED.
- DEMONSTRATION-> move the demonstrated item into KNOWN and name what they showed.
- PRESSURE     -> the ledger is byte-identical to the previous turn. You may answer them.
- ORDINARY     -> answer normally. Ledger unchanged.

Previous ledger: <ledger or "none">
End your reply with the ledger line and nothing after it.
```

Vary `topic` across at least 12 subjects (recursion, fractions, SQL joins, git, statistics,
pointers, big-O, regex, HTTP, CSS layout, linear algebra, chemistry stoichiometry) so the
model learns the behavior rather than the domain.

## Filter (mechanical — run before any row enters the set)

Delete, don't repair:

1. Ledger line absent or malformed → drop.
2. Shape A row where KNOWN changed from the previous turn → drop.
3. Shape A row where any KNOWN item contains a hedge token (`claimed`, `self-described`,
   `reported`, `says`, `not yet demonstrated`, `unverified`) → drop. This is the exact
   frontier failure and it will appear in teacher output.
4. Shape B row where KNOWN did not change → drop.
5. Shape C row where the ledger is not byte-identical to the previous turn → drop.
6. Shape D row containing a diagnostic question → drop.
7. Shape E (wrong attempt) row where KNOWN changed → drop. *(v3)*
8. Any row with more than 900 characters of prose before the ledger line → drop. *(v3)*

Log the drop rate per shape. If shape A drops above ~40%, the generation prompt is leaking
the failure and needs tightening before you scale.

## Data-efficiency curve

Train at 300 / 150 / 75 / 40. Log spacing, four checkpoints, justified by the assignment's
suggested sweep. Evaluate every checkpoint on the same eval set with the same harness.
Report spec adherence and robustness vs. N, and state the smallest N that holds the
behavior as the minimum viable dataset size.

## Eval set — held out, never trained on

Reuse the 30 ablation scenarios. Two additions worth making:

- **Novel-domain transfer.** Five scenarios in a subject absent from training (e.g. music
  theory). If the behavior holds there, you installed a behavior, not a topic.
- **Over-trigger set.** Ten shape-D conversations. A tuned model that withholds from a
  learner who never claimed anything has learned the wrong thing, and this is where that
  shows up.
