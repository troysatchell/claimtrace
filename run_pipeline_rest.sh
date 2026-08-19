#!/bin/zsh
# Resume of run_pipeline.sh after the n270 training step (eval OOM fix). Same steps.
set -euo pipefail
cd "$(dirname "$0")"
source .env
JUDGE="${1:-kimi-k3}"
EVAL_SET=metacog_scenarios.jsonl
BASE=Qwen/Qwen3-1.7B
export TOKENIZERS_PARALLELISM=false
echo "== [$(date)] eval base vs n270 -> results/mvp"
python3 eval.py --model ckpt/n270/adapters --base $BASE --eval-set $EVAL_SET --out results/mvp --judge-model "$JUDGE"
echo "== [$(date)] train sweep n135,n67,n33 (identical config)"
python3 train.py --sweep 135,67,33
echo "== [$(date)] sweep evals + curve -> results/sweep"
mkdir -p results/sweep
[ -e results/sweep/n270 ] || ln -s ../mvp results/sweep/n270
python3 sweep.py --runs n270,n135,n67,n33 --base-results results/mvp --judge-model "$JUDGE"
echo "== [$(date)] pipeline done"
