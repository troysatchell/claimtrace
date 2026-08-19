#!/usr/bin/env python3
"""Judge the prompt-ceiling ablation transcripts with the SAME rubric eval.py uses for base-vs-tuned.

    python ablation_judge.py --transcripts results/prompt-ceiling-ablation/transcripts.jsonl \
        --scenarios metacog_scenarios.jsonl --out results/prompt-ceiling-ablation

Writes <out>/judge_transcripts.jsonl (each ablation conversation + judge verdict) and
<out>/judged_table.md: per model × strategy, mean Spec-adherence (deterministic: clean conversations
/ n, exactly what the ablation table's "clean runs" column is) and Robustness (judge: held_ledger ×
no_backfill over the pressure turns), so the ablation and the base-vs-tuned table are scored by one
rubric (eval.py JUDGE_PROMPT) and are comparable column for column.
"""

import argparse, json, pathlib, statistics, sys
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor

import eval as harness


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--transcripts", required=True)
    ap.add_argument("--scenarios", default="metacog_scenarios.jsonl")
    ap.add_argument("--out", required=True)
    ap.add_argument("--judge-model", default=harness.JUDGE_MODEL)
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()

    scen = {s["id"]: s for s in (json.loads(l) for l in open(args.scenarios) if l.strip())}
    rows = [json.loads(l) for l in open(args.transcripts) if l.strip()]
    out = pathlib.Path(args.out); out.mkdir(parents=True, exist_ok=True)
    jt = out / "judge_transcripts.jsonl"
    prior = {}
    if jt.exists():  # resume: keep verdicts already obtained
        for l in open(jt):
            r = json.loads(l)
            if r.get("judge") and r["judge"].get("failure_mode") not in harness.JUDGE_FAILURES:
                prior[(r["model"], r["strategy"], r["scenario_id"])] = r["judge"]

    todo = []
    for r in rows:
        turns = r["transcript"]
        flags = scen[r["scenario_id"]]["turns"]
        for t, f in zip(turns, flags):
            t["pressure"] = bool(f.get("pressure"))
        r["judge"] = prior.get((r["model"], r["strategy"], r["scenario_id"]))
        if any(t["pressure"] for t in turns) and not r["judge"]:
            r["_in"] = harness.judge_transcript(turns)
            todo.append(r)
    print(f"judging {len(todo)} conversations with {args.judge_model} ({len(prior)} cached)", file=sys.stderr)
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for r, j in zip(todo, pool.map(lambda r: harness.judge(r["_in"], args.judge_model), todo)):
            r["judge"] = j
    for r in rows:
        r.pop("_in", None)
    with open(jt, "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")

    cells = defaultdict(list)
    for r in rows:
        cells[(r["model"], r["strategy"])].append(r)
    lines = ["| model | strategy | n | spec adherence (clean convs / n) | robustness (judge) | judged | held_ledger | no_backfill | judge failure modes |",
             "|---|---|---|---|---|---|---|---|---|"]
    for (model, strategy), rs in cells.items():
        judged = [r["judge"] for r in rs if r.get("judge") and r["judge"].get("failure_mode") not in harness.JUDGE_FAILURES]
        rob = statistics.mean(j["held_ledger"] * j["no_backfill"] for j in judged) if judged else None
        fm = Counter(j["failure_mode"] for j in judged)
        lines.append(f"| {model} | {strategy} | {len(rs)} | {sum(1 for r in rs if r['clean']) / len(rs):.2f} | "
                     f"{rob:.2f} | {len(judged)} | {sum(j['held_ledger'] for j in judged)}/{len(judged)} | "
                     f"{sum(j['no_backfill'] for j in judged)}/{len(judged)} | {dict(fm)} |"
                     if rob is not None else f"| {model} | {strategy} | {len(rs)} | {sum(1 for r in rs if r['clean']) / len(rs):.2f} | - | 0 | - | - | - |")
    table = "\n".join(lines)
    (out / "judged_table.md").write_text(
        f"Judge: {args.judge_model}, rubric = eval.py JUDGE_PROMPT (full transcript, pressure turns marked; "
        f"held_ledger × no_backfill on pressure turns).\n\n{table}\n")
    print(table)


if __name__ == "__main__":
    main()
