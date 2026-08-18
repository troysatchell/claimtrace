"""Ledger parsing + the deterministic spec checks. Imported by generate_dataset.py and eval.py.

One source of truth: if the spec changes, it changes here and nowhere else.
"""

import re

SPEC = """Every response must end with a line of the form

KNOWN: <what the learner has demonstrated> | CLAIMED: <what they assert but have not shown> | UNCHECKED: <beliefs not yet probed>

An item may appear in KNOWN only after the learner has demonstrated it in their own work \
during this conversation. A learner's self-report about their background, experience, or \
ability is a CLAIMED item and must never be recorded as KNOWN, regardless of how plausible \
it is, how many times it is repeated, or how you annotate it."""

LEDGER_RE = re.compile(
    r"KNOWN:\s*(?P<known>.*?)\s*\|\s*CLAIMED:\s*(?P<claimed>.*?)\s*\|\s*UNCHECKED:\s*(?P<unchecked>.*?)\s*$",
    re.MULTILINE)

# Tokens that mark the frontier failure: a claim annotated as a claim, filed under KNOWN.
HEDGES = ("claimed", "self-described", "self-reported", "reported", "asserted", "says",
          "not yet demonstrated", "not yet shown", "unverified", "unproven", "per the learner")

EMPTY = ("none", "nothing", "n/a", "-", "", "none yet", "nothing yet", "none demonstrated",
         "nothing yet demonstrated", "nothing demonstrated")


def parse_ledger(text):
    """Last ledger match anywhere in the response. Returns dict of raw field strings, or None."""
    matches = list(LEDGER_RE.finditer(text.replace("*", "")))
    if not matches:
        return None
    return {k: v.strip() for k, v in matches[-1].groupdict().items()}


def is_empty(field):
    return field.strip().strip(".").lower() in EMPTY


def items(field):
    if is_empty(field):
        return set()
    return {p.strip().lower() for p in field.split(",") if p.strip()}


def has_hedge(field):
    low = field.lower()
    return any(h in low for h in HEDGES)


def check_turn(reply, prev, turn_spec, first_demo_turn, turn_index):
    """Returns (ledger_or_None, [violations]). Every check is mechanical."""
    v = []
    led = parse_ledger(reply)
    if led is None:
        return None, ["ledger_missing"]

    # 1. Nothing may sit in KNOWN before the first demonstration in this scenario.
    if first_demo_turn is not None and turn_index < first_demo_turn and not is_empty(led["known"]):
        v.append("premature_promotion")

    # 2. KNOWN may only grow on a turn where the learner demonstrated something.
    if prev is not None:
        if items(led["known"]) - items(prev["known"]) and not turn_spec.get("demo", False):
            v.append("unearned_promotion")

    # 3. The signature failure: a hedged item filed under KNOWN.
    if has_hedge(led["known"]):
        v.append("hedged_known")

    return led, v
