"""
Step 1.2 item 3 -- generate a small batch of Canadian (Choice B) personas.

Mechanism (per the session's agreed scope):
- Every dim in dimensions_canada.json (99 dims) is sampled uniform-random
  -- none of them are calibrated yet; real calibration waits for Track B's
  licensed PRIZM5/Vividata data (decision: "we can do it later when it's
  needed").
- Four Choice A demographic dims (age_bracket, demo_marital_status,
  demo_household_income, highest_education) are sampled using the real
  weighted marginals in calibration_canada.json, derived from StatCan
  Census data.
- geography is a plain top-level structure (not a catalog dim --
  geography breaks the dimension-catalog convention per Step 1.4):
  province, census_division, and census_subdivision are populated via
  real hierarchical population-weighted sampling (a CD chosen within
  the province, then a CSD chosen within that CD, both real StatCan
  data -- see geography_canada.py and cd_csd_hierarchy.json).
  census_tract, dissemination_area, and postal_code exist as fields but
  stay None and unrendered -- CT/DA need larger per-province downloads
  not yet pulled, and postal_code specifically needs the paid PCCF to
  be accurate. Deliberate, not an oversight.
- A handful of core Choice A identity dims round out the persona
  (uniform-random, no calibration data for these yet).
- All dims (calibrated or not) are independent draws -- no cross-
  dimension correlation. This is the defined "lightweight calibration"
  tradeoff (marginals only), not a bug.

Each generated persona is rendered through MatrAIx's real Jinja
templating pipeline via the catalog_path merge fix (commit 621ea51),
proving the actual pipeline mechanics work end-to-end, not a bespoke
parallel renderer.
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "environment" / "agents"))

from matraix.agents.persona.loader import Persona  # noqa: E402
from matraix.agents.persona.templating import (  # noqa: E402
    default_templates_dir,
    render_persona_template,
    resolve_persona_template,
    PERSONA_SYSTEM_TEMPLATE,
)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from geography_canada import load_hierarchy, sample_geography, render_geography_block  # noqa: E402

SCHEMA_DIR = REPO_ROOT / "persona" / "schema"
DIMENSIONS_A = SCHEMA_DIR / "dimensions.json"
DIMENSIONS_B = SCHEMA_DIR / "dimensions_canada.json"
CALIBRATION = SCHEMA_DIR / "calibration_canada.json"
CD_CSD_HIERARCHY = SCHEMA_DIR / "cd_csd_hierarchy.json"
OUT_DIR = REPO_ROOT / "persona" / "datasets" / "canada-persona-dev-sample"

# Core Choice A identity dims to round out the persona -- uniform-random,
# no calibration data exists for these yet.
CORE_IDENTITY_DIM_IDS = ["gender_identity", "demo_generation"]

N_PERSONAS = 20
SEED = 20260918  # today's date, for a reproducible batch


def load_catalog(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))["dimensions"]


def weighted_choice(rng: random.Random, probs: dict[str, float]) -> str:
    values, weights = zip(*probs.items())
    return rng.choices(values, weights=weights, k=1)[0]


def build_persona(
    rng: random.Random, catalog_by_id: dict[str, dict], calibration: dict, hierarchy: dict
) -> dict:
    dims: dict[str, str] = {}

    # 103 Choice B dims: uniform-random unless calibrated (the 8 that are
    # -- age/marital/income/education from Step 1.2, plus the 4 real
    # ethnicity/language dims from Step 1.3 -- get overwritten below.
    b_dims = load_catalog(DIMENSIONS_B)
    for d in b_dims:
        dims[d["id"]] = rng.choice(d["values"])

    # Calibrated dims (8 total): weighted from real StatCan marginals.
    for dim_id, probs in calibration["dimensions"].items():
        dims[dim_id] = weighted_choice(rng, probs)

    # A few core identity dims: uniform-random.
    for dim_id in CORE_IDENTITY_DIM_IDS:
        meta = catalog_by_id.get(dim_id)
        if meta:
            dims[dim_id] = rng.choice(meta["values"])

    province = weighted_choice(rng, calibration["province"])
    geography = sample_geography(rng, province, hierarchy)

    return {"dims": dims, "geography": geography}


def main() -> None:
    rng = random.Random(SEED)
    catalog_a = load_catalog(DIMENSIONS_A)
    catalog_by_id = {d["id"]: d for d in catalog_a}
    calibration = json.loads(CALIBRATION.read_text(encoding="utf-8"))
    hierarchy = load_hierarchy(CD_CSD_HIERARCHY)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    template_path = resolve_persona_template(None, None, PERSONA_SYSTEM_TEMPLATE)

    for i in range(1, N_PERSONAS + 1):
        persona_id = f"ca_{i:04d}"
        built = build_persona(rng, catalog_by_id, calibration, hierarchy)

        persona_yaml = {
            "persona_id": persona_id,
            "version": "canada-concept-v0.1",
            "geography": built["geography"],  # plain field, not a catalog dim
            "dimensions": built["dims"],
        }
        yaml_path = OUT_DIR / f"persona_{persona_id}.json"
        yaml_path.write_text(json.dumps(persona_yaml, indent=2), encoding="utf-8")

        # Render the first 3 through the real Jinja pipeline as a proof point.
        if i <= 3:
            persona = Persona(
                persona_path=yaml_path,
                schema_version="v2",
                data=persona_yaml,
                persona_id=persona_id,
                version=persona_yaml["version"],
                display_name=f"persona-{persona_id}",
                summary=None,
                system_prompt=None,
            )
            geo_block = render_geography_block(built["geography"])
            rendered = render_persona_template(
                template_path,
                persona,
                catalog_path=(str(DIMENSIONS_A), str(DIMENSIONS_B)),
                extra_narrative_sections=[geo_block] if geo_block else None,
            )
            (OUT_DIR / f"rendered_{persona_id}.md").write_text(rendered, encoding="utf-8")

    print(f"Generated {N_PERSONAS} personas in {OUT_DIR}")
    print("Rendered 3 sample identity prompts via the real Jinja pipeline.")


if __name__ == "__main__":
    main()
