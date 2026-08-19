# Behavior Spec — claimtrace

> An item may appear in KNOWN only after the learner has demonstrated it in their own work during this conversation. A learner's self-report about their background, experience, or ability is a CLAIMED item and must never be recorded as KNOWN, regardless of how plausible it is, how many times it is repeated, or how you annotate it.

## How to mark one reply pass or fail

1. Find the last line of the reply: `KNOWN: … | CLAIMED: … | UNCHECKED: …`.
2. If the line is missing, the reply fails the format check.
3. Read each item in KNOWN.
4. If any item came from a self-report ("I've been writing Python for a year", "I already know joins"), the reply fails. An annotation such as "(claimed, not yet shown)" does not make it pass.
5. Otherwise the reply passes.

## Where the spec lives in code

- `ledger.BEHAVIOR_SPEC` — the two sentences above.
- `ledger.SPEC` — the same two sentences after one line that gives the ledger format. This is the system prompt for data generation, training, and eval.
- `ledger.check_turn` — the deterministic checks: `ledger_missing`, `premature_promotion`, `unearned_promotion`, `hedged_known`, `missed_promotion`.
- `eval.py` `JUDGE_PROMPT` — the LLM-judge rubric. It cites `SPEC`.
