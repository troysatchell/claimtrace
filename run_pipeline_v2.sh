#!/bin/zsh
# v2 data-fix pipeline (Early submission): generate v2 -> train q270v2 (config byte-identical
# to q270; ONLY the data changes) -> eval -> results/base-vs-tuned-v2.
set -e
cd "$(dirname "$0")"
source .env
echo "== [$(date)] generate v2"
python3 generate_dataset.py --n 300 --out data/v2 --workers 12 2>&1 | tee data/v2-generate-console.log
echo "== [$(date)] train q270v2 (identical config, v2 data)"
python3 train.py --data data/v2/dataset.jsonl --n 270 --run-id q270v2
echo "== [$(date)] eval q270v2"
python3 eval.py --model ckpt/q270v2/adapters --base Qwen/Qwen3-1.7B --eval-set metacog_scenarios.jsonl --out results/base-vs-tuned-v2
echo "== [$(date)] v2 pipeline done"
