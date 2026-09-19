"""
V0 Tier 2 -- face validity against already-published Canadian findings.
Generate small batches of Choice B personas (real demographic
calibration, uncalibrated psychographics/purchase dims -- what's built
now), run equivalent questions through the real local model, compare
the simulated aggregate against real published numbers. Directional
agreement is the bar, not exact match -- small N here (8 per group)
means this tests direction/magnitude plausibility, not precision.

Three published findings, each with a real source:
1. Private label -- 62% of Canadians buy store brands to save money
   (Retail Council of Canada / Leger, via NOW Toronto reporting).
2. Sales/promotion responsiveness -- 76% of Canadians are buying items
   on sale (Eagle Eye Canada/US grocery loyalty survey).
3. Regional alcohol preference -- Quebec: wine 43.5% of alcohol sales
   (wine-dominant); rest of Canada: beer 36.0%, wine 31.4%
   (beer-dominant) (CBRE Canada / Statista). Tests real geography
   sampling, not just purchase-behavior dims.
"""
from __future__ import annotations

import copy
import json
import os
import random
import sys
from collections import Counter
from datetime import datetime, timezone

REPO_ROOT = os.path.expanduser("~/simulator/MatrAIx")
sys.path.insert(0, os.path.join(REPO_ROOT, "application/playground"))
sys.path.insert(0, os.path.join(REPO_ROOT, "packages/playground/src"))
sys.path.insert(0, os.path.join(REPO_ROOT, "src"))
sys.path.insert(0, os.path.join(REPO_ROOT, "environment/agents"))
sys.path.insert(0, os.path.join(REPO_ROOT, "persona/schema"))

from backend.service.survey_types import SurveyEvalConfig, SurveyInstrument, SurveyQuestion
from playground.inprocess.survey_eval import InprocessSurveyEvalRunner
from playground.types import Persona as EvalPersona
from generate_canada_personas import (
    build_persona, load_catalog, DIMENSIONS_A, CALIBRATION, CD_CSD_HIERARCHY,
)
from geography_canada import load_hierarchy

CATALOG_PATH = (
    os.path.join(REPO_ROOT, "persona/schema/dimensions.json"),
    os.path.join(REPO_ROOT, "persona/schema/dimensions_canada.json"),
)
OUT_DIR = os.path.join(REPO_ROOT, "persona/datasets/canada-persona-dev-sample")

config = SurveyEvalConfig(persona_model="openai/qwen3:8b-lowvram")
runner = InprocessSurveyEvalRunner()

N_PER_GROUP = 8
SEED = 20260919


def ask(persona_dict: dict, question: SurveyQuestion, label: str):
    instrument = SurveyInstrument(
        id=f"tier2-{question.id}", title=f"Tier 2: {question.id}",
        description="V0 Tier 2 face validity test.",
        ask_rationale=True, ask_confidence=True, questions=[question],
    )
    yaml_path = os.path.join(OUT_DIR, f"_tier2_tmp_{label}.json")
    with open(yaml_path, "w", encoding="utf-8") as f:
        json.dump(persona_dict, f)
    eval_persona = EvalPersona(id=f"tier2-{label}", name=label, source="mock")
    result = runner(
        eval_persona, instrument, config=config,
        created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        persona_yaml_path=yaml_path, on_event=None, job_dir=None,
        catalog_path=CATALOG_PATH,
    )
    os.remove(yaml_path)
    return result.answers[0]


def main():
    rng = random.Random(SEED)
    catalog_a = load_catalog(DIMENSIONS_A)
    catalog_by_id = {d["id"]: d for d in catalog_a}
    calibration = json.loads(open(os.path.join(REPO_ROOT, "persona/schema/calibration_canada.json")).read())
    hierarchy = load_hierarchy(os.path.join(REPO_ROOT, "persona/schema/cd_csd_hierarchy.json"))

    all_results = {}

    # --- Finding 1: private label (62% buy store brands to save money) ---
    print("=" * 70)
    print("Finding 1: Private label -- published 62% buy store brands to save money")
    print("=" * 70)
    q1 = SurveyQuestion(
        id="q_private_label",
        prompt=(
            "Do you regularly buy store-brand (private label) groceries instead of "
            "national brands specifically to save money? Answer Yes or No."
        ),
        type="single_choice", options=["Yes", "No"], construct="private_label", required=True,
    )
    f1_answers = []
    for i in range(N_PER_GROUP):
        built = build_persona(rng, catalog_by_id, calibration, hierarchy)
        persona_yaml = {"persona_id": f"t2f1_{i}", "version": "v0.1",
                         "geography": built["geography"], "dimensions": built["dims"]}
        ans = ask(persona_yaml, q1, f"f1_{i}")
        f1_answers.append(ans.value)
        print(f"  [{i}] {ans.value} -- {ans.rationale[:100]}")
    pct_yes = sum(1 for a in f1_answers if str(a).strip().lower() == "yes") / len(f1_answers)
    print(f"Simulated: {pct_yes:.0%} Yes  |  Published: 62%")
    all_results["private_label"] = {"answers": f1_answers, "simulated_pct_yes": pct_yes, "published_pct": 0.62}

    # --- Finding 2: sales/promotion responsiveness (76% buying items on sale) ---
    print("\n" + "=" * 70)
    print("Finding 2: Sales responsiveness -- published 76% are buying items on sale")
    print("=" * 70)
    q2 = SurveyQuestion(
        id="q_sales_response",
        prompt=(
            "Over the past month, have you specifically bought grocery items because "
            "they were on sale or discounted? Answer Yes or No."
        ),
        type="single_choice", options=["Yes", "No"], construct="promotion_response", required=True,
    )
    f2_answers = []
    for i in range(N_PER_GROUP):
        built = build_persona(rng, catalog_by_id, calibration, hierarchy)
        persona_yaml = {"persona_id": f"t2f2_{i}", "version": "v0.1",
                         "geography": built["geography"], "dimensions": built["dims"]}
        ans = ask(persona_yaml, q2, f"f2_{i}")
        f2_answers.append(ans.value)
        print(f"  [{i}] {ans.value} -- {ans.rationale[:100]}")
    pct_yes2 = sum(1 for a in f2_answers if str(a).strip().lower() == "yes") / len(f2_answers)
    print(f"Simulated: {pct_yes2:.0%} Yes  |  Published: 76%")
    all_results["sales_response"] = {"answers": f2_answers, "simulated_pct_yes": pct_yes2, "published_pct": 0.76}

    # --- Finding 3: regional alcohol preference (Quebec wine vs rest-of-Canada beer) ---
    print("\n" + "=" * 70)
    print("Finding 3: Regional alcohol preference -- Quebec wine-dominant, rest-of-Canada beer-dominant")
    print("=" * 70)
    q3 = SurveyQuestion(
        id="q_alcohol_pref",
        prompt="If you had to pick one, which do you prefer: beer or wine?",
        type="single_choice", options=["Beer", "Wine"], construct="alcohol_preference", required=True,
    )

    def force_province(built, province_name):
        built["geography"]["province"] = province_name
        built["geography"]["census_division"] = None
        built["geography"]["census_subdivision"] = None
        return built

    qc_answers, on_answers = [], []
    for i in range(N_PER_GROUP):
        built = build_persona(rng, catalog_by_id, calibration, hierarchy)
        built = force_province(built, "Quebec")
        persona_yaml = {"persona_id": f"t2f3_qc_{i}", "version": "v0.1",
                         "geography": built["geography"], "dimensions": built["dims"]}
        ans = ask(persona_yaml, q3, f"f3_qc_{i}")
        qc_answers.append(ans.value)
        print(f"  QC[{i}] {ans.value} -- {ans.rationale[:100]}")
    for i in range(N_PER_GROUP):
        built = build_persona(rng, catalog_by_id, calibration, hierarchy)
        built = force_province(built, "Ontario")
        persona_yaml = {"persona_id": f"t2f3_on_{i}", "version": "v0.1",
                         "geography": built["geography"], "dimensions": built["dims"]}
        ans = ask(persona_yaml, q3, f"f3_on_{i}")
        on_answers.append(ans.value)
        print(f"  ON[{i}] {ans.value} -- {ans.rationale[:100]}")

    qc_wine_pct = sum(1 for a in qc_answers if str(a).strip().lower() == "wine") / len(qc_answers)
    on_wine_pct = sum(1 for a in on_answers if str(a).strip().lower() == "wine") / len(on_answers)
    print(f"Quebec simulated: {qc_wine_pct:.0%} Wine  |  Published: wine-dominant (43.5% of sales, vs beer nationally lower)")
    print(f"Ontario simulated: {on_wine_pct:.0%} Wine  |  Published: beer-dominant (beer 36.0% vs wine 31.4% nationally)")
    all_results["regional_alcohol"] = {
        "qc_answers": qc_answers, "on_answers": on_answers,
        "qc_wine_pct": qc_wine_pct, "on_wine_pct": on_wine_pct,
    }

    with open(os.path.join(OUT_DIR, "tier2_face_validity_results.json"), "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)
    print("\nDone.")


if __name__ == "__main__":
    main()
