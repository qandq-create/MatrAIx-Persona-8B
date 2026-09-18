"""
Tier 1 re-run of the two failed cases, with the identified confounding
dims neutralized in the base persona first -- isolates whether the
original failures were a real mechanism problem or a test-design
confound (competing unvaried dims in the shared base persona).
"""
from __future__ import annotations

import copy
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

BASE_PERSONA_PATH = os.path.join(
    REPO_ROOT, "persona/datasets/canada-persona-dev-sample/persona_ca_0001.json"
)
CATALOG_PATH = (
    os.path.join(REPO_ROOT, "persona/schema/dimensions.json"),
    os.path.join(REPO_ROOT, "persona/schema/dimensions_canada.json"),
)
OUT_DIR = os.path.join(REPO_ROOT, "persona/datasets/canada-persona-dev-sample")

config = SurveyEvalConfig(persona_model="openai/qwen3:8b-lowvram")
runner = InprocessSurveyEvalRunner()

with open(BASE_PERSONA_PATH, encoding="utf-8") as f:
    BASE_PERSONA = json.load(f)

# Neutralize the identified confound for both re-tests: the general
# price-orientation dim that was leaking into/overriding the
# category-specific dims being tested.
NEUTRALIZED_BASE = copy.deepcopy(BASE_PERSONA)
NEUTRALIZED_BASE["dimensions"]["psych_product_quality_vs_price"] = "Balanced"

TEST_CASES = [
    {
        "name": "Household income and price sensitivity (controlled)",
        "dim": "demo_household_income",
        "low_value": "<$25k",
        "high_value": "$200k+",
        "extra_neutralize": {},  # psych_product_quality_vs_price already neutralized in base
        "expect": "high_value ($200k+) scores HIGHER likelihood to subscribe (less price resistance)",
        "question": SurveyQuestion(
            id="q_price_v2",
            prompt=(
                "FocusLoop, a family coordination app, costs $9.99/month after a "
                "14-day free trial. How likely are you to subscribe once the trial ends?"
            ),
            type="likert", min_value=1, max_value=5, construct="purchase_intent", required=True,
        ),
    },
    {
        "name": "Alcohol quality vs. price orientation (controlled)",
        "dim": "psych_alcohol_quality_orientation",
        "low_value": "Price-driven",
        "high_value": "Quality-driven regardless of price",
        "extra_neutralize": {"purch_alcohol_price_tier": "Mid-range"},
        "expect": "high_value (quality-driven) scores HIGHER likelihood to buy premium",
        "question": SurveyQuestion(
            id="q_beer_v2",
            prompt=(
                "A premium craft beer costs twice as much as a regular beer but is "
                "rated much higher quality by reviewers. How likely are you to buy it "
                "for your next purchase?"
            ),
            type="likert", min_value=1, max_value=5, construct="premium_purchase", required=True,
        ),
    },
]


def run_variant(persona_dict: dict, question: SurveyQuestion, label: str):
    instrument = SurveyInstrument(
        id=f"tier1v2-{question.id}", title=f"Tier 1 controlled: {question.id}",
        description="V0 Tier 1 controlled re-run.",
        ask_rationale=True, ask_confidence=True, questions=[question],
    )
    yaml_path = os.path.join(OUT_DIR, f"_tier1v2_tmp_{label}.json")
    with open(yaml_path, "w", encoding="utf-8") as f:
        json.dump(persona_dict, f)
    eval_persona = EvalPersona(id=f"tier1v2-{label}", name=label, source="mock")
    result = runner(
        eval_persona, instrument, config=config,
        created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        persona_yaml_path=yaml_path, on_event=None, job_dir=None,
        catalog_path=CATALOG_PATH,
    )
    os.remove(yaml_path)
    return result.answers[0]


results = []
for case in TEST_CASES:
    print("=" * 70)
    print(case["name"])
    print("=" * 70)

    low_persona = copy.deepcopy(NEUTRALIZED_BASE)
    high_persona = copy.deepcopy(NEUTRALIZED_BASE)
    for k, v in case["extra_neutralize"].items():
        low_persona["dimensions"][k] = v
        high_persona["dimensions"][k] = v
    low_persona["dimensions"][case["dim"]] = case["low_value"]
    high_persona["dimensions"][case["dim"]] = case["high_value"]

    low_answer = run_variant(low_persona, case["question"], f"{case['dim']}_low_v2")
    high_answer = run_variant(high_persona, case["question"], f"{case['dim']}_high_v2")

    print(f"LOW  ({case['low_value']}): value={low_answer.value} conf={low_answer.confidence}")
    print(f"     rationale: {low_answer.rationale}")
    print(f"HIGH ({case['high_value']}): value={high_answer.value} conf={high_answer.confidence}")
    print(f"     rationale: {high_answer.rationale}")

    shifted_as_expected = float(high_answer.value) > float(low_answer.value)
    print(f"Expected: {case['expect']}")
    print(f"Shifted as expected: {shifted_as_expected} (low={low_answer.value}, high={high_answer.value})")
    print()

    results.append({
        "name": case["name"], "dim": case["dim"],
        "low_answer": low_answer.value, "low_rationale": low_answer.rationale,
        "high_answer": high_answer.value, "high_rationale": high_answer.rationale,
        "shifted_as_expected": shifted_as_expected,
    })

print("=" * 70)
print("SUMMARY (controlled re-run)")
print("=" * 70)
n_pass = sum(1 for r in results if r["shifted_as_expected"])
print(f"{n_pass}/{len(results)} test cases shifted in the expected direction")
for r in results:
    status = "PASS" if r["shifted_as_expected"] else "FAIL"
    print(f"  [{status}] {r['name']}: {r['low_answer']} -> {r['high_answer']}")

with open(os.path.join(OUT_DIR, "tier1_controlled_rerun_results.json"), "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)
