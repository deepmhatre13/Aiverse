"""
Tests for LearningPathGenerator service.

Converted to Django's TestCase runner (manage.py test) so they execute in the
same environment as the rest of the suite instead of silently failing with
"ModuleNotFoundError: No module named 'pytest'".
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from learner.models import ConceptMastery
from learner.services.path_generator import LearningPathGenerator, get_learning_path_for_user
from learn.models import Lesson, Course, Module

User = get_user_model()


class LearningPathGeneratorTestBase(TestCase):
    """Shared fixtures implemented as plain helper data (created once per class)."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        cls.module = Module.objects.create(
            name='Test Module',
            slug='test-module',
            description='Test module description',
            order=1
        )
        cls.course = Course.objects.create(
            title='Test Course',
            slug='test-course',
            description='Test course description',
            module=cls.module,
            is_published=True
        )
        lessons_data = [
            {'title': 'Lesson 1: Regression', 'concept_tag': 'regression', 'order': 1, 'duration_minutes': 15},
            {'title': 'Lesson 2: Classification', 'concept_tag': 'classification', 'order': 2, 'duration_minutes': 20},
            {'title': 'Lesson 3: Regression Advanced', 'concept_tag': 'regression', 'order': 3, 'duration_minutes': 25},
            {'title': 'Lesson 4: Neural Networks', 'concept_tag': 'neural_networks', 'order': 4, 'duration_minutes': 30},
        ]
        cls.lessons = [
            Lesson.objects.create(course=cls.course, **data)
            for data in lessons_data
        ]
        # Regression: mastered
        ConceptMastery.objects.create(
            user=cls.user,
            concept_tag='regression',
            mastery_score=0.85,
            quiz_mastery=0.9,
            coding_mastery=0.8,
            is_struggling=False
        )
        # Classification: unmastered
        ConceptMastery.objects.create(
            user=cls.user,
            concept_tag='classification',
            mastery_score=0.5,
            quiz_mastery=0.4,
            coding_mastery=0.6,
            is_struggling=False
        )
        # Neural networks: struggling
        ConceptMastery.objects.create(
            user=cls.user,
            concept_tag='neural_networks',
            mastery_score=0.3,
            quiz_mastery=0.2,
            coding_mastery=0.4,
            quiz_attempts=4,
            coding_attempts=2,
            is_struggling=True
        )



class TestLearningPathGenerator(LearningPathGeneratorTestBase):
    """Test LearningPathGenerator class."""

    def test_generate_path_basic(self):
        """Test basic path generation."""
        generator = LearningPathGenerator(self.user.id)
        path = generator.generate_path()

        self.assertIn('ordered_lessons', path)
        self.assertIn('current_focus', path)
        self.assertIn('estimated_completion_hours', path)
        self.assertIn('mastery_vector', path)

        # Should have lessons
        self.assertGreater(len(path['ordered_lessons']), 0)

        # Current focus should be struggling or unmastered concept
        self.assertIn(path['current_focus'], ['neural_networks', 'classification'])

    def test_concept_priority(self):
        """Test concept priority ordering."""
        generator = LearningPathGenerator(self.user.id)
        priority = generator._compute_concept_priority()

        # Struggling concepts should come first
        self.assertIn('neural_networks', priority[:2])

        # Mastered concepts should come last
        self.assertIn('regression', priority[-2:])

    def test_mastery_vector(self):
        """Test mastery vector building."""
        generator = LearningPathGenerator(self.user.id)
        vector = generator._build_mastery_vector()

        self.assertIn('regression', vector)
        self.assertIn('classification', vector)
        self.assertIn('neural_networks', vector)

        self.assertEqual(vector['regression'], 0.85)
        self.assertEqual(vector['classification'], 0.5)
        self.assertEqual(vector['neural_networks'], 0.3)

    def test_estimate_completion_time(self):
        """Test completion time estimation."""
        generator = LearningPathGenerator(self.user.id)
        path = generator.generate_path()

        self.assertGreater(path['estimated_completion_hours'], 0)
        # Should be reasonable (not too high or low)
        self.assertGreaterEqual(path['estimated_completion_hours'], 0.1)
        self.assertLessEqual(path['estimated_completion_hours'], 100)


class TestGetLearningPathForUser(LearningPathGeneratorTestBase):
    """Test convenience function."""

    def test_get_learning_path_for_user(self):
        """Test getting learning path for user."""
        path = get_learning_path_for_user(self.user.id)

        self.assertIsInstance(path, dict)
        self.assertIn('ordered_lessons', path)
        self.assertIn('current_focus', path)
        self.assertIn('mastery_vector', path)


class TestLearningPathAPI(LearningPathGeneratorTestBase):
    """Test learning path API endpoint."""

    def test_learning_path_view(self):
        """Test LearningPathView endpoint."""
        self.client.force_login(self.user)

        response = self.client.get('/api/learner/learning-path/')

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertIn('ordered_lessons', data)
        self.assertIn('current_focus', data)
        self.assertIn('estimated_completion_hours', data)
        self.assertIn('mastery_vector', data)


class TestKnowledgeGapView(LearningPathGeneratorTestBase):
    """Test knowledge gap detection."""

    def test_knowledge_gaps_none(self):
        """Test when no knowledge gaps exist (fresh user, no masteries)."""
        fresh_user = User.objects.create_user(
            username='cleanuser',
            email='clean@example.com',
            password='pw123456',
        )
        self.client.force_login(fresh_user)

        response = self.client.get('/api/learner/knowledge-gaps/')

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertIn('gaps', data)
        self.assertIn('total_gaps', data)
        self.assertEqual(data['total_gaps'], 0)

    def test_knowledge_gaps_detected(self):
        """Test when knowledge gaps are detected."""
        self.client.force_login(self.user)

        response = self.client.get('/api/learner/knowledge-gaps/')

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # neural_networks should be detected as gap (mastery=0.3, attempts=6)
        self.assertGreaterEqual(data['total_gaps'], 1)

        gap_tags = [g['concept_tag'] for g in data['gaps']]
        self.assertIn('neural_networks', gap_tags)


class TestRevisionScheduler(LearningPathGeneratorTestBase):
    """Test spaced repetition scheduler."""

    def test_calculate_next_review_mastered(self):
        """Test next review for mastered concept."""
        mastery = ConceptMastery.objects.get(user=self.user, concept_tag='regression')
        from learner.services.revision_scheduler import RevisionScheduler

        scheduler = RevisionScheduler(mastery)
        next_review = scheduler.calculate_next_review()

        # Mastered concepts should have longer intervals
        self.assertIsNotNone(next_review)

    def test_calculate_next_review_struggling(self):
        """Test next review for struggling concept."""
        mastery = ConceptMastery.objects.get(user=self.user, concept_tag='neural_networks')
        from learner.services.revision_scheduler import RevisionScheduler

        scheduler = RevisionScheduler(mastery)
        next_review = scheduler.calculate_next_review()

        # Struggling concepts should have shorter intervals
        self.assertIsNotNone(next_review)
