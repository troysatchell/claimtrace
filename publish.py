#!/usr/bin/env python3
"""Publish the artifacts the brief grades: the model on Hugging Face Hub (public) with its
exact commit hash, and the dataset. Prints and records both revision hashes.

    hf auth login                                   # once
    python publish.py --run n270 --user <hf-user>   # fuses ckpt/n270/adapters into the base,
                                                    # uploads <user>/claimtrace-qwen3-1.7b (model)
                                                    # and <user>/claimtrace-ledger-dataset (dataset)

The fused model is plain HF-format Qwen3 safetensors (mlx_lm.fuse on a bf16 base), so both
`mlx_lm.load("<user>/claimtrace-qwen3-1.7b")` and `transformers` load it -- which is what
`eval.py --model <hf-repo-id> --eval-set <path>` needs on a grader's box. The adapter directory
is uploaded alongside under adapters/ for provenance. Revision hashes land in
results/publish.json and should be copied into the README's submission block.
"""

import argparse, json, pathlib, subprocess, sys, time


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="n270", help="run id under ckpt/ and results/train/")
    ap.add_argument("--user", required=True, help="HF namespace (user or org)")
    ap.add_argument("--base", default="Qwen/Qwen3-1.7B")
    ap.add_argument("--model-repo", default=None)
    ap.add_argument("--dataset-repo", default=None)
    ap.add_argument("--private", action="store_true", help="(default is public, as the brief requires)")
    args = ap.parse_args()

    from huggingface_hub import HfApi, whoami
    try:
        me = whoami()["name"]
    except Exception as e:
        sys.exit(f"not logged in to Hugging Face ({e}); run `hf auth login` first")
    api = HfApi()
    model_repo = args.model_repo or f"{args.user}/claimtrace-qwen3-1.7b"
    dataset_repo = args.dataset_repo or f"{args.user}/claimtrace-ledger-dataset"
    adapter_dir = pathlib.Path("ckpt") / args.run / "adapters"
    fused_dir = pathlib.Path("ckpt") / args.run / "fused"
    if not adapter_dir.exists():
        sys.exit(f"{adapter_dir} not found; train first")

    print(f"== fusing {adapter_dir} into {args.base} -> {fused_dir}", file=sys.stderr)
    subprocess.run([sys.executable, "-m", "mlx_lm", "fuse", "--model", args.base,
                    "--adapter-path", str(adapter_dir), "--save-path", str(fused_dir)], check=True)

    summary = json.load(open(pathlib.Path("results") / "train" / args.run / "summary.json"))
    card = f"""---
base_model: {args.base}
library_name: transformers
license: apache-2.0
tags: [claimtrace, tutoring, lora, mlx]
---
# claimtrace — Qwen3-1.7B tuned to keep a claim-provenance ledger

Behavior spec (BEHAVIOR_SPEC.md): {open('BEHAVIOR_SPEC.md').read().split('>')[1].split(chr(10))[0].strip()}

Fused from LoRA adapters trained with `train.py` (run `{args.run}`, commit `{summary['commit']}`,
{summary['optimizer_steps']} optimizer steps, effective batch {summary['effective_batch']},
final val loss {summary.get('final_val_loss')}). Adapter sha256 `{summary['final_adapter']['sha256']}`.
Eval: `python eval.py --model {model_repo} --base {args.base} --eval-set metacog_scenarios.jsonl`
(repo: see README). Adapters (mlx_lm format) are under `adapters/`.
"""
    (fused_dir / "README.md").write_text(card)

    print(f"== uploading model to {model_repo}", file=sys.stderr)
    api.create_repo(model_repo, repo_type="model", private=args.private, exist_ok=True)
    info = api.upload_folder(folder_path=str(fused_dir), repo_id=model_repo, repo_type="model",
                             commit_message=f"claimtrace {args.run} fused (commit {summary['commit'][:12]})")
    api.upload_folder(folder_path=str(adapter_dir), repo_id=model_repo, repo_type="model",
                      path_in_repo="adapters", allow_patterns=["adapter_config.json", "adapters.safetensors"],
                      commit_message="mlx_lm adapters")
    model_rev = api.list_repo_commits(model_repo, repo_type="model")[0].commit_id

    print(f"== uploading dataset to {dataset_repo}", file=sys.stderr)
    api.create_repo(dataset_repo, repo_type="dataset", private=args.private, exist_ok=True)
    api.upload_file(path_or_fileobj="data/dataset.jsonl", path_in_repo="dataset.jsonl",
                    repo_id=dataset_repo, repo_type="dataset")
    api.upload_file(path_or_fileobj="data/drop_report.json", path_in_repo="drop_report.json",
                    repo_id=dataset_repo, repo_type="dataset")
    api.upload_file(path_or_fileobj="dataset_spec.md", path_in_repo="README.md",
                    repo_id=dataset_repo, repo_type="dataset")
    ds_rev = api.list_repo_commits(dataset_repo, repo_type="dataset")[0].commit_id

    out = {"model_repo": model_repo, "model_revision": model_rev,
           "dataset_repo": dataset_repo, "dataset_revision": ds_rev,
           "run": args.run, "train_commit": summary["commit"],
           "adapter_sha256": summary["final_adapter"]["sha256"],
           "published_by": me, "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    pathlib.Path("results").mkdir(exist_ok=True)
    (pathlib.Path("results") / "publish.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))
    print(f"\nEval against the published revision:\n  python eval.py --model {model_repo} "
          f"--base {args.base} --eval-set metacog_scenarios.jsonl --out results/base-vs-tuned-hf", file=sys.stderr)


if __name__ == "__main__":
    main()
