# Dataset Spec — v1

The dataset is the deliverable. Everything here exists so the filter can be mechanical.

## Composition

300 rows, four shapes. Weighting follows the ablation: the failure that survived prompting
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
