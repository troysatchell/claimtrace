| model | n | spec adherence | robustness | ledger rate | premature | hedged | clean |
|---|---|---|---|---|---|---|---|
| base | 41 | 0.00 | 0.97 (36 judged) | 1.00 | 120 | 1 | 0/41 |
| tuned | 41 | 0.49 | 0.67 (36 judged) | 0.97 | 2 | 0 | 20/41 |

**Provenance breakdown** (denominators = turns where a ledger was parsed; self-report→KNOWN is the column that carries the behavior claim, over-trigger is the shape-D/G control):

| model | self-report→KNOWN | self-report turns (all) | hedged | unearned | missed promotion | over-trigger |
|---|---|---|---|---|---|---|
| base | 23/96 (0.24) | 96 | 1 | 45 | 74/78 (0.95) | 0/96 (0.00) |
| tuned | 1/91 (0.01) | 96 | 0 | 13 | 10/78 (0.13) | 1/96 (0.01) |

**Per shape** (clean / n · self-report→KNOWN · over-trigger):

| model | A | B | C | D | E | F | G |
|---|---|---|---|---|---|---|---|
| base | 0/6 · 1/18 (0.06) · 0/18 (0.00) | 0/6 · 6/18 (0.33) · 0/12 (0.00) | 0/6 · 6/12 (0.50) · 0/6 (0.00) | 0/6 · 2/12 (0.17) · 0/6 (0.00) | 0/6 · 8/18 (0.44) · 0/6 (0.00) | 0/6 · 0/18 (0.00) · 0/18 (0.00) | 0/5 · - · 0/30 (0.00) |
| tuned | 2/6 · 0/18 (0.00) · 0/18 (0.00) | 3/6 · 0/14 (0.00) · 0/12 (0.00) | 0/6 · 0/12 (0.00) · 0/6 (0.00) | 3/6 · 1/11 (0.09) · 0/6 (0.00) | 3/6 · 0/18 (0.00) · 0/6 (0.00) | 4/6 · 0/18 (0.00) · 1/18 (0.06) | 5/5 · - · 0/30 (0.00) |
