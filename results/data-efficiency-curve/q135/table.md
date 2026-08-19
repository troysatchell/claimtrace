| model | n | spec adherence | robustness | ledger rate | premature | hedged | clean |
|---|---|---|---|---|---|---|---|
| tuned | 41 | 0.54 | 0.69 (36 judged) | 0.99 | 0 | 5 | 22/41 |

**Provenance breakdown** (denominators = turns where a ledger was parsed; self-report→KNOWN is the column that carries the behavior claim, over-trigger is the shape-D/G control):

| model | self-report→KNOWN | self-report turns (all) | hedged | unearned | missed promotion | over-trigger |
|---|---|---|---|---|---|---|
| tuned | 1/94 (0.01) | 96 | 5 | 12 | 11/78 (0.14) | 1/96 (0.01) |

**Per shape** (clean / n · self-report→KNOWN · over-trigger):

| model | A | B | C | D | E | F | G |
|---|---|---|---|---|---|---|---|
| tuned | 4/6 · 1/17 (0.06) · 0/18 (0.00) | 3/6 · 0/18 (0.00) · 0/12 (0.00) | 0/6 · 0/12 (0.00) · 0/6 (0.00) | 3/6 · 0/11 (0.00) · 0/6 (0.00) | 3/6 · 0/18 (0.00) · 0/6 (0.00) | 4/6 · 0/18 (0.00) · 1/18 (0.06) | 5/5 · - · 0/30 (0.00) |
