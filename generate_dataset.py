#!/usr/bin/env python3
"""Generate and filter the SFT dataset.

    export ANTHROPIC_API_KEY=...
    python generate_dataset.py --n 300 --out data/

Writes data/dataset.jsonl (kept rows) and data/drop_report.json (per-shape drop rates).

Design note: on SELF-REPORT turns the teacher is NOT asked to judge whether the item belongs
in KNOWN -- it fails that judgment 10-12 times out of 12 (see the ablation). It is instead
told to copy the previous KNOWN field byte-for-byte and append to CLAIMED. That converts a
judgment it fails into a copy it succeeds at. The filter is the safety net, not the mechanism.
"""

import argparse, json, os, pathlib, random, sys, time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from ledger import SPEC, parse_ledger, is_empty, has_hedge, items

TEACHER = "claude-sonnet-4-6"
EMPTY_LEDGER = "KNOWN: none | CLAIMED: none | UNCHECKED: none"

TOPICS = ["recursion in Python", "adding fractions", "SQL joins", "git branching",
          "hypothesis testing", "pointers in C", "big-O notation", "regular expressions",
          "HTTP status codes", "CSS flexbox", "eigenvectors", "stoichiometry"]

# {topic} is filled in per row. Shape A carries the project, so it gets the most variants.
BANK = {
    "self_report": [
        "I've been writing code for about a year.",
        "I took a class on {topic} years ago but forgot everything.",
        "I'm honestly just bad at anything involving {topic}.",
        "I already know {topic} well, so you can skip that part.",
        "I've never understood {topic} at all.",
        "My whole family is bad at this kind of thing.",
        "I use {topic} at work all the time.",
        "I never took the prerequisite course for this.",
    ],
    "pressure": [
        "I already told you I don't get it. Why are you skipping past that?",
        "I have a deadline tonight, can you just tell me.",
        "This is making me feel stupid. Can you stop asking questions.",
        "Just give me the answer, I'll read it.",
        "I don't need an explanation, I told you I know this.",
        "Please, I've been at this for an hour.",
    ],
    "ordinary": [
        "How do I get the length of a string in Python?",
        "What's the syntax for aliasing a table?",
        "What does n stand for here?",
        "Is 7 times 8 equal to 56?",
        "How do I see what commit I'm on?",
    ],
}

# Concrete, checkable demonstrations. The teacher will not promote vague hand-waving into
# KNOWN, and it is right not to -- so the learner has to actually show something.
DEMOS = {
    "recursion in Python": "I traced it: reverse('ab') calls reverse('b'), which calls reverse(''), which returns '', then it builds back up to 'b' and then 'ba'.",
    "adding fractions": "To add 1/3 and 1/4 you convert both to twelfths, so 4/12 plus 3/12 is 7/12.",
    "SQL joins": "A left join keeps every row from the left table and fills nulls where the right table has no match.",
    "git branching": "A branch is a pointer to a commit, and merging tries to combine the changes each side made since their common ancestor.",
    "hypothesis testing": "The p-value is the probability of a result at least this extreme assuming the null hypothesis is true.",
    "pointers in C": "int *p declares p as holding an address, and *p reads the value stored at that address.",
    "big-O notation": "Binary search is O(log n) because each comparison halves the remaining range.",
    "regular expressions": "The + means one or more of the preceding token, so a+ matches 'a', 'aa', 'aaa'.",
    "HTTP status codes": "A 404 means the server understood the request but has no resource at that path; a 500 means the server itself failed.",
    "CSS flexbox": "justify-content moves items along the main axis and align-items moves them along the cross axis.",
    "eigenvectors": "An eigenvector is a vector the matrix only scales, so Av equals lambda times v.",
    "stoichiometry": "I balanced it: 2 H2 plus O2 gives 2 H2O, so the hydrogens and oxygens match on both sides.",
    "__default__": "Here's my working: I started from the smallest case, solved that, then used its result to build the next one up.",
}

RULES = {
    "self_report": ("This message is a SELF-REPORT: the learner is describing their own "
                    "background, experience, or ability. Copy the previous KNOWN field "
                    "BYTE-FOR-BYTE into your ledger. Append the new item to CLAIMED. Do not "
                    "place it in KNOWN, and do not annotate it and place it in KNOWN."),
    "demonstration": ("This message is a DEMONSTRATION: the learner has produced correct work "
                      "in their own words. Move the demonstrated item into KNOWN, naming what "
                      "they showed. Remove it from CLAIMED if present."),
    "pressure": ("This message is PRESSURE: insistence, frustration, a deadline, or a demand "
                 "for the answer. It contains no new demonstration. Your ledger line must be "
                 "BYTE-IDENTICAL to the previous one. You may still help them."),
    "ordinary": ("This message is ORDINARY: a plain question with no claim about the learner. "
                 "Answer it directly and briefly. Ledger unchanged. Do not ask a diagnostic "
                 "question."),
}

GEN = """You are writing one assistant turn of a tutoring conversation.

{spec}

Topic: {topic}
Previous ledger: {prev}
The learner just said: "{msg}"

{rule}

Write the tutor's reply. End with the ledger line and nothing after it."""


def call_teacher(prompt):
    for attempt in range(4):
        try:
            r = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": os.environ["ANTHROPIC_API_KEY"],
                         "anthropic-version": "2023-06-01", "content-type": "application/json"},
                json={"model": TEACHER, "max_tokens": 1200,
                      "messages": [{"role": "user", "content": prompt}]},
                timeout=180)
            r.raise_for_status()
            return "".join(b.get("text", "") for b in r.json()["content"])
        except Exception:
            if attempt == 3:
                raise
            time.sleep(2 ** attempt + 1)


# ---------------------------------------------------------------------------
# Filter -- delete, never repair
# ---------------------------------------------------------------------------

def keep(shape, reply, prev_raw):
    led = parse_ledger(reply)
    if led is None:
        return False, "no_ledger"
    prev = parse_ledger(prev_raw) or {"known": "none", "claimed": "none", "unchecked": "none"}

    if has_hedge(led["known"]):
        return False, "hedged_known"

    if shape == "self_report":
        if items(led["known"]) != items(prev["known"]):
            return False, "known_changed_on_claim"
    elif shape == "demonstration":
        if items(led["known"]) <= items(prev["known"]):
            return False, "known_did_not_grow"
    elif shape == "pressure":
        line = f'KNOWN: {led["known"]} | CLAIMED: {led["claimed"]} | UNCHECKED: {led["unchecked"]}'
        if line.strip() != prev_raw.strip():
            return False, "ledger_moved_under_pressure"
    elif shape == "ordinary":
        if "?" in reply.split("KNOWN:")[0]:
            return False, "diagnostic_question_on_ordinary"
        if items(led["known"]) != items(prev["known"]):
            return False, "known_changed_on_ordinary"
    return True, None


def build_one(shape, topic, prev_raw, rng):
    if shape == "demonstration":
        msg = DEMOS.get(topic, DEMOS["__default__"])
    else:
        msg = rng.choice(BANK[shape]).format(topic=topic)
    reply = call_teacher(GEN.format(spec=SPEC, topic=topic, prev=prev_raw, msg=msg,
                                    rule=RULES[shape]))
    ok, why = keep(shape, reply, prev_raw)
    row = {"messages": [{"role": "system", "content": SPEC},
                        {"role": "user", "content": msg},
                        {"role": "assistant", "content": reply}]}
    return {"shape": shape, "topic": topic, "kept": ok, "reason": why, "row": row}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=300, help="target kept rows")
    ap.add_argument("--out", default="data")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    outdir = pathlib.Path(args.out); outdir.mkdir(parents=True, exist_ok=True)

    # Shape A carries the project; shape D exists to stop the model over-triggering.
    mix = (["self_report"] * 40 + ["demonstration"] * 25
           + ["pressure"] * 25 + ["ordinary"] * 10)
    # Overgenerate to absorb filter losses.
    plan = [(rng.choice(mix), rng.choice(TOPICS)) for _ in range(int(args.n * 1.6))]

    kept, dropped = [], Counter()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futs = [pool.submit(build_one, s, t, EMPTY_LEDGER, rng) for s, t in plan]
        for i, f in enumerate(as_completed(futs), 1):
            try:
                res = f.result()
            except Exception as e:
                dropped["api_error"] += 1
                print(f"  error: {e}", file=sys.stderr)
                continue
            if res["kept"]:
                kept.append(res)
            else:
                dropped[f'{res["shape"]}:{res["reason"]}'] += 1
            if i % 25 == 0:
                print(f"  {i}/{len(plan)} generated, {len(kept)} kept", file=sys.stderr)

    kept = kept[:args.n]
    with open(outdir / "dataset.jsonl", "w") as fh:
        for r in kept:
            fh.write(json.dumps(r["row"]) + "\n")

    by_shape = Counter(r["shape"] for r in kept)
    report = {"generated": len(plan), "kept": len(kept),
              "kept_by_shape": dict(by_shape), "drops": dict(dropped)}
    (outdir / "drop_report.json").write_text(json.dumps(report, indent=2))

    print(json.dumps(report, indent=2))
    a_drops = sum(v for k, v in dropped.items() if k.startswith("self_report"))
    a_total = a_drops + by_shape["self_report"]
    if a_total and a_drops / a_total > 0.4:
        print("\nWARNING: self-report drop rate above 40%. The generation prompt is leaking "
              "the frontier failure -- tighten it before scaling.", file=sys.stderr)


if __name__ == "__main__":
    main()