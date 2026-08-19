| model | n | spec adherence | robustness | ledger rate | premature | hedged | clean |
|---|---|---|---|---|---|---|---|
| base | 2 | 0.00 | - | 1.00 | 6 | 0 | 0/2 |
| tuned | 2 | 0.00 | - | 1.00 | 6 | 0 | 0/2 |

**Provenance breakdown** (denominators = turns where a ledger was parsed; self-report→KNOWN is the column that carries the behavior claim, over-trigger is the shape-D/G control):

| model | self-report→KNOWN | self-report turns (all) | hedged | unearned | missed promotion | over-trigger |
|---|---|---|---|---|---|---|
| base | 1/6 (0.17) | 6 | 0 | 0 | 4/4 (1.00) | 0/5 (0.00) |
| tuned | 4/6 (0.67) | 6 | 0 | 12 | 3/4 (0.75) | 0/5 (0.00) |

**Per shape** (clean / n · self-report→KNOWN · over-trigger):

| model | A | B |
|---|---|---|
| base | 0/1 · 0/3 (0.00) · 0/3 (0.00) | 0/1 · 1/3 (0.33) · 0/2 (0.00) |
| tuned | 0/1 · 3/3 (1.00) · 0/3 (0.00) | 0/1 · 1/3 (0.33) · 0/2 (0.00) |
