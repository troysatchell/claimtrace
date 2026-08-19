#!/usr/bin/env python3
"""Render REPORT.md and gaps.md from matrix.after-mvp.json (compare mode). Re-run after editing the matrix."""
import json, re, pathlib
from collections import Counter
D = pathlib.Path(__file__).parent
m = json.load(open(D / "matrix.after-mvp.json"))
bl = json.load(open(D / "matrix.baseline.json"))
basev = {r["id"]: r["verdict"] for r in bl["requirements"]}
inv = open(D / "inventory.md").read()
def field(id, name):
    sec = inv.split(f"## {id}\n")[1].split("\n## ")[0]
    mm = re.search(rf"\*\*{name}:\*\* (.*)", sec); return mm.group(1).strip() if mm else ""
def short(id):
    q = field(id, "Quote").strip('"'); return (q[:70] + "…") if len(q) > 72 else q
cnt = Counter(r["verdict"] for r in m["requirements"])
order = ["VERIFIED", "IMPLEMENTED-UNVERIFIED", "PARTIAL", "MISSING", "N/A", "BLOCKED", "ASSUMED"]
summary = open(D / "summary.md").read() if (D / "summary.md").exists() else ""
L = ["# Requirements Audit — Trained_SLM (claimtrace)",
     f"**Commit:** {m['commit'][:12]} (dirty: {', '.join(m['dirty_paths'])}) · **Date:** {m['date']} · **Docs:** SLM (p.1–4) · **Mode:** compare `{m['label']}` vs `{m['baselineRef']}` (2026-08-17)\n",
     "## Summary"]
L += [f"- {v}: {cnt[v]}" for v in order if cnt.get(v)]
L += ["", summary.strip(), "", "## Coverage and limitations", open(D / "coverage.md").read().strip(), "", "## Matrix",
      "| ID | Requirement (short) | Ticket(s) | Evidence | Verdict |", "|---|---|---|---|---|"]
for r in m["requirements"]:
    evs = ", ".join(f"{e['file']}:{e['line']}" for e in r["evidence"]) or "—"
    L.append(f"| {r['id']} | {short(r['id'])} | BLOCKED | {evs} | {r['verdict']} |")
L.append("\n## Gaps")
for r in m["requirements"]:
    if r["verdict"] in ("MISSING", "PARTIAL"):
        L.append(f"- **{r['id']} — {r['verdict']}**: {r['notes'] or ''} *Suggested:* {r['suggested_scope']}")
L += ["\n## Orphan tickets\nNone (ticket dimension BLOCKED).", "\n## Blocked / assumed",
      f"- Ticket dimension: {m['ticket_mapping']['reason']} Unblock: {m['ticket_mapping']['unblock']}"]
for r in m["requirements"]:
    if r["verdict"] == "ASSUMED":
        L.append(f"- {r['id']} ASSUMED — {r['assumption']} (question: {m['needs_ruling'][0]['question']})")
L += ["\n## Delta (compare mode)", "| ID | baseline verdict | now | evidence change |", "|---|---|---|---|"]
for r in m["requirements"]:
    if basev[r["id"]] != r["verdict"]:
        evs = ", ".join(f"{e['file']}:{e['line']}" for e in r["evidence"][:3]) or "—"
        L.append(f"| {r['id']} | {basev[r['id']]} | {r['verdict']} | {evs} |")
L += ["\n## Verification performed", "| Command | Result | Bears on |", "|---|---|---|"]
for c in m["commands_run"]:
    L.append(f"| `{c['command'][:110]}` | {c['result'][:120].replace(chr(10), ' / ')} | {', '.join(c['bears_on'])} |")
L.append("\nCaptured excerpts for VERIFIED rows:\n")
for r in m["requirements"]:
    if r["verdict"] == "VERIFIED" and r["verification"]:
        L.append(f"**{r['id']}** — `{r['verification']['command'][:120]}`\n```\n{r['verification']['result_excerpt']}\n```")
(D / "REPORT.md").write_text("\n".join(L) + "\n")
G = [f"# Requirements gaps — Trained_SLM ({m['date']}, commit {m['commit'][:12]})\n",
     "## Unticketed requirements (ticket dimension BLOCKED — every gap is unticketed)\n"]
for r in m["requirements"]:
    if r["verdict"] in ("MISSING", "PARTIAL"):
        G += [f"### {r['id']} — {r['verdict']}", f"- **Quote:** \"{field(r['id'], 'Quote').strip(chr(34))}\"",
              f"- **Source:** {field(r['id'], 'Source')}", f"- **Meaning in code:** {field(r['id'], 'Meaning in code')}",
              f"- **What is missing:** {r['notes'] or '—'}", f"- **Suggested scope:** {r['suggested_scope']}\n"]
G.append("## Orphan tickets\n- None (ticket dimension BLOCKED: no Linear project scoped to this repo).")
(D / "gaps.md").write_text("\n".join(G) + "\n")
print("rendered:", dict(cnt))
