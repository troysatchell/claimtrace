#!/usr/bin/env python3
"""DPO on top of the SFT model (stretch ladder item 1). Runs on a CUDA box / Colab T4 —
not on the Mac training path (mlx_lm has no DPO trainer).

    pip install "trl>=0.11" peft transformers datasets accelerate bitsandbytes
    python3 train_dpo.py                      # defaults: pinned SFT revision, data/dpo/pairs.jsonl

Pairs come from build_dpo_pairs.py: chosen = the filtered SFT reply, rejected = the same
reply with its ledger mechanically corrupted (claim promoted / pressure cave / appended
probe). Because each pair differs only by the violation, DPO's preference signal is the
behavior itself. Measure the delta over SFT alone with the same one-command eval:

    python3 eval.py --model <out> --base Qwen/Qwen3-1.7B --eval-set metacog_scenarios.jsonl --out results/base-vs-tuned-dpo
"""

import argparse, json


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="troysaved/claimtrace-qwen3-1.7b")
    ap.add_argument("--revision", default="f6532284babb0fbb1388ce98a6aa28523e3c899c",
                    help="SFT checkpoint of record (q236v2); see results/publish.json")
    ap.add_argument("--pairs", default="data/dpo/pairs.jsonl")
    ap.add_argument("--out", default="ckpt/dpo")
    ap.add_argument("--beta", type=float, default=0.1)
    ap.add_argument("--epochs", type=float, default=1.0)
    ap.add_argument("--lr", type=float, default=5e-6)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--push", default=None, help="HF repo id to push adapters to")
    args = ap.parse_args()

    import torch
    from datasets import Dataset
    from peft import LoraConfig
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from trl import DPOConfig, DPOTrainer

    tok = AutoTokenizer.from_pretrained(args.model, revision=args.revision)
    model = AutoModelForCausalLM.from_pretrained(
        args.model, revision=args.revision, torch_dtype=torch.bfloat16, device_map="auto")

    rows = [json.loads(l) for l in open(args.pairs)]
    ds = Dataset.from_list([{"prompt": r["prompt"], "chosen": r["chosen"], "rejected": r["rejected"]}
                            for r in rows])
    print(f"{len(ds)} preference pairs from {args.pairs}")

    peft_cfg = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05, task_type="CAUSAL_LM",
                          target_modules=["q_proj", "k_proj", "v_proj", "o_proj"])
    cfg = DPOConfig(output_dir=args.out, beta=args.beta, num_train_epochs=args.epochs,
                    per_device_train_batch_size=1, gradient_accumulation_steps=8,
                    learning_rate=args.lr, lr_scheduler_type="cosine", warmup_ratio=0.05,
                    logging_steps=10, seed=args.seed, bf16=True, report_to="none",
                    max_length=4096, max_prompt_length=3584)
    trainer = DPOTrainer(model=model, args=cfg, train_dataset=ds,
                         processing_class=tok, peft_config=peft_cfg)
    trainer.train()
    trainer.save_model(args.out)
    tok.save_pretrained(args.out)
    if args.push:
        trainer.push_to_hub(args.push)
    print(f"saved to {args.out}; eval with eval.py to measure the delta over SFT")


if __name__ == "__main__":
    main()
