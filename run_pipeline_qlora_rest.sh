#!/bin/zsh
# Continuation of run_pipeline_qlora.sh with the pinned judge (claude-sonnet-4-6) once the key was fixed.
# Waits for the q270 training (already running) to finish, then eval -> sweep -> curve.
set -euo pipefail
cd "$(dirname "$0")"
source .env
JUDGE="${1:-claude-sonnet-4-6}"
EVAL_SET=metacog_scenarios.jsonl
BASE=Qwen/Qwen3-1.7B
export TOKENIZERS_PARALLELISM=false
echo "== [$(date)] waiting for ckpt/q270 training to finish"
until [ -f results/train/q270/summary.json ]; do sleep 30; done
echo "== [$(date)] eval base vs q270 -> results/mvp-qlora (judge $JUDGE)"
python3 eval.py --model ckpt/q270/adapters --base $BASE --eval-set $EVAL_SET --out results/mvp-qlora --judge-model "$JUDGE"
echo "== [$(date)] train QLoRA sweep q135,q67,q33 (identical config)"
python3 train.py --sweep 135,67,33 --run-prefix q
echo "== [$(date)] sweep evals + curve -> results/sweep-qlora"
mkdir -p results/sweep-qlora
[ -e results/sweep-qlora/q270 ] || ln -s ../mvp-qlora results/sweep-qlora/q270
python3 sweep.py --runs q270,q135,q67,q33 --base-results results/mvp-qlora --out results/sweep-qlora --judge-model "$JUDGE"
echo "== [$(date)] pipeline done"
