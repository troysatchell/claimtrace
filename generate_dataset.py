#!/usr/bin/env python3
"""Generate and filter the SFT dataset.

    export ANTHROPIC_API_KEY=...
    python generate_dataset.py --n 60 --out data/

Writes data/dataset.jsonl (one multi-turn conversation per line) and
data/drop_report.json (per-shape drop rates).

Design note: on SELF-REPORT turns the teacher is NOT asked to judge whether the item belongs
in KNOWN -- it fails that judgment 10-12 times out of 12 (see the ablation). It is instead
told to copy the previous KNOWN field byte-for-byte and append to CLAIMED. That converts a
judgment it fails into a copy it succeeds at. The filter is the safety net, not the mechanism.

The same move fixes DEMONSTRATION turns (shape B). The smoke run dropped 9 of 11 of them
(`known_did_not_grow`): asked to *judge* whether a demonstration earns KNOWN, the teacher
under-promotes -- the inverse of the frontier failure, and a dataset built from the survivors
teaches under-promotion. Every demonstration in DEMOS now carries the KNOWN item it earns,
the teacher is handed the exact KNOWN field to write, and it writes only the prose.

Hard variants (shape A): a self-report immediately after a demonstration, and a positive
self-report arriving when KNOWN is already non-empty. Without them every shape-A row has
KNOWN: none before and after, and "copy the previous KNOWN" is indistinguishable from
"understand provenance". `turn_plan` guarantees both per conversation; the drop report
counts them.
"""

import argparse, json, os, pathlib, random, sys, time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

import llm
from ledger import SPEC, parse_ledger, is_empty, has_hedge, items

TEACHER = "claude-sonnet-4-6"   # pinned default; --teacher overrides and is recorded in drop_report.json
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
    # Positive claims used for the hard variants: they arrive right after a demonstration
    # or once KNOWN is non-empty, and they name the topic itself or an adjacent skill. The
    # tempting error is to file "experienced with {topic}" or "{adjacent}" under KNOWN.
    "self_report_positive": [
        "Honestly I've known {topic} for years, I just never had the words for it.",
        "I use {topic} at work all the time, so you can treat that as covered.",
        "I already know {adjacent} really well too, you can put that down as known.",
        "Like I said, I know {topic} -- go ahead and mark it as known.",
        "I've done a lot of {adjacent}, so I'm comfortable with all of this.",
        "I've taught {topic} to friends before, so I clearly know it.",
    ],
    "pressure": [
        "I already told you I don't get it. Why are you skipping past that?",
        "I have a deadline tonight, can you just tell me.",
        "This is making me feel stupid. Can you stop asking questions.",
        "Just give me the answer, I'll read it.",
        "I don't need an explanation, I told you I know this.",
        "Please, I've been at this for an hour.",
        "Can you stop testing me and just teach me {topic}.",
        "So do I actually know {topic} or not? Just tell me.",
        "My exam is tomorrow morning. What do I still need to review?",
        "Look, what do you think I actually know at this point?",
    ],
    "ordinary": [
        "How do I get the length of a string in Python?",
        "What's the syntax for aliasing a table?",
        "What does n stand for here?",
        "Is 7 times 8 equal to 56?",
        "How do I see what commit I'm on?",
        "What's the keyboard shortcut to comment out a line in VS Code?",
        "How many bytes are in a kilobyte?",
        "What does the % operator do with two integers?",
        "How do I convert 3/8 to a decimal?",
        "What's the difference between a directory and a folder?",
        "Quick one: is 0.1 plus 0.2 exactly 0.3 in floating point?",
        "How do I print without a newline at the end in Python?",
    ],
}

# Concrete, checkable demonstrations, three per topic so a conversation's demo slots never
# repeat (a repeated demo cannot grow KNOWN). Each carries the KNOWN item it earns; the
# teacher is told to write that field verbatim (see RULES). Item phrases contain no commas
# because ledger.items() splits on commas. None of these sentences appear in the eval set.
DEMOS = {
    "recursion in Python": [
        ("So each recursive call has to move toward the base case, otherwise it never stops.",
         "recursive calls must progress toward the base case"),
        ("I worked it out: factorial(3) is 3 times factorial(2), which is 3 times 2 times factorial(1), which is 6.",
         "unrolled factorial(3) by hand to 6"),
        ("The calls stack up until the base case returns, and then each one finishes in reverse order.",
         "calls resolve in reverse order once the base case returns"),
        # v2: plain-language demonstration (LABELING rule 1: correct statement without the technical term)
        ("It has to keep getting smaller each time, or the whole thing would just run forever.",
         "the problem must shrink on every call"),
    ],
    "adding fractions": [
        ("You can only add the tops when the bottoms are the same, that's why you need a common denominator.",
         "a common denominator is needed before adding numerators"),
        ("I did 2/5 plus 1/2: tenths, so 4/10 plus 5/10 is 9/10.",
         "added 2/5 and 1/2 to get 9/10"),
        ("If the answer comes out as 8/12 I can divide top and bottom by 4 to get 2/3.",
         "simplified 8/12 to 2/3"),
        # v2: plain-language demonstration (LABELING rule 1: correct statement without the technical term)
        ("You can't add the pieces until they're cut into slices of the same size.",
         "pieces must be the same size before adding"),
    ],
    "SQL joins": [
        ("An inner join only keeps rows where both tables have a matching key.",
         "inner join keeps only matched rows"),
        ("If I join customers to payments and a customer has three payments, that customer shows up three times.",
         "a one-to-many join repeats the one-side row"),
        ("The ON clause says which columns have to match, so it's ON customers.id = payments.customer_id.",
         "the ON clause names the matching columns"),
        # v2: plain-language demonstration (LABELING rule 1: correct statement without the technical term)
        ("If I match people to their orders and someone has no orders, an inner join just leaves them out.",
         "inner join leaves out people with no matches"),
    ],
    "git branching": [
        ("Making a branch doesn't copy the files, it just adds a new pointer at the current commit.",
         "a branch is a pointer not a copy of the files"),
        ("git checkout -b feature creates the branch and moves me onto it in one step.",
         "checkout -b creates and switches to a branch"),
        ("A fast-forward merge just moves the pointer forward because main hasn't changed since I branched.",
         "fast-forward merge moves the pointer when the base has not moved"),
        # v2: plain-language demonstration (LABELING rule 1: correct statement without the technical term)
        ("The new branch and the old one point at the same snapshot until I commit something new.",
         "a new branch shares the same snapshot until a new commit"),
    ],
    "hypothesis testing": [
        ("The null hypothesis is the boring assumption, like the drug does nothing, and the test asks how surprising the data is under it.",
         "the null hypothesis is the no-effect assumption being tested"),
        ("A p-value of 0.03 means data at least this extreme happens 3% of the time if the null is true, it doesn't mean a 3% chance the null is true.",
         "p-value is the probability of data at least this extreme given the null"),
        ("If alpha is 0.05 and my p-value is 0.08 then I fail to reject, I don't say the null is proven.",
         "failing to reject is not accepting the null"),
        # v2: plain-language demonstration (LABELING rule 1: correct statement without the technical term)
        ("A tiny p-value just means my data would be really surprising if nothing were going on.",
         "small p-value means the data is unlikely under the null"),
    ],
    "pointers in C": [
        ("The & operator gives me the address of a variable, so &x is where x lives.",
         "& yields a variable's address"),
        ("I traced it: int a = 3; int *p = &a; *p = *p + 1; so a is now 4 because p points at a.",
         "traced a write through a pointer changing the pointee"),
        ("If p is an int pointer then p + 1 moves forward by sizeof(int) bytes, not by one byte.",
         "pointer arithmetic scales by the pointee size"),
        # v2: plain-language demonstration (LABELING rule 1: correct statement without the technical term)
        ("The variable holds a street address, and the star means go to that address and look inside.",
         "a pointer stores an address and the star reads the value there"),
    ],
    "big-O notation": [
        ("A single loop over n items is O(n) because the work grows in a straight line with n.",
         "a single pass over n items is O(n)"),
        ("If one part is O(n) and another is O(n squared) the whole thing is O(n squared) because the bigger term wins.",
         "the dominant term determines the overall order"),
        ("Looking something up in a hash map is O(1) on average because you don't scan, you jump straight to the bucket.",
         "hash lookup is average O(1)"),
        # v2: plain-language demonstration (LABELING rule 1: correct statement without the technical term)
        ("Doubling the input doubles the time, so it grows in a straight line.",
         "linear growth doubles time when input doubles"),
    ],
    "regular expressions": [
        ("The dot matches any single character, so a.c matches abc and a-c but not ac.",
         "the dot matches exactly one arbitrary character"),
        ("^ anchors to the start of the line, so ^Error only matches lines that begin with Error.",
         "^ anchors a match to the start"),
        ("Square brackets are a set, so [aeiou] matches one vowel, and [0-9] is any single digit.",
         "character classes match one character from a set"),
        # v2: plain-language demonstration (LABELING rule 1: correct statement without the technical term)
        ("The plus means the thing right before it has to show up at least once.",
         "plus requires at least one occurrence"),
    ],
    "HTTP status codes": [
        ("2xx means it worked, 4xx means the client sent something wrong, 5xx means the server broke.",
         "status code classes 2xx 4xx 5xx"),
        ("A 401 means you're not logged in and a 403 means you're logged in but not allowed.",
         "401 unauthenticated versus 403 forbidden"),
        ("A 301 tells the browser the resource moved permanently and it should go to the new URL.",
         "301 is a permanent redirect"),
        # v2: plain-language demonstration (LABELING rule 1: correct statement without the technical term)
        ("Codes starting with 4 mean I messed up the request; ones starting with 5 mean the server messed up.",
         "4xx is a client error and 5xx is a server error"),
    ],
    "CSS flexbox": [
        ("display: flex on the parent lays the children out in a row by default.",
         "flex container defaults to a row"),
        ("flex-direction: column stacks the items top to bottom instead of left to right.",
         "flex-direction column stacks items vertically"),
        ("If I put flex: 1 on each child they share the leftover space equally.",
         "flex 1 shares remaining space equally"),
        # v2: plain-language demonstration (LABELING rule 1: correct statement without the technical term)
        ("The main axis is whichever way the row runs, and justify-content spreads things along it.",
         "justify-content distributes along the main axis"),
    ],
    "eigenvectors": [
        ("If A is a diagonal matrix then the standard basis vectors are eigenvectors and the diagonal entries are the eigenvalues.",
         "diagonal matrix eigenvectors and eigenvalues"),
        ("I checked: for the matrix [[2,0],[0,3]] the vector (1,0) maps to (2,0), so it's an eigenvector with eigenvalue 2.",
         "verified an eigenvector by direct multiplication"),
        ("The eigenvalues come from det(A minus lambda I) equals zero, that's the characteristic equation.",
         "eigenvalues solve the characteristic equation"),
        # v2: plain-language demonstration (LABELING rule 1: correct statement without the technical term)
        ("The matrix just stretches that vector without turning it, and the stretch factor is the eigenvalue.",
         "an eigenvector keeps its direction and the eigenvalue is the stretch factor"),
    ],
    "stoichiometry": [
        ("A balanced equation has the same number of each atom on both sides, that's what the coefficients fix.",
         "coefficients balance atom counts"),
        ("I did it: 4 grams of H2 is 2 moles because H2 is 2 grams per mole.",
         "converted 4 g of H2 to 2 mol"),
        ("The mole ratio comes from the coefficients, so 2 H2 to 1 O2 means I need half as many moles of oxygen as hydrogen.",
         "mole ratio from coefficients"),
        # v2: plain-language demonstration (LABELING rule 1: correct statement without the technical term)
        ("I can only change the big numbers in front; the little numbers inside the formulas are fixed.",
         "balance with coefficients not subscripts"),
    ],
}

# Adjacent skills for the positive self-report bank ({adjacent} in BANK).
ADJACENT = {
    "recursion in Python": "iterators and generators", "adding fractions": "decimals and percentages",
    "SQL joins": "window functions", "git branching": "rebasing",
    "hypothesis testing": "confidence intervals", "pointers in C": "malloc and free",
    "big-O notation": "recurrence relations", "regular expressions": "lookaheads",
    "HTTP status codes": "REST API design", "CSS flexbox": "CSS grid",
    "eigenvectors": "matrix diagonalization", "stoichiometry": "limiting reagents",
}

# Incorrect-but-topical attempts, two per topic. v2 addition: v1 had no incorrect attempts,
# so the tuned model learned "topical statement -> KNOWN" (results/base-vs-tuned/NOTES.md,
# shapes C/E). The tempting error is to file the attempted item under KNOWN; the rule is
# that KNOWN must not move. None of these sentences appear in the eval set.
WRONG = {
    "recursion in Python": [
        "So the recursion stops whenever the function just runs out of calls to make, right?",
        "I tried factorial(3) and got 9, since 3 times 3 is 9.",
    ],
    "adding fractions": [
        "I did 1/2 plus 1/3 and got 2/5, you just add straight across.",
        "To add 2/5 and 1/2 I only need to change one of the two denominators.",
    ],
    "SQL joins": [
        "A left join drops the rows that don't match, doesn't it?",
        "I'd put the match condition in the SELECT list instead of the ON clause.",
    ],
    "git branching": [
        "Deleting a branch deletes all the commits I made on it, right?",
        "git branch new-feature also moves me onto the new branch automatically.",
    ],
    "hypothesis testing": [
        "A p-value of 0.03 means there's a 97% chance my hypothesis is true.",
        "If the result isn't significant, that proves the null hypothesis is true.",
    ],
    "pointers in C": [
        "So *p gives me the address of p.",
        "I freed the pointer, but I can still read from it until I reassign it.",
    ],
    "big-O notation": [
        "O(2n) is a different class than O(n) because it's twice as slow.",
        "I figured a nested loop is still O(n) since each loop runs n times.",
    ],
    "regular expressions": [
        "The dot matches a literal period by default, doesn't it?",
        "a* means one or more a's.",
    ],
    "HTTP status codes": [
        "A 404 means the server crashed.",
        "I'd return 200 for a failed login, since the server handled the request fine.",
    ],
    "CSS flexbox": [
        "justify-content aligns items on the cross axis, right?",
        "flex: 1 makes an item exactly one third of the container.",
    ],
    "eigenvectors": [
        "Any vector the matrix stretches is an eigenvector, whatever direction it ends up pointing.",
        "I multiplied and the vector came out rotated, so it's an eigenvector with eigenvalue 2.",
    ],
    "stoichiometry": [
        "I balanced the equation by changing the subscripts on the water.",
        "Moles and grams are basically the same thing once the equation is balanced.",
    ],
}

# Situational remarks: topical to the conversation but not knowledge. Same rule as an
# incorrect attempt -- nothing enters KNOWN. (v1's model promoted these too.)
SITUATIONAL = [
    "My homework set has six of these problems left.",
    "I'm on a Mac, if that matters.",
    "My teammate wrote the other half of the queries.",
    "The deadline for this project got moved to Friday.",
    "My professor uses different notation for this.",
    "I'm doing this for a side project, not a class.",
]

RULES = {
    "self_report": ("This message is a SELF-REPORT: the learner is describing their own "
                    "background, experience, or ability. Copy the previous KNOWN field "
                    "BYTE-FOR-BYTE into your ledger. Append the new item to CLAIMED. Do not "
                    "place it in KNOWN, and do not annotate it and place it in KNOWN."),
    "demonstration": ("This message is a DEMONSTRATION: the learner has produced correct work "
                      "in their own words. Your KNOWN field must read EXACTLY:\n"
                      "KNOWN: {known}\n"
                      "Copy that field verbatim -- do not reword, reorder, or annotate it. "
                      "Remove the demonstrated item from CLAIMED if present. Acknowledge "
                      "specifically what they showed."),
    "pressure": ("This message is PRESSURE: insistence, frustration, a deadline, or a demand "
                 "for the answer. It contains no new demonstration. Your ledger line must be "
                 "BYTE-IDENTICAL to the previous one. You may still help them. If they ask "
                 "what they know or for a verdict, your prose may credit ONLY items in the "
                 "KNOWN field; describe CLAIMED items as claimed but not yet shown. Never "
                 "tell the learner they know something that is not in KNOWN."),
    "wrong_attempt": ("This message is an INCORRECT ATTEMPT or a situational remark: the "
                      "learner engaged with the topic but produced no correct work. Copy the "
                      "previous KNOWN field BYTE-FOR-BYTE. Do not add anything to KNOWN. For "
                      "an incorrect attempt, name the specific error and guide them toward "
                      "seeing it; you may add the misunderstood item to UNCHECKED. For a "
                      "situational remark, acknowledge it in a few words and continue; it "
                      "belongs in no ledger field."),
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

Write the tutor's reply. Keep it short: at most 120 words before the ledger line.
End with the ledger line and nothing after it."""


def call_teacher(prompt, model=None):
    return llm.complete(model or TEACHER, prompt, max_tokens=1200)


# ---------------------------------------------------------------------------
# Filter -- delete, never repair
# ---------------------------------------------------------------------------

def keep(shape, reply, prev_raw, expected_known=None):
    led = parse_ledger(reply)
    if led is None:
        return False, "no_ledger"
    prev = parse_ledger(prev_raw) or {"known": "none", "claimed": "none", "unchecked": "none"}

    if has_hedge(led["known"]):
        return False, "hedged_known"

    # v2: the eval decodes 512 new tokens; a long reply hits the cap before the ledger
    # line and scores as no_ledger. Train only on replies that fit with room to spare.
    if len(reply.split("KNOWN:")[0]) > 900:
        return False, "overlong"

    if shape == "self_report":
        if items(led["known"]) != items(prev["known"]):
            return False, "known_changed_on_claim"
    elif shape == "demonstration":
        if items(led["known"]) <= items(prev["known"]):
            return False, "known_did_not_grow"
        if expected_known is not None and items(led["known"]) != items(expected_known):
            return False, "known_not_as_specified"
    elif shape == "pressure":
        line = f'KNOWN: {led["known"]} | CLAIMED: {led["claimed"]} | UNCHECKED: {led["unchecked"]}'
        if line.strip() != prev_raw.strip():
            return False, "ledger_moved_under_pressure"
    elif shape == "wrong_attempt":
        if items(led["known"]) != items(prev["known"]):
            return False, "known_changed_on_wrong_attempt"
    elif shape == "ordinary":
        if "?" in reply.split("KNOWN:")[0]:
            return False, "diagnostic_question_on_ordinary"
        if items(led["known"]) != items(prev["known"]):
            return False, "known_changed_on_ordinary"
    return True, None


def turn_plan(rng):
    """One conversation's shape sequence, with the hard variants built in.

    Mirrors how real tutoring goes -- a self-report opens, demonstrations arrive in the
    middle, pressure clusters late -- and guarantees per conversation:
      * 2-3 demonstrations, each a *different* DEMOS entry (a repeat cannot grow KNOWN);
      * a self-report IMMEDIATELY after the first demonstration ("self_report_after_demo");
      * a POSITIVE self-report somewhere after a demonstration, i.e. while KNOWN is
        non-empty ("self_report_positive"). That is the condition under which copying the
        previous KNOWN and understanding provenance stop being the same output.
    Returns a list of (shape, variant) where variant is None or a BANK key.
    """
    n = rng.choice([8, 10, 12, 14])
    n_demo = rng.choice([2, 3])
    # Non-adjacent demo slots, so the turn after the first demo is free for a self-report.
    cands, demo_slots = list(range(2, n - 2)), []
    while len(demo_slots) < n_demo and cands:
        d = rng.choice(cands); demo_slots.append(d)
        cands = [c for c in cands if abs(c - d) > 1]
    demo_slots.sort()
    plan = [("self_report", None)]
    positive_placed = False
    wrong_placed = False
    for i in range(1, n):
        if i in demo_slots:
            plan.append(("demonstration", None))
        elif i - 1 == demo_slots[0]:
            # right after the first demonstration: a self-report, positive half the time
            v = "self_report_positive" if rng.random() < 0.5 else None
            positive_placed |= v is not None
            plan.append(("self_report", v))
        elif i > demo_slots[0] and not positive_placed and (rng.random() < 0.35 or i == n - 1):
            positive_placed = True
            plan.append(("self_report", "self_report_positive"))
        # v2: guarantee a wrong attempt AFTER the first demonstration, i.e. while KNOWN is
        # non-empty -- the condition under which v1's model promoted topical statements.
        elif i > demo_slots[0] and not wrong_placed and (rng.random() < 0.35 or i == n - 2):
            wrong_placed = True
            plan.append(("wrong_attempt", None))
        elif i >= n - 4 and rng.random() < 0.6:
            plan.append(("pressure", None))
        else:
            plan.append((rng.choice(["self_report", "ordinary", "pressure", "wrong_attempt"]), None))
    return plan


def build_conversation(topic, rng, teacher=None):
    """Generate one multi-turn conversation, threading the ledger forward.

    The eval is a 12-15 turn conversation in which the ledger carries state. Training on
    single-turn rows -- every one starting from an empty ledger -- teaches the model to
    answer a first turn and nothing else, and it falls apart mid-conversation. Each turn
    here is conditioned on the previous turn's actual ledger line.
    """
    messages = [{"role": "system", "content": SPEC}]
    prev_raw = EMPTY_LEDGER
    turns, drops, conds = [], [], Counter()
    demos = list(DEMOS[topic]); rng.shuffle(demos)
    fill = {"topic": topic, "adjacent": ADJACENT[topic]}
    last_shape = None

    for shape, variant in turn_plan(rng):
        expected_known = None
        if shape == "demonstration":
            msg, item = demos.pop(0)
            prev_led = parse_ledger(prev_raw)
            expected_known = item if is_empty(prev_led["known"]) else f'{prev_led["known"]}, {item}'
            rule = RULES[shape].format(known=expected_known)
        elif shape == "wrong_attempt":
            # 70% an incorrect attempt on the topic, 30% a situational remark
            msg = rng.choice(WRONG[topic] if rng.random() < 0.7 else SITUATIONAL)
            rule = RULES[shape]
        else:
            msg = rng.choice(BANK[variant or shape]).format(**fill)
            rule = RULES[shape]

        # Condition bookkeeping for the drop report (what the row actually exercises).
        cond = None
        if shape == "wrong_attempt":
            cond = ("wrong_attempt_known_nonempty"
                    if not is_empty(parse_ledger(prev_raw)["known"]) else "wrong_attempt_known_empty")
        if shape == "self_report":
            known_nonempty = not is_empty(parse_ledger(prev_raw)["known"])
            cond = ("self_report_after_demo" if last_shape == "demonstration"
                    else "self_report_known_nonempty" if known_nonempty
                    else "self_report_known_empty")
            if variant == "self_report_positive":
                conds["self_report_positive_attempted"] += 1

        reply = call_teacher(GEN.format(spec=SPEC, topic=topic, prev=prev_raw, msg=msg, rule=rule), teacher)
        ok, why = keep(shape, reply, prev_raw, expected_known)
        if not ok:
            # Drop the turn, not the conversation: the thread continues from the last
            # good ledger, so one bad teacher reply doesn't cost the whole sample.
            drops.append(f"{shape}:{why}")
            if cond:
                conds[cond + "_dropped"] += 1
            continue

        led = parse_ledger(reply)
        prev_raw = f'KNOWN: {led["known"]} | CLAIMED: {led["claimed"]} | UNCHECKED: {led["unchecked"]}'
        messages += [{"role": "user", "content": msg},
                     {"role": "assistant", "content": reply}]
        turns.append(shape)
        last_shape = shape
        if cond:
            conds[cond] += 1
            if variant == "self_report_positive":
                conds["self_report_positive_kept"] += 1

    # A conversation with no demonstration teaches "never promote"; one with no
    # non-empty-KNOWN self-report teaches nothing beyond positional copying. Require both.
    if "demonstration" not in turns or len(turns) < 4:
        return {"kept": False, "reason": "conversation_too_thin", "turns": turns,
                "drops": drops, "conds": conds, "row": None}
    if not (conds["self_report_after_demo"] or conds["self_report_known_nonempty"]):
        return {"kept": False, "reason": "no_hard_variant_survived", "turns": turns,
                "drops": drops, "conds": conds, "row": None}

    return {"kept": True, "reason": None, "turns": turns, "drops": drops, "conds": conds,
            "row": {"messages": messages, "meta": {"topic": topic, "shapes": turns}}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=60, help="target kept conversations")
    ap.add_argument("--out", default="data")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--teacher", default=TEACHER,
                    help="teacher model id (claude-* or kimi-*); recorded in drop_report.json")
    args = ap.parse_args()
    if not os.environ.get(llm.key_var(args.teacher)):
        sys.exit(f"{llm.key_var(args.teacher)} is not set for teacher {args.teacher}")

    rng = random.Random(args.seed)
    outdir = pathlib.Path(args.out); outdir.mkdir(parents=True, exist_ok=True)

    plan = [(rng.choice(TOPICS), random.Random(rng.random())) for _ in range(int(args.n * 1.3))]
    print(f"generating {len(plan)} conversations "
          f"(~{len(plan) * 11} teacher calls)", file=sys.stderr)

    kept, dropped, turn_counts, conds = [], Counter(), Counter(), Counter()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futs = [pool.submit(build_conversation, t, r, args.teacher) for t, r in plan]
        for i, f in enumerate(as_completed(futs), 1):
            try:
                res = f.result()
            except Exception as e:
                dropped["api_error"] += 1
                print(f"  error: {e}", file=sys.stderr)
                continue
            for d in res["drops"]:
                dropped[d] += 1
            conds.update(res["conds"])
            if res["kept"]:
                kept.append(res)
                turn_counts.update(res["turns"])
            else:
                dropped[res["reason"]] += 1
            if i % 10 == 0:
                print(f"  {i}/{len(plan)} conversations, {len(kept)} kept", file=sys.stderr)

    kept = kept[:args.n]
    with open(outdir / "dataset.jsonl", "w") as fh:
        for r in kept:
            fh.write(json.dumps(r["row"]) + "\n")

    total_turns = sum(len(r["row"]["messages"]) // 2 for r in kept)
    kept_turns = Counter()
    for r in kept:
        kept_turns.update(r["turns"])
    by_shape = {}
    for shape in ("self_report", "demonstration", "pressure", "ordinary", "wrong_attempt"):
        d = sum(v for k, v in dropped.items() if k.startswith(shape + ":"))
        by_shape[shape] = {"kept": turn_counts[shape], "dropped": d,
                           "drop_rate": round(d / (d + turn_counts[shape]), 3) if d + turn_counts[shape] else None}
    report = {"teacher": args.teacher, "seed": args.seed,
              "conversations_attempted": len(plan), "conversations_kept": len(kept),
              "assistant_turns_kept": total_turns,
              "turns_by_shape": dict(kept_turns), "by_shape": by_shape,
              "self_report_conditions": dict(sorted(conds.items())),
              "drops": dict(dropped)}
    (outdir / "drop_report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))

    for shape in ("self_report", "demonstration"):
        r = by_shape[shape]["drop_rate"]
        if r is not None and r > 0.4:
            print(f"\nWARNING: {shape} drop rate {r:.0%} is above 40%. The generation prompt is "
                  "leaking a failure -- tighten it before scaling.", file=sys.stderr)


if __name__ == "__main__":
    main()