---
title: claimtrace — base vs tuned
emoji: 📒
colorFrom: gray
colorTo: green
sdk: gradio
sdk_version: 5.44.1
app_file: app.py
pinned: false
license: apache-2.0
models:
  - Qwen/Qwen3-1.7B
  - troysaved/claimtrace-qwen3-1.7b
---

# claimtrace — live base-vs-tuned demo

Type any learner turn. Both `Qwen/Qwen3-1.7B` (base) and `troysaved/claimtrace-qwen3-1.7b`
(tuned) answer under the same system prompt and continue their own conversation. Each reply is
checked mechanically with `ledger.check_turn` (same code as the repo's `eval.py` / `compare.py`).

The rule: an item may go to `KNOWN` only after the learner demonstrates it in this conversation.
A self-report ("I've been doing Python for a year") is `CLAIMED`, never `KNOWN`.

Repo, eval harness, and results: https://github.com/troysatchell/claimtrace

Env vars: `TUNED_MODEL`, `TUNED_REVISION` (pin the HF revision), `BASE_MODEL`.
On CPU hardware expect ~1–3 tokens/s per model; upgrade to a GPU for a snappy demo.
