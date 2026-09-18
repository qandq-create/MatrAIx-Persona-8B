"""
V0 Tier 0 -- statistical composition check. Generate a larger sample
(not written to disk as individual persona files -- this is a pure
sampling-distribution check, not a persona-batch build) and verify the
aggregate distribution of the 8 really-calibrated dims matches
calibration_canada.json's target marginals (StatCan-derived) within
sampling tolerance. Prerequisite check, not yet "business value" -- if
this fails, nothing built on top of it can be trusted.
"""
from __future__ import annotations

import json
import random
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "environment" / "agents"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from generate_canada_personas import (  # noqa: E402
    build_persona, load_catalog, DIMENSIONS_A, CALIBRATION, CD_CSD_HIERARCHY, SEED,
)
from geography_canada import load_hierarchy  # noqa: E402

N_SAMPLES = 300


def main() -> None:
    rng = random.Random(SEED + 1)  # distinct from the persona-batch seed
    catalog_a = load_catalog(DIMENSIONS_A)
    catalog_by_id = {d["id"]: d for d in catalog_a}
    calibration = json.loads(CALIBRATION.read_text(encoding="utf-8"))
    hierarchy = load_hierarchy(CD_CSD_HIERARCHY)

    tallies: dict[str, Counter] = {dim: Counter() for dim in calibration["dimensions"]}
    province_tally = Counter()

    for _ in range(N_SAMPLES):
        built = build_persona(rng, catalog_by_id, calibration, hierarchy)
        for dim in tallies:
            tallies[dim][built["dims"][dim]] += 1
        province_tally[built["geography"]["province"]] += 1

    max_abs_diff_overall = 0.0
    print(f"N = {N_SAMPLES}\n")
    for dim, target_probs in calibration["dimensions"].items():
        print(f"=== {dim} ===")
        print(f"{'value':<35} {'target':>8} {'observed':>9} {'diff':>7}")
        max_diff = 0.0
        for value, target_p in target_probs.items():
            observed_p = tallies[dim][value] / N_SAMPLES
            diff = observed_p - target_p
            max_diff = max(max_diff, abs(diff))
            print(f"{value:<35} {target_p:>8.4f} {observed_p:>9.4f} {diff:>+7.4f}")
        max_abs_diff_overall = max(max_abs_diff_overall, max_diff)
        print(f"  max abs diff: {max_diff:.4f}\n")

    print("=== province (also calibrated, separate from dimensions block) ===")
    print(f"{'value':<30} {'target':>8} {'observed':>9} {'diff':>7}")
    prov_max_diff = 0.0
    for value, target_p in calibration["province"].items():
        observed_p = province_tally[value] / N_SAMPLES
        diff = observed_p - target_p
        prov_max_diff = max(prov_max_diff, abs(diff))
        print(f"{value:<30} {target_p:>8.4f} {observed_p:>9.4f} {diff:>+7.4f}")
    print(f"  max abs diff: {prov_max_diff:.4f}\n")

    overall_max = max(max_abs_diff_overall, prov_max_diff)
    print(f"Overall max abs diff across all calibrated dims + province: {overall_max:.4f}")
    # Rough tolerance check: with N=300 and the smallest real target
    # probabilities in the ~0.001-0.01 range (e.g. Inuit at 0.0019), some
    # sampling noise on rare categories is expected and not a bug -- flag
    # only if a *large-probability* category is meaningfully off.
    print("\nLargest-probability values per dim (where deviation would matter most):")
    for dim, target_probs in calibration["dimensions"].items():
        top_value = max(target_probs, key=target_probs.get)
        target_p = target_probs[top_value]
        observed_p = tallies[dim][top_value] / N_SAMPLES
        print(f"  {dim}: {top_value!r} target={target_p:.4f} observed={observed_p:.4f} diff={observed_p-target_p:+.4f}")


if __name__ == "__main__":
    main()
