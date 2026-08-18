"""One text-completion helper for the frontier APIs used by the teacher and the judge.

Routes on the model id: `claude-*` -> Anthropic Messages API (ANTHROPIC_API_KEY),
`kimi-*` -> Moonshot's OpenAI-compatible endpoint (MOONSHOT_API_KEY). Thinking is disabled
on both so the call is plain prompting, matching metacog_precheck.py. Retries transient
HTTP errors; raises on anything else so a bad key fails loudly instead of silently
producing an empty dataset.
"""

import os, time
import requests

RETRY_STATUS = {408, 409, 425, 429, 500, 502, 503, 504, 529}
MOONSHOT_BASE = "https://api.moonshot.ai/v1"


def provider(model):
    if model.startswith("claude"):
        return "anthropic"
    if model.startswith("kimi"):
        return "moonshot"
    raise ValueError(f"no provider for model id {model!r} (expected claude-* or kimi-*)")


def key_var(model):
    return {"anthropic": "ANTHROPIC_API_KEY", "moonshot": "MOONSHOT_API_KEY"}[provider(model)]


def _anthropic(model, system, user, max_tokens, timeout):
    r = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": os.environ["ANTHROPIC_API_KEY"],
                 "anthropic-version": "2023-06-01", "content-type": "application/json"},
        json={"model": model, "max_tokens": max_tokens,
              **({"system": system} if system else {}),
              "messages": [{"role": "user", "content": user}]},
        timeout=timeout)
    r.raise_for_status()
    return "".join(b.get("text", "") for b in r.json()["content"] if b.get("type") == "text")


def _moonshot(model, system, user, max_tokens, timeout):
    msgs = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": user}]
    r = requests.post(
        f"{MOONSHOT_BASE}/chat/completions",
        headers={"Authorization": f"Bearer {os.environ['MOONSHOT_API_KEY']}",
                 "content-type": "application/json"},
        json={"model": model, "max_tokens": max_tokens, "messages": msgs,
              "thinking": {"type": "disabled"}},
        timeout=timeout)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"] or ""


def complete(model, user, system=None, max_tokens=1200, timeout=180, retries=4):
    fn = _anthropic if provider(model) == "anthropic" else _moonshot
    delay = 2.0
    for attempt in range(retries + 1):
        try:
            return fn(model, system, user, max_tokens, timeout)
        except requests.HTTPError as e:
            status = e.response.status_code if e.response is not None else None
            if status not in RETRY_STATUS or attempt == retries:
                raise
        except (requests.ConnectionError, requests.Timeout):
            if attempt == retries:
                raise
        time.sleep(delay)
        delay = min(delay * 2, 60)
