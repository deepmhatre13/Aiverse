"""
Learning Path Generator Service

Generates personalized learning paths based on ConceptMastery state,
adapting course/module ordering to learner's current mastery levels.
"""

from typing import Dict, List, Optional
from django.db.models import QuerySet
from django.contrib.auth import get_user_model
from learn.models import Lesson, Course, Module
from learner.models import ConceptMastery, LearnerProfile, CONCEPT_TAGS
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class LearningPathGenerator:
    """Generates adaptive learning paths per user based on mastery state."""
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.user = User.objects.get(id=user_id)
        self.masteries = self._load_masteries()
        self.profile = self._load_profile()
    
    def _load_masteries(self) -> Dict[str, ConceptMastery]:
        """Load all ConceptMastery objects for user into dict keyed by concept_tag."""
        masteries = ConceptMastery.objects.filter(user_id=self.user_id)
        return {m.concept_tag: m for m in masteries}
    
    def _load_profile(self) -> Optional[LearnerProfile]:
        """Load LearnerProfile if exists."""
        try:
            return LearnerProfile.objects.get(user_id=self.user_id)
        except LearnerProfile.DoesNotExist:
            return None
    
    def generate_path(self) -> Dict:
        """
        Generate personalized learning path.
        
        Returns:
            Dict with ordered_lessons, current_focus, estimated_completion_hours, mastery_vector
        """
        logger.info(f"Generating learning path for user {self.user_id}")
        
        # Build mastery vector
        mastery_vector = self._build_mastery_vector()
        
        # Determine concept priority order
        concept_priority = self._compute_concept_priority()
        
        # Get lessons in priority order
        ordered_lessons = self._get_ordered_lessons(concept_priority)
        
        # Estimate completion time
        estimated_hours = self._estimate_completion_time(ordered_lessons)
        
        # Determine current focus (first unmastered concept)
        current_focus = self._determine_current_focus(concept_priority)
        
        return {
            "ordered_lessons": ordered_lessons,
            "current_focus": current_focus,
            "estimated_completion_hours": estimated_hours,
            "mastery_vector": mastery_vector,
            "user_id": self.user_id,
        }
    
    def _build_mastery_vector(self) -> Dict[str, float]:
        """Build mastery score vector for all 31 concept tags."""
        vector = {}
        for tag, _ in CONCEPT_TAGS:
            mastery = self.masteries.get(tag)
            vector[tag] = mastery.mastery_score if mastery else 0.0
        return vector
    
    def _compute_concept_priority(self) -> List[str]:
        """
        Compute priority order for concepts.
        
        Priority:
        1. Struggling concepts (is_struggling=True, mastery < 0.4) - need intervention
        2. Unmastered concepts (mastery < 0.7) - need practice
        3. New concepts (no mastery record) - need introduction
        4. Mastered concepts (mastery >= 0.8) - lowest priority
        """
        struggling = []
        unmastered = []
        new_concepts = []
        mastered = []
        
        for tag, _ in CONCEPT_TAGS:
            mastery = self.masteries.get(tag)
            if not mastery:
                new_concepts.append(tag)
            elif mastery.is_struggling:
                struggling.append(tag)
            elif mastery.mastery_score < 0.7:
                unmastered.append(tag)
            elif mastery.mastery_score >= 0.8:
                mastered.append(tag)
            else:
                # 0.7 <= mastery < 0.8: approaching mastery
                unmastered.append(tag)
        
        # Sort each group by mastery ascending (worst first)
        def sort_by_mastery(tags):
            return sorted(tags, key=lambda t: self.masteries.get(t).mastery_score if self.masteries.get(t) else 0)
        
        return sort_by_mastery(struggling) + sort_by_mastery(unmastered) + new_concepts + mastered
    
    def _get_ordered_lessons(self, concept_priority: List[str]) -> List[Dict]:
        """
        Get lessons ordered by concept priority.
        
        For each concept, return next uncompleted lesson.
        """
        ordered_lessons = []
        completed_lesson_ids = set()
        
        # Get completed lessons
        from learn.models import LessonProgress
        completed = LessonProgress.objects.filter(
            user=self.user,
            is_completed=True
        ).values_list('lesson_id', flat=True)
        completed_lesson_ids = set(completed)
        
        for concept_tag in concept_priority:
            # Get next uncompleted lesson for this concept
            lesson = self._get_next_lesson(concept_tag, completed_lesson_ids)
            if lesson:
                ordered_lessons.append({
                    "lesson_id": lesson.id,
                    "title": lesson.title,
                    "concept_tag": concept_tag,
                    "estimated_minutes": lesson.duration_minutes,
                    "difficulty": lesson.difficulty,
                    "course_id": lesson.course_id,
                    "course_title": lesson.course.title,
                })
                completed_lesson_ids.add(lesson.id)
        
        # Limit to next 20 lessons for initial path
        return ordered_lessons[:20]
    
    def _get_next_lesson(self, concept_tag: str, completed_ids: set) -> Optional[Lesson]:
        """
        Get next uncompleted lesson for a concept.
        
        Checks prerequisites are met (all prerequisite lessons are completed).
        """
        lessons = Lesson.objects.filter(
            concept_tag=concept_tag,
            is_active=True
        ).order_by('course__module__order', 'order')
        
        for lesson in lessons:
            if lesson.id in completed_ids:
                continue
            
            # Check prerequisites
            prereqs = lesson.prerequisites.filter(is_active=True)
            prereqs_met = all(p.id in completed_ids for p in prereqs)
            
            if prereqs_met:
                return lesson
        
        return None
    
    def _estimate_completion_time(self, ordered_lessons: List[Dict]) -> float:
        """Estimate total completion time in hours, adjusted by learning velocity."""
        total_minutes = sum(lesson["estimated_minutes"] for lesson in ordered_lessons)
        base_hours = total_minutes / 60.0
        
        # Adjust by learning velocity if available
        if self.profile and self.profile.learning_velocity > 0:
            # learning_velocity is lessons per week
            # Assume average lesson is 15 minutes
            avg_lesson_minutes = 15
            expected_minutes_per_week = self.profile.learning_velocity * avg_lesson_minutes
            if expected_minutes_per_week > 0:
                adjustment = (total_minutes / expected_minutes_per_week) * 7 * 24
                return round(adjustment, 1)
        
        return round(base_hours, 1)
    
    def _determine_current_focus(self, concept_priority: List[str]) -> str:
        """Determine the current focus concept (first unmastered or struggling)."""
        for tag in concept_priority:
            mastery = self.masteries.get(tag)
            if not mastery or mastery.mastery_score < 0.7 or mastery.is_struggling:
                return tag
        return concept_priority[0] if concept_priority else "unknown"


def get_learning_path_for_user(user_id: int) -> Dict:
    """
    Convenience function to generate learning path for a user.
    
    Args:
        user_id: User ID
        
    Returns:
        Learning path dict
    """
    generator = LearningPathGenerator(user_id)
    return generator.generate_path()