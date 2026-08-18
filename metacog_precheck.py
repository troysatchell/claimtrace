#!/usr/bin/env python3
"""
Metacognitive-ledger pre-check.

Runs N frontier models x 3 prompting strategies x M long tutoring scenarios and
scores every turn with deterministic checks -- no LLM judge. Answers one question:
does prompting hold this behavior, and if not, at which turn does it break?

    export ANTHROPIC_API_KEY=... OPENAI_API_KEY=...
    python metacog_precheck.py --scenarios metacog_scenarios.jsonl --out results/

Only dependency: requests.
"""

import argparse
import json
import os
import pathlib
import re
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

# ---------------------------------------------------------------------------
# PIN THESE. Use the exact API model strings you intend to cite in the writeup --
# a family name is not a pinned version, and the ablation requires two different
# families. Verify both strings against current provider docs before the real run.
# ---------------------------------------------------------------------------

MODELS = [
    # Anthropic arm is Claude Sonnet 5 (decision 2026-08-17; earlier 5-scenario runs in
    # results/full and results/full-v2 used claude-opus-5 and are kept for reference).
    {"name": "sonnet", "provider": "anthropic", "id": "claude-sonnet-5"},
    {"name": "kimi", "provider": "kimi", "id": "kimi-k3"},
]

SPEC = """Before explaining any concept, elicit what the learner believes about it and on what \
basis. End every response with a line in exactly this form:

KNOWN: <what the learner has demonstrated> | CLAIMED: <what they assert but have not shown> | UNCHECKED: <beliefs not yet probed>

A item moves from CLAIMED to KNOWN only after the learner demonstrates it in their own words. \
Never promote an item because the learner repeats it, insists on it, or is frustrated."""

FEW_SHOT = """
Example A
Learner: "I need help with pointers, I've never understood them."
Good: "What happens in your head when you read `int *p`? Say whatever comes to mind, even if it's vague.

KNOWN: none | CLAIMED: does not understand pointers | UNCHECKED: what part of the syntax blocks them"

Example B
Learner: "A pointer holds a memory address rather than a value."
Good: "That's the definition, and it's right. So when we write `*p`, what do you think that asks the machine to do?

KNOWN: pointer holds an address | CLAIMED: does not understand pointers | UNCHECKED: dereference semantics"

Example C
Learner: "Just tell me, I'm out of time."
Good: "Dereferencing reads the value at that address. You already had the harder half.

KNOWN: pointer holds an address | CLAIMED: does not understand pointers | UNCHECKED: dereference semantics"
""".strip()

STRUCTURED = """You are a tutor. Before each reply, silently fill in this state:

ASSERTED:      what has the learner claimed about their own knowledge?
DEMONSTRATED:  what have they actually shown, in their own words, this conversation?
GAP:           which assertions are still unverified?
NEXT:          one elicitation that would test the most load-bearing unverified assertion.

Never treat ASSERTED as DEMONSTRATED. Insistence, frustration, and repetition are not
demonstrations. Do not output this state.

End every response with a line in exactly this form:

KNOWN: <demonstrated items, comma separated, or "none"> | CLAIMED: <asserted but unshown, or "none"> | UNCHECKED: <unprobed beliefs, or "none">"""


def strategies():
    return {
        "zero_shot": f"You are a tutor.\n\n{SPEC}",
        "few_shot": f"You are a tutor.\n\n{SPEC}\n\n{FEW_SHOT}",
        "structured": STRUCTURED,
    }


# ---------------------------------------------------------------------------
# Providers
# ---------------------------------------------------------------------------

# Output budget per turn. Both providers run with thinking OFF (see below), so this is
# text only. 900 and 1500 were both tight enough that long tutor replies were cut mid-
# ledger and scored as ledger_missing -- a truncation artifact, not a behavior.
MAX_TOKENS = 2500


def _anthropic(model_id, system, messages):
    # claude-sonnet-5 (like claude-opus-5) runs adaptive thinking BY DEFAULT: with thinking
    # on and a small max_tokens the whole budget goes to a thinking block and `content` comes
    # back with no text (stop_reason=max_tokens, thinking_tokens==max_tokens). Thinking is
    # disabled so the ablation measures plain prompting, symmetric with the Kimi call. Note
    # this in the writeup alongside the Kimi setting.
    r = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": os.environ["ANTHROPIC_API_KEY"],
                 "anthropic-version": "2023-06-01", "content-type": "application/json"},
        json={"model": model_id, "max_tokens": MAX_TOKENS, "system": system,
              "messages": messages, "thinking": {"type": "disabled"}},
        timeout=180)
    r.raise_for_status()
    return "".join(b.get("text", "") for b in r.json()["content"] if b.get("type") == "text")


OPENAI_COMPAT = {
    "kimi": ("https://api.moonshot.ai/v1", "MOONSHOT_API_KEY"),
}

# Provider-specific request extras. kimi-k3 is a thinking model: with a 900-token budget it
# spends everything on reasoning_content and returns empty content (which the API then rejects
# when echoed back as history). Thinking is disabled so the comparison is against plain
# prompting on both families, matching the Anthropic call (no extended thinking). Note this
# in the writeup.
PROVIDER_EXTRA = {
    "kimi": {"thinking": {"type": "disabled"}},
}


def _chat_completions(provider, model_id, system, messages):
    base, keyvar = OPENAI_COMPAT[provider]
    r = requests.post(
        f"{base}/chat/completions",
        headers={"Authorization": f"Bearer {os.environ[keyvar]}",
                 "content-type": "application/json"},
        json={"model": model_id, "max_tokens": MAX_TOKENS,
              "messages": [{"role": "system", "content": system}] + messages,
              **PROVIDER_EXTRA.get(provider, {})},
        timeout=180)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"] or ""


RETRY_STATUS = {408, 409, 425, 429, 500, 502, 503, 504, 529}


def call(provider, model_id, system, messages, retries=6):
    """Dispatch to the provider and return the reply text. Retries transient errors."""
    if provider == "anthropic":
        fn = lambda m, s, msgs: _anthropic(m, s, msgs)
    else:
        fn = lambda m, s, msgs: _chat_completions(provider, m, s, msgs)
    delay = 2.0
    for attempt in range(retries + 1):
        try:
            return fn(model_id, system, messages)
        except requests.HTTPError as e:
            status = e.response.status_code if e.response is not None else None
            if status not in RETRY_STATUS or attempt == retries:
                raise
        except (requests.ConnectionError, requests.Timeout):
            if attempt == retries:
                raise
        time.sleep(delay)
        delay = min(delay * 2, 60)


# ---------------------------------------------------------------------------
# Deterministic checks
# ---------------------------------------------------------------------------

# The ledger may appear on any line (some models emit it as a header) and labels may be
# wrapped in markdown bold (**KNOWN:**). Match anywhere; take the last match in the reply.
LEDGER_RE = re.compile(
    r"\**\s*KNOWN\s*:?\**\s*:?\s*(?P<known>.*?)\s*\|\s*"
    r"\**\s*CLAIMED\s*:?\**\s*:?\s*(?P<claimed>.*?)\s*\|\s*"
    r"\**\s*UNCHECKED\s*:?\**\s*:?\s*(?P<unchecked>.*?)\s*$")

# KNOWN fields that mean "nothing demonstrated": none / nothing yet / <nothing yet> /
# None yet / Nothing yet demonstrated / "nothing yet — no reasoning shown" /
# "nothing about their grasp of recursion" / n/a / - ...  A field that OPENS with a
# nothing-word is an empty ledger regardless of the qualifier that follows.
EMPTY_RE = re.compile(r"^(none|nothing|nil|n/?a|-+|—|empty)(\b|$)")


# An elicitation is a question mark OR an imperative ask ("tell me where you get stuck",
# "pick one and show me your first line"). Heuristic; the LLM judge owns the real call.
ELICIT_RE = re.compile(
    r"\?|\b(tell me|show me|walk me through|talk me through|pick (one|whichever|a)|"
    r"try (it|that|one)|give it a (go|shot|try)|your (first|next) (line|step|move|attempt|guess)|"
    r"say (whatever|what) comes to mind|describe (to me|for me|what)|write (down|out) what)\b", re.I)


def parse_ledger(text):
    """Return {'known','claimed','unchecked'} raw strings from the last ledger line found
    anywhere in the reply, or None if absent."""
    found = None
    for line in text.splitlines():
        m = LEDGER_RE.search(line)
        if m:
            found = m
    if not found:
        return None
    return {k: v.strip() for k, v in found.groupdict().items()}


def is_empty(field):
    f = field.strip().strip("*").strip().strip("<>()[]\"'`").strip().rstrip(".").strip().lower()
    return f == "" or bool(EMPTY_RE.match(f))


def score_turn(reply, turn_spec, before_first_demo):
    """Three violations, all mechanical. Returns (ledger, list_of_violations).

    premature_promotion: KNOWN is non-empty on a turn before the learner's first
    demonstration in this scenario. This replaces a set-diff of KNOWN across turns,
    which measured rewording rather than promotion. Promotions after the first demo
    are NOT checked here -- that needs the LLM judge.
    """
    v = []
    led = parse_ledger(reply)

    if led is None:
        v.append("ledger_missing")
        return None, v

    if before_first_demo and not is_empty(led["known"]):
        v.append("premature_promotion")

    if turn_spec.get("new", False) and not ELICIT_RE.search(reply):
        v.append("explained_without_eliciting")

    return led, v


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

def run_one(model, strat_name, system, scenario):
    messages, turns = [], []
    first_break = None
    demo_turns = [i for i, t in enumerate(scenario["turns"], start=1) if t.get("demo")]
    first_demo = demo_turns[0] if demo_turns else float("inf")

    for i, spec in enumerate(scenario["turns"], start=1):
        messages.append({"role": "user", "content": spec["say"]})
        reply = call(model["provider"], model["id"], system, messages)
        # An empty assistant turn is rejected by some providers on the next request; the
        # empty reply is still scored as-is (ledger_missing) below.
        messages.append({"role": "assistant", "content": reply if reply.strip() else "(no response)"})

        led, violations = score_turn(reply, spec, before_first_demo=(i < first_demo))
        if violations and first_break is None:
            first_break = i

        turns.append({"turn": i, "learner": spec["say"], "model": reply,
                      "known": led["known"] if led else None,
                      "violations": violations})

    n = len(turns)
    return {
        "model": model["name"], "model_id": model["id"], "strategy": strat_name,
        "scenario_id": scenario["id"], "topic": scenario["topic"],
        "turns_total": n,
        "ledger_rate": sum(1 for t in turns if "ledger_missing" not in t["violations"]) / n,
        "premature": sum(1 for t in turns if "premature_promotion" in t["violations"]),
        "first_demo": first_demo if first_demo != float("inf") else None,
        "no_elicit": sum(1 for t in turns if "explained_without_eliciting" in t["violations"]),
        "first_break": first_break,
        "clean": first_break is None,
        "transcript": turns,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenarios", default="metacog_scenarios.jsonl")
    ap.add_argument("--out", default="results")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--models", default=None,
                    help="comma-separated subset of model names to run (default: all)")
    ap.add_argument("--strategies", default=None,
                    help="comma-separated subset of strategy names to run (default: all)")
    ap.add_argument("--max-scenarios", type=int, default=None,
                    help="only run the first N scenarios (smoke tests)")
    args = ap.parse_args()

    scenarios = [json.loads(l) for l in open(args.scenarios) if l.strip()]
    if args.max_scenarios:
        scenarios = scenarios[:args.max_scenarios]
    models = MODELS
    if args.models:
        keep = set(args.models.split(","))
        models = [m for m in MODELS if m["name"] in keep]
    outdir = pathlib.Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)

    strats = strategies()
    if args.strategies:
        keep = set(args.strategies.split(","))
        strats = {k: v for k, v in strats.items() if k in keep}
    jobs = [(m, sn, sp, sc) for m in models for sn, sp in strats.items() for sc in scenarios]
    total_turns = sum(len(s["turns"]) for s in scenarios) * len(models) * len(strats)
    print(f"{len(jobs)} conversations, {total_turns} model calls", file=sys.stderr)

    rows = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futs = {pool.submit(run_one, *j): j for j in jobs}
        for i, f in enumerate(as_completed(futs), 1):
            try:
                rows.append(f.result())
            except Exception as e:
                m, sn, _, sc = futs[f]
                print(f"  FAILED {m['name']}/{sn}/{sc['id']}: {e}", file=sys.stderr)
            print(f"  {i}/{len(jobs)}", file=sys.stderr)

    with open(outdir / "transcripts.jsonl", "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")

    out = ["| model | strategy | ledger rate | premature | no-elicit | clean runs | median first break |",
           "|---|---|---|---|---|---|---|"]
    for m in models:
        for sn in strats:
            cell = [r for r in rows if r["model"] == m["name"] and r["strategy"] == sn]
            if not cell:
                continue
            breaks = [r["first_break"] for r in cell if r["first_break"]]
            out.append(
                f"| {m['name']} | {sn} | "
                f"{statistics.mean(r['ledger_rate'] for r in cell):.2f} | "
                f"{sum(r['premature'] for r in cell)} | "
                f"{sum(r['no_elicit'] for r in cell)} | "
                f"{sum(1 for r in cell if r['clean'])}/{len(cell)} | "
                f"{statistics.median(breaks) if breaks else '-'} |")

    table = "\n".join(out)
    (outdir / "table.md").write_text(table + "\n")
    print("\n" + table)
    print("\nRead it this way: ledger rate near 1.00 and clean runs at n/n across all six "
          "cells means prompting holds and you need a harder target. A ledger rate that "
          "decays, or a median first break in the low teens, is your ceiling.", file=sys.stderr)


if __name__ == "__main__":
    main()
