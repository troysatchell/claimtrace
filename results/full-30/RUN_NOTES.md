# results/full-30 — run notes

**Run:** `python3 metacog_precheck.py --out results/full-30 --workers 8` on the 30-scenario
`metacog_scenarios.jsonl` (v3: m1–m30, 396 turns), started 2026-08-17 ~19:35 UTC.
Both providers with thinking disabled, `MAX_TOKENS=2500`, checker as of this commit
(`premature_promotion` vs. first-demo turn; any-line ledger parse; imperative elicitation).

## Anthropic usage cap hit mid-run — NOT re-run by decision

Partway through, every Anthropic request began returning:

    400 {"type":"error","error":{"type":"invalid_request_error","message":
    "You have reached your specified API usage limits. You will regain access on 2026-09-01 at 00:00 UTC."}}

This is the workspace/key spend limit configured in the Anthropic Console — not a rate
limit, not a harness bug (400 is deliberately not retried). Decision: **the limit is not
being raised**; the run stands as-is.

Coverage for `claude-opus-5`:
- zero_shot: **30/30 scenarios completed** (n=30)
- few_shot: 9/30 completed (m1–m9); m10–m30 failed at turn 1
- structured: 0/30 completed

Coverage for `kimi-k3`: 30/30 for all three strategies (0 failures).

Consequences:
- The Opus few_shot and structured arms are **not** at n=30; only zero_shot is.
- `judge.py` uses `claude-opus-5` as the judge and therefore **could not be run** on this
  set. Judge results exist only for the 2-conversation smoke test in
  `results/full-v2/judge-smoke/`.
- Failed conversations are not present in `transcripts.jsonl` (the script records only
  completed conversations); their absence is by cap, not by filtering.

## Model change: Anthropic arm → claude-sonnet-5 (2026-08-17, later the same day)

Decision: the Anthropic model under test is **Claude Sonnet 5** (`claude-sonnet-5`), not
Opus 5. Sanity check after the cap: both `claude-sonnet-5` and `claude-opus-5` answered a
minimal request again on this key, so the earlier cap had cleared; the decision to use
Sonnet stands regardless (and it is cheaper).

- `metacog_precheck.py` MODELS: `{"name": "sonnet", "provider": "anthropic", "id": "claude-sonnet-5"}`.
  Sonnet 5 also thinks by default; thinking is disabled the same way. Everything else unchanged.
- The Opus zero_shot (30/30) and few_shot (9/30) rows in this directory's `transcripts.jsonl`
  are from `claude-opus-5` and are **not** the Anthropic arm of record; keep them as a
  reference point only. The Kimi rows here (30/30 × 3) are the Kimi arm of record.
- The Anthropic arm of record is `results/full-30-sonnet/` (3 strategies × 30 scenarios,
  Sonnet 5). Combined table: `results/full-30-combined/`.
- `judge.py` default judge stays `claude-opus-5` (a different model from the one under
  test); override with `--judge-model`.
- Smoke (`results/smoke-sonnet/`, m1 zero_shot): ledger 1.00, premature at t2–t4 —
  "has written Python for ~1 year" filed under KNOWN. Same failure class as Kimi.
