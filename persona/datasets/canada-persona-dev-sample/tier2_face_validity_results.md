# V0 Tier 2 — Face validity against published Canadian findings

Three real, published, checkable Canadian consumer statistics, each run
as an equivalent question against N=8 Choice B personas through the
real local model. Directional agreement is the bar (per TRD-1), not
exact match — N=8 per group is small, this tests plausibility, not
precision.

## Finding 1: Private label — a real, well-understood gap
**Published**: 62% of Canadians buy store brands to save money
(Retail Council of Canada / Leger survey, reported via NOW Toronto).
**Simulated**: 38% Yes.

**Diagnosis, not just a number**: `purch_grocery_brand_orientation` has
5 uniform-random values — `Store-brand preferring`, `Mostly
store-brand`, `Balanced`, `Mostly national brands`, `National-brand
loyal`. Only 2 of 5 lean toward "yes" on a private-label question:
2/5 = 40%, which is what the simulated 38% actually reflects — the
uncalibrated uniform baseline, not a reasoning failure. **This is
exactly the kind of gap real calibration would close**: real Canadian
data skews meaningfully toward store-brand adoption (62%, not 40%),
and PRIZM5/Vividata (or even a public StatCan/industry marginal, if one
existed at this granularity) would directly correct this dimension's
distribution.

## Finding 2: Sales responsiveness — a near-exact match, reported honestly
**Published**: 76% of Canadians are buying items on sale (Eagle Eye
Canada/US grocery loyalty survey).
**Simulated**: 75% Yes.

**Diagnosis — this match is very likely coincidental, not evidence of
accuracy**: `purch_grocery_promotion_usage` has 4 uniform-random values
— `Never`, `Occasionally`, `Regularly`, `Always`. 3 of 4 plausibly
count as "yes, bought something on sale recently": 3/4 = 75%, matching
the simulated rate almost exactly. The real population rate (76%)
happens to land close to what a 4-category uniform baseline produces
when 3 of 4 categories lean "yes" — **this is a property of the
schema's category count, not evidence the uncalibrated model is
predicting reality.** Worth being explicit about this rather than
claiming a win: it would be dishonest to present this as proof of
accuracy in an Environics pitch when the real driver is coincidental
alignment between category count and the true population rate.

## Finding 3: Regional alcohol preference — directionally wrong, and diagnostic
**Published**: Quebec is wine-dominant (wine 43.5% of alcohol sales);
rest of Canada (Ontario, etc.) is beer-dominant (beer 36.0% vs. wine
31.4% nationally).
**Simulated**: Quebec 62% Wine; **Ontario 88% Wine** — both provinces
show heavy wine preference, and Ontario is *higher* than Quebec, the
opposite of the real contrast.

**Diagnosis — this is the most informative result of the three, and it
reveals something structural, not a bug**: `purch_alcohol_category_preference`
is sampled completely independently of `geography.province` in the
current pipeline — this is by design (Track A's lightweight calibration
uses independent draws, no cross-dimension correlation, the same
tradeoff already documented for age/income/education in Step 1.2).
There is currently **no mechanism at all** connecting a persona's
province to their category preferences — geography exists purely as an
unrelated field the model happens to see in the prompt. The elevated
wine answers for *both* provinces likely come from other, unrelated
psychographic dims (several rationales reference "status
consciousness," "premium quality," "luxury experiences" — general
`psych_*` dims, not anything province-specific) leaking into an
ambiguous forced binary choice, similar to the confound diagnosed in
Tier 1.

**This is exactly the kind of gap Tier 4 exists to surface for the
Environics conversation**: real geography-behavior correlation (which
PRIZM5's segment structure, and Vividata's regional data, genuinely
encode) is precisely what's missing here, and precisely what licensing
their data would add — not just better marginal distributions (Finding
1's gap), but real *joint* structure between where someone lives and
what they buy, which independent draws structurally cannot produce no
matter how well-calibrated each dimension's marginal is individually.

## Summary — what this tells us going into Tier 3/4
- Marginal-distribution gaps (Finding 1) are real, expected, and
  directly named-able as calibration targets.
- Coincidental matches (Finding 2) must be diagnosed, not just
  celebrated — reporting this honestly is itself part of the technical
  credibility case for the Environics pitch.
- Cross-dimension correlation gaps (Finding 3, geography-behavior) are
  the deepest and most valuable finding: they show precisely why
  *joint* calibration (Stage 1's real graph, or PRIZM5/Vividata's
  segment-level structure) is necessary, not just richer marginals.
