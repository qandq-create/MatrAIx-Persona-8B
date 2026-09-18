"""
Step 1.4 -- Canadian geography block. Deliberately NOT a
dimensions_canada.json entry: geography's real cardinality (293 census
divisions, 5,253 census subdivisions, 56,204 dissemination areas,
745,284 postal codes) breaks the small-closed-value-list convention
every dimension relies on, and it's strictly hierarchical (a CSD is
necessarily inside one specific CD), unlike the mostly-independent
dims in dimensions_canada.json. Kept out of persona_dimension_catalog.py
entirely; handled here instead, and appended to the render as an extra
narrative section via templating.py's extra_narrative_sections hook.

Structure: province -> census_division -> census_subdivision are
populated with real, hierarchically weighted StatCan data (derived, not
hand-set -- see cd_csd_hierarchy.json). census_tract, dissemination_area,
and postal_code exist as fields in the returned structure (ready for
Track B) but stay None and are not rendered -- CT/DA need larger
per-province downloads not yet pulled, and postal_code specifically
needs the paid PCCF to be accurate, which doesn't exist yet. This is a
deliberate decision (see TRD-1 Step 1.4 / decision on FSALDU handling),
not an oversight -- never populate postal_code with a fabricated value.
"""
from __future__ import annotations

import json
import random
import re
from pathlib import Path
from typing import Any

_TYPE_SUFFIX_RE = re.compile(r"\s*\([A-Z]{1,6}\)\s*$")


def _clean_name(raw: str) -> str:
    """Strip StatCan's trailing geography-type code (e.g. '(CDR)', '(T)')
    and normalize whitespace -- the real name, not the internal type tag."""
    name = _TYPE_SUFFIX_RE.sub("", raw).strip()
    return re.sub(r"\s+", " ", name)


def load_hierarchy(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sample_geography(rng: random.Random, province: str, hierarchy: dict[str, Any]) -> dict[str, Any]:
    """Hierarchically sample a real CD within the given province, then a
    real CSD within that CD -- each weighted by real 2021 population, not
    independent draws (unlike every dims_canada.json dimension)."""
    cds = hierarchy["census_divisions"]
    csds = hierarchy["census_subdivisions"]

    province_cds = {code: cd for code, cd in cds.items() if cd["province"] == province}
    if not province_cds:
        raise ValueError(f"No census divisions found for province: {province}")
    cd_codes = list(province_cds.keys())
    cd_weights = [province_cds[c]["population"] for c in cd_codes]
    chosen_cd_code = rng.choices(cd_codes, weights=cd_weights, k=1)[0]
    chosen_cd = province_cds[chosen_cd_code]

    cd_csds = {code: csd for code, csd in csds.items() if csd["cd_code"] == chosen_cd_code}
    if cd_csds:
        csd_codes = list(cd_csds.keys())
        csd_weights = [cd_csds[c]["population"] for c in csd_codes]
        # population can be 0 for some unorganized/unpopulated CSDs
        if sum(csd_weights) == 0:
            csd_weights = [1] * len(csd_codes)
        chosen_csd_code = rng.choices(csd_codes, weights=csd_weights, k=1)[0]
        chosen_csd_name = _clean_name(cd_csds[chosen_csd_code]["name"])
    else:
        chosen_csd_name = None

    return {
        "province": province,
        "census_division": _clean_name(chosen_cd["name"]),
        "census_subdivision": chosen_csd_name,
        "census_tract": None,  # needs larger per-province DA-inclusive downloads, not yet pulled
        "dissemination_area": None,  # same
        "fsa": None,  # free/public boundary data exists but not yet wired to a sampling table
        "postal_code": None,  # needs the paid PCCF to be accurate -- deliberately never fabricated
    }


def render_geography_block(geo: dict[str, Any]) -> str:
    """Build a markdown block matching the same '### Heading\\n- Label: value'
    shape dimension sections use, but only for populated fields."""
    label_map = [
        ("province", "Province"),
        ("census_division", "Census Division"),
        ("census_subdivision", "Census Subdivision"),
        ("census_tract", "Census Tract"),
        ("dissemination_area", "Dissemination Area"),
        ("fsa", "Forward Sortation Area"),
        ("postal_code", "Postal Code"),
    ]
    lines = ["### Geography"]
    for key, label in label_map:
        value = geo.get(key)
        if value is not None:
            lines.append(f"- {label}: {value}")
    if len(lines) == 1:
        return ""
    return "\n".join(lines)
