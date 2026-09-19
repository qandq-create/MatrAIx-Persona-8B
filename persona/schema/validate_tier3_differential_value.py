"""
V0 Tier 3 -- Choice A vs. Choice B differential value battery. Same
matched pair as the original Step 1.2 item 4 comparison (mock Priya
Nair vs. ca_0001), 6 retail-relevant questions spanning pricing,
promotion response, channel preference, brand switching, and two
category-specific scenarios. Not testing "do they differ" (already
shown) -- testing whether Choice B's answers are more actionable for a
retail marketer, i.e. grounded in real purchase-behavior/psychographic
data Choice A's schema simply doesn't have.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

REPO_ROOT = os.path.expanduser("~/simulator/MatrAIx")
sys.path.insert(0, os.path.join(REPO_ROOT, "application/playground"))
sys.path.insert(0, os.path.join(REPO_ROOT, "packages/playground/src"))
sys.path.insert(0, os.path.join(REPO_ROOT, "src"))

from backend.service.survey_types import SurveyEvalConfig, SurveyInstrument, SurveyQuestion
from playground.inprocess.survey_eval import InprocessSurveyEvalRunner
from playground.types import Persona as EvalPersona

CHOICE_A_YAML = os.path.expanduser("~/simulator/scratch/mock_persona.yaml")
CHOICE_B_YAML = os.path.join(
    REPO_ROOT, "persona/datasets/canada-persona-dev-sample/persona_ca_0001.json"
)
CHOICE_B_CATALOG = (
    os.path.join(REPO_ROOT, "persona/schema/dimensions.json"),
    os.path.join(REPO_ROOT, "persona/schema/dimensions_canada.json"),
)

config = SurveyEvalConfig(persona_model="openai/qwen3:8b-lowvram")
runner = InprocessSurveyEvalRunner()

QUESTIONS = [
    {
        "name": "Pricing (subscription)",
        "prompt": (
            "A local gym is offering a $45/month membership with no long-term "
            "contract. How likely are you to sign up?"
        ),
    },
    {
        "name": "Promotion response",
        "prompt": (
            "Your regular grocery store is running a 'Buy One Get One 50% Off' "
            "promotion this week on items you normally buy. How likely are you to "
            "take advantage of it?"
        ),
    },
    {
        "name": "Channel preference",
        "prompt": (
            "You need a new winter coat. Would you rather shop in-store at a mall "
            "department store, or order online and have it delivered? How likely "
            "are you to choose in-store?"
        ),
    },
    {
        "name": "Brand switching",
        "prompt": (
            "Your usual brand of coffee just raised its price by $2 per bag. A "
            "similar-quality competitor brand is $2 cheaper. How likely are you to "
            "switch brands?"
        ),
    },
    {
        "name": "Category-specific: home improvement",
        "prompt": (
            "You have a leaky kitchen faucet. How likely are you to attempt to fix "
            "it yourself rather than hiring a plumber?"
        ),
    },
    {
        "name": "Category-specific: dining",
        "prompt": (
            "A new restaurant just opened in your neighborhood offering a tasting "
            "menu at $85 per person. How likely are you to try it in the next month?"
        ),
    },
]


def run(label: str, yaml_path: str, eval_id: str, name: str, prompt: str, qid: str, catalog_path=None):
    instrument = SurveyInstrument(
        id=f"tier3-{qid}", title=f"Tier 3: {qid}",
        description="V0 Tier 3 differential value test.",
        ask_rationale=True, ask_confidence=True,
        questions=[SurveyQuestion(
            id=qid, prompt=prompt, type="likert", min_value=1, max_value=5,
            construct="tier3", required=True,
        )],
    )
    eval_persona = EvalPersona(id=eval_id, name=name, source="mock")
    result = runner(
        eval_persona, instrument, config=config,
        created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        persona_yaml_path=yaml_path, on_event=None, job_dir=None,
        catalog_path=catalog_path,
    )
    return result.answers[0]


all_results = []
for i, q in enumerate(QUESTIONS):
    qid = f"q{i}"
    print("=" * 70)
    print(q["name"])
    print("=" * 70)
    print(f"Q: {q['prompt']}\n")

    a_answer = run("A", CHOICE_A_YAML, "choice-a-001", "Priya Nair", q["prompt"], qid)
    b_answer = run("B", CHOICE_B_YAML, "choice-b-001", "ca_0001", q["prompt"], qid, catalog_path=CHOICE_B_CATALOG)

    print(f"CHOICE A: value={a_answer.value} conf={a_answer.confidence}")
    print(f"  rationale: {a_answer.rationale}")
    print(f"CHOICE B: value={b_answer.value} conf={b_answer.confidence}")
    print(f"  rationale: {b_answer.rationale}")
    print()

    all_results.append({
        "name": q["name"], "prompt": q["prompt"],
        "choice_a": {"value": a_answer.value, "confidence": a_answer.confidence, "rationale": a_answer.rationale},
        "choice_b": {"value": b_answer.value, "confidence": b_answer.confidence, "rationale": b_answer.rationale},
    })

OUT_DIR = os.path.join(REPO_ROOT, "persona/datasets/canada-persona-dev-sample")
with open(os.path.join(OUT_DIR, "tier3_differential_value_results.json"), "w", encoding="utf-8") as f:
    json.dump(all_results, f, indent=2)
print("Done.")
