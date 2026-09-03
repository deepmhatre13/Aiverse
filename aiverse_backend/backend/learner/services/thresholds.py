"""Centralized deterministic thresholds for learner mastery and readiness.

These values are intentionally explainable and reused across the learner stack
instead of being duplicated across views, services, and serializers.
"""

from __future__ import annotations

# Preserve the repo's existing canonical threshold semantics: 0.75+ is satisfied,
# anything above 0.30 is partial, and below that is missing. This keeps the
# current learner logic and tests stable while still exposing the richer
# readiness labels that Phase 2 needs.
SATISFIED_MASTERY = 0.75
PARTIALLY_MASTERED_MASTERY = 0.30
WEAK_MASTERY = 0.40


def classify_mastery_score(score: float | None, *, missing_is_unknown: bool = False) -> str:
    """Return the canonical readiness label for a mastery score.

    Canonical values are:
    - satisfied
    - partially_mastered
    - missing
    - unknown
    """
    if score is None:
        return "unknown" if missing_is_unknown else "missing"
    if score >= SATISFIED_MASTERY:
        return "satisfied"
    if score >= PARTIALLY_MASTERED_MASTERY:
        return "partially_mastered"
    return "missing"


def legacy_status_for(score: float | None, *, missing_is_unknown: bool = False) -> str:
    """Return the legacy status string used by existing callers/tests."""
    readiness = classify_mastery_score(score, missing_is_unknown=missing_is_unknown)
    aliases = {
        "satisfied": "satisfied",
        "partially_mastered": "partial",
        "missing": "missing",
        "unknown": "unknown",
    }
    return aliases.get(readiness, readiness)
