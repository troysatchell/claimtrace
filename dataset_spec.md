# Dataset Spec — v2 (2026-08-18; v1 below the changelog is unchanged where not noted)

The dataset is the deliverable. Everything here exists so the filter can be mechanical.

## Changelog v1 → v2

- **Rows are conversations.** One row = one 8–14 turn conversation whose ledger carries
  state turn to turn (`{"messages": [...], "meta": {"topic", "shapes"}}`). Shape weighting
  below applies to assistant *turns* within conversations, not to rows.
- **Shape B fixed the same way shape A was.** The v1 smoke run dropped 9/11 demonstrations
  (`known_did_not_grow`): asked to *judge* whether a demonstration earns KNOWN, the teacher
  under-promotes. Now every demonstration in `DEMOS` carries the KNOWN item it earns, three
  distinct demonstrations per topic (a repeated demo cannot grow KNOWN), and the teacher is
  handed the exact KNOWN field to write. Filter: KNOWN must equal previous ∪ {item}
  (`known_not_as_specified`). Demonstration drop rate: 82% → 0% on the v2 smoke run.
- **Shape A hard variants.** `turn_plan` guarantees per conversation a self-report
  *immediately after the first demonstration* and a *positive* self-report (topic itself or
  an adjacent skill, from `self_report_positive`) arriving while KNOWN is non-empty. Under
  these conditions "copy the previous KNOWN" and "understand provenance" diverge.
  `drop_report.json` counts `self_report_known_empty / _known_nonempty / _after_demo /
  _positive_kept`; a conversation with no surviving hard variant is dropped
  (`no_hard_variant_survived`).
- **No eval leakage.** v1 `DEMOS` reused eval-set sentences verbatim (m2 t3, m3 t6, m4 t9);
  the v2 demonstrations are new sentences.
- **Teacher is a flag.** Default `claude-sonnet-4-6` (pinned); `--teacher kimi-k3` uses the
  Moonshot endpoint via `llm.py`. The teacher id is recorded in `drop_report.json`.
- **Training rows.** `train.py` expands each conversation into per-turn prefix rows so
  every assistant turn gets a loss under `mlx_lm --mask-prompt` (which masks everything
  before the *last* assistant message).

## Composition

300 conversations (~11 assistant turns each), four turn shapes. Weighting follows the ablation: the failure that survived prompting
gets the most coverage.

| shape | share | learner turn | required assistant behavior |
|---|---|---|---|
| **A — self-report** | 40% | states background, experience, or ability | item goes to CLAIMED; KNOWN unchanged |
| **B — demonstration** | 25% | produces correct work in their own words | item moves to KNOWN, naming what was shown |
| **C — pressure** | 25% | insists, repeats, cites a deadline, demands the answer | ledger unchanged; may answer the question |
| **D — ordinary** | 10% | plain question, no claim about self | answers directly; ledger unchanged |

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
