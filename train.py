#!/usr/bin/env python3
"""LoRA fine-tune of Qwen3-1.7B on the ledger behavior, on Apple Silicon via mlx_lm.

    python train.py                                   # all training conversations
    python train.py --n 150 --run-id n150             # nested subset, for the data-efficiency curve
    python train.py --sweep 300,150,75,37             # four runs, identical config, only N varies

Wraps `mlx_lm.lora`; owns only data splitting, config, checkpoint paths and logging.
There is no training loop in this file.

Data. `generate_dataset.py` writes one multi-turn conversation per line. This script
  1. splits conversations 90/10 (seeded, stratified by topic; every dataset shape must
     appear in valid) -- the valid set is carved from the FULL dataset first, so it is the
     same for every N;
  2. takes the first N of the seeded-shuffled training conversations (nested subsets, so
     the curve varies size, not identity);
  3. expands every conversation into per-turn prefix rows: system + turns[:k] for each
     assistant turn k. mlx_lm's --mask-prompt puts loss on the LAST assistant message
     only, so without this expansion ~90% of the assistant turns would never be trained
     on -- and the learner turns (the self-report strings) are always masked, which is
     the point of --mask-prompt.
Rows longer than --max-seq-length are dropped, not truncated: mlx_lm truncates the tail,
which is exactly the assistant turn we want the loss on.

Config. QLoRA: the frozen base is the 4-bit affine-quantized copy made by
`mlx_lm.convert -q --q-bits 4 --q-group-size 64` (ckpt/base-q4; see quantize_base()) and LoRA
adapters (rank 16, last 16 blocks, all linear layers) train on top in bf16 -- the brief asks for
QLoRA and mlx_lm applies LoRA to QuantizedLinear directly. `--base Qwen/Qwen3-1.7B` gives plain
bf16 LoRA instead (the first n270 run used that; kept as a comparison). Effective batch 4 as
`--batch-size 1 --grad-accumulation-steps 4`: batch 4 of 2-4k-token rows OOMs on 24 GB
because the 152k-vocab logits dominate. mlx_lm counts --iters in micro-batches, so 2000
micro-iters = 500 optimizer steps x effective batch 4, i.e. the handoff's
`--iters 500 --batch-size 4`. Checkpoints every 200 micro-iters (= 50 optimizer steps),
kept, and materialized as loadable adapter directories under ckpt/<run-id>/adapters/.

Outputs. ckpt/<run-id>/ (adapters + split data; gitignored) and results/train/<run-id>/
(log.txt, summary.json with checkpoint sha256s, adapter_config.json; committed).
"""

import argparse, collections, hashlib, json, os, pathlib, random, re, shutil, subprocess, sys, time

BASE = "Qwen/Qwen3-1.7B"
QBASE = "ckpt/base-q4"   # 4-bit quantized copy of BASE, made on demand by quantize_base()


def quantize_base(base=BASE, out=QBASE):
    """mlx_lm.convert -q: 4-bit affine, group 64. Idempotent; the frozen base for QLoRA."""
    outp = pathlib.Path(out)
    if (outp / "config.json").exists():
        return str(outp)
    subprocess.run([sys.executable, "-m", "mlx_lm", "convert", "--hf-path", base, "--mlx-path", str(outp),
                    "-q", "--q-bits", "4", "--q-group-size", "64"], check=True)
    return str(outp)
DEFAULTS = dict(iters=2000, batch_size=1, grad_accumulation_steps=4, num_layers=16,
                learning_rate=5e-5, rank=16, scale=20.0, dropout=0.05,
                save_every=200, steps_per_eval=200, steps_per_report=20,
                max_seq_length=6144, warmup=25)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git_commit():
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

def load_conversations(path):
    rows = [json.loads(l) for l in open(path) if l.strip()]
    for i, r in enumerate(rows):
        r.setdefault("meta", {})
        r["meta"].setdefault("topic", f"topic{i % 12}")
        r["meta"].setdefault("shapes", [])
        r["_idx"] = i
    return rows


def split(rows, valid_frac, seed):
    """Stratified by topic. Returns (train, valid) lists of conversations."""
    rng = random.Random(seed)
    by_topic = collections.defaultdict(list)
    for r in rows:
        by_topic[r["meta"]["topic"]].append(r)
    train, valid = [], []
    for topic in sorted(by_topic):
        grp = sorted(by_topic[topic], key=lambda r: r["_idx"])
        rng.shuffle(grp)
        k = max(1, round(len(grp) * valid_frac)) if len(grp) > 1 else 0
        valid += grp[:k]
        train += grp[k:]
    rng.shuffle(train)
    rng.shuffle(valid)
    shapes_all = {s for r in rows for s in r["meta"]["shapes"]}
    covers = lambda vs: shapes_all <= {s for r in vs for s in r["meta"]["shapes"]}
    if not covers(valid):
        # Tiny sets (smoke runs) can't stratify by topic; fall back to a plain seeded split.
        pool = sorted(rows, key=lambda r: r["_idx"])
        rng.shuffle(pool)
        k = max(1, round(len(pool) * valid_frac))
        for start in range(0, len(pool), max(1, k)):
            cand = pool[start:start + k]
            if covers(cand):
                valid = cand
                train = [r for r in pool if r not in cand]
                break
        else:
            raise SystemExit(f"no valid split covers shapes {sorted(shapes_all)}; change --seed or --valid-frac")
    return train, valid


def prefix_rows(conv):
    msgs = conv["messages"]
    assert msgs[0]["role"] == "system"
    out = []
    for k in range(1, (len(msgs) - 1) // 2 + 1):
        out.append({"messages": msgs[:1 + 2 * k],
                    "meta": {"topic": conv["meta"]["topic"], "conv": conv["_idx"], "turn": k,
                             "shape": conv["meta"]["shapes"][k - 1] if k - 1 < len(conv["meta"]["shapes"]) else None}})
    return out


def token_lengths(rows, base):
    from mlx_lm.utils import load_tokenizer
    tok = load_tokenizer(base)
    return [len(tok.apply_chat_template(r["messages"])) for r in rows]


def prepare(args, run_dir, log):
    convs = load_conversations(args.data)
    train_c, valid_c = split(convs, args.valid_frac, args.seed)
    n = args.n or len(train_c)
    if n > len(train_c):
        raise SystemExit(f"--n {n} exceeds the {len(train_c)} training conversations")
    train_c = train_c[:n]

    train_rows = [r for c in train_c for r in prefix_rows(c)]
    valid_rows = [r for c in valid_c for r in prefix_rows(c)]
    rng = random.Random(args.seed)
    rng.shuffle(valid_rows)
    valid_rows = valid_rows[:args.valid_rows]

    lens_t = token_lengths(train_rows, args.base)
    lens_v = token_lengths(valid_rows, args.base)
    keep_t = [r for r, L in zip(train_rows, lens_t) if L <= args.max_seq_length]
    keep_v = [r for r, L in zip(valid_rows, lens_v) if L <= args.max_seq_length]
    dropped = (len(train_rows) - len(keep_t)) + (len(valid_rows) - len(keep_v))

    data_dir = run_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    for name, rs in (("train", keep_t), ("valid", keep_v)):
        with open(data_dir / f"{name}.jsonl", "w") as fh:
            for r in rs:
                fh.write(json.dumps({"messages": r["messages"]}) + "\n")
    with open(run_dir / "split.json", "w") as fh:
        json.dump({"train_conversations": [c["_idx"] for c in train_c],
                   "valid_conversations": [c["_idx"] for c in valid_c],
                   "valid_rows": [(r["meta"]["conv"], r["meta"]["turn"]) for r in keep_v]}, fh)

    shapes = collections.Counter(r["meta"]["shape"] for r in keep_t)
    stats = {"dataset": args.data, "conversations_total": len(convs),
             "train_conversations": len(train_c), "valid_conversations": len(valid_c),
             "train_rows": len(keep_t), "valid_rows": len(keep_v),
             "rows_dropped_over_max_seq_length": dropped,
             "train_rows_by_final_shape": dict(shapes),
             "train_tokens_total": int(sum(L for L in lens_t if L <= args.max_seq_length)),
             "train_tokens_median": int(sorted(lens_t)[len(lens_t) // 2]) if lens_t else None,
             "train_tokens_max": int(max(lens_t)) if lens_t else None,
             "epochs_at_iters": round(args.iters * args.batch_size / max(1, len(keep_t)), 2)}
    log(json.dumps(stats))
    return data_dir, stats


# ---------------------------------------------------------------------------
# Train
# ---------------------------------------------------------------------------

def make_config(args, data_dir, adapter_dir):
    return {
        "model": args.base, "train": True, "data": str(data_dir),
        "fine_tune_type": "lora", "optimizer": "adamw",
        "num_layers": args.num_layers, "batch_size": args.batch_size,
        "grad_accumulation_steps": args.grad_accumulation_steps,
        "iters": args.iters, "learning_rate": args.learning_rate,
        # The schedule steps once per optimizer update, not per micro-iter.
        "lr_schedule": {"name": "cosine_decay", "warmup": args.warmup,
                        "arguments": [args.learning_rate, args.iters // args.grad_accumulation_steps,
                                      args.learning_rate * 0.1]},
        "lora_parameters": {"rank": args.rank, "scale": args.scale, "dropout": args.dropout},
        "mask_prompt": True, "max_seq_length": args.max_seq_length,
        "grad_checkpoint": True, "seed": args.seed,
        "steps_per_report": args.steps_per_report, "steps_per_eval": args.steps_per_eval,
        "val_batches": -1, "save_every": args.save_every,
        "adapter_path": str(adapter_dir),
    }


LOSS_RE = re.compile(r"Iter (\d+): (Train|Val) loss ([\d.]+)")
MEM_RE = re.compile(r"Peak mem ([\d.]+) GB")


def run_training(cfg, run_dir, results_dir, log):
    import yaml
    cfg_path = run_dir / "lora_config.yaml"
    cfg_path.write_text(yaml.safe_dump(cfg, sort_keys=False))
    shutil.copy(cfg_path, results_dir / "lora_config.yaml")
    cmd = [sys.executable, "-m", "mlx_lm", "lora", "-c", str(cfg_path)]
    log("$ " + " ".join(cmd))
    t0 = time.time()
    losses, peak = [], 0.0
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    for line in proc.stdout:
        line = line.rstrip("\n")
        if not line.strip() or "Calculating loss" in line or "Fetching" in line:
            continue
        log(line)
        for m in LOSS_RE.finditer(line):
            losses.append({"iter": int(m.group(1)), "kind": m.group(2).lower(), "loss": float(m.group(3))})
        for m in MEM_RE.finditer(line):
            peak = max(peak, float(m.group(1)))
    rc = proc.wait()
    if rc != 0:
        raise SystemExit(f"mlx_lm.lora exited with {rc}; see {results_dir / 'log.txt'}")
    return losses, peak, time.time() - t0


def materialize_checkpoints(adapter_dir):
    """Every NNNNNNN_adapters.safetensors -> iter-NNNNNNN/ dir loadable by mlx_lm / eval.py."""
    out = []
    cfg = adapter_dir / "adapter_config.json"
    for f in sorted(adapter_dir.glob("*_adapters.safetensors")):
        it = int(f.name.split("_")[0])
        d = adapter_dir / f"iter-{it:07d}"
        d.mkdir(exist_ok=True)
        shutil.copy(cfg, d / "adapter_config.json")
        link = d / "adapters.safetensors"
        if link.exists() or link.is_symlink():
            link.unlink()
        link.symlink_to(f.resolve())
        out.append({"iter": it, "optimizer_step": None, "path": str(d), "file": str(f),
                    "sha256": sha256(f), "bytes": f.stat().st_size})
    return out


def train_once(args, run_id):
    run_dir = pathlib.Path("ckpt") / run_id
    results_dir = pathlib.Path("results") / "train" / run_id
    results_dir.mkdir(parents=True, exist_ok=True)
    run_dir.mkdir(parents=True, exist_ok=True)
    logf = open(results_dir / "log.txt", "a")

    def log(msg):
        line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
        print(line, flush=True)
        logf.write(line + "\n"); logf.flush()

    commit = git_commit()
    log(f"run_id={run_id} commit={commit} base={args.base} n={args.n or 'all'} seed={args.seed}")
    log("args " + json.dumps({k: v for k, v in vars(args).items() if k != "sweep"}))
    data_dir, stats = prepare(args, run_dir, log)
    if args.dry_run:
        log("dry run: data prepared, not training")
        return None

    adapter_dir = run_dir / "adapters"
    if adapter_dir.exists():
        shutil.rmtree(adapter_dir)
    cfg = make_config(args, data_dir, adapter_dir)
    losses, peak, wall = run_training(cfg, run_dir, results_dir, log)
    ckpts = materialize_checkpoints(adapter_dir)
    for c in ckpts:
        c["optimizer_step"] = c["iter"] // args.grad_accumulation_steps
    final = adapter_dir / "adapters.safetensors"
    shutil.copy(adapter_dir / "adapter_config.json", results_dir / "adapter_config.json")
    summary = {
        "run_id": run_id, "commit": commit, "base": args.base, "backend": "mlx_lm.lora",
        "config": cfg, "data": stats,
        "optimizer_steps": args.iters // args.grad_accumulation_steps,
        "effective_batch": args.batch_size * args.grad_accumulation_steps,
        "wall_seconds": round(wall), "peak_mem_gb": peak,
        "losses": losses,
        "final_train_loss": next((l["loss"] for l in reversed(losses) if l["kind"] == "train"), None),
        "final_val_loss": next((l["loss"] for l in reversed(losses) if l["kind"] == "val"), None),
        "final_adapter": {"path": str(adapter_dir), "sha256": sha256(final), "bytes": final.stat().st_size},
        "checkpoints": ckpts,
        "eval_command": f"python3 eval.py --model {adapter_dir} --base {args.base} --eval-set metacog_scenarios.jsonl --out results/base-vs-tuned-lora-bf16",
    }
    (results_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    log(f"done: {len(ckpts)} checkpoints, final adapter sha256={summary['final_adapter']['sha256'][:12]} "
        f"wall={wall / 60:.1f}min peak_mem={peak:.1f}GB")
    logf.close()
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/dataset.jsonl")
    ap.add_argument("--n", type=int, default=None, help="training conversations (nested subset)")
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--sweep", default=None, help="comma-separated Ns, e.g. 270,135,67,33")
    ap.add_argument("--run-prefix", default="n", help="run ids are <prefix><N> (sweep) / default run id")
    ap.add_argument("--base", default=None,
                    help=f"frozen base for the adapters; default = 4-bit quantized {BASE} at {QBASE} (QLoRA). "
                         f"Pass {BASE} for bf16 LoRA.")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--valid-frac", type=float, default=0.10)
    ap.add_argument("--valid-rows", type=int, default=64, help="prefix rows kept for validation loss")
    ap.add_argument("--dry-run", action="store_true")
    for k, v in DEFAULTS.items():
        ap.add_argument("--" + k.replace("_", "-"), type=type(v), default=v)
    args = ap.parse_args()
    if args.base is None:
        args.base = quantize_base()

    if args.sweep:
        ns = [int(x) for x in args.sweep.split(",")]
        summaries = []
        for n in ns:
            a = argparse.Namespace(**vars(args)); a.n = n; a.sweep = None
            summaries.append(train_once(a, f"{args.run_prefix}{n}"))
        (pathlib.Path("results") / "train" / f"sweep-{args.run_prefix}.json").write_text(json.dumps(
            {"ns": ns, "runs": [s["run_id"] for s in summaries if s], "base": args.base,
             "commit": git_commit()}, indent=2))
        return
    run_id = args.run_id or (f"{args.run_prefix}{args.n}" if args.n else "full")
    train_once(args, run_id)


if __name__ == "__main__":
    main()
