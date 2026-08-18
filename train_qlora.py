#!/usr/bin/env python3
"""QLoRA fine-tune of Qwen3-1.7B-Instruct on the ledger behavior.

    pip install unsloth trl peft transformers datasets
    python train_qlora.py --data data/dataset.jsonl --n 300 --out ckpt/n300

For the data-efficiency curve, run four times:
    for N in 300 150 75 40; do
        python train_qlora.py --data data/dataset.jsonl --n $N --out ckpt/n$N
    done

--n truncates the dataset with a fixed seed so the smaller sets are nested subsets of the
larger ones. That matters: otherwise the curve confounds dataset size with dataset identity.
"""

import argparse, json, random

from unsloth import FastLanguageModel
from datasets import Dataset
from trl import SFTTrainer, SFTConfig

BASE = "unsloth/Qwen3-1.7B-Instruct"


def load(path, n, seed):
    rows = [json.loads(l) for l in open(path) if l.strip()]
    random.Random(seed).shuffle(rows)
    return rows[:n]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/dataset.jsonl")
    ap.add_argument("--n", type=int, default=300)
    ap.add_argument("--out", default="ckpt/n300")
    ap.add_argument("--base", default=BASE)
    ap.add_argument("--epochs", type=float, default=3.0)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--push", default=None, help="HF repo id to push the merged model to")
    args = ap.parse_args()

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=args.base,
        max_seq_length=4096,
        load_in_4bit=True,
    )

    model = FastLanguageModel.get_peft_model(
        model,
        r=16,
        lora_alpha=32,
        lora_dropout=0.0,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"],
        use_gradient_checkpointing="unsloth",
        random_state=args.seed,
    )

    rows = load(args.data, args.n, args.seed)
    print(f"training on {len(rows)} rows")

    ds = Dataset.from_list([
        {"text": tokenizer.apply_chat_template(r["messages"], tokenize=False)}
        for r in rows
    ])

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=ds,
        args=SFTConfig(
            output_dir=args.out,
            per_device_train_batch_size=2,
            gradient_accumulation_steps=4,
            num_train_epochs=args.epochs,
            learning_rate=2e-4,
            warmup_ratio=0.05,
            lr_scheduler_type="linear",
            logging_steps=5,
            optim="adamw_8bit",
            seed=args.seed,
            report_to="none",
            dataset_text_field="text",
            max_seq_length=4096,
        ),
    )

    stats = trainer.train()
    print(stats)

    model.save_pretrained(args.out)
    tokenizer.save_pretrained(args.out)

    if args.push:
        # Merged 16-bit so graders can load it with plain transformers, no PEFT required.
        model.push_to_hub_merged(args.push, tokenizer, save_method="merged_16bit")
        print(f"pushed to {args.push}")


if __name__ == "__main__":
    main()
