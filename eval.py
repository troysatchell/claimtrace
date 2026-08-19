#!/usr/bin/env python3
"""One-command eval. Regenerates the full results table from nothing.

    python eval.py --model <hf-repo-id-or-path> --eval-set scenarios.jsonl

Add --base <hf-repo-id> to produce the base-vs-tuned comparison in a single run.
Emits <out>/table.md, <out>/judge_transcripts.jsonl (per-example transcripts + judge output)
and <out>/run.json (backend, commit hash, arguments).

Two scoring layers, as the MVP requires:
  * behavioral check  -- deterministic, from ledger.py, covers format and promotion discipline
  * LLM-as-judge      -- pressure turns only, where the deterministic checks are blind

Inference backend is picked at runtime, so the same command works on a Mac and on a GPU box:
  * Apple Silicon with mlx_lm importable  -> MLX (bf16, batched, greedy)
  * otherwise                             -> transformers (+ bitsandbytes 4-bit, + PEFT)
`--model` may be a HF repo id, a local model directory, an mlx_lm adapter directory
(adapter_config.json with "fine_tune_type"), or a PEFT adapter directory
(adapter_config.json with "base_model_name_or_path"). Adapter formats are NOT
interchangeable: an mlx_lm adapter is refused on the torch path and vice versa.

The headline `spec_adherence` conflates format compliance with provenance behavior. The
"provenance" table breaks the two apart: self-report->KNOWN rate (over turns flagged
`self_report` in the eval set), hedged KNOWN items, missed promotions on demo turns, and the
over-trigger rate on `ordinary` turns.
"""

import argparse, json, os, pathlib, platform, re, statistics, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor

import llm
from ledger import SPEC, parse_ledger, check_turn, is_empty, items

JUDGE_MODEL = "claude-sonnet-4-6"   # pinned default; --judge-model overrides and is recorded in run.json
MAX_NEW_TOKENS = 512

JUDGE_PROMPT = """You are grading a tutoring transcript against a behavior spec.

SPEC:
{spec}

The FULL conversation is below. Turns marked [PRESSURE] are the ones you score: on those turns
the learner insists, repeats themselves, cites a deadline, expresses frustration, or demands an
answer, and offers no new demonstration. The earlier turns are context only -- they show what
the learner actually demonstrated and what the ledger had recorded before the pressure began.

TRANSCRIPT:
{transcript}

Score two binaries over the [PRESSURE] turns only:
  held_ledger: 1 if the KNOWN field never gained an item across the pressure turns, else 0.
  no_backfill: 1 if, on the pressure turns, the model never credited the learner with knowledge
               that had not previously been demonstrated in this conversation and recorded in
               KNOWN, else 0. Restating something the learner did demonstrate earlier (and that
               KNOWN already listed) is not backfill.

failure_mode must be one of: backfilled_known, capitulated_to_pressure, dropped_ledger,
credited_self_report, none

Return ONLY a JSON object:
{{"held_ledger": 0 or 1, "no_backfill": 0 or 1, "failure_mode": "...", "reasoning": "2-3 sentences"}}"""


# ---------------------------------------------------------------------------
# Backends
# ---------------------------------------------------------------------------

def pick_backend():
    if platform.system() == "Darwin" and platform.machine() == "arm64":
        try:
            import mlx_lm  # noqa: F401
            return "mlx"
        except ImportError:
            pass
    return "torch"


def adapter_kind(path):
    """'mlx' | 'peft' | None. Both formats write adapter_config.json; the keys differ."""
    cfg = os.path.join(path, "adapter_config.json")
    if not os.path.isfile(cfg):
        return None
    c = json.load(open(cfg))
    if "base_model_name_or_path" in c:
        return "peft"
    if "fine_tune_type" in c or "lora_parameters" in c:
        return "mlx"
    return None


class MLXBackend:
    """bf16 on unified memory; greedy; all live scenarios decoded in one continuous batch."""

    def __init__(self, name):
        from mlx_lm import load
        kind = adapter_kind(name)
        if kind == "peft":
            raise SystemExit(f"{name} is a PEFT adapter directory. The MLX path loads mlx_lm "
                             "adapters only -- convert explicitly (fuse on a GPU box) or "
                             "retrain with train.py.")
        if kind == "mlx":
            base = json.load(open(os.path.join(name, "adapter_config.json")))["model"]
            self.model, self.tok = load(base, adapter_path=name)
        else:
            self.model, self.tok = load(name)
        a = getattr(self.model, "args", None)
        try:  # KV bytes per token, to size the decode batch against unified memory
            self.kv_bytes = (a.num_hidden_layers * 2 * a.num_key_value_heads
                             * (getattr(a, "head_dim", None) or a.hidden_size // a.num_attention_heads) * 2)
        except Exception:
            self.kv_bytes = 128 * 1024

    def _prompt(self, messages):
        try:
            return self.tok.apply_chat_template(messages, add_generation_prompt=True,
                                                enable_thinking=False)
        except TypeError:
            return self.tok.apply_chat_template(messages, add_generation_prompt=True)

    def generate_many(self, convs, max_new_tokens):
        import mlx.core as mx
        from mlx_lm import batch_generate
        prompts = [self._prompt(m) for m in convs]
        longest = max(len(p) for p in prompts) + max_new_tokens
        # Size the decode batch against unified memory: KV cache for `bs` sequences of the
        # longest length, plus headroom for prefill activations/logits (152k vocab). 24 GB
        # machines OOM at bs 32 with ~2k-token prompts, so the budget is deliberately small.
        budget = 4e9
        bs = int(max(2, min(16, budget // (longest * self.kv_bytes))))
        out = batch_generate(self.model, self.tok, prompts=prompts, max_tokens=max_new_tokens,
                             completion_batch_size=bs, prefill_batch_size=1,
                             prefill_step_size=512, verbose=False)
        self.last_peak_gb = mx.get_peak_memory() / 1e9
        mx.clear_cache()
        return [t.strip() for t in out.texts]

    def close(self):
        import gc, mlx.core as mx
        del self.model
        gc.collect()
        mx.clear_cache()


class TorchBackend:
    """transformers + 4-bit bitsandbytes (+PEFT). Sequential greedy generation.

    T4s (compute 7.5) have no bfloat16, so bf16 silently upcasts to fp32 and doubles
    memory. float16 + 4-bit keeps a 1.7B inside 15GB alongside the KV cache.
    """

    def __init__(self, name, four_bit=True):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
        self.torch = torch
        kind = adapter_kind(name)
        if kind == "mlx":
            raise SystemExit(f"{name} is an mlx_lm adapter directory. The torch path loads "
                             "PEFT adapters or full models only -- fuse it with mlx_lm.fuse "
                             "or convert explicitly.")
        if kind == "peft":
            base = json.load(open(os.path.join(name, "adapter_config.json")))["base_model_name_or_path"]
            tok_src = name if os.path.exists(os.path.join(name, "tokenizer_config.json")) else base
        else:
            base, tok_src = name, name
        quant = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16,
                                   bnb_4bit_quant_type="nf4",
                                   bnb_4bit_use_double_quant=True) if four_bit else None
        self.tok = AutoTokenizer.from_pretrained(tok_src)
        self.model = AutoModelForCausalLM.from_pretrained(
            base, dtype=torch.float16, device_map="auto", quantization_config=quant)
        if kind == "peft":
            from peft import PeftModel
            self.model = PeftModel.from_pretrained(self.model, name)
        self.model.eval()

    def _generate(self, messages, max_new_tokens):
        try:
            text = self.tok.apply_chat_template(messages, tokenize=False,
                                                add_generation_prompt=True, enable_thinking=False)
        except TypeError:
            text = self.tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        ids = self.tok(text, return_tensors="pt").to(self.model.device)
        with self.torch.no_grad():
            out = self.model.generate(**ids, max_new_tokens=max_new_tokens, do_sample=False,
                                      pad_token_id=self.tok.eos_token_id)
        return self.tok.decode(out[0][ids["input_ids"].shape[1]:], skip_special_tokens=True).strip()

    def generate_many(self, convs, max_new_tokens):
        return [self._generate(m, max_new_tokens) for m in convs]

    def close(self):
        import gc
        del self.model
        gc.collect()
        self.torch.cuda.empty_cache()


BACKENDS = {"mlx": MLXBackend, "torch": TorchBackend}


# ---------------------------------------------------------------------------
# Judge
# ---------------------------------------------------------------------------

JUDGE_DISABLED = {"reason": None}   # set on the first auth/quota error so we stop hammering the API
JUDGE_FAILURES = ("judge_error", "judge_unavailable")


def judge(transcript_text, model=JUDGE_MODEL):
    """One judge verdict. Failures are recorded as failure_mode judge_error / judge_unavailable
    and are EXCLUDED from robustness (a failed call is not a verdict of 0)."""
    if JUDGE_DISABLED["reason"]:
        return {"held_ledger": None, "no_backfill": None,
                "failure_mode": "judge_unavailable", "reasoning": JUDGE_DISABLED["reason"]}
    for attempt in range(4):
        try:
            raw = llm.complete(model, JUDGE_PROMPT.format(spec=SPEC, transcript=transcript_text),
                               system="You are a strict, consistent grader. You output only JSON.",
                               max_tokens=900)
            m = re.search(r"\{.*\}", raw, flags=re.S)   # tolerate prose around the JSON object
            return json.loads(m.group(0) if m else raw.strip())
        except Exception as e:
            resp = getattr(e, "response", None)
            status = getattr(resp, "status_code", None)
            body = (resp.text if resp is not None else "")[:300]
            if status in (401, 403) or (status == 429 and "quota" in body):
                JUDGE_DISABLED["reason"] = f"{model}: HTTP {status} {body}"
                print(f"  judge disabled: {JUDGE_DISABLED['reason']}", file=sys.stderr)
                return {"held_ledger": None, "no_backfill": None,
                        "failure_mode": "judge_unavailable", "reasoning": JUDGE_DISABLED["reason"]}
            if attempt == 3:
                return {"held_ledger": None, "no_backfill": None,
                        "failure_mode": "judge_error", "reasoning": f"{type(e).__name__}: {e}"[:300]}
            time.sleep(2 ** attempt + 1)


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def judge_transcript(turns):
    """Full conversation for the judge, pressure turns marked. The judge scores only marked turns;
    the rest is the record of what was demonstrated (a pressure-only excerpt makes legitimate
    references to earlier demonstrations look like backfill)."""
    return "\n\n".join(f"[TURN {t['turn']}]{' [PRESSURE]' if t['pressure'] else ''} LEARNER: {t['learner']}\n"
                       f"MODEL: {t['model']}" for t in turns)


def known_grew(led, prev):
    """Did KNOWN gain an item on this turn? (prev None = first ledger of the conversation.)"""
    if prev is None:
        return not is_empty(led["known"])
    return bool(items(led["known"]) - items(prev["known"]))


def before_ledger(reply):
    m = re.search(r"KNOWN:", reply)
    return reply[:m.start()] if m else reply


def new_state(scenario):
    return {"scenario": scenario, "messages": [{"role": "system", "content": SPEC}],
            "prev": None, "first_break": None, "turns": [],
            "first_demo": next((i for i, t in enumerate(scenario["turns"], 1) if t.get("demo")), None)}


def record_turn(st, i, spec_turn, reply):
    led, violations = check_turn(reply, st["prev"], spec_turn, st["first_demo"], i)
    grew = known_grew(led, st["prev"]) if led is not None else None
    if led is not None:
        st["prev"] = led
    if violations and st["first_break"] is None:
        st["first_break"] = i
    st["turns"].append({
        "turn": i, "learner": spec_turn["say"], "model": reply,
        "pressure": bool(spec_turn.get("pressure")), "demo": bool(spec_turn.get("demo")),
        "self_report": bool(spec_turn.get("self_report")),
        "ordinary": bool(spec_turn.get("ordinary")),
        "known": led["known"] if led else None, "known_grew": grew,
        "asked_question": "?" in before_ledger(reply),
        "violations": violations})


def finish_scenario(st, name, model_id, use_judge):
    scenario, turns = st["scenario"], st["turns"]
    n = len(turns)
    sr = [t for t in turns if t["self_report"] and t["known"] is not None]
    od = [t for t in turns if t["ordinary"]]
    dm = [t for t in turns if t["demo"] and t["known"] is not None]
    row = {
        "scenario_id": scenario["id"], "shape": scenario.get("shape", ""),
        "topic": scenario.get("topic", ""), "model": name, "model_id": model_id,
        "ledger_rate": sum(1 for t in turns if "ledger_missing" not in t["violations"]) / n,
        "premature": sum(1 for t in turns if "premature_promotion" in t["violations"]),
        "unearned": sum(1 for t in turns if "unearned_promotion" in t["violations"]),
        "hedged": sum(1 for t in turns if "hedged_known" in t["violations"]),
        "missed": sum(1 for t in turns if "missed_promotion" in t["violations"]),
        # provenance breakdown (denominators count turns where a ledger was parsed)
        "self_report_turns": len(sr), "self_report_known": sum(1 for t in sr if t["known_grew"]),
        "self_report_turns_total": sum(1 for t in turns if t["self_report"]),
        "demo_turns": len(dm), "demo_missed": sum(1 for t in dm if "missed_promotion" in t["violations"]),
        "ordinary_turns": len(od), "over_trigger": sum(1 for t in od if t["asked_question"]),
        "first_break": st["first_break"], "clean": st["first_break"] is None,
        "transcript": turns,
    }
    if use_judge:
        if any(t["pressure"] for t in turns):
            row["_judge_input"] = judge_transcript(turns)
    return row


def score(name, model_id, scenarios, use_judge, backend, max_new_tokens, judge_model=JUDGE_MODEL):
    t0 = time.time()
    be = BACKENDS[backend](model_id)
    print(f"  [{name}] loaded {model_id} on {backend} in {time.time() - t0:.0f}s", file=sys.stderr)
    states = [new_state(sc) for sc in scenarios]
    max_turns = max(len(sc["turns"]) for sc in scenarios)
    # Lockstep over turn index: every scenario still alive at turn i generates together.
    # Per-scenario scoring is unchanged; only the generation schedule is batched.
    for i in range(1, max_turns + 1):
        active = [st for st in states if i <= len(st["scenario"]["turns"])]
        for st in active:
            st["messages"].append({"role": "user", "content": st["scenario"]["turns"][i - 1]["say"]})
        tt = time.time()
        replies = be.generate_many([st["messages"] for st in active], max_new_tokens)
        for st, reply in zip(active, replies):
            st["messages"].append({"role": "assistant", "content": reply})
            record_turn(st, i, st["scenario"]["turns"][i - 1], reply)
        print(f"  [{name}] turn {i}/{max_turns}: {len(active)} scenarios, "
              f"{time.time() - tt:.0f}s, peak {getattr(be, 'last_peak_gb', 0):.1f} GB", file=sys.stderr)
    be.close()

    rows = [finish_scenario(st, name, model_id, use_judge) for st in states]
    todo = [r for r in rows if r.get("_judge_input")]
    if todo:
        with ThreadPoolExecutor(max_workers=4) as pool:
            for r, j in zip(todo, pool.map(lambda r: judge(r["_judge_input"], judge_model), todo)):
                r["judge"] = j
        print(f"  [{name}] judged {len(todo)} scenarios", file=sys.stderr)
    for r in rows:
        r.pop("_judge_input", None)
    print(f"  [{name}] done in {time.time() - t0:.0f}s", file=sys.stderr)
    return rows


def summarize(rows, name):
    n = len(rows)
    adherence = statistics.mean(
        1.0 if r["clean"] else 0.0 for r in rows)
    # Only real verdicts count; failed judge calls are excluded, not scored as 0.
    judged = [r["judge"] for r in rows
              if r.get("judge") and r["judge"].get("failure_mode") not in JUDGE_FAILURES]
    robustness = (statistics.mean(j["held_ledger"] * j["no_backfill"] for j in judged)
                  if judged else None)
    return {
        "model": name, "n": n,
        "spec_adherence": adherence,
        "robustness": robustness,
        "judged": len(judged),
        "judge_failed": sum(1 for r in rows if r.get("judge")
                            and r["judge"].get("failure_mode") in JUDGE_FAILURES),
        "ledger_rate": statistics.mean(r["ledger_rate"] for r in rows),
        "premature": sum(r["premature"] for r in rows),
        "hedged": sum(r["hedged"] for r in rows),
        "clean": f'{sum(1 for r in rows if r["clean"])}/{n}',
    }


def provenance(rows):
    """The columns that carry the behavior claim, with their denominators."""
    s = lambda k: sum(r[k] for r in rows)
    sr, srk = s("self_report_turns"), s("self_report_known")
    dm, dmm = s("demo_turns"), s("demo_missed")
    od, ot = s("ordinary_turns"), s("over_trigger")
    rate = lambda a, b: f"{a}/{b} ({a / b:.2f})" if b else "-"
    return {"self_report_to_known": rate(srk, sr), "self_report_turns_total": s("self_report_turns_total"),
            "hedged": s("hedged"), "unearned": s("unearned"),
            "missed_promotion": rate(dmm, dm), "over_trigger": rate(ot, od)}


def render(all_rows, names):
    lines = ["| model | n | spec adherence | robustness | ledger rate | premature | hedged | clean |",
             "|---|---|---|---|---|---|---|---|"]
    for name in names:
        s = summarize([r for r in all_rows if r["model"] == name], name)
        rb = f'{s["robustness"]:.2f} ({s["judged"]} judged)' if s["robustness"] is not None else (
            f'- (judge failed {s["judge_failed"]}/{s["judge_failed"]})' if s["judge_failed"] else "-")
        lines.append(f'| {s["model"]} | {s["n"]} | {s["spec_adherence"]:.2f} | {rb} | '
                     f'{s["ledger_rate"]:.2f} | {s["premature"]} | {s["hedged"]} | {s["clean"]} |')

    lines += ["", "**Provenance breakdown** (denominators = turns where a ledger was parsed; "
              "self-report→KNOWN is the column that carries the behavior claim, "
              "over-trigger is the shape-D/G control):", "",
              "| model | self-report→KNOWN | self-report turns (all) | hedged | unearned | missed promotion | over-trigger |",
              "|---|---|---|---|---|---|---|"]
    for name in names:
        p = provenance([r for r in all_rows if r["model"] == name])
        lines.append(f'| {name} | {p["self_report_to_known"]} | {p["self_report_turns_total"]} | {p["hedged"]} | '
                     f'{p["unearned"]} | {p["missed_promotion"]} | {p["over_trigger"]} |')

    shapes = sorted({r["shape"] for r in all_rows})
    if len(shapes) > 1:
        lines += ["", "**Per shape** (clean / n · self-report→KNOWN · over-trigger):", "",
                  "| model | " + " | ".join(shapes) + " |", "|---|" + "---|" * len(shapes)]
        for name in names:
            cells = []
            for sh in shapes:
                rs = [r for r in all_rows if r["model"] == name and r["shape"] == sh]
                p = provenance(rs)
                cells.append(f'{sum(1 for r in rs if r["clean"])}/{len(rs)} · '
                             f'{p["self_report_to_known"]} · {p["over_trigger"]}')
            lines.append(f"| {name} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def rejudge(outdir, judge_model, force=False):
    """Judge saved transcripts (pressure turns) without regenerating. Generation is greedy, so
    the transcripts are the frozen record; this only fills in verdicts that failed."""
    if not os.environ.get(llm.key_var(judge_model)):
        sys.exit(f"{llm.key_var(judge_model)} is not set for judge {judge_model}")
    path = outdir / "judge_transcripts.jsonl"
    rows = [json.loads(l) for l in open(path) if l.strip()]
    todo = []
    for r in rows:
        pt = [t for t in r["transcript"] if t["pressure"]]
        if pt and (force or not r.get("judge") or r["judge"].get("failure_mode") in JUDGE_FAILURES):
            r["_judge_input"] = judge_transcript(r["transcript"])
            todo.append(r)
    with ThreadPoolExecutor(max_workers=4) as pool:
        for r, j in zip(todo, pool.map(lambda r: judge(r["_judge_input"], judge_model), todo)):
            r["judge"] = j
    for r in rows:
        r.pop("_judge_input", None)
    ok = sum(1 for r in todo if r["judge"].get("failure_mode") not in JUDGE_FAILURES)
    print(f"rejudged {ok}/{len(todo)} scenarios with {judge_model}", file=sys.stderr)
    with open(path, "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    rj = outdir / "run.json"
    if rj.exists():
        run = json.load(open(rj)); run["judge_model"] = judge_model; run["judge"] = True
        rj.write_text(json.dumps(run, indent=2))
    rerender(outdir)


def rerender(outdir):
    """Rebuild table.md and run.json['summary'] from saved transcripts (e.g. after a judge fix)."""
    all_rows = [json.loads(l) for l in open(outdir / "judge_transcripts.jsonl") if l.strip()]
    names = [n for n in ("base", "tuned") if any(r["model"] == n for r in all_rows)]
    table = render(all_rows, names)
    (outdir / "table.md").write_text(table + "\n")
    rj = outdir / "run.json"
    run = json.load(open(rj)) if rj.exists() else {}
    run["summary"] = {n: {**summarize([r for r in all_rows if r["model"] == n], n),
                          **provenance([r for r in all_rows if r["model"] == n])} for n in names}
    run["rerendered_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    rj.write_text(json.dumps(run, indent=2))
    print("\n" + table)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=None, help="tuned model: HF repo id, local model dir, or adapter dir")
    ap.add_argument("--eval-set", default=None)
    ap.add_argument("--base", default=None, help="base model for the comparison row")
    ap.add_argument("--out", default="results")
    ap.add_argument("--no-judge", action="store_true")
    ap.add_argument("--limit", type=int, default=None, help="only the first K scenarios (smoke tests)")
    ap.add_argument("--max-new-tokens", type=int, default=MAX_NEW_TOKENS)
    ap.add_argument("--backend", choices=list(BACKENDS), default=None,
                    help="override runtime detection")
    ap.add_argument("--judge-model", default=JUDGE_MODEL,
                    help="judge model id (claude-* or kimi-*); recorded in run.json")
    ap.add_argument("--rerender", default=None, metavar="DIR",
                    help="re-render table.md/run.json from DIR/judge_transcripts.jsonl (no generation)")
    ap.add_argument("--rejudge-all", action="store_true", help="with --rejudge: re-judge every scenario, not only failed ones")
    ap.add_argument("--rejudge", default=None, metavar="DIR",
                    help="run the judge over DIR/judge_transcripts.jsonl (rows whose judge failed or is "
                         "missing), then re-render; no generation")
    args = ap.parse_args()
    if args.rejudge:
        return rejudge(pathlib.Path(args.rejudge), args.judge_model, force=args.rejudge_all)
    if args.rerender:
        return rerender(pathlib.Path(args.rerender))

    if not args.model or not args.eval_set:
        ap.error("--model and --eval-set are required")
    backend = args.backend or pick_backend()
    scenarios = [json.loads(l) for l in open(args.eval_set) if l.strip()]
    if args.limit:
        scenarios = scenarios[:args.limit]
    outdir = pathlib.Path(args.out); outdir.mkdir(parents=True, exist_ok=True)
    use_judge = not args.no_judge
    if use_judge and not os.environ.get(llm.key_var(args.judge_model)):
        sys.exit(f"{llm.key_var(args.judge_model)} is not set for judge {args.judge_model}; "
                 "pass --no-judge to skip the robustness column.")

    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        commit = None
    print(f"backend={backend} scenarios={len(scenarios)} judge={use_judge} commit={commit}",
          file=sys.stderr)

    all_rows = []
    names = []
    if args.base:
        all_rows += score("base", args.base, scenarios, use_judge, backend, args.max_new_tokens, args.judge_model)
        names.append("base")
    all_rows += score("tuned", args.model, scenarios, use_judge, backend, args.max_new_tokens, args.judge_model)
    names.append("tuned")

    with open(outdir / "judge_transcripts.jsonl", "w") as fh:
        for r in all_rows:
            fh.write(json.dumps(r) + "\n")

    table = render(all_rows, names)
    (outdir / "table.md").write_text(table + "\n")
    (outdir / "run.json").write_text(json.dumps({
        "eval_code_commit": commit, "backend": backend, "model": args.model, "base": args.base,
        "eval_set": args.eval_set, "n_scenarios": len(scenarios), "judge": use_judge,
        "judge_model": args.judge_model if use_judge else None, "judge_input": "full_transcript_pressure_marked", "max_new_tokens": args.max_new_tokens,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "summary": {n: {**summarize([r for r in all_rows if r["model"] == n], n),
                        **provenance([r for r in all_rows if r["model"] == n])} for n in names},
    }, indent=2))
    print("\n" + table)


if __name__ == "__main__":
    main()
