"""
Weak Topic Analyzer Service

Analyzes user's concept mastery to identify weak and strong topics,
computes trends, and updates LearnerProfile.
"""

from typing import Dict, List, Optional
from django.contrib.auth import get_user_model
from django.db.models import QuerySet
from learner.models import ConceptMastery, LearnerProfile, CONCEPT_TAGS
from learner.services.thresholds import classify_mastery_score
from tracking.models import LearnerEvent
import logging
from datetime import timedelta
from django.utils import timezone

logger = logging.getLogger(__name__)
User = get_user_model()


class WeakTopicAnalyzer:
    """Analyzes user's weak and strong topics."""
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.user = User.objects.get(id=user_id)
    
    def analyze_user_weak_topics(self, user_id: int = None) -> List[Dict]:
        """
        Analyze and return user's weak topics.
        
        Weak topics are defined as:
        - is_struggling=True, OR
        - mastery_score < 0.5
        
        Returns list sorted by mastery_score ascending (worst first).
        """
        user_id = user_id or self.user_id
        
        masteries = ConceptMastery.objects.filter(
            user_id=user_id
        ).select_related('user')
        
        weak_topics = []
        for mastery in masteries:
            readiness = classify_mastery_score(mastery.mastery_score)
            # Check if weak using the canonical learner readiness states.
            if mastery.is_struggling or readiness in {'missing', 'partially_mastered'}:
                trend = self._compute_topic_trend(user_id, mastery.concept_tag)

                weak_topics.append({
                    'concept_tag': mastery.concept_tag,
                    'mastery_score': mastery.mastery_score,
                    'quiz_mastery': mastery.quiz_mastery,
                    'coding_mastery': mastery.coding_mastery,
                    'trend': trend,
                    'quiz_attempts': mastery.quiz_attempts,
                    'coding_attempts': mastery.coding_attempts,
                    'total_attempts': mastery.quiz_attempts + mastery.coding_attempts,
                    'is_struggling': mastery.is_struggling,
                    'bkt_trace': mastery.bkt_trace
                })
        
        # Sort by mastery_score ascending (worst first)
        weak_topics.sort(key=lambda x: x['mastery_score'])
        
        return weak_topics
    
    def analyze_user_strengths(self, user_id: int = None) -> List[Dict]:
        """
        Analyze and return user's strong topics.
        
        Strong topics: mastery_score >= 0.8
        Returns list sorted by mastery_score descending (best first).
        """
        user_id = user_id or self.user_id
        
        masteries = ConceptMastery.objects.filter(
            user_id=user_id,
            mastery_score__gte=0.8
        )
        
        strong_topics = []
        for mastery in masteries:
            if classify_mastery_score(mastery.mastery_score) != 'satisfied':
                continue
            trend = self._compute_topic_trend(user_id, mastery.concept_tag)

            strong_topics.append({
                'concept_tag': mastery.concept_tag,
                'mastery_score': mastery.mastery_score,
                'quiz_mastery': mastery.quiz_mastery,
                'coding_mastery': mastery.coding_mastery,
                'trend': trend,
                'total_attempts': mastery.quiz_attempts + mastery.coding_attempts,
                'bkt_trace': mastery.bkt_trace
            })
        
        # Sort by mastery_score descending (best first)
        strong_topics.sort(key=lambda x: x['mastery_score'], reverse=True)
        
        return strong_topics
    
    def _compute_topic_trend(self, user_id: int, concept_tag: str) -> str:
        """
        Compute trend for a topic based on recent mastery changes.
        
        Returns: 'improving', 'stable', or 'declining'
        """
        try:
            mastery = ConceptMastery.objects.get(user_id=user_id, concept_tag=concept_tag)
            bkt_trace = mastery.bkt_trace or []
            
            if len(bkt_trace) < 3:
                return 'stable'  # Not enough data
            
            # Get last 5 trace values
            recent = bkt_trace[-5:] if len(bkt_trace) >= 5 else bkt_trace
            
            # Calculate average change
            changes = []
            for i in range(1, len(recent)):
                change = recent[i] - recent[i-1]
                changes.append(change)
            
            if not changes:
                return 'stable'
            
            avg_change = sum(changes) / len(changes)
            
            # Thresholds for trend classification
            if avg_change > 0.05:
                return 'improving'
            elif avg_change < -0.05:
                return 'declining'
            else:
                return 'stable'
                
        except ConceptMastery.DoesNotExist:
            return 'stable'
    
    def update_learner_profile(self, user_id: int = None) -> Dict:
        """
        Update LearnerProfile with weak/strong concepts and overall mastery.
        
        Returns updated profile data.
        """
        user_id = user_id or self.user_id
        
        # Get weak and strong topics
        weak_topics = self.analyze_user_weak_topics(user_id)
        strong_topics = self.analyze_user_strengths(user_id)
        
        # Calculate overall mastery
        all_masteries = ConceptMastery.objects.filter(user_id=user_id)
        if all_masteries.exists():
            total_mastery = sum(m.mastery_score for m in all_masteries)
            overall_mastery = round(total_mastery / all_masteries.count(), 4)
        else:
            overall_mastery = 0.0
        
        # Determine estimated skill level
        if overall_mastery >= 0.8:
            skill_level = 'advanced'
        elif overall_mastery >= 0.5:
            skill_level = 'intermediate'
        else:
            skill_level = 'beginner'
        
        # Update or create LearnerProfile
        profile, created = LearnerProfile.objects.get_or_create(user_id=user_id)
        profile.weak_concepts = [t['concept_tag'] for t in weak_topics]
        profile.strong_concepts = [t['concept_tag'] for t in strong_topics]
        profile.overall_mastery = overall_mastery
        profile.estimated_skill_level = skill_level
        profile.last_active = timezone.now()
        profile.save()
        
        logger.info(
            f"Updated LearnerProfile for user {user_id}: "
            f"mastery={overall_mastery:.2f}, weak={len(weak_topics)}, strong={len(strong_topics)}"
        )
        
        return {
            'user_id': user_id,
            'overall_mastery': overall_mastery,
            'estimated_skill_level': skill_level,
            'weak_concepts': profile.weak_concepts,
            'strong_concepts': profile.strong_concepts,
            'weak_count': len(weak_topics),
            'strong_count': len(strong_topics)
        }
    
    def get_trend_summary(self, user_id: int = None) -> Dict:
        """
        Get trend summary for all weak topics.
        
        Returns:
            Dict with improving, stable, declining topic counts
        """
        user_id = user_id or self.user_id
        weak_topics = self.analyze_user_weak_topics(user_id)
        
        improving = []
        stable = []
        declining = []
        
        for topic in weak_topics:
            if topic['trend'] == 'improving':
                improving.append(topic)
            elif topic['trend'] == 'declining':
                declining.append(topic)
            else:
                stable.append(topic)
        
        return {
            'improving': improving,
            'stable': stable,
            'declining': declining,
            'total_weak': len(weak_topics)
        }


def analyze_user_weak_topics(user_id: int) -> List[Dict]:
    """Convenience function to analyze weak topics."""
    analyzer = WeakTopicAnalyzer(user_id)
    return analyzer.analyze_user_weak_topics()


def analyze_user_strengths(user_id: int) -> List[Dict]:
    """Convenience function to analyze strong topics."""
    analyzer = WeakTopicAnalyzer(user_id)
    return analyzer.analyze_user_strengths()


def update_learner_profile_topics(user_id: int) -> Dict:
    """Convenience function to update learner profile."""
    analyzer = WeakTopicAnalyzer(user_id)
    return analyzer.update_learner_profile()