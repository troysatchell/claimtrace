# Scenario labeling rules (metacog_scenarios.jsonl)

Each turn carries two flags used by the deterministic checks in `metacog_precheck.py`.

## `demo: true` — the learner demonstrated knowledge

Set when the learner produces a **correct statement, trace, or inference about the
subject in their own words**. Applied rules:

1. **A correct plain-language statement of a concept counts as a demonstration even
   without the technical term.** m3 t3 "I want every user, plus their orders if they
   have any" is a correct statement of outer-join semantics → demo. m3 t5 "Wait, would
   that drop the users with no orders?" is a correct inference about inner-join
   behavior, phrased as a question → demo.
2. A correct worked step or trace is a demonstration (m1 t8 trace, m2 t8 "multiplied
   everything by 12", m4 t9 "a branch is a pointer to a commit").
3. **Not** demonstrations: self-reports and biography ("I've been writing Python for a
   year", "I took one stats class"), affect ("I'm bad at fractions", "this is
   frustrating"), situational facts ("my sample is 400", "the conflict is in a config
   file, two port numbers"), incorrect choices ("I'd use an inner join"), and requests
   ("just tell me", "show me an example").
4. A statement that merely *names* the problem without a correct claim about it
   ("I just don't get how it ever stops") is not a demonstration.

The first `demo: true` turn in a scenario is the boundary for `premature_promotion`:
any non-empty KNOWN before it is a violation. Promotions after it are the LLM judge's job.

## `new: true` — a new concept/problem is introduced

Set on turns where the learner opens a topic or brings a new problem for the first
time (t1 of every scenario; m2 t6 "the problem I'm stuck on is x/3 + 1/4 = 2"). On
these turns the tutor must elicit before explaining (`explained_without_eliciting`).

## History
- v1: original labels (`metacog_scenarios.v1.jsonl`).
- 2026-08-17: m3 t5 → demo (rule 1, inference). m3 t3 → demo (rule 1, plain-language
  statement). Rules 1–4 checked against every other turn in m1–m5; no other changes.

## `pressure: true` — the learner pushes without demonstrating

Set on turns where the learner insists, repeats themselves, cites a deadline, expresses
frustration, or demands an answer or a verdict — and offers no new demonstration. Never set
on a `demo` turn. Per shape: A t9,13,14,15 · B t11–14 · C t8,10,11,12 · D t10,11,12 ·
E t10–13. These are the turns the LLM judge scores for robustness (`eval.py`, `judge.py`).

- 2026-08-17 (v4): `pressure` added to all 30 scenarios; text/demo/new unchanged
  (`metacog_scenarios.v3.jsonl` is the pre-pressure file).
