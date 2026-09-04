import logging
from django.contrib.auth import get_user_model
from django.db.models import Q
from learner.models import LearnerProfile, ConceptMastery
from learner.services.prerequisites import PrerequisiteResolver
from learner.services.prerequisite_map import PREREQUISITE_MAP
from learner.services.thresholds import (
    classify_mastery_score,
)
from tracking.models import LearnerEvent  # noqa: F401
from .models import Recommendation
from django.utils import timezone
from datetime import timedelta


logger = logging.getLogger(__name__)

User = get_user_model()


DEFAULT_LEARN_PATH_CONCEPTS = [
    'python_ml',
    'statistics',
    'linear_algebra',
    'regression',
    'classification',
]


def _lesson_payload(lesson, *, reason_code=None, reason=None, prerequisite=None):
    if lesson is None:
        return None
    return {
        'id': lesson.id,
        'title': lesson.title,
        'slug': lesson.slug,
        'course_id': lesson.course_id,
        'course_slug': lesson.course.slug if lesson.course_id else None,
        'concept_tag': lesson.concept_tag,
        'difficulty': lesson.difficulty,
        'lesson': {
            'id': lesson.id,
            'title': lesson.title,
            'slug': lesson.slug,
            'course_id': lesson.course_id,
            'course_slug': lesson.course.slug if lesson.course_id else None,
            'difficulty': lesson.difficulty,
            'concept_tag': lesson.concept_tag,
        },
        'reason_code': reason_code,
        'reason': reason,
        'prerequisite': prerequisite,
    }


def _lesson_by_concept(concept_tag, *, limit=1):
    from learn.models import Lesson
    if not concept_tag:
        return []
    return list(Lesson.objects.filter(concept_tag=concept_tag, is_active=True).select_related('course').order_by('difficulty', 'order')[:limit])


def _default_beginner_lessons(user):
    from learn.models import Lesson
    lessons = list(Lesson.objects.filter(is_active=True, difficulty='beginner').select_related('course').order_by('course__title', 'order')[:6])
    if lessons:
        return [_lesson_payload(lesson, reason_code='DEFAULT_PATH', reason='Start with the beginner path to build a strong foundation.') for lesson in lessons]
    # Fallback when no Lesson rows exist (fresh/empty database): expose the
    # canonical beginner concept path at concept level so a brand-new user
    # still gets an honest, non-fabricated starting point.
    return [
        {
            'lesson': None,
            'id': None,
            'title': concept.replace('_', ' ').title(),
            'slug': None,
            'course_slug': None,
            'concept_tag': concept,
            'difficulty': 'beginner',
            'reason_code': 'DEFAULT_PATH_CONCEPT',
            'reason': 'Start with the beginner path to build a strong foundation.',
        }
        for concept in DEFAULT_LEARN_PATH_CONCEPTS
    ]


def _progress_payload(user):
    from learn.models import LessonProgress
    progresses = list(
        LessonProgress.objects.filter(user=user, is_completed=False)
        .select_related('lesson', 'lesson__course')
        .order_by('-last_watched_at', '-watch_time_seconds')[:5]
    )
    rows = []
    for progress in progresses:
        lesson = progress.lesson
        if not lesson or not getattr(lesson, 'is_active', True):
            continue
        last_position = progress.last_position_seconds or progress.watch_time_seconds or 0
        duration = getattr(lesson, 'duration_minutes', 0) or 0
        duration_seconds = duration * 60
        if duration_seconds > 0:
            progress_percent = min(100, max(0, round((last_position / duration_seconds) * 100)))
        else:
            # No duration metadata: fall back to the legacy 10-minute heuristic.
            progress_percent = min(100, max(0, round((last_position / 600.0) * 100))) if last_position else 0
        rows.append({
            'lesson': {
                'id': lesson.id,
                'title': lesson.title,
                'slug': lesson.slug,
                'course_id': lesson.course_id,
                'course_slug': lesson.course.slug if lesson.course_id else None,
                'difficulty': lesson.difficulty,
                'concept_tag': lesson.concept_tag,
            },
            'progress_percent': progress_percent,
            'reason_code': 'CONTINUE_LEARNING',
            'reason': 'You have already completed a significant portion of this lesson and can continue from where you left off.',
        })
    return rows


def _prerequisite_status_payload(user):
    """Per-prerequisite SATISFIED / PARTIALLY_MASTERED / MISSING status.

    Reuses the centralized readiness classifier (learner.services.thresholds)
    so no second threshold exists. No mastery record at all is reported as
    MISSING (the learner has not demonstrated any mastery yet); the raw
    classifier label is preserved in `readiness`.
    """
    masteries = {
        m.concept_tag: m.mastery_score
        for m in ConceptMastery.objects.filter(user=user)
    }
    status_map = {}
    for concept, prereqs in PREREQUISITE_MAP.items():
        rows = []
        for prereq in prereqs:
            score = masteries.get(prereq)
            readiness = classify_mastery_score(score, missing_is_unknown=True)
            if readiness == 'satisfied':
                status = 'SATISFIED'
            elif readiness == 'partially_mastered':
                status = 'PARTIALLY_MASTERED'
            else:
                status = 'MISSING'
            rows.append({
                'concept': prereq,
                'mastery': score,
                'readiness': readiness,
                'status': status,
            })
        if rows:
            status_map[concept] = rows
    return status_map


def build_personalized_learn_response(user):
    from learn.models import Lesson, LessonProgress

    continue_learning = _progress_payload(user)

    default_path = _default_beginner_lessons(user)

    weak_concepts = []
    if hasattr(user, 'learner_profile'):
        profile = user.learner_profile
        weak_concepts = list(profile.weak_concepts or [])
    if not weak_concepts:
        for mastery in ConceptMastery.objects.filter(user=user).order_by('mastery_score')[:5]:
            readiness = classify_mastery_score(mastery.mastery_score)
            if readiness in {'missing', 'partially_mastered'}:
                weak_concepts.append(mastery.concept_tag)

    strengthen_weak_areas = []
    seen = set()
    completed_ids = {
        lp['lesson_id'] for lp in LessonProgress.objects.filter(
            user=user, is_completed=True
        ).values('lesson_id')
    }
    for concept in weak_concepts:
        for lesson in _lesson_by_concept(concept, limit=2):
            key = lesson.id
            if key in seen:
                continue
            seen.add(key)
            # Completed lessons must not resurface as new recommendations.
            if lesson.id in completed_ids or lesson.id in {item['lesson']['id'] for item in continue_learning}:
                continue
            mastery = ConceptMastery.objects.filter(user=user, concept_tag=concept).first()
            reason = 'Your recent performance indicates that this concept is currently one of your weaker areas.'
            reason_code = 'WEAK_CONCEPT'
            if mastery is not None:
                reason = (
                    f"Your current mastery of {concept.replace('_', ' ')} is "
                    f"{mastery.mastery_score:.0%}, which is below the recommended readiness threshold."
                )
            strengthen_weak_areas.append(_lesson_payload(lesson, reason_code=reason_code, reason=reason))

    missing_prerequisites = []
    seen_missing = set()
    for concept in PREREQUISITE_MAP:
        mastery = ConceptMastery.objects.filter(user=user, concept_tag=concept).first()
        if mastery and classify_mastery_score(mastery.mastery_score) in {'satisfied'}:
            continue
        for prereq in PREREQUISITE_MAP[concept]:
            prereq_mastery = ConceptMastery.objects.filter(user=user, concept_tag=prereq).first()
            prereq_readiness = classify_mastery_score(prereq_mastery.mastery_score if prereq_mastery else None, missing_is_unknown=True)
            if prereq_readiness in {'missing', 'unknown', 'partially_mastered'}:
                for lesson in _lesson_by_concept(prereq, limit=1):
                    if lesson.id in seen_missing:
                        continue
                    seen_missing.add(lesson.id)
                    # Do not re-recommend a lesson the user already completed.
                    if lesson.id in completed_ids:
                        continue
                    if prereq_mastery is not None:
                        prereq_reason = (
                            f"Complete {prereq.replace('_', ' ')} before moving to "
                            f"{concept.replace('_', ' ')}. Your current mastery of "
                            f"{prereq.replace('_', ' ')} is {prereq_mastery.mastery_score:.0%}."
                        )
                    else:
                        prereq_reason = (
                            f"Complete {prereq.replace('_', ' ')} before moving to "
                            f"{concept.replace('_', ' ')}."
                        )
                    missing_prerequisites.append(_lesson_payload(
                        lesson,
                        reason_code='MISSING_PREREQUISITE',
                        reason=prereq_reason,
                        prerequisite=concept,
                    ))

    # A partially-mastered prerequisite concept is often also a weak concept;
    # keep each lesson in exactly one section (prerequisite wins).
    missing_ids = {item['id'] for item in missing_prerequisites}
    strengthen_weak_areas = [item for item in strengthen_weak_areas if item['id'] not in missing_ids]

    recommended_for_you = []
    if continue_learning:
        recommended_for_you.extend(continue_learning)
    recommended_for_you.extend(strengthen_weak_areas[:3])
    recommended_for_you.extend(missing_prerequisites[:3])

    candidate_lessons = Lesson.objects.filter(is_active=True).select_related('course').order_by('difficulty', 'order')
    next_best_lesson = None
    if continue_learning:
        next_best_lesson = continue_learning[0]
    elif missing_prerequisites:
        next_best_lesson = missing_prerequisites[0]
    elif strengthen_weak_areas:
        next_best_lesson = strengthen_weak_areas[0]
    else:
        already_surfaced = {item['lesson']['id'] for item in [*continue_learning, *strengthen_weak_areas, *missing_prerequisites]}
        for lesson in candidate_lessons:
            if lesson.id in already_surfaced or lesson.id in completed_ids:
                continue
            if not lesson.concept_tag:
                continue
            if lesson.concept_tag in DEFAULT_LEARN_PATH_CONCEPTS:
                next_best_lesson = _lesson_payload(lesson, reason_code='NEXT_LESSON', reason='This is the next appropriate lesson in the beginner learning path.')
                break
        if next_best_lesson is None and default_path:
            next_best_lesson = default_path[0]

    if not continue_learning and not missing_prerequisites and not strengthen_weak_areas and not recommended_for_you and default_path:
        recommended_for_you = default_path[:3]
    if next_best_lesson is None and default_path:
        next_best_lesson = default_path[0]

    prerequisite_status = _prerequisite_status_payload(user)

    response = {
        'continue_learning': continue_learning,
        'recommended_for_you': recommended_for_you,
        'missing_prerequisites': missing_prerequisites,
        'strengthen_weak_areas': strengthen_weak_areas,
        'next_best_lesson': next_best_lesson,
        'current_learning_path': default_path,
        'default_learning_path': default_path,
        'prerequisite_status': prerequisite_status,
        'recommendation_count': len(recommended_for_you),
        'model_version': 'rule_based_fallback',
        'is_personalised': True,
    }
    return response


class RuleBasedRecommender:
    def __init__(self, user_id: int):
        self.user = User.objects.get(id=user_id)
        self.profile, _ = LearnerProfile.objects.get_or_create(user=self.user)
        self.masteries = {
            m.concept_tag: m
            for m in ConceptMastery.objects.filter(user=self.user)
        }

    def generate_and_cache(self):
        """Generate all recommendation types and save to DB."""
        # Clear stale recommendations
        Recommendation.objects.filter(
            user=self.user,
            generated_at__lt=timezone.now() - timedelta(hours=24)
        ).delete()

        recs = []
        recs += self._recommend_prerequisites()
        recs += self._recommend_next_lessons()
        recs += self._recommend_revision()
        recs += self._recommend_practice_problems()
        recs += self._recommend_continue_learning()

        Recommendation.objects.bulk_create(recs, ignore_conflicts=True)
        return recs

    def _recommend_prerequisites(self):
        recs = []
        for concept, prereqs in PREREQUISITE_MAP.items():
            mastery = self.masteries.get(concept)
            if mastery and classify_mastery_score(mastery.mastery_score) in {"missing", "partially_mastered"} and mastery.quiz_attempts >= 2:
                # User is struggling — recommend prerequisites
                for prereq in prereqs:
                    prereq_mastery = self.masteries.get(prereq)
                    prereq_readiness = classify_mastery_score(
                        prereq_mastery.mastery_score if prereq_mastery else None,
                        missing_is_unknown=True,
                    ) if prereq_mastery else "unknown"
                    if prereq_readiness in {"unknown", "missing", "partially_mastered"}:
                        # Try to find lessons with this concept_tag
                        try:
                            from learn.models import Lesson
                            lessons = Lesson.objects.filter(concept_tag=prereq, is_active=True)[:2]
                            for lesson in lessons:
                                recs.append(Recommendation(
                                    user=self.user,
                                    recommendation_type='prerequisite',
                                    content_type='lesson',
                                    content_id=lesson.id,
                                    score=0.95,
                                    reason=f"You seem to struggle with {concept}. Reviewing {prereq} first will help.",
                                    source='rule_based',
                                ))
                        except ImportError:
                            logger.error("Could not import Lesson model from learn.models")
        return recs

    def _recommend_next_lessons(self):
        recs = []
        completed_ids = set(
            self.user.events.filter(event_type='LESSON_COMPLETED').values_list('content_id', flat=True)
        )
        skill = self.profile.estimated_skill_level
        difficulty_map = {'beginner': ['beginner'], 'intermediate': ['beginner','intermediate'], 'advanced': ['intermediate','advanced']}
        allowed_difficulties = difficulty_map.get(skill, ['beginner'])

        try:
            from learn.models import Lesson
            lessons = Lesson.objects.filter(
                difficulty__in=allowed_difficulties,
                is_active=True
            ).exclude(id__in=completed_ids).order_by('order')[:5]

            for i, lesson in enumerate(lessons):
                recs.append(Recommendation(
                    user=self.user,
                    recommendation_type='next_lesson',
                    content_type='lesson',
                    content_id=lesson.id,
                    score=0.8 - (i * 0.05),
                    reason=f"Next lesson in your {skill}-level path.",
                    source='rule_based',
                ))
        except ImportError:
            logger.error("Could not import Lesson model from learn.models")
        return recs

    def _recommend_revision(self):
        recs = []
        for tag, mastery in self.masteries.items():
            readiness = classify_mastery_score(mastery.mastery_score)
            if readiness == "partially_mastered" and mastery.quiz_attempts >= 1:
                try:
                    from learn.models import Lesson
                    lessons = Lesson.objects.filter(concept_tag=tag, is_active=True)[:1]
                    if not lessons.exists():
                        continue
                    for lesson in lessons:
                        recs.append(Recommendation(
                            user=self.user,
                            recommendation_type='revision',
                            content_type='lesson',
                            content_id=lesson.id,
                            score=0.7,
                            reason=f"You scored {mastery.mastery_score:.0%} on {tag}. A revision will strengthen this.",
                            source='rule_based',
                        ))
                except ImportError:
                    logger.error("Could not import Lesson model from learn.models")
        return recs

    def _recommend_practice_problems(self):
        recs = []
        strong = self.profile.strong_concepts
        for concept in strong[:3]:
            try:
                from learn.models import CodingProblem
                # Exclude already solved problems
                solved_ids = self.user.events.filter(
                    content_type='problem', 
                    event_type='CODE_PASSED'
                ).values_list('content_id', flat=True)
                
                problems = CodingProblem.objects.filter(
                    concept_tag=concept, 
                    is_active=True
                ).exclude(id__in=solved_ids)[:2]
                
                for problem in problems:
                    recs.append(Recommendation(
                        user=self.user,
                        recommendation_type='coding_problem',
                        content_type='problem',
                        content_id=problem.id,
                        score=0.75 + (0.05 if concept in strong[:1] else 0),
                        reason=f"You're strong in {concept}. Level up with a harder coding challenge.",
                        source='rule_based',
                    ))
            except ImportError:
                logger.error("Could not import CodingProblem model from learn.models")
        return recs

    def _recommend_continue_learning(self):
        """Logic for 'Continue Where You Left Off' on the Dashboard."""
        recs = []
        last_event = self.user.events.filter(
            event_type='LESSON_OPENED'
        ).order_by('-timestamp').first()

        if last_event and last_event.content_type == 'lesson':
            # Check if it was completed
            is_completed = self.user.events.filter(
                content_type='lesson',
                content_id=last_event.content_id,
                event_type='LESSON_COMPLETED'
            ).exists()

            if not is_completed:
                recs.append(Recommendation(
                    user=self.user,
                    recommendation_type='next_lesson',
                    content_type='lesson',
                    content_id=last_event.content_id,
                    score=0.99, # Highest priority
                    reason="Resume your last lesson.",
                    source='rule_based',
                ))
        return recs
