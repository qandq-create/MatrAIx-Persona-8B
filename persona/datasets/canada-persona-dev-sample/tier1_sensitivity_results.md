# V0 Tier 1 — Sensitivity/internal-consistency battery

Paired personas identical except for one target dimension, same
question run against both through the real local model
(`qwen3:8b-lowvram` via Ollama), checking whether the answer shifts in
the expected direction. Not a test of *realism* (that's Tiers 2-3) —
this isolates whether the *mechanism* responds correctly to its own
inputs, which is the prerequisite for trusting any future calibration.

## Round 1 — four independent pairs, one shared base persona

| Test | Low → High | Result |
|---|---|---|
| Grocery brand orientation (National-brand loyal → Store-brand preferring) | 4 → 5 | ✅ PASS |
| Environmental willingness-to-pay (Not willing → Very willing) | 2 → 3 | ✅ PASS |
| Household income (<$25k → $200k+) | 3 → 3 | ❌ FAIL |
| Alcohol quality vs. price (Price-driven → Quality-driven) | 2 → 2 | ❌ FAIL |

**2/4 passed.** The two failures were diagnosed, not just recorded: the
shared base persona (`ca_0001`) carried an unvaried, strongly-worded
dimension — `psych_product_quality_vs_price: "Price is the deciding
factor"` — that leaked into both failed answers. The alcohol test's
HIGH variant (`psych_alcohol_quality_orientation: "Quality-driven
regardless of price"`) answered *"Price is the deciding factor for
alcohol purchases... I prioritize value over higher quality ratings"* —
using the general dimension's exact phrasing, contradicting the
specific dimension actually being tested.

## Round 2 — same two tests, confound neutralized

Set `psych_product_quality_vs_price: "Balanced"` in the base (and
`purch_alcohol_price_tier: "Mid-range"` for the alcohol test, removing
a second price-anchor), re-ran both failed cases.

| Test | Low → High | Result |
|---|---|---|
| Household income (controlled) | 2 → 3 | ✅ PASS |
| Alcohol quality vs. price (controlled) | 3 → 4 | ✅ PASS |

**2/2 passed once the confound was removed.**

## Overall verdict: 4/4 genuine passes, one real methodological finding
The mechanism works correctly — every dimension tested moved the
model's answer in the expected direction once tested in isolation.
The two apparent failures were a **test-design confound**, not a
mechanism problem: building all pairs from one shared base persona
meant an unvaried, strongly-worded dimension could dominate over the
dimension actually being varied.

**A genuine finding worth carrying forward, not just a test artifact:**
the schema currently has both a *general* price-orientation dimension
(`psych_product_quality_vs_price`) and *category-specific* ones
(`psych_alcohol_quality_orientation`, and implicitly similar ones for
other categories) that can carry conflicting values for the same
persona — and when they do, the model's resolution between them is
inconsistent rather than reliably favoring the more specific one. This
is worth a schema design pass later: either make category-specific dims
explicitly override the general one in the render, or reconsider
whether both need to coexist. Flagged here for Tier 4 (negotiation
leverage / gap analysis), not acted on now.

## Methodological lesson for future Tier 1-style tests
Build each pair from a **neutral base** (or explicitly control known
related dims), not one shared base persona carrying arbitrary strong
opinions on unrelated categories — otherwise a real mechanism success
can look like a false failure.
