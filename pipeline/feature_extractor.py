"""
IMPORTANT: Personal/demographic fields (city, school_type, has_mentor)
are intentionally NOT extracted as features. They are used only in
fairness_audit.py for bias detection.
"""

import numpy as np
from typing import Dict, List, Any, Optional
from config import (
    OLYMPIAD_LEVEL_MAP,
    OLYMPIAD_RESULT_MAP,
    PROJECT_ROLE_MAP,
    PROJECT_TYPES,
    STRUCTURED_FEATURES,
    CURRENT_YEAR,
)


def extract_features(candidate: Dict[str, Any]) -> np.ndarray:
    features = {}
    edu = candidate.get("education", {})
    features["f_gpa"] = _extract_gpa(edu)
    features["f_olympiad_count"] = _extract_olympiad_count(edu)
    features["f_olympiad_max_level"] = _extract_olympiad_max_level(edu)
    features["f_olympiad_has_prize"] = _extract_olympiad_has_prize(edu)
    features["f_courses_count"] = _extract_courses_count(edu)
    features["f_courses_completed_ratio"] = _extract_courses_completed_ratio(edu)

    exp = candidate.get("experience", {})
    projects = exp.get("projects", [])
    features["f_project_count"] = _extract_project_count(projects)
    features["f_founder_ratio"] = _extract_founder_ratio(projects)
    features["f_has_technical_project"] = _extract_has_project_type(projects, "technical")
    features["f_has_social_project"] = _extract_has_project_type(projects, "social")
    features["f_project_diversity"] = _extract_project_diversity(projects)
    features["f_max_team_size"] = _extract_max_team_size(projects)
    features["f_solo_project_count"] = _extract_solo_project_count(projects)

    olympiads = edu.get("olympiads", [])
    features["f_role_progression"] = _extract_role_progression(projects)
    features["f_scope_progression"] = _extract_scope_progression(projects, olympiads)
    features["f_skill_diversity_growth"] = _extract_skill_diversity_growth(projects)
    features["f_activity_years_span"] = _extract_activity_years_span(projects, olympiads)
    features["f_persistence_signal"] = _extract_persistence_signal(olympiads, projects)
    features["f_activity_recency"] = _extract_activity_recency(projects, olympiads)

    meta = candidate.get("bot_metadata", {})
    features["f_session_duration"] = meta.get("session_duration_sec", 0)
    features["f_essay_typing_duration"] = meta.get("essay_typing_duration_sec", 0)
    features["f_total_pauses"] = _extract_total_pauses(meta)

    vector = np.array(
        [features[name] for name in STRUCTURED_FEATURES],
        dtype=np.float32,
    )
    return vector


def extract_features_dict(candidate: Dict[str, Any]) -> Dict[str, float]:
    """
    Same as extract_features but returns a named dict (useful for debugging).
    """
    vector = extract_features(candidate)
    return dict(zip(STRUCTURED_FEATURES, vector.tolist()))


# Education helpers
def _extract_gpa(edu: dict) -> float:
    gpa = edu.get("gpa", 0.0)
    return float(np.clip(gpa, 0.0, 5.0))


def _extract_olympiad_count(edu: dict) -> int:
    return len(edu.get("olympiads", []))


def _extract_olympiad_max_level(edu: dict) -> int:
    olympiads = edu.get("olympiads", [])
    if not olympiads:
        return 0
    levels = [OLYMPIAD_LEVEL_MAP.get(o.get("level", ""), 0) for o in olympiads]
    return max(levels)


def _extract_olympiad_has_prize(edu: dict) -> int:
    olympiads = edu.get("olympiads", [])
    for o in olympiads:
        if OLYMPIAD_RESULT_MAP.get(o.get("result", ""), 0) >= 2:
            return 1
    return 0


def _extract_courses_count(edu: dict) -> int:
    return len(edu.get("courses", []))


def _extract_courses_completed_ratio(edu: dict) -> float:
    courses = edu.get("courses", [])
    if not courses:
        return 0.0
    completed = sum(1 for c in courses if c.get("completed", False))
    return completed / len(courses)


# Experience helpers

def _extract_project_count(projects: list) -> int:
    return len(projects)


def _extract_founder_ratio(projects: list) -> float:
    if not projects:
        return 0.0
    founder_count = sum(
        1 for p in projects
        if p.get("role", "") in ("founder", "co_founder")
    )
    return founder_count / len(projects)


def _extract_has_project_type(projects: list, project_type: str) -> int:
    for p in projects:
        if p.get("type", "") == project_type:
            return 1
    return 0


def _extract_project_diversity(projects: list) -> int:
    types = set(p.get("type", "other") for p in projects)
    return len(types)


def _extract_max_team_size(projects: list) -> int:
    if not projects:
        return 0
    sizes = [p.get("team_size", 1) for p in projects]
    return max(sizes)


def _extract_solo_project_count(projects: list) -> int:
    return sum(1 for p in projects if p.get("team_size", 1) == 1)


# Trajectory helpers

def _extract_role_progression(projects: list) -> float:
    """
    Measures how candidate's role grew over time.
    Sorted by year, compute the slope of role values.
    Higher = candidate progressed from participant to founder.
    """
    if len(projects) < 2:
        return 0.0

    sorted_projects = sorted(projects, key=lambda p: p.get("year", 0))
    roles = [PROJECT_ROLE_MAP.get(p.get("role", "participant"), 0) for p in sorted_projects]

    # Simple: difference between average role in later half vs earlier half
    mid = len(roles) // 2
    early_avg = np.mean(roles[:mid]) if mid > 0 else roles[0]
    late_avg = np.mean(roles[mid:])
    return float(late_avg - early_avg)


def _extract_scope_progression(projects: list, olympiads: list) -> float:
    """
    Measures growth in scope: team sizes growing, olympiad levels growing.
    """
    progression = 0.0

    # Project scope: team size growth
    if len(projects) >= 2:
        sorted_p = sorted(projects, key=lambda p: p.get("year", 0))
        sizes = [p.get("team_size", 1) for p in sorted_p]
        mid = len(sizes) // 2
        early = np.mean(sizes[:mid]) if mid > 0 else sizes[0]
        late = np.mean(sizes[mid:])
        if early > 0:
            progression += (late - early) / early  # relative growth

    # Olympiad scope: level growth
    if len(olympiads) >= 2:
        sorted_o = sorted(olympiads, key=lambda o: o.get("year", 0))
        levels = [OLYMPIAD_LEVEL_MAP.get(o.get("level", ""), 0) for o in sorted_o]
        progression += levels[-1] - levels[0]

    return float(progression)


def _extract_skill_diversity_growth(projects: list) -> int:
    """
    How many distinct skill types the candidate acquired over time.
    """
    if not projects:
        return 0
    types_by_year = {}
    for p in projects:
        year = p.get("year", 0)
        ptype = p.get("type", "other")
        if year not in types_by_year:
            types_by_year[year] = set()
        types_by_year[year].add(ptype)

    # Count cumulative new types over years
    seen = set()
    growth = 0
    for year in sorted(types_by_year.keys()):
        new_types = types_by_year[year] - seen
        growth += len(new_types)
        seen.update(new_types)
    return growth


def _extract_activity_years_span(projects: list, olympiads: list) -> int:
    """
    How many years between first and last recorded activity.
    """
    years = []
    for p in projects:
        if "year" in p:
            years.append(p["year"])
    for o in olympiads:
        if "year" in o:
            years.append(o["year"])

    if len(years) < 2:
        return 0
    return max(years) - min(years)


def _extract_persistence_signal(olympiads: list, projects: list) -> int:
    """
    Did the candidate retry something after a failure?
    Signals: participated in olympiad again after non-prize result,
    or continued a project type after a setback.
    """
    # Check olympiads: same subject, later year, after a non-prize
    subjects_failed = {}
    for o in sorted(olympiads, key=lambda x: x.get("year", 0)):
        subj = o.get("subject", "")
        result = o.get("result", "")
        year = o.get("year", 0)

        if subj in subjects_failed and year > subjects_failed[subj]:
            return 1  # Retried after failure

        if OLYMPIAD_RESULT_MAP.get(result, 0) < 2:  # Not a prize
            if subj not in subjects_failed:
                subjects_failed[subj] = year

    # Check projects: multiple projects of same type across years
    type_years = {}
    for p in projects:
        ptype = p.get("type", "other")
        year = p.get("year", 0)
        if ptype not in type_years:
            type_years[ptype] = []
        type_years[ptype].append(year)

    for ptype, years in type_years.items():
        if len(years) >= 2 and max(years) - min(years) >= 1:
            return 1  # Sustained effort in same domain

    return 0


def _extract_activity_recency(projects: list, olympiads: list) -> int:
    """
    How recent is the latest activity? Lower = more recent = better.
    Returns years since last activity.
    """
    years = []
    for p in projects:
        if "year" in p:
            years.append(p["year"])
    for o in olympiads:
        if "year" in o:
            years.append(o["year"])

    if not years:
        return 5  # No activity at all — max penalty
    return CURRENT_YEAR - max(years)


# ============================================================
# Bot metadata helpers
# ============================================================

def _extract_total_pauses(meta: dict) -> int:
    """Total number of significant pauses during bot session."""
    pauses = meta.get("pauses", [])
    return len(pauses)


# ============================================================
# Batch extraction
# ============================================================

def extract_batch(candidates: List[Dict[str, Any]]) -> np.ndarray:
    """
    Extract features for a list of candidates.

    Returns:
        np.ndarray of shape (n_candidates, n_features)
    """
    return np.array([extract_features(c) for c in candidates])


# ============================================================
# CLI test
# ============================================================

if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) < 2:
        print("Usage: python feature_extractor.py <candidate.json>")
        sys.exit(1)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        candidate = json.load(f)

    features = extract_features_dict(candidate)
    print("\n=== Extracted Features ===")
    for name, value in features.items():
        print(f"  {name:35s} = {value:.4f}")
    print(f"\nTotal features: {len(features)}")
