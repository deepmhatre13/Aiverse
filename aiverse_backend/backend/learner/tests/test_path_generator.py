"""
Tests for LearningPathGenerator service.
"""

import pytest
from django.contrib.auth import get_user_model
from learner.models import ConceptMastery, LearnerProfile
from learner.services.path_generator import LearningPathGenerator, get_learning_path_for_user
from learn.models import Lesson, Course, Module
from tracking.models import LearnerEvent

User = get_user_model()


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def module(db):
    """Create a test module."""
    return Module.objects.create(
        name='Test Module',
        slug='test-module',
        description='Test module description',
        order=1
    )


@pytest.fixture
def course(db, module):
    """Create a test course."""
    return Course.objects.create(
        title='Test Course',
        slug='test-course',
        description='Test course description',
        module=module,
        is_published=True
    )


@pytest.fixture
def lessons(db, course):
    """Create test lessons with different concept tags."""
    lessons_data = [
        {'title': 'Lesson 1: Regression', 'concept_tag': 'regression', 'order': 1, 'duration_minutes': 15},
        {'title': 'Lesson 2: Classification', 'concept_tag': 'classification', 'order': 2, 'duration_minutes': 20},
        {'title': 'Lesson 3: Regression Advanced', 'concept_tag': 'regression', 'order': 3, 'duration_minutes': 25},
        {'title': 'Lesson 4: Neural Networks', 'concept_tag': 'neural_networks', 'order': 4, 'duration_minutes': 30},
    ]
    
    created_lessons = []
    for data in lessons_data:
        lesson = Lesson.objects.create(
            course=course,
            **data
        )
        created_lessons.append(lesson)
    
    return created_lessons


@pytest.fixture
def concept_masteries(db, user):
    """Create concept mastery records for user."""
    masteries = []
    
    # Regression: mastered
    m1 = ConceptMastery.objects.create(
        user=user,
        concept_tag='regression',
        mastery_score=0.85,
        quiz_mastery=0.9,
        coding_mastery=0.8,
        is_struggling=False
    )
    masteries.append(m1)
    
    # Classification: unmastered
    m2 = ConceptMastery.objects.create(
        user=user,
        concept_tag='classification',
        mastery_score=0.5,
        quiz_mastery=0.4,
        coding_mastery=0.6,
        is_struggling=False
    )
    masteries.append(m2)
    
    # Neural networks: struggling
    m3 = ConceptMastery.objects.create(
        user=user,
        concept_tag='neural_networks',
        mastery_score=0.3,
        quiz_mastery=0.2,
        coding_mastery=0.4,
        quiz_attempts=4,
        coding_attempts=2,
        is_struggling=True
    )
    masteries.append(m3)
    
    return masteries


class TestLearningPathGenerator:
    """Test LearningPathGenerator class."""
    
    def test_generate_path_basic(self, user, concept_masteries, lessons):
        """Test basic path generation."""
        generator = LearningPathGenerator(user.id)
        path = generator.generate_path()
        
        assert 'ordered_lessons' in path
        assert 'current_focus' in path
        assert 'estimated_completion_hours' in path
        assert 'mastery_vector' in path
        
        # Should have lessons
        assert len(path['ordered_lessons']) > 0
        
        # Current focus should be struggling or unmastered concept
        assert path['current_focus'] in ['neural_networks', 'classification']
    
    def test_concept_priority(self, user, concept_masteries):
        """Test concept priority ordering."""
        generator = LearningPathGenerator(user.id)
        priority = generator._compute_concept_priority()
        
        # Struggling concepts should come first
        assert 'neural_networks' in priority[:2]
        
        # Mastered concepts should come last
        assert 'regression' in priority[-2:]
    
    def test_mastery_vector(self, user, concept_masteries):
        """Test mastery vector building."""
        generator = LearningPathGenerator(user.id)
        vector = generator._build_mastery_vector()
        
        assert 'regression' in vector
        assert 'classification' in vector
        assert 'neural_networks' in vector
        
        assert vector['regression'] == 0.85
        assert vector['classification'] == 0.5
        assert vector['neural_networks'] == 0.3
    
    def test_estimate_completion_time(self, user, concept_masteries, lessons):
        """Test completion time estimation."""
        generator = LearningPathGenerator(user.id)
        path = generator.generate_path()
        
        assert path['estimated_completion_hours'] > 0
        # Should be reasonable (not too high or low)
        assert 0.1 <= path['estimated_completion_hours'] <= 100


class TestGetLearningPathForUser:
    """Test convenience function."""
    
    def test_get_learning_path_for_user(self, user, concept_masteries, lessons):
        """Test getting learning path for user."""
        path = get_learning_path_for_user(user.id)
        
        assert isinstance(path, dict)
        assert 'ordered_lessons' in path
        assert 'current_focus' in path
        assert 'mastery_vector' in path


class TestLearningPathAPI:
    """Test learning path API endpoint."""
    
    def test_learning_path_view(self, client, user, concept_masteries, lessons):
        """Test LearningPathView endpoint."""
        client.force_login(user)
        
        response = client.get('/api/learner/learning-path/')
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'ordered_lessons' in data
        assert 'current_focus' in data
        assert 'estimated_completion_hours' in data
        assert 'mastery_vector' in data


class TestKnowledgeGapView:
    """Test knowledge gap detection."""
    
    def test_knowledge_gaps_none(self, client, user):
        """Test when no knowledge gaps exist."""
        client.force_login(user)
        
        response = client.get('/api/learner/knowledge-gaps/')
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'gaps' in data
        assert 'total_gaps' in data
        assert data['total_gaps'] == 0
    
    def test_knowledge_gaps_detected(self, client, user, concept_masteries):
        """Test when knowledge gaps are detected."""
        client.force_login(user)
        
        response = client.get('/api/learner/knowledge-gaps/')
        
        assert response.status_code == 200
        data = response.json()
        
        # neural_networks should be detected as gap (mastery=0.3, attempts=6)
        assert data['total_gaps'] >= 1
        
        gap_tags = [g['concept_tag'] for g in data['gaps']]
        assert 'neural_networks' in gap_tags


class TestRevisionScheduler:
    """Test spaced repetition scheduler."""
    
    def test_calculate_next_review_mastered(self, user, concept_masteries):
        """Test next review for mastered concept."""
        mastery = ConceptMastery.objects.get(user=user, concept_tag='regression')
        from learner.services.revision_scheduler import RevisionScheduler
        
        scheduler = RevisionScheduler(mastery)
        next_review = scheduler.calculate_next_review()
        
        # Mastered concepts should have longer intervals
        assert next_review is not None
    
    def test_calculate_next_review_struggling(self, user, concept_masteries):
        """Test next review for struggling concept."""
        mastery = ConceptMastery.objects.get(user=user, concept_tag='neural_networks')
        from learner.services.revision_scheduler import RevisionScheduler
        
        scheduler = RevisionScheduler(mastery)
        next_review = scheduler.calculate_next_review()
        
        # Struggling concepts should have shorter intervals
        assert next_review is not None