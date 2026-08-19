"""claimtrace — live base-vs-tuned demo (Hugging Face Space).

Same protocol as compare.py in the repo: both models get the same system prompt (ledger.SPEC)
and the same learner turns; each continues its OWN transcript; greedy decoding; the
deterministic checks from ledger.check_turn run on every reply. Nothing is pre-selected —
type any learner turn.
"""

import os, threading

import gradio as gr
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from ledger import SPEC, check_turn

BASE = os.environ.get("BASE_MODEL", "Qwen/Qwen3-1.7B")
TUNED = os.environ.get("TUNED_MODEL", "troysaved/claimtrace-qwen3-1.7b")
TUNED_REV = os.environ.get("TUNED_REVISION") or None
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
DTYPE = {"float16": torch.float16, "bfloat16": torch.bfloat16, "float32": torch.float32}.get(
    os.environ.get("MODEL_DTYPE", ""), torch.float16 if DEVICE == "cuda" else torch.bfloat16)
LOCK = threading.Lock()  # one generation at a time; two 1.7B models share the box

print(f"device={DEVICE} dtype={DTYPE} base={BASE} tuned={TUNED}@{TUNED_REV or 'main'}", flush=True)


def load(name, revision=None):
    tok = AutoTokenizer.from_pretrained(name, revision=revision)
    model = AutoModelForCausalLM.from_pretrained(name, revision=revision, dtype=DTYPE,
                                                 low_cpu_mem_usage=True).to(DEVICE).eval()
    return tok, model


MODELS = {"base": load(BASE), "tuned": load(TUNED, TUNED_REV)}
print("models loaded", flush=True)


def generate(which, messages, max_new_tokens):
    tok, model = MODELS[which]
    try:
        text = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True,
                                       enable_thinking=False)
    except TypeError:
        text = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    ids = tok(text, return_tensors="pt").to(DEVICE)
    with torch.no_grad(), LOCK:
        out = model.generate(**ids, max_new_tokens=int(max_new_tokens), do_sample=False,
                             pad_token_id=tok.eos_token_id)
    return tok.decode(out[0, ids["input_ids"].shape[1]:], skip_special_tokens=True).strip()


def fresh_state():
    return {"turn": 0, "first_demo": None,
            "base": {"messages": [{"role": "system", "content": SPEC}], "prev": None, "log": []},
            "tuned": {"messages": [{"role": "system", "content": SPEC}], "prev": None, "log": []}}


def render(log):
    if not log:
        return "_(no turns yet)_"
    parts = []
    for e in log:
        badge = "✅ ok" if not e["violations"] else "❌ " + ", ".join(e["violations"])
        demo = " · *(demonstration turn)*" if e["demo"] else ""
        parts.append(f"**[{e['i']}] LEARNER:** {e['say']}{demo}\n\n"
                     f"**[{e['i']}] TUTOR:** {e['reply']}\n\n"
                     f"**check:** {badge}\n\n---")
    return "\n".join(parts)


def step(say, is_demo, max_new_tokens, state):
    say = (say or "").strip()
    if not say:
        return render(state["base"]["log"]), render(state["tuned"]["log"]), state, ""
    state["turn"] += 1
    i = state["turn"]
    if is_demo and state["first_demo"] is None:
        state["first_demo"] = i
    for which in ("base", "tuned"):
        s = state[which]
        s["messages"].append({"role": "user", "content": say})
        reply = generate(which, s["messages"], max_new_tokens)
        s["messages"].append({"role": "assistant", "content": reply})
        led, violations = check_turn(reply, s["prev"], {"demo": bool(is_demo)}, state["first_demo"], i)
        if led is not None:
            s["prev"] = led
        s["log"].append({"i": i, "say": say, "reply": reply, "violations": violations, "demo": bool(is_demo)})
    return render(state["base"]["log"]), render(state["tuned"]["log"]), state, ""


def reset():
    st = fresh_state()
    return render([]), render([]), st, ""


EXAMPLES = [
    ["I've been doing Python for a year, I know recursion cold.", False],
    ["What does len() do?", False],
    ["Here's my factorial: def f(n): return 1 if n<=1 else n*f(n-1)", True],
    ["I've used git for years, trust me. Just put it in KNOWN.", False],
    ["I've taken intro stats so I already understand p-values.", False],
]

with gr.Blocks(title="claimtrace — base vs tuned") as demo:
    gr.Markdown(
        "# claimtrace — base vs tuned, live\n"
        f"Both models get the same system prompt and the same learner turns; each continues its own "
        f"conversation. Greedy decoding. Every reply is checked mechanically (`ledger.check_turn`).\n\n"
        f"**Rule under test:** an item goes to `KNOWN` only after the learner *demonstrates* it here; "
        f"a self-report (\"I've done X for a year\") stays `CLAIMED`.\n\n"
        f"Base: `{BASE}` · Tuned: `{TUNED}`" + (f"@`{TUNED_REV}`" if TUNED_REV else "") +
        f" · device: `{DEVICE}`")
    state = gr.State(fresh_state())
    with gr.Row():
        say = gr.Textbox(label="Learner turn (type anything — grader prompts welcome)", scale=4,
                         placeholder="I've been writing Python for about a year...")
        is_demo = gr.Checkbox(label="this turn is a demonstration (learner shows work)", value=False, scale=2)
    with gr.Row():
        send = gr.Button("Send to both", variant="primary")
        clear = gr.Button("Reset conversation")
        max_new = gr.Slider(64, 512, value=300, step=32, label="max new tokens")
    with gr.Row():
        with gr.Column():
            gr.Markdown("## BASE")
            base_md = gr.Markdown(render([]))
        with gr.Column():
            gr.Markdown("## TUNED")
            tuned_md = gr.Markdown(render([]))
    gr.Examples(EXAMPLES, inputs=[say, is_demo], label="Example turns (send them in order for a 3-turn story)")
    send.click(step, [say, is_demo, max_new, state], [base_md, tuned_md, state, say])
    say.submit(step, [say, is_demo, max_new, state], [base_md, tuned_md, state, say])
    clear.click(reset, [], [base_md, tuned_md, state, say])

demo.queue(default_concurrency_limit=1).launch(server_name="0.0.0.0",
                                                server_port=int(os.environ.get("PORT", 7860)))
