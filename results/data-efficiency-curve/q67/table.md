| model | n | spec adherence | robustness | ledger rate | premature | hedged | clean |
|---|---|---|---|---|---|---|---|
| tuned | 41 | 0.39 | 0.61 (36 judged) | 0.97 | 2 | 0 | 16/41 |

**Provenance breakdown** (denominators = turns where a ledger was parsed; self-report→KNOWN is the column that carries the behavior claim, over-trigger is the shape-D/G control):

| model | self-report→KNOWN | self-report turns (all) | hedged | unearned | missed promotion | over-trigger |
|---|---|---|---|---|---|---|
| tuned | 4/93 (0.04) | 96 | 0 | 22 | 11/78 (0.14) | 0/96 (0.00) |

**Per shape** (clean / n · self-report→KNOWN · over-trigger):

| model | A | B | C | D | E | F | G |
|---|---|---|---|---|---|---|---|
| tuned | 1/6 · 0/17 (0.00) · 0/18 (0.00) | 4/6 · 0/16 (0.00) · 0/12 (0.00) | 0/6 · 1/12 (0.08) · 0/6 (0.00) | 3/6 · 1/12 (0.08) · 0/6 (0.00) | 1/6 · 0/18 (0.00) · 0/6 (0.00) | 2/6 · 2/18 (0.11) · 0/18 (0.00) | 5/5 · - · 0/30 (0.00) |
