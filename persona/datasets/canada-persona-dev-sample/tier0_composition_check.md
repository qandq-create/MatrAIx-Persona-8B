# V0 Tier 0 — Statistical composition check

Generated N=300 personas (in-memory sampling, not written as individual
files — this is a pure distribution check) and compared the aggregate
frequency of each calibrated dimension's values against
`calibration_canada.json`'s real StatCan-derived target probabilities,
using a chi-square goodness-of-fit test per dimension (null hypothesis:
the sampler's output distribution matches the target distribution).

## Result: all 9 checks pass

| Dimension | χ² | df | p-value | Verdict |
|---|---:|---:|---:|---|
| `age_bracket` | 4.63 | 10 | 0.915 | PASS |
| `demo_marital_status` | 12.32 | 7 | 0.090 | PASS |
| `demo_household_income` | 9.41 | 4 | 0.052 | PASS |
| `highest_education`* | 4.73 | 6 | 0.579 | PASS |
| `linguistic_community` | 1.76 | 3 | 0.624 | PASS |
| `primary_language_canada` | 11.87 | 12 | 0.456 | PASS |
| `demo_ethnicity_canada` | 9.75 | 11 | 0.553 | PASS |
| `indigenous_identity` | 6.33 | 4 | 0.176 | PASS |
| `province` | 13.84 | 12 | 0.311 | PASS |

\* `highest_education` has 3 categories with exact 0% target probability
(No formal, Some college, Postdoc — real gaps in what StatCan's
categories support, documented in Decision 0022/calibration notes, not
sampler bugs). Confirmed those categories got exactly 0 observations in
300 samples, then excluded them from the chi-square test (a category
with 0 expected frequency breaks the test statistic, not a meaningful
comparison).

No dimension shows p < 0.05 — no evidence of systematic sampling bias.
The largest raw percentage-point deviations (`demo_marital_status`'s
Married at +8.0pp, `demo_household_income`'s $50k-100k at -6.3pp,
`province`'s Quebec at +5.4pp) are fully consistent with expected
sampling noise at N=300, not artifacts of an implementation bug — this
is exactly what the chi-square test (which accounts for sample size and
the full category distribution, not just eyeballing one category) is
for.

## What this establishes
This is a prerequisite check, not "business value" yet: it confirms the
sampler mechanism is sound — it genuinely reproduces the real
StatCan-derived marginal distributions at scale, across all 8 calibrated
dimensions plus province, with no detectable bias. If this had failed,
nothing built on top of it (Tiers 1-4, V1-V3) could be trusted. It
passed cleanly.

## Next
Tier 1 — sensitivity/internal-consistency battery (paired personas
differing in one dimension, checking the model's answer shifts in the
expected direction).
