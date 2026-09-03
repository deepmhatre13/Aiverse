"""
Prerequisite resolution service.

Canonical, reusable resolver that determines, for a requested concept, the
status of each declared prerequisite (satisfied / partially mastered /
missing) and which prerequisite the learner should tackle next.

It reuses the existing concept prerequisite map (recommendations.services.
PREREQUISITE_MAP) and ConceptMastery records as the single source of truth --
no duplicate data and no new models.
"""
import logging
from typing import Dict, List

from learner.models import ConceptMastery
from learner.services.thresholds import (
    classify_mastery_score,
    legacy_status_for,
)

logger = logging.getLogger(__name__)

# Reuse the single existing source of truth for concept -> prerequisite edges.
from recommendations.services import PREREQUISITE_MAP  # noqa: E402


class PrerequisiteResolver:
    """Resolve prerequisite status for a concept given a user's masteries."""

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.masteries: Dict[str, ConceptMastery] = {
            m.concept_tag: m
            for m in ConceptMastery.objects.filter(user_id=user_id)
        }

    def _score(self, concept_tag: str) -> float | None:
        mastery = self.masteries.get(concept_tag)
        return mastery.mastery_score if mastery else None

    @staticmethod
    def prereqs_for(concept_tag: str) -> List[str]:
        """Declared prerequisites for a concept (may be empty -> foundational)."""
        return list(PREREQUISITE_MAP.get(concept_tag, []))

    def resolve(self, concept_tag: str) -> Dict:
        """Return prerequisite status + recommended next step for ``concept_tag``.

        Returns a dict with:
          - concept: the requested concept
          - prerequisites: list of {concept, mastery, readiness, status} sorted as
            declared in PREREQUISITE_MAP
          - recommended_next: missing prerequisites ordered by ascending
            mastery (weakest gap first), i.e. what to learn next
        """
        prereqs = self.prereqs_for(concept_tag)
        statuses: List[Dict] = []
        missing: List[str] = []

        for tag in prereqs:
            score = self._score(tag)
            readiness = classify_mastery_score(score, missing_is_unknown=True)
            status = legacy_status_for(score, missing_is_unknown=True)
            if readiness in {"missing", "unknown"}:
                missing.append(tag)
            statuses.append({
                "concept": tag,
                "mastery": round(score, 4) if score is not None else 0.0,
                "readiness": readiness,
                "status": status,
            })

        # Recommend the weakest missing prerequisite first.
        missing.sort(key=lambda t: self._score(t) if self._score(t) is not None else 0.0)

        return {
            "concept": concept_tag,
            "prerequisites": statuses,
            "recommended_next": missing,
        }


def resolve_prerequisites(user_id: int, concept_tag: str) -> Dict:
    """Convenience wrapper around :class:`PrerequisiteResolver`."""
    return PrerequisiteResolver(user_id).resolve(concept_tag)
