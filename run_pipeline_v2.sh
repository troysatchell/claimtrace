#!/bin/zsh
# v2 continuation: data/v2 already generated (265 convs, kimi-k3). Train q236v2 with the
# q270 config (identical; only the data differs) -> eval -> results/base-vs-tuned-v2.
set -e
cd "$(dirname "$0")"
source .env
echo "== [$(date)] train q236v2 (identical config, v2 data)"
python3 train.py --data data/v2/dataset.jsonl --run-id q236v2
echo "== [$(date)] eval q236v2"
python3 eval.py --model ckpt/q236v2/adapters --base Qwen/Qwen3-1.7B --eval-set metacog_scenarios.jsonl --out results/base-vs-tuned-v2
echo "== [$(date)] v2 pipeline done"
