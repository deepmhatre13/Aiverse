"""Phase 3 tests: Personalized Learn experience.

Covers:
1. New user fallback (no fabricated personalization).
2. Continue Learning (LessonProgress driven).
3. Satisfied prerequisite.
4. Missing prerequisite.
5. Partial prerequisite mastery.
6. Weak concept recommendation with explainable reason.
7. Under the hood: map identity, thresholds, endpoint.
8. Completed lesson handling.
9. Recommendation reason presence.
10. Centralized readiness threshold.
11. Personalized Learn endpoint.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase

from rest_framework.test import APITestCase

from learn.models import Course, Lesson, LessonProgress
from learner.models import ConceptMastery
from learner.services.prerequisites import PREREQUISITE_MAP as MAP_FROM_PREREQUISITES
from learner.services.prerequisite_map import PREREQUISITE_MAP as MAP_FROM_MAP_MODULE
from learner.services.thresholds import (
    SATISFIED_MASTERY,
    PARTIALLY_MASTERED_MASTERY,
    classify_mastery_score,
)
from recommendations.services import (
    build_personalized_learn_response,
    PREREQUISITE_MAP as MAP_FROM_RECOMMENDATIONS,
)

User = get_user_model()


class CentralizedThresholdTests(TestCase):
    """Step 10: centralized readiness threshold is the single source."""

    def test_threshold_values(self):
        self.assertEqual(SATISFIED_MASTERY, 0.75)
        self.assertEqual(PARTIALLY_MASTERED_MASTERY, 0.30)

    def test_classification_boundaries(self):
        self.assertEqual(classify_mastery_score(0.75), 'satisfied')
        self.assertEqual(classify_mastery_score(0.74), 'partially_mastered')
        self.assertEqual(classify_mastery_score(0.30), 'partially_mastered')
        self.assertEqual(classify_mastery_score(0.29), 'missing')
        self.assertEqual(classify_mastery_score(None), 'missing')
        self.assertEqual(classify_mastery_score(None, missing_is_unknown=True), 'unknown')


class PersonalizedLearnServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='phase3@example.com', username='phase3', password='pw'
        )

    def _create_lesson(self, concept_tag, difficulty='beginner'):
        course = Course.objects.create(
            title=f'{concept_tag.title()} Course',
            slug=f'{concept_tag}-course-{Lesson.objects.count() + 1}',
            is_published=True,
        )
        return Lesson.objects.create(
            course=course,
            title=f'{concept_tag.title()} Lesson',
            slug=f'{concept_tag}-lesson-{Lesson.objects.count() + 1}',
            concept_tag=concept_tag,
            difficulty=difficulty,
            is_active=True,
            duration_minutes=10,
        )

    # --- 1. New user fallback -------------------------------------------
    def test_new_user_gets_default_beginner_path_without_fabricated_data(self):
        payload = build_personalized_learn_response(self.user)

        self.assertTrue(payload['current_learning_path'])
        self.assertTrue(payload['recommended_for_you'])
        self.assertEqual(payload['continue_learning'], [])
        self.assertEqual(payload['missing_prerequisites'], [])
        self.assertTrue(payload['next_best_lesson'])
        path_concepts = {
            item['concept_tag'] for item in payload['current_learning_path']
        }
        self.assertTrue(path_concepts)

    # --- 2. Continue Learning -------------------------------------------
    def test_continue_learning_prioritizes_in_progress_lesson(self):
        lesson = self._create_lesson('numpy_pandas')
        LessonProgress.objects.create(
            user=self.user,
            lesson=lesson,
            watch_time_seconds=360,  # 6 of 10 minutes = 60%
            last_position_seconds=360,
            is_completed=False,
        )

        payload = build_personalized_learn_response(self.user)

        self.assertEqual(payload['continue_learning'][0]['lesson']['id'], lesson.id)
        self.assertEqual(payload['continue_learning'][0]['progress_percent'], 60)
        self.assertEqual(payload['next_best_lesson']['id'], lesson.id)
        self.assertEqual(payload['recommended_for_you'][0]['lesson']['id'], lesson.id)

    # --- 8. Completed lesson handling -----------------------------------
    def test_completed_lessons_are_not_recommended(self):
        lesson = self._create_lesson('classification')
        LessonProgress.objects.create(
            user=self.user,
            lesson=lesson,
            watch_time_seconds=600,
            is_completed=True,
        )
        ConceptMastery.objects.create(
            user=self.user,
            concept_tag='classification',
            mastery_score=0.20,
            is_struggling=True,
        )

        payload = build_personalized_learn_response(self.user)

        self.assertEqual(payload['continue_learning'], [])
        rec_ids = {item['id'] for item in payload['recommended_for_you']}
        self.assertNotIn(lesson.id, rec_ids)
        self.assertNotIn(
            lesson.id, {i['id'] for i in payload['strengthen_weak_areas']}
        )

    # --- 4/5. Missing / partial prerequisites ---------------------------
    def test_missing_prerequisite_blocks_advanced_recommendation(self):
        prereq_lesson = self._create_lesson('linear_algebra')
        advanced_lesson = self._create_lesson('neural_networks', difficulty='advanced')
        ConceptMastery.objects.create(
            user=self.user, concept_tag='linear_algebra', mastery_score=0.10
        )
        ConceptMastery.objects.create(
            user=self.user, concept_tag='neural_networks', mastery_score=0.72
        )

        payload = build_personalized_learn_response(self.user)

        self.assertTrue(
            any(
                item['lesson']['id'] == prereq_lesson.id
                for item in payload['missing_prerequisites']
            )
        )
        self.assertEqual(payload['next_best_lesson']['id'], prereq_lesson.id)
        self.assertNotEqual(payload['next_best_lesson']['id'], advanced_lesson.id)

    def test_partial_prerequisite_mastery_is_surfaced(self):
        self._create_lesson('linear_algebra')
        self._create_lesson('neural_networks', difficulty='advanced')
        ConceptMastery.objects.create(
            user=self.user, concept_tag='linear_algebra', mastery_score=0.45
        )

        payload = build_personalized_learn_response(self.user)

        status_rows = {
            r['concept']: r for r in payload['prerequisite_status']['neural_networks']
        }
        self.assertEqual(status_rows['linear_algebra']['status'], 'PARTIALLY_MASTERED')
        self.assertEqual(status_rows['linear_algebra']['mastery'], 0.45)
        self.assertTrue(
            any(
                item['concept_tag'] == 'linear_algebra'
                for item in payload['missing_prerequisites']
            )
        )

class PrerequisiteMapIdentityTests(TestCase):
    """Step 2: exactly one PREREQUISITE_MAP, shared across apps."""

    def test_all_modules_share_one_map_object(self):
        self.assertIs(MAP_FROM_RECOMMENDATIONS, MAP_FROM_PREREQUISITES)
        self.assertIs(MAP_FROM_MAP_MODULE, MAP_FROM_PREREQUISITES)

    def test_prerequisites_service_does_not_import_recommendations(self):
        import inspect
        import learner.services.prerequisites as prereq_service

        source = inspect.getsource(prereq_service)
        self.assertNotIn('recommendations', source)

    def test_recommendations_imports_map_from_map_module(self):
        import inspect
        import recommendations.services as reco_service

        source = inspect.getsource(reco_service)
        self.assertIn('from learner.services.prerequisite_map import', source)
class RemainingRecommendationTests(TestCase):
    """Satisfied prerequisites, weak concepts, and explainable reasons."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='remaining@example.com', username='remaining', password='pw'
        )

    def _create_lesson(self, concept_tag, difficulty='beginner'):
        course = Course.objects.create(
            title=f'{concept_tag.title()} Course',
            slug=f'{concept_tag}-course-{Lesson.objects.count() + 1}',
            is_published=True,
        )
        return Lesson.objects.create(
            course=course,
            title=f'{concept_tag.title()} Lesson',
            slug=f'{concept_tag}-lesson-{Lesson.objects.count() + 1}',
            concept_tag=concept_tag,
            difficulty=difficulty,
            is_active=True,
            duration_minutes=10,
        )

    # --- 3. Satisfied prerequisite --------------------------------------
    def test_satisfied_prerequisite_is_not_recommended(self):
        self._create_lesson('linear_algebra')
        self._create_lesson('neural_networks', difficulty='advanced')
        ConceptMastery.objects.create(
            user=self.user, concept_tag='linear_algebra', mastery_score=0.90
        )
        ConceptMastery.objects.create(
            user=self.user, concept_tag='neural_networks', mastery_score=0.80
        )

        payload = build_personalized_learn_response(self.user)

        self.assertEqual(payload['missing_prerequisites'], [])
        status_rows = {
            r['concept']: r for r in payload['prerequisite_status']['neural_networks']
        }
        self.assertEqual(status_rows['linear_algebra']['status'], 'SATISFIED')

    # --- 6. Weak concept recommendation with reason ----------------------
    def test_weak_concept_recommendation_contains_explainable_reason(self):
        lesson = self._create_lesson('classification')
        ConceptMastery.objects.create(
            user=self.user,
            concept_tag='classification',
            mastery_score=0.44,
            quiz_attempts=2,
            is_struggling=True,
        )

        payload = build_personalized_learn_response(self.user)

        weak_items = {
            item['lesson']['id']: item
            for item in payload['strengthen_weak_areas']
        }
        self.assertIn(lesson.id, weak_items)
        item = weak_items[lesson.id]
        self.assertEqual(item['reason_code'], 'WEAK_CONCEPT')
        self.assertIn('44%', item['reason'])
        self.assertIn('classification', item['reason'].lower())

    # --- 7. Weak concept with no corresponding Lesson ---------------------
    def test_weak_concept_without_lesson_is_safe(self):
        ConceptMastery.objects.create(
            user=self.user,
            concept_tag='classification',
            mastery_score=0.20,
            quiz_attempts=3,
            is_struggling=True,
        )

        payload = build_personalized_learn_response(self.user)

        self.assertIsInstance(payload['strengthen_weak_areas'], list)
        self.assertIsInstance(payload['recommended_for_you'], list)
        self.assertIsInstance(payload['next_best_lesson'], (dict, type(None)))

    # --- 9. Recommendation reasons ---------------------------------------
    def test_every_recommendation_carries_a_reason_and_reason_code(self):
        self._create_lesson('linear_algebra')
        ConceptMastery.objects.create(
            user=self.user, concept_tag='linear_algebra', mastery_score=0.10
        )

        payload = build_personalized_learn_response(self.user)

        for item in [
            *payload['continue_learning'],
            *payload['missing_prerequisites'],
            *payload['strengthen_weak_areas'],
            *payload['recommended_for_you'],
        ]:
            self.assertTrue(item.get('reason'), f'missing reason for {item}')
            self.assertTrue(
                item.get('reason_code'), f'missing reason_code for {item}'
            )


class PersonalizedLearnEndpointTests(APITestCase):
    """Step 11: the existing personalized Learn endpoint, extended in place."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='endpoint@example.com', username='endpoint', password='pw'
        )
        self.client.force_authenticate(user=self.user)

    def test_learn_recommendations_endpoint_returns_personalized_payload(self):
        response = self.client.get('/api/learn/recommendations/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        for key in (
            'continue_learning',
            'recommended_for_you',
            'missing_prerequisites',
            'strengthen_weak_areas',
            'next_best_lesson',
            'current_learning_path',
            'prerequisite_status',
        ):
            self.assertIn(key, data)
        self.assertTrue(data['is_personalised'])

    def test_learn_recommendations_endpoint_requires_authentication(self):
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/learn/recommendations/')
        self.assertIn(response.status_code, (401, 403))

