| model | n | spec adherence | robustness | ledger rate | premature | hedged | clean |
|---|---|---|---|---|---|---|---|
| tuned | 41 | 0.32 | 0.56 (36 judged) | 0.95 | 4 | 0 | 13/41 |

**Provenance breakdown** (denominators = turns where a ledger was parsed; self-report→KNOWN is the column that carries the behavior claim, over-trigger is the shape-D/G control):

| model | self-report→KNOWN | self-report turns (all) | hedged | unearned | missed promotion | over-trigger |
|---|---|---|---|---|---|---|
| tuned | 7/87 (0.08) | 96 | 0 | 16 | 19/78 (0.24) | 5/96 (0.05) |

**Per shape** (clean / n · self-report→KNOWN · over-trigger):

| model | A | B | C | D | E | F | G |
|---|---|---|---|---|---|---|---|
| tuned | 0/6 · 0/15 (0.00) · 3/18 (0.17) | 3/6 · 0/17 (0.00) · 1/12 (0.08) | 0/6 · 1/11 (0.09) · 0/6 (0.00) | 1/6 · 4/10 (0.40) · 0/6 (0.00) | 2/6 · 1/17 (0.06) · 0/6 (0.00) | 2/6 · 1/17 (0.06) · 1/18 (0.06) | 5/5 · - · 0/30 (0.00) |
