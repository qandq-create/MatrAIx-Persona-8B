# Step 1.2 item 4 — Choice A vs. Choice B qualitative comparison

Same survey instrument (the FocusLoop pricing question from the original
Priya Nair walkthrough), run against a Choice A persona and a Choice B
Canadian concept persona, through the real local model
(`qwen3:8b-lowvram` via Ollama), using `InprocessSurveyEvalRunner` — the
actual MatrAIx code path, not a mocked/scripted response.

## Question
> FocusLoop, a family coordination app, costs $9.99/month after a 14-day
> free trial. How likely are you to subscribe once the trial ends?
> (1-5 Likert, rationale + confidence requested)

## Choice A — mock Priya Nair
- **Identity**: 35-44, Ontario, Woman, Parent of young kids, English,
  Practitioner, High conscientiousness, Risk-averse, Core value:
  Security, **Economic motivation: Cost-sensitive**, Interested in
  Technology, Passionate about Parenting, Healthcare domain.
- **Answer**: value=3, confidence=0.75
- **Rationale**: *"As a parent, I see value in family coordination, but
  the $9.99/month cost may be a barrier without clear benefits during
  the trial."*

## Choice B — Canadian concept persona `ca_0001`
- **Identity**: 65-74, Self-described gender, Married, **Household
  income band: $25k-50k** (real, StatCan-calibrated), Boomer,
  Vocational/cert education, plus ~100 Canadian consumer-behavior and
  psychographic dims (somewhat concerned about privacy, price-driven on
  alcohol, low health-consciousness priority, rigorous recycler, heavy
  TV/radio consumer, etc.).
- **Answer**: value=3, confidence=0.7
- **Rationale**: *"The $9.99/month price feels high for my income level,
  but the family coordination utility might justify it if I need it for
  managing household tasks."*

## What this shows
Both personas land on the same Likert value, but the *rationale* in each
case traces directly to that persona's actual dimension data — not
generic filler:
- Choice A's reasoning is anchored to her `life_stage`
  ("As a parent...") and `economic_motivation` ("cost-sensitive").
- Choice B's reasoning is anchored to her real calibrated
  `demo_household_income` value — the model correctly read "$25k-50k"
  and reasoned "price feels high for my income level," a framing Choice
  A's persona never produces because her income band isn't in the same
  low-income bracket.

This confirms the model is genuinely conditioning on persona content,
not producing generic answers regardless of who's asked — which is
what Step 1.2's acceptance criterion actually needs, more than any
particular topical "Canadian-ness" in a single answer. (province wasn't
part of the rendered narrative for this run — it's a plain top-level
field per Step 1.4, not yet wired into the identity prompt itself;
that's Step 1.4's job, not this comparison's.)

## Infrastructure fixed to make this run possible
Two rendering call sites had the same latent bug as `templating.py`
(commit `621ea51`) — they accepted no `catalog_path` at all, so running
a Choice B persona through the real survey-eval code path would have
silently degraded its 99 Canadian dims to raw-id labels dumped in an
unsorted bucket, rather than the properly organized sections. Fixed:
- `playground/user_sim/prompt.py`'s `render_persona_block`
- `playground/inprocess/survey_eval.py`'s `persona_system_prompt` and
  `InprocessSurveyEvalRunner.__call__`

All three changes are backward-compatible (`catalog_path=None` default
preserves prior single-catalog behavior exactly) — verified by Choice
A's run above rendering identically to how it always has.
