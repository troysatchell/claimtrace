#!/usr/bin/env python3
"""Live base-vs-tuned comparison on one conversation (for the demo's grader-supplied prompt).

    python compare.py --tuned ckpt/n270/adapters "I've been writing Python for a year." \\
        "Quick question, what does len() do?" "A base case is where the recursion stops."

Each positional argument is one learner turn; both models see the same system prompt
(ledger.SPEC) and the same learner turns, and each continues its OWN transcript. Prints both
replies per turn and the deterministic check on each ledger, so the audience can see the
provenance difference live rather than in a pre-selected transcript. Same backend detection
as eval.py (MLX on Apple Silicon, transformers otherwise).
"""

import argparse, sys

import eval as harness
from ledger import SPEC, check_turn


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("turns", nargs="+", help="learner turns, in order")
    ap.add_argument("--tuned", required=True, help="tuned model / adapter dir / HF repo id")
    ap.add_argument("--base", default="Qwen/Qwen3-1.7B")
    ap.add_argument("--demo-turns", default="", help="comma-separated 1-based turn indices that are demonstrations")
    ap.add_argument("--max-new-tokens", type=int, default=400)
    ap.add_argument("--backend", choices=list(harness.BACKENDS), default=None)
    args = ap.parse_args()

    backend = args.backend or harness.pick_backend()
    demo = {int(x) for x in args.demo_turns.split(",") if x.strip()}
    first_demo = min(demo) if demo else None
    for name, model_id in (("BASE", args.base), ("TUNED", args.tuned)):
        print(f"\n{'=' * 24} {name}: {model_id} ({backend}) {'=' * 24}")
        be = harness.BACKENDS[backend](model_id)
        messages, prev = [{"role": "system", "content": SPEC}], None
        for i, say in enumerate(args.turns, 1):
            messages.append({"role": "user", "content": say})
            reply = be.generate_many([messages], args.max_new_tokens)[0]
            messages.append({"role": "assistant", "content": reply})
            led, violations = check_turn(reply, prev, {"demo": i in demo}, first_demo, i)
            if led is not None:
                prev = led
            print(f"\n[{i}] LEARNER: {say}\n[{i}] {name}: {reply}\n"
                  f"    check: {violations or 'ok'}")
        be.close()


if __name__ == "__main__":
    main()
