| model | n | spec adherence | robustness | ledger rate | premature | hedged | clean |
|---|---|---|---|---|---|---|---|
| base | 41 | 0.00 | 0.94 (36 judged) | 1.00 | 120 | 1 | 0/41 |
| tuned | 41 | 0.80 | 0.83 (36 judged) | 1.00 | 0 | 0 | 33/41 |

**Provenance breakdown** (denominators = turns where a ledger was parsed; self-report→KNOWN is the column that carries the behavior claim, over-trigger is the shape-D/G control):

| model | self-report→KNOWN | self-report turns (all) | hedged | unearned | missed promotion | over-trigger |
|---|---|---|---|---|---|---|
| base | 23/96 (0.24) | 96 | 1 | 45 | 74/78 (0.95) | 0/96 (0.00) |
| tuned | 0/96 (0.00) | 96 | 0 | 1 | 8/78 (0.10) | 14/96 (0.15) |

**Per shape** (clean / n · self-report→KNOWN · over-trigger):

| model | A | B | C | D | E | F | G |
|---|---|---|---|---|---|---|---|
| base | 0/6 · 1/18 (0.06) · 0/18 (0.00) | 0/6 · 6/18 (0.33) · 0/12 (0.00) | 0/6 · 6/12 (0.50) · 0/6 (0.00) | 0/6 · 2/12 (0.17) · 0/6 (0.00) | 0/6 · 8/18 (0.44) · 0/6 (0.00) | 0/6 · 0/18 (0.00) · 0/18 (0.00) | 0/5 · - · 0/30 (0.00) |
| tuned | 6/6 · 0/18 (0.00) · 3/18 (0.17) | 6/6 · 0/18 (0.00) · 4/12 (0.33) | 1/6 · 0/12 (0.00) · 1/6 (0.17) | 6/6 · 0/12 (0.00) · 0/6 (0.00) | 4/6 · 0/18 (0.00) · 0/6 (0.00) | 5/6 · 0/18 (0.00) · 6/18 (0.33) | 5/5 · - · 0/30 (0.00) |
