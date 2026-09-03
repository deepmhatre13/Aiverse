from django.contrib.auth import get_user_model
from django.test import TestCase

from learn.models import Course, Lesson, LessonProgress
from learner.models import ConceptMastery
from recommendations.models import Recommendation
from recommendations.serializers import RecommendationSerializer
from recommendations.services import RuleBasedRecommender, build_personalized_learn_response

User = get_user_model()


class RuleBasedRecommenderTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='reco@example.com', username='recommender', password='pw'
        )

    def test_missing_lesson_falls_back_safely_for_revision_recommendation(self):
        ConceptMastery.objects.create(
            user=self.user,
            concept_tag='classification',
            mastery_score=0.60,
            quiz_attempts=2,
        )
        recommender = RuleBasedRecommender(self.user.id)
        recs = recommender.generate_and_cache()
        self.assertFalse(any(r.recommendation_type == 'revision' for r in recs))

    def test_learn_response_uses_default_beginner_path_for_new_user(self):
        payload = build_personalized_learn_response(self.user)
        self.assertIn('current_learning_path', payload)
        self.assertTrue(payload['current_learning_path'])
        self.assertTrue(payload['recommended_for_you'])
        self.assertEqual(payload['continue_learning'], [])
        self.assertEqual(payload['missing_prerequisites'], [])

    def test_learn_response_prioritizes_active_lesson_progress(self):
        course = Course.objects.create(title='ML Basics', slug='ml-basics', is_published=True)
        lesson = Lesson.objects.create(
            course=course,
            title='NumPy Basics',
            slug='numpy-basics',
            concept_tag='numpy_pandas',
            difficulty='beginner',
            is_active=True,
        )
        LessonProgress.objects.create(
            user=self.user,
            lesson=lesson,
            watch_time_seconds=600,
            last_position_seconds=600,
            is_completed=False,
        )

        payload = build_personalized_learn_response(self.user)
        self.assertEqual(payload['continue_learning'][0]['lesson']['id'], lesson.id)
        self.assertGreaterEqual(payload['continue_learning'][0]['progress_percent'], 60)

    def test_missing_prerequisite_blocks_advanced_recommendation(self):
        course = Course.objects.create(title='Advanced ML', slug='advanced-ml', is_published=True)
        prereq_lesson = Lesson.objects.create(
            course=course,
            title='Linear Algebra Basics',
            slug='linear-algebra-basics',
            concept_tag='linear_algebra',
            difficulty='beginner',
            is_active=True,
        )
        advanced_lesson = Lesson.objects.create(
            course=course,
            title='Neural Networks',
            slug='neural-networks',
            concept_tag='neural_networks',
            difficulty='advanced',
            is_active=True,
        )
        ConceptMastery.objects.create(user=self.user, concept_tag='linear_algebra', mastery_score=0.20)
        ConceptMastery.objects.create(user=self.user, concept_tag='neural_networks', mastery_score=0.72)

        payload = build_personalized_learn_response(self.user)
        self.assertTrue(any(item['lesson']['id'] == prereq_lesson.id for item in payload['missing_prerequisites']))
        self.assertNotEqual(payload['next_best_lesson']['id'], advanced_lesson.id)

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

    def _create_lesson(self, concept_tag='classification'):
        course = Course.objects.create(
            title=f'{concept_tag.title()} Course',
            slug=f'{concept_tag}-course',
            is_published=True,
        )
        return Lesson.objects.create(
            course=course,
            title=f'{concept_tag.title()} Lesson',
            slug=f'{concept_tag}-lesson',
            concept_tag=concept_tag,
            difficulty='beginner',
            is_active=True,
        )

    def test_partially_mastered_concept_generates_revision_recommendation(self):
        self._create_lesson('classification')
        ConceptMastery.objects.create(
            user=self.user,
            concept_tag='classification',
            mastery_score=0.60,
            quiz_attempts=2,
        )

        recommender = RuleBasedRecommender(self.user.id)
        recs = recommender.generate_and_cache()

        self.assertTrue(any(r.recommendation_type == 'revision' for r in recs))
        self.assertTrue(Recommendation.objects.filter(
            user=self.user,
            recommendation_type='revision',
        ).exists())

    def test_satisfied_concept_does_not_generate_revision_recommendation(self):
        self._create_lesson('classification')
        ConceptMastery.objects.create(
            user=self.user,
            concept_tag='classification',
            mastery_score=0.90,
            quiz_attempts=2,
        )

        recommender = RuleBasedRecommender(self.user.id)
        recs = recommender.generate_and_cache()

        self.assertFalse(any(r.recommendation_type == 'revision' for r in recs))

    def test_serializer_includes_frontend_metadata_for_lesson_recommendations(self):
        lesson = self._create_lesson('classification')
        recommendation = Recommendation.objects.create(
            user=self.user,
            recommendation_type='revision',
            content_type='lesson',
            content_id=lesson.id,
            score=0.86,
            reason='Review the lesson again.',
            source='rule_based',
        )

        data = RecommendationSerializer(recommendation).data

        self.assertEqual(data['title'], lesson.title)
        self.assertEqual(data['slug'], lesson.slug)
        self.assertEqual(data['course_slug'], lesson.course.slug)
        self.assertEqual(data['difficulty'], lesson.difficulty)
        self.assertEqual(data['concept_tag'], lesson.concept_tag)
        self.assertEqual(data['final_score'], 0.86)
