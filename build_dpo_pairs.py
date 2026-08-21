#!/usr/bin/env python3
"""Build DPO preference pairs from the SFT dataset — no teacher calls.

Each pair shares the conversation prefix (prompt). `chosen` is the filtered on-spec reply
from the dataset. `rejected` is the same reply with its ledger mechanically corrupted into
the exact failure the behavior spec forbids:

  self_report   -> the newly-CLAIMED item is moved into KNOWN (the frontier failure the
                   prompt-ceiling ablation measured: best prompt still does this 10/12).
  wrong_attempt -> the learner's incorrect/topical statement is filed under KNOWN
                   (the MVP failure the v2 dataset fixed: unearned 15 -> 1).
  pressure      -> the first CLAIMED item is promoted (caving to insistence).
  ordinary      -> a diagnostic question is appended before the ledger line (the v2
                   residual: over-trigger 0.15 on ordinary turns).

Because the corruption is mechanical, every rejected reply differs from its chosen twin by
exactly the violation and nothing else -- the preference signal is the behavior, not style.

    python3 build_dpo_pairs.py --data data/v2/dataset.jsonl --out data/dpo
"""

import argparse, json, pathlib, random
from collections import Counter

from ledger import parse_ledger, is_empty


def items_list(field):
    return [] if is_empty(field) else [x.strip() for x in field.split(",") if x.strip()]


def ledger_line(known, claimed, unchecked):
    j = lambda xs: ", ".join(xs) if xs else "none"
    return f"KNOWN: {j(known)} | CLAIMED: {j(claimed)} | UNCHECKED: {j(unchecked)}"


def swap_ledger(reply, known, claimed, unchecked):
    head = reply[: reply.rindex("KNOWN:")]
    return head + ledger_line(known, claimed, unchecked)


def corrupt(shape, reply, prev, user_msg, rng):
    led = parse_ledger(reply)
    if led is None:
        return None
    known, claimed, unchecked = items_list(led["known"]), items_list(led["claimed"]), items_list(led["unchecked"])
    prev_claimed = items_list(prev["claimed"]) if prev else []
    if shape == "self_report":
        new = [c for c in claimed if c not in prev_claimed]
        if not new:
            return None
        item = new[0]
        return swap_ledger(reply, known + [item], [c for c in claimed if c != item], unchecked)
    if shape == "wrong_attempt":
        item = " ".join(user_msg.replace(",", "").split()[:7]).rstrip(".?!").lower()
        return swap_ledger(reply, known + [item], claimed, unchecked)
    if shape == "pressure":
        if not claimed:
            return None
        item = claimed[0]
        return swap_ledger(reply, known + [item], claimed[1:], unchecked)
    if shape == "ordinary":
        head = reply[: reply.rindex("KNOWN:")].rstrip()
        probe = rng.choice(["Quick check: can you explain why that works?",
                            "Before we move on — how would you do it yourself?",
                            "Does that make sense so far? Try restating it."])
        return head + "\n\n" + probe + "\n\n" + reply[reply.rindex("KNOWN:"):]
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/v2/dataset.jsonl")
    ap.add_argument("--out", default="data/dpo")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    rng = random.Random(args.seed)
    outdir = pathlib.Path(args.out); outdir.mkdir(parents=True, exist_ok=True)

    pairs, counts = [], Counter()
    for line in open(args.data):
        row = json.loads(line)
        msgs, shapes = row["messages"], row["meta"]["shapes"]
        prev = None
        for k, shape in enumerate(shapes):
            user, asst = msgs[1 + 2 * k], msgs[2 + 2 * k]
            rej = corrupt(shape, asst["content"], prev, user["content"], rng)
            led = parse_ledger(asst["content"])
            if led is not None:
                prev = led
            if rej is None:
                counts[shape + ":skipped"] += 1
                continue
            pairs.append({"prompt": msgs[: 2 + 2 * k],
                          "chosen": [{"role": "assistant", "content": asst["content"]}],
                          "rejected": [{"role": "assistant", "content": rej}],
                          "meta": {"topic": row["meta"]["topic"], "shape": shape, "turn": k + 1}})
            counts[shape] += 1

    rng.shuffle(pairs)
    with open(outdir / "pairs.jsonl", "w") as fh:
        for p in pairs:
            fh.write(json.dumps(p) + "\n")
    report = {"source": args.data, "seed": args.seed, "pairs": len(pairs), "by_shape": dict(counts)}
    (outdir / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
