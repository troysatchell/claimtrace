#!/bin/zsh
# Full loop on a tiny batch: generate -> train -> eval. ~5 minutes on an M4 Pro.
#   ./smoke.sh                 # regenerates data/smoke-v2 with the teacher (needs an API key)
#   ./smoke.sh --skip-generate # reuse the committed data/smoke-v2 (no key needed)
# Log goes to results/smoke-loop/log.txt (committed). Judge is off here (--no-judge) so the
# smoke test needs no key past generation; the real eval runs the judge.
set -euo pipefail
cd "$(dirname "$0")"
[ -f .env ] && source .env
export TOKENIZERS_PARALLELISM=false
TEACHER="${TEACHER:-claude-sonnet-4-6}"
OUT=results/smoke-loop; mkdir -p $OUT
{
echo "== smoke loop $(date) commit $(git rev-parse HEAD)"
if [[ "${1:-}" == "--skip-generate" ]]; then
  echo "== generate: SKIPPED (reusing data/smoke-v2: $(wc -l < data/smoke-v2/dataset.jsonl) conversations, teacher $(python3 -c 'import json;print(json.load(open("data/smoke-v2/drop_report.json"))["teacher"])'))"
else
  echo "== generate: python3 generate_dataset.py --n 6 --out data/smoke-v2 --workers 6 --seed 1 --teacher $TEACHER"
  python3 generate_dataset.py --n 6 --out data/smoke-v2 --workers 6 --seed 1 --teacher "$TEACHER"
fi
echo "== train: python3 train.py --data data/smoke-v2/dataset.jsonl --run-id smoke --iters 8 --save-every 8 --steps-per-eval 8 --steps-per-report 4 --valid-rows 4 --valid-frac 0.5"
python3 train.py --data data/smoke-v2/dataset.jsonl --run-id smoke --iters 8 --save-every 8 --steps-per-eval 8 --steps-per-report 4 --valid-rows 4 --valid-frac 0.5
echo "== eval: python3 eval.py --model ckpt/smoke/adapters --base Qwen/Qwen3-1.7B --eval-set metacog_scenarios.jsonl --out $OUT/eval --limit 2 --max-new-tokens 160 --no-judge"
python3 eval.py --model ckpt/smoke/adapters --base Qwen/Qwen3-1.7B --eval-set metacog_scenarios.jsonl --out $OUT/eval --limit 2 --max-new-tokens 160 --no-judge
echo "== smoke loop done $(date)"
} 2>&1 | grep -v "PyTorch\|Fetching" | tee $OUT/log.txt
