#!/bin/zsh
# QLoRA pipeline (the brief's configuration): q270 -> base-vs-tuned -> sweep q135,q67,q33 -> curve.
# Same steps as run_pipeline.sh; only the frozen base differs (ckpt/base-q4, 4-bit).
set -euo pipefail
cd "$(dirname "$0")"
source .env
JUDGE="${1:-kimi-k3}"
EVAL_SET=metacog_scenarios.jsonl
BASE=Qwen/Qwen3-1.7B
export TOKENIZERS_PARALLELISM=false
echo "== [$(date)] train q270 (QLoRA, all training conversations)"
python3 train.py --n 270 --run-id q270
echo "== [$(date)] eval base vs q270 -> results/mvp-qlora"
python3 eval.py --model ckpt/q270/adapters --base $BASE --eval-set $EVAL_SET --out results/mvp-qlora --judge-model "$JUDGE"
echo "== [$(date)] train QLoRA sweep q135,q67,q33 (identical config)"
python3 train.py --sweep 135,67,33 --run-prefix q
echo "== [$(date)] sweep evals + curve -> results/sweep-qlora"
mkdir -p results/sweep-qlora
[ -e results/sweep-qlora/q270 ] || ln -s ../mvp-qlora results/sweep-qlora/q270
python3 sweep.py --runs q270,q135,q67,q33 --base-results results/mvp-qlora --out results/sweep-qlora --judge-model "$JUDGE"
echo "== [$(date)] pipeline done"
