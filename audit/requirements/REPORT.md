# Requirements Audit — Trained_SLM
**Commit:** none (not a git repo — tree pinned by sha256 in matrix `tree_snapshot`) · **Date:** 2026-08-17T18:15:20Z · **Docs:** SLM (p.1–4) · **Mode:** baseline · **Inventory:** PRE-SKIM (first extraction, not yet user-confirmed)

## Summary
- **VERIFIED:** 1
- **IMPLEMENTED-UNVERIFIED:** 2
- **PARTIAL:** 8
- **MISSING:** 35
- **N/A:** 8
- **BLOCKED:** 0
- **ASSUMED:** 1

The prompt-ceiling precheck — the only executable artifact in the repo and the vehicle for the MVP gate (Ablation 1) — cannot run: `call()` in `metacog_precheck.py:122-126` builds a provider lambda but never invokes or returns it, so every reply is `None`, all 30 conversations fail at `parse_ledger` before a single API request is made, and the run silently emits a header-only table (`verify.precheck`: 30/30 FAILED, zero cost). Fixing that one function is the first thing to do. Behind it sit two more ablation-gate gaps: the scenario set is 5 where the brief's floor is 30 per model×strategy (SLM-R15), and the precheck is deterministic by design where the brief requires the *same LLM-as-judge rubric* later used for base-vs-tuned (SLM-R16) — the current script is a precursor, not the ablation. Everything else on the rubric (dataset generation, QLoRA training, `eval.py`, HF checkpoint, data-efficiency curve, Brainlift) is not started: 35 of 55 requirements are MISSING. What is in place is sound: two pinned frontier ids from different families that both resolve against live keys (VERIFIED), three strategies, a tutoring-scoped spec, and three mechanical failure-mode checks that are the right seed for the harness's behavioral check.

## Coverage and limitations
- **Inventory is unconfirmed.** This is the first extraction; the skill's skim gate was not waited on because the run was unattended. Skim `inventory.md`, edit freely, then re-run `/requirements-audit baseline` — the IDs are stable, so edits will not renumber anything.
- **Ticket dimension BLOCKED.** tickets.project is null and the Troysatchell team spans 8 projects (LabelHunter, PlugForge, FleetGraph, Clavira Pilot Readiness, ShipShape Audit Remediation, AgentForge, Verilo, Week 2 Multimodal Evidence Agent) — none of them is this repo. Sweeping the whole team would report other projects' work as this project's orphans. Every row's Ticket cell is `BLOCKED`, meaning *never checked*, not *checked and none found*. Unblock: Create a Linear project for this SLM work under Troysatchell, set tickets.project to its exact name in audit/requirements.config.yaml, and re-run.
- **`verify.eval` NOT RUN** — `eval.py` does not exist. Rows SLM-R6, R20, R24, R38, R42, R49 lean on it and are MISSING for that reason.
- **`verify.precheck` ran red** (30/30 conversations failed before any API call). Rows SLM-R1, R11, R14, R17, R29 cannot go past PARTIAL / IMPLEMENTED-UNVERIFIED until it runs green.
- **One ASSUMED verdict below the flood cap (SLM-R7).** The ambiguity should have been asked, not assumed; it is recorded in `needs_ruling` and in *Blocked / assumed* below. Answer the yes/no question, log the ruling in `interpretations.md`, and re-run before treating this baseline as comparable.
- **No git repository.** Citations are valid only against the working tree at sweep time; the matrix pins `metacog_precheck.py`, `metacog_scenarios.jsonl`, and the PDF by sha256. Ordering requirements (SLM-R8) cannot be checked until the repo is under git.
- **Side effects:** the precheck run wrote `audit/requirements/runs/precheck/{table.md,transcripts.jsonl}` (both effectively empty). No application files, databases, or external services were mutated. The two provider probes were read-only `GET /models` calls (no generation, no cost).
- **Statically traced only:** 2 rows (IMPLEMENTED-UNVERIFIED). Fan-out was not used (55 requirements, but a 2-file repo — tracing was exhaustive inline).
- **Stretch items (SLM-R53–R55)** are optional per the brief; they are inventoried so the matrix is complete but their MISSING verdicts carry no pass/fail weight.

## Matrix
| ID | Requirement (short) | Ticket(s) | Evidence | Verdict |
|---|---|---|---|---|
| SLM-R1 | Behavior not already reliable under prompting | BLOCKED | `metacog_precheck.py:33`<br>`metacog_precheck.py:81` | PARTIAL |
| SLM-R2 | Falsifiable Behavior Spec (1–2 sentences), before code | BLOCKED | `metacog_precheck.py:38` | PARTIAL |
| SLM-R3 | Target is a learning/teaching behavior | BLOCKED | `metacog_precheck.py:38`<br>`metacog_precheck.py:83`<br>`metacog_scenarios.jsonl:1` | IMPLEMENTED-UNVERIFIED |
| SLM-R4 | Distilled dataset generation | BLOCKED | — | MISSING |
| SLM-R5 | QLoRA fine-tune of small open model | BLOCKED | — | MISSING |
| SLM-R6 | Prove tuned beats base with numbers | BLOCKED | — | MISSING |
| SLM-R7 | One target, one context | BLOCKED | `metacog_precheck.py:38`<br>`metacog_scenarios.jsonl:1` | ASSUMED |
| SLM-R8 | Eval harness before any training | BLOCKED | — | N/A |
| SLM-R9 | Fix data, not hyperparameters | BLOCKED | — | N/A |
| SLM-R10 | Measure target behavior, not benchmarks | BLOCKED | — | MISSING |
| SLM-R11 | Prompt-ceiling proven with numbers before FT code | BLOCKED | `metacog_precheck.py:33`<br>`metacog_precheck.py:223`<br>`metacog_precheck.py:242` | PARTIAL |
| SLM-R12 | Ablation presented at Architecture Defense | BLOCKED | — | N/A |
| SLM-R13 | ≥2 frontier models, different families | BLOCKED | `metacog_precheck.py:34`<br>`metacog_precheck.py:35` | VERIFIED |
| SLM-R14 | ≥3 strategies: zero/few-shot/structured | BLOCKED | `metacog_precheck.py:83`<br>`metacog_precheck.py:84`<br>`metacog_precheck.py:85`<br>`metacog_precheck.py:223` | IMPLEMENTED-UNVERIFIED |
| SLM-R15 | ≥30 scenarios per model×strategy | BLOCKED | `metacog_scenarios.jsonl:1`<br>`metacog_precheck.py:223` | PARTIAL |
| SLM-R16 | Scored by same LLM-as-judge rubric as base-vs-tuned | BLOCKED | — | MISSING |
| SLM-R17 | Results table: Spec-adherence + Robustness | BLOCKED | `metacog_precheck.py:242`<br>`metacog_precheck.py:259` | PARTIAL |
| SLM-R18 | Paragraph naming surviving failure mode | BLOCKED | — | MISSING |
| SLM-R19 | ≥4 checkpoints at different N | BLOCKED | — | MISSING |
| SLM-R20 | Every checkpoint on same eval set (own + held-out) | BLOCKED | — | MISSING |
| SLM-R21 | Performance-vs-N curve | BLOCKED | — | MISSING |
| SLM-R22 | Justified minimum viable N (Brainlift) | BLOCKED | — | MISSING |
| SLM-R23 | Public HF checkpoint + commit hash | BLOCKED | — | MISSING |
| SLM-R24 | One-command eval.py | BLOCKED | — | MISSING |
| SLM-R25 | Raw judge transcripts JSONL | BLOCKED | — | MISSING |
| SLM-R26 | Harness runnable on staff held-out set | BLOCKED | — | MISSING |
| SLM-R27 | Pinned HF + eval-code hashes | BLOCKED | — | MISSING |
| SLM-R28 | Live grader prompt in demo (base vs tuned) | BLOCKED | — | N/A |
| SLM-R29 | Ablation script rerunnable by grader | BLOCKED | `metacog_precheck.py:122`<br>`metacog_precheck.py:124`<br>`metacog_precheck.py:126`<br>`metacog_precheck.py:185` | PARTIAL |
| SLM-R30 | Data-efficiency training logs included | BLOCKED | — | MISSING |
| SLM-R31 | MVP due Tue midnight | BLOCKED | — | N/A |
| SLM-R32 | Early Submission due Thu midnight | BLOCKED | — | N/A |
| SLM-R33 | Final Submission due Sun noon | BLOCKED | — | N/A |
| SLM-R34 | MVP: finalized Behavior Spec | BLOCKED | `metacog_precheck.py:38` | PARTIAL |
| SLM-R35 | MVP: ablation report submitted | BLOCKED | — | MISSING |
| SLM-R36 | MVP: harness — LLM-as-judge scoring | BLOCKED | — | MISSING |
| SLM-R37 | MVP: harness — behavioral failure-mode check | BLOCKED | `metacog_precheck.py:155`<br>`metacog_precheck.py:161`<br>`metacog_precheck.py:167`<br>`metacog_precheck.py:170` | PARTIAL |
| SLM-R38 | MVP: harness — base-vs-tuned comparison | BLOCKED | — | MISSING |
| SLM-R39 | MVP: generate→train→eval smoke loop | BLOCKED | — | MISSING |
| SLM-R40 | MVP: first dataset generated + filtered | BLOCKED | — | MISSING |
| SLM-R41 | MVP: first QLoRA run | BLOCKED | — | MISSING |
| SLM-R42 | MVP: first base-vs-tuned numbers | BLOCKED | — | MISSING |
| SLM-R43 | Early: failure mode fixed via v2 data | BLOCKED | — | MISSING |
| SLM-R44 | Early: updated numbers + delta + transcripts | BLOCKED | — | MISSING |
| SLM-R45 | Early: ≥2 curve points (or reason) | BLOCKED | — | MISSING |
| SLM-R46 | Early: draft artifacts | BLOCKED | — | MISSING |
| SLM-R47 | Final: dataset published | BLOCKED | — | MISSING |
| SLM-R48 | Final: HF model public + inference demo | BLOCKED | — | MISSING |
| SLM-R49 | Final: harness + table on own + held-out | BLOCKED | — | MISSING |
| SLM-R50 | Final: full curve + min N | BLOCKED | — | MISSING |
| SLM-R51 | Final: Brainlift | BLOCKED | — | MISSING |
| SLM-R52 | Final: 3–5 min demo video w/ live prompt | BLOCKED | — | N/A |
| SLM-R53 | Stretch: DPO | BLOCKED | — | MISSING |
| SLM-R54 | Stretch: adversarial eval | BLOCKED | — | MISSING |
| SLM-R55 | Stretch: composed behavior | BLOCKED | — | MISSING |

## Gaps
MISSING + PARTIAL rows; the missing part is named. Full handoff detail with suggested scope is in `gaps.md`.

| ID | Verdict | What is missing |
|---|---|---|
| SLM-R1 | PARTIAL | No completed run and no stated reliability bar exist, so the 'hard test' is unproven. metacog_precheck.py is, by its own docstring (line 6: 'deterministic checks -- no LLM judge'), a cheap precursor to the ablation, and it is currently non-runnable: call() (lines 122-126) builds `fn` but never invokes or returns it, so every reply is None and all 30 conversations fail at parse_ledger before any API request is made (verify.precheck exit: 30/30 FAILED, empty table). |
| SLM-R2 | PARTIAL | SPEC (lines 38-44) is falsifiable but is a multi-sentence system prompt, not a one-or-two-sentence standalone spec; no spec document exists. |
| SLM-R4 | MISSING | No implementing code in code_roots. |
| SLM-R5 | MISSING | No implementing code in code_roots. |
| SLM-R6 | MISSING | No implementing code in code_roots. |
| SLM-R10 | MISSING | No implementing code in code_roots. No eval harness exists to trace metrics for. The precheck's deterministic metrics (score_turn, lines 155-170) are behavior-targeted, which is the intended direction. |
| SLM-R11 | PARTIAL | Script exists but produced no numbers. metacog_precheck.py is, by its own docstring (line 6: 'deterministic checks -- no LLM judge'), a cheap precursor to the ablation, and it is currently non-runnable: call() (lines 122-126) builds `fn` but never invokes or returns it, so every reply is None and all 30 conversations fail at parse_ledger before any API request is made (verify.precheck exit: 30/30 FAILED, empty table). |
| SLM-R15 | PARTIAL | verify.scenario_count → 5 scenarios; the brief's floor is 30 per model×strategy. |
| SLM-R16 | MISSING | No implementing code in code_roots. metacog_precheck.py is deterministic by design (line 6: 'no LLM judge'); there is no LLM-as-judge and no shared rubric module. |
| SLM-R17 | PARTIAL | Per-model×strategy table exists but reports ledger-specific mechanical metrics, not the two named metrics; the captured run produced a header-only table (0 rows). |
| SLM-R18 | MISSING | No implementing code in code_roots. |
| SLM-R19 | MISSING | No implementing code in code_roots. |
| SLM-R20 | MISSING | No implementing code in code_roots. |
| SLM-R21 | MISSING | No implementing code in code_roots. |
| SLM-R22 | MISSING | No implementing code in code_roots. |
| SLM-R23 | MISSING | No implementing code in code_roots. |
| SLM-R24 | MISSING | No implementing code in code_roots. verify.eval NOT RUN — eval.py does not exist. |
| SLM-R25 | MISSING | No implementing code in code_roots. |
| SLM-R26 | MISSING | No implementing code in code_roots. |
| SLM-R27 | MISSING | No implementing code in code_roots. |
| SLM-R29 | PARTIAL | Script is present but a grader cannot rerun even one point: metacog_precheck.py is, by its own docstring (line 6: 'deterministic checks -- no LLM judge'), a cheap precursor to the ablation, and it is currently non-runnable: call() (lines 122-126) builds `fn` but never invokes or returns it, so every reply is None and all 30 conversations fail at parse_ledger before any API request is made (verify.precheck exit: 30/30 FAILED, empty table). |
| SLM-R30 | MISSING | No implementing code in code_roots. |
| SLM-R34 | PARTIAL | Same artifact as SLM-R2; not finalized as a standalone one-to-two-sentence spec. |
| SLM-R35 | MISSING | No implementing code in code_roots. |
| SLM-R36 | MISSING | No implementing code in code_roots. |
| SLM-R37 | PARTIAL | Behavioral checks for the spec's failure modes exist, but only inside the ablation precheck; no eval harness applies them to base/tuned model outputs. |
| SLM-R38 | MISSING | No implementing code in code_roots. |
| SLM-R39 | MISSING | No implementing code in code_roots. |
| SLM-R40 | MISSING | No implementing code in code_roots. |
| SLM-R41 | MISSING | No implementing code in code_roots. |
| SLM-R42 | MISSING | No implementing code in code_roots. |
| SLM-R43 | MISSING | No implementing code in code_roots. |
| SLM-R44 | MISSING | No implementing code in code_roots. |
| SLM-R45 | MISSING | No implementing code in code_roots. |
| SLM-R46 | MISSING | No implementing code in code_roots. |
| SLM-R47 | MISSING | No implementing code in code_roots. |
| SLM-R48 | MISSING | No implementing code in code_roots. |
| SLM-R49 | MISSING | No implementing code in code_roots. |
| SLM-R50 | MISSING | No implementing code in code_roots. |
| SLM-R51 | MISSING | No implementing code in code_roots. |
| SLM-R53 | MISSING | No implementing code in code_roots. |
| SLM-R54 | MISSING | No implementing code in code_roots. |
| SLM-R55 | MISSING | No implementing code in code_roots. |

## Orphan tickets
None checked — ticket dimension BLOCKED (see Coverage and limitations).

## Blocked / assumed
- **All rows — tickets `BLOCKED`.** Unblock: Create a Linear project for this SLM work under Troysatchell, set tickets.project to its exact name in audit/requirements.config.yaml, and re-run.
- **SLM-R7 — ASSUMED.** Question: Does 'one context' mean the tutoring interaction context (so five different subject topics in metacog_scenarios.jsonl are fine), rather than a single subject? (yes/no: is multi-subject tutoring acceptable as one context?) Traced under: *Yes — one context = 1:1 tutoring; multi-subject is acceptable.* — flagged for a ruling; log it in `interpretations.md` as I-01 and re-run.

## Verification performed
| Command | Result | Bears on |
|---|---|---|
| `python3 -c "import json;rows=[json.loads(l) for l in open('metacog_scenarios.jsonl') if l.strip()];print('scenarios',len(rows),'turns',sum(len(r['turns']) for r in rows))"` | exit 0 — scenarios 5 turns 66 | SLM-R15, SLM-R3, SLM-R7 |
| `python3 -m py_compile metacog_precheck.py && echo compile-ok` | exit 0 — compile-ok — Syntax only; runtime failure found by verify.precheck. | SLM-R29 |
| `set -a && . ./.env && set +a && curl -s -w '\nHTTP %{http_code}\n' https://api.anthropic.com/v1/models/claude-opus-5 -H "x-api-key: $ANTHROPIC_API_KEY" -H 'anthropic-version: 2023-06-01'` | HTTP 200 — model object for claude-opus-5 returned — Read-only GET; no generation. | SLM-R13 |
| `set -a && . ./.env && set +a && curl -s https://api.moonshot.ai/v1/models -H "Authorization: Bearer $MOONSHOT_API_KEY"` | HTTP 200 — model ids: kimi-k2.6, kimi-k2.7-code, kimi-k2.7-code-highspeed, kimi-k3 — Read-only GET; no generation. | SLM-R13 |
| `set -a && . ./.env && set +a && python3 metacog_precheck.py --scenarios metacog_scenarios.jsonl --out audit/requirements/runs/precheck` | exit 0 (script swallows per-conversation exceptions) — 30/30 conversations FAILED with "'NoneType' object has no attribute 'strip'"; table.md header-only; transcripts.jsonl empty; zero API requests made — Output written to audit/requirements/runs/precheck/. No cost incurred: call() never invokes the provider. | SLM-R1, SLM-R11, SLM-R14, SLM-R17, SLM-R29 |
| `python3 eval.py --model <hf-repo-id> --eval-set <path>` | NOT RUN — eval.py does not exist in the repo. | SLM-R6, SLM-R20, SLM-R24, SLM-R38, SLM-R42, SLM-R49 |

### Captured output — VERIFIED rows
**SLM-R13** — `set -a && . ./.env && set +a && curl -s -w '\nHTTP %{http_code}\n' https://api.anthropic.com/v1/models/claude-opus-5 -H "x-api-key: $ANTHROPIC_API_KEY" -H 'anthropic-version: 2023-06-01'  &&  set -a && . ./.env && set +a && curl -s https://api.moonshot.ai/v1/models -H "Authorization: Bearer $MOONSHOT_API_KEY"`
```
{"type":"model","id":"claude-opus-5","display_name":"Claude Opus 5","created_at":"2026-07-24T00:00:00Z",...}
HTTP 200
['kimi-k2.6', 'kimi-k2.7-code', 'kimi-k2.7-code-highspeed', 'kimi-k3']
HTTP 200
```

### Captured output — verify.precheck (red)
```
exit 0 (script swallows per-conversation exceptions) — 30/30 conversations FAILED with "'NoneType' object has no attribute 'strip'"; table.md header-only; transcripts.jsonl empty; zero API requests made

  FAILED kimi/structured/m4: 'NoneType' object has no attribute 'strip'
  29/30
  FAILED kimi/structured/m5: 'NoneType' object has no attribute 'strip'
  30/30
| model | strategy | ledger rate | unearned | no-elicit | clean runs | median first break |
|---|---|---|---|---|---|---|
```
