#!/usr/bin/env python3
"""Data-efficiency curve: eval every sweep run on the same set, tabulate and plot vs N.

    python train.py --sweep 270,135,67,33          # identical config, only N varies
    python sweep.py --runs n270,n135,n67,n33 --base-results results/mvp

For each run it calls `eval.py --model ckpt/<run>/adapters ...` (skipped if
results/sweep/<run>/run.json already exists), then reads run.json + results/train/<run>/
summary.json and writes results/sweep/table.md and results/sweep/curve.png. The base row
comes from --base-results (an eval.py output dir that included --base) so the base model
is generated once, not once per N.
"""

import argparse, json, pathlib, subprocess, sys


def load_json(p):
    return json.load(open(p))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", required=True, help="comma-separated run ids under ckpt/ and results/train/")
    ap.add_argument("--eval-set", default="metacog_scenarios.jsonl")
    ap.add_argument("--base-results", default="results/mvp", help="eval.py --out dir that has a base row")
    ap.add_argument("--out", default="results/sweep")
    ap.add_argument("--judge-model", default=None)
    ap.add_argument("--no-judge", action="store_true")
    args = ap.parse_args()

    out = pathlib.Path(args.out); out.mkdir(parents=True, exist_ok=True)
    runs = args.runs.split(",")
    rows = []
    for run in runs:
        rj = out / run / "run.json"
        if not rj.exists():
            cmd = [sys.executable, "eval.py", "--model", f"ckpt/{run}/adapters", "--eval-set", args.eval_set,
                   "--out", str(out / run)]
            if args.no_judge:
                cmd.append("--no-judge")
            if args.judge_model:
                cmd += ["--judge-model", args.judge_model]
            print("$ " + " ".join(cmd), file=sys.stderr)
            subprocess.run(cmd, check=True)
        r = load_json(rj)["summary"]["tuned"]
        s = load_json(pathlib.Path("results") / "train" / run / "summary.json")
        rows.append({"run": run, "N": s["data"]["train_conversations"], "rows": s["data"]["train_rows"],
                     "epochs": s["data"]["epochs_at_iters"], "final_val_loss": s.get("final_val_loss"), **r})
    rows.sort(key=lambda r: r["N"])

    base = None
    bj = pathlib.Path(args.base_results) / "run.json"
    if bj.exists():
        b = load_json(bj)["summary"].get("base")
        if b:
            base = {"run": "base", "N": 0, "rows": 0, "epochs": 0, "final_val_loss": None, **b}

    def fmt(r):
        rb = f'{r["robustness"]:.2f}' if r.get("robustness") is not None else "-"
        vl = f'{r["final_val_loss"]:.3f}' if r.get("final_val_loss") is not None else "-"
        return (f'| {r["run"]} | {r["N"]} | {r["rows"]} | {r["epochs"]} | {vl} | {r["spec_adherence"]:.2f} | {rb} | '
                f'{r["ledger_rate"]:.2f} | {r["hedged"]} | {r["self_report_to_known"]} | {r["missed_promotion"]} | '
                f'{r["over_trigger"]} | {r["clean"]} |')

    lines = ["| run | N (train convs) | train rows | epochs | val loss | spec adherence | robustness | ledger rate | hedged | self-report→KNOWN | missed promotion | over-trigger | clean |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    if base:
        lines.append(fmt(base))
    lines += [fmt(r) for r in rows]
    table = "\n".join(lines)
    (out / "table.md").write_text(table + "\n")
    (out / "sweep_summary.json").write_text(json.dumps({"base": base, "runs": rows}, indent=2))
    print(table)

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(6.5, 4))
        Ns = [r["N"] for r in rows]
        ax.plot(Ns, [r["spec_adherence"] for r in rows], "o-", label="spec adherence (clean conversations)")
        if all(r.get("robustness") is not None for r in rows):
            ax.plot(Ns, [r["robustness"] for r in rows], "s-", label="robustness (judge, pressure turns)")
        srk = [float(r["self_report_to_known"].split("(")[1].rstrip(")")) if "(" in r["self_report_to_known"] else None for r in rows]
        if all(v is not None for v in srk):
            ax.plot(Ns, srk, "^--", label="self-report→KNOWN rate (lower is better)")
        if base:
            ax.axhline(base["spec_adherence"], color="gray", ls=":", label=f'base spec adherence {base["spec_adherence"]:.2f}')
        ax.set_xscale("log", base=2); ax.set_xticks(Ns); ax.set_xticklabels([str(n) for n in Ns])
        ax.set_xlabel("N training conversations (identical config, nested subsets)")
        ax.set_ylabel("rate"); ax.set_ylim(-0.02, 1.02); ax.grid(alpha=.3); ax.legend(fontsize=8)
        ax.set_title("Data efficiency: Qwen3-1.7B LoRA on the ledger behavior")
        fig.tight_layout(); fig.savefig(out / "curve.png", dpi=150)
        print(f"wrote {out / 'curve.png'}")
    except Exception as e:  # plot is a convenience; the table is the record
        print(f"plot skipped: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
