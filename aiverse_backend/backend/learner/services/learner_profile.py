"""
Learner aggregate profile service (LearnerProfileService).

NOTE on module location: this class previously lived in the top-level
``learner/services.py`` module. Because ``learner/services/`` is a regular
Python package (it contains ``__init__.py``), a same-named module file is
shadowed by the package -- so ``learner.services`` resolved to the package and
``LearnerProfileService`` was unreachable (ImportError). It is now a real
submodule of the package, and re-exported lazily from the package ``__init__``
so existing import paths (``from learner.services import
LearnerProfileService``) keep working.
"""
import statistics as stats_lib

from django.contrib.auth import get_user_model

from learner.models import LearnerProfile, ConceptMastery
from learner.services.thresholds import classify_mastery_score
from tracking.models import LearnerEvent

User = get_user_model()


class LearnerProfileService:
    @staticmethod
    def recompute(user_id: int):
        user = User.objects.get(id=user_id)
        profile, _ = LearnerProfile.objects.get_or_create(user=user)
        masteries = ConceptMastery.objects.filter(user=user)

        if masteries.exists():
            scores = [m.mastery_score for m in masteries]
            profile.overall_mastery = round(stats_lib.mean(scores), 4)
            profile.weak_concepts = [
                m.concept_tag for m in masteries
                if classify_mastery_score(m.mastery_score) in {'missing', 'partially_mastered'}
            ]
            profile.strong_concepts = [
                m.concept_tag for m in masteries
                if classify_mastery_score(m.mastery_score) == 'satisfied'
            ]
            # Skill level estimation
            if profile.overall_mastery < 0.35:
                profile.estimated_skill_level = 'beginner'
            elif profile.overall_mastery < 0.65:
                profile.estimated_skill_level = 'intermediate'
            else:
                profile.estimated_skill_level = 'advanced'

        # Engagement score
        events = LearnerEvent.objects.filter(user=user)
        completions = events.filter(event_type__in=['LESSON_COMPLETED', 'VIDEO_COMPLETED', 'CODE_PASSED', 'QUIZ_PASSED']).count()
        total = max(events.count(), 1)
        profile.engagement_score = round(min(1.0, completions / total), 4)

        # Frustration score: ratio of failures to total attempts
        failures = events.filter(event_type__in=['QUIZ_FAILED', 'CODE_FAILED', 'CODE_ERROR']).count()
        attempts = events.filter(event_type__in=['QUIZ_SUBMITTED', 'CODE_SUBMITTED']).count()
        profile.frustration_score = round(failures / max(attempts, 1), 4)

        profile.total_lessons_completed = events.filter(event_type='LESSON_COMPLETED').count()
        profile.total_problems_solved = events.filter(event_type='CODE_PASSED').count()
        profile.total_quizzes_passed = events.filter(event_type='QUIZ_PASSED').count()
        latest_event = events.order_by('-timestamp').first()
        if latest_event:
            profile.last_active = latest_event.timestamp
        profile.save()
        return profile
