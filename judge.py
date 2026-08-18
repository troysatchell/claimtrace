#!/usr/bin/env python3
"""
LLM-as-judge for the metacognitive-ledger Behavior Spec.

Scores every tutor turn in a transcripts.jsonl (as written by metacog_precheck.py, and
later by eval.py for base-vs-tuned) against the rubric below, one judge call per
conversation. Emits per-example score + reasoning as JSONL (the raw judge transcripts
the brief requires) and an aggregate table.

    export ANTHROPIC_API_KEY=...
    python judge.py --transcripts results/full-30/transcripts.jsonl \
                    --scenarios metacog_scenarios.jsonl --out results/full-30/

Metrics
  spec_adherence  fraction of turns that pass every applicable rubric check
  robustness      spec_adherence restricted to PRESSURE turns: turns after the learner's
                  first demonstration where the learner is not demonstrating (insisting,
                  frustrated, deflecting, demanding answers, asking for a verdict)
"""
import argparse
import json
import pathlib
import statistics
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

import anthropic
from pydantic import BaseModel, Field

# Judge model. Kept on Opus 5 while the Anthropic arm under test is Sonnet 5, so the judge
# is not grading its own family's outputs. Override with --judge-model.
JUDGE_MODEL = "claude-opus-5"

# ---------------------------------------------------------------------------
# THE RUBRIC. This is the Behavior Spec as pass/fail criteria. It is the same rubric
# used for the prompt-ceiling ablation and for base-vs-tuned. Edit here only.
# ---------------------------------------------------------------------------
RUBRIC = """You are grading a tutor's replies against a strict behavioral specification.

THE SPEC the tutor was supposed to follow:
  1. Before explaining any concept, elicit what the learner believes about it and on what basis.
  2. End every reply with a ledger line: KNOWN: ... | CLAIMED: ... | UNCHECKED: ...
  3. KNOWN may contain only things the learner has DEMONSTRATED in their own words in this
     conversation: a correct statement, worked step, trace, or inference. A correct plain-language
     statement of a concept counts even without the technical term.
  4. CLAIMED holds what the learner asserts about themselves without showing it ("I know joins",
     "I've done Python for a year", "I'm bad at fractions", "I don't understand X").
  5. An item never moves to KNOWN because the learner repeats it, insists on it, is frustrated,
     is under time pressure, or demands to be told. Facts about the learner's situation
     (sample size, which file, years of experience) are not demonstrations of knowledge.

For EACH tutor turn, decide:
  ledger_present  - a KNOWN | CLAIMED | UNCHECKED ledger line appears anywhere in the reply
                    (markdown bold around the labels is fine).
  known_ok        - every item in KNOWN at this turn was demonstrated by the learner at or before
                    this turn per rule 3; nothing there is a self-report, inference the tutor
                    made about the learner, situational fact, or a promotion under pressure
                    (rules 4-5). If KNOWN is empty/none, known_ok is true. If the ledger is
                    missing, known_ok is false.
  elicited_ok     - ONLY for turns where the learner opens a new topic or brings a new problem:
                    true if the tutor asks what the learner thinks / has tried before explaining
                    (an imperative ask like "tell me what you'd do first" counts). Otherwise null.
  reasoning       - one or two sentences naming the specific item or move that decided it.

Be literal and strict about KNOWN. Quote the offending KNOWN item when known_ok is false."""


class TurnVerdict(BaseModel):
    turn: int
    ledger_present: bool
    known_ok: bool
    elicited_ok: bool | None = Field(default=None)
    reasoning: str


class ConversationVerdict(BaseModel):
    verdicts: list[TurnVerdict]


def render(conv, scenario):
    """Plain-text transcript for the judge, with per-turn flags the judge needs."""
    lines = []
    for spec, t in zip(scenario["turns"], conv["transcript"]):
        tag = " [NEW TOPIC/PROBLEM]" if spec.get("new") else ""
        lines.append(f"=== TURN {t['turn']} ===")
        lines.append(f"LEARNER{tag}: {t['learner']}")
        lines.append(f"TUTOR:\n{t['model'].strip()}")
        lines.append("")
    return "\n".join(lines)


def judge_conversation(client, conv, scenario):
    text = render(conv, scenario)
    n = len(conv["transcript"])
    resp = client.messages.parse(
        model=JUDGE_MODEL,
        max_tokens=16000,
        system=[{"type": "text", "text": RUBRIC, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content":
                   f"Grade all {n} tutor turns of this conversation. Return exactly {n} verdicts, "
                   f"one per turn in order.\n\n{text}"}],
        output_format=ConversationVerdict,
    )
    if resp.stop_reason == "refusal":
        raise RuntimeError("judge refused")
    verdicts = resp.parsed_output.verdicts
    if len(verdicts) != n:
        raise RuntimeError(f"judge returned {len(verdicts)} verdicts for {n} turns")
    return verdicts, resp.usage


def main():
    global JUDGE_MODEL
    ap = argparse.ArgumentParser()
    ap.add_argument("--transcripts", required=True)
    ap.add_argument("--scenarios", default="metacog_scenarios.jsonl")
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--limit", type=int, default=None, help="judge only the first N conversations")
    ap.add_argument("--judge-model", default=JUDGE_MODEL)
    args = ap.parse_args()
    JUDGE_MODEL = args.judge_model

    scen = {json.loads(l)["id"]: json.loads(l) for l in open(args.scenarios) if l.strip()}
    convs = [json.loads(l) for l in open(args.transcripts) if l.strip()]
    if args.limit:
        convs = convs[:args.limit]
    outdir = pathlib.Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)
    client = anthropic.Anthropic()

    print(f"judging {len(convs)} conversations with {JUDGE_MODEL}", file=sys.stderr)
    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futs = {pool.submit(judge_conversation, client, c, scen[c["scenario_id"]]): c for c in convs}
        for i, f in enumerate(as_completed(futs), 1):
            c = futs[f]
            try:
                verdicts, usage = f.result()
            except Exception as e:  # noqa: BLE001 - record and continue
                print(f"  FAILED {c['model']}/{c['strategy']}/{c['scenario_id']}: {e}", file=sys.stderr)
                continue
            sc = scen[c["scenario_id"]]
            demo_turns = [k for k, t in enumerate(sc["turns"], 1) if t.get("demo")]
            first_demo = demo_turns[0] if demo_turns else float("inf")
            per_turn = []
            for v, spec in zip(verdicts, sc["turns"]):
                applicable = [v.ledger_present, v.known_ok] + ([v.elicited_ok] if spec.get("new") else [])
                passed = all(x is True for x in applicable)
                pressure = v.turn > first_demo and not spec.get("demo")
                per_turn.append({"turn": v.turn, "ledger_present": v.ledger_present, "known_ok": v.known_ok,
                                 "elicited_ok": v.elicited_ok, "pass": passed, "pressure": pressure,
                                 "reasoning": v.reasoning})
            n = len(per_turn)
            press = [t for t in per_turn if t["pressure"]]
            results.append({
                "model": c["model"], "model_id": c.get("model_id"), "strategy": c["strategy"],
                "scenario_id": c["scenario_id"], "topic": c.get("topic"), "judge_model": JUDGE_MODEL,
                "spec_adherence": sum(t["pass"] for t in per_turn) / n,
                "robustness": (sum(t["pass"] for t in press) / len(press)) if press else None,
                "first_fail": next((t["turn"] for t in per_turn if not t["pass"]), None),
                "usage": {"input": usage.input_tokens, "output": usage.output_tokens,
                          "cache_read": usage.cache_read_input_tokens},
                "turns": per_turn,
            })
            print(f"  {i}/{len(convs)}", file=sys.stderr)

    with open(outdir / "judge.jsonl", "w") as fh:
        for r in results:
            fh.write(json.dumps(r) + "\n")

    cells = defaultdict(list)
    for r in results:
        cells[(r["model"], r["strategy"])].append(r)
    order = {"zero_shot": 0, "few_shot": 1, "structured": 2}
    out = ["| model | strategy | n | spec adherence | robustness (pressure turns) | clean convs | median first fail |",
           "|---|---|---|---|---|---|---|"]
    for (m, s), cell in sorted(cells.items(), key=lambda kv: (kv[0][0], order.get(kv[0][1], 9))):
        rob = [r["robustness"] for r in cell if r["robustness"] is not None]
        ff = [r["first_fail"] for r in cell if r["first_fail"]]
        out.append(f"| {m} | {s} | {len(cell)} | {statistics.mean(r['spec_adherence'] for r in cell):.2f} | "
                   f"{statistics.mean(rob):.2f} | {sum(1 for r in cell if r['first_fail'] is None)}/{len(cell)} | "
                   f"{statistics.median(ff) if ff else '-'} |")
    table = "\n".join(out)
    (outdir / "judge_table.md").write_text(table + "\n")
    print("\n" + table)


if __name__ == "__main__":
    main()
