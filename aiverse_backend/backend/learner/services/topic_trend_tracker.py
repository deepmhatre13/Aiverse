"""
Topic Trend Tracker Service

Computes trends for user's concept mastery over time using linear regression.
"""

from typing import Dict, List, Optional
from django.contrib.auth import get_user_model
from learner.models import ConceptMastery
import logging
from datetime import timedelta
from django.utils import timezone

logger = logging.getLogger(__name__)
User = get_user_model()


class TopicTrendTracker:
    """Tracks and computes trends for concept mastery."""
    
    def __init__(self, user_id: int):
        self.user_id = user_id
    
    def compute_trend(self, user_id: int, concept_tag: str) -> Dict:
        """
        Compute trend for a specific concept.
        
        Args:
            user_id: User ID
            concept_tag: Concept tag to analyze
            
        Returns:
            Dict with trend direction, slope, and confidence
        """
        try:
            mastery = ConceptMastery.objects.get(user_id=user_id, concept_tag=concept_tag)
            bkt_trace = mastery.bkt_trace or []
            
            if len(bkt_trace) < 3:
                return {
                    'concept_tag': concept_tag,
                    'trend': 'stable',
                    'slope': 0.0,
                    'confidence': 'low',
                    'data_points': len(bkt_trace)
                }
            
            # Get last 10 trace values
            recent = bkt_trace[-10:] if len(bkt_trace) >= 10 else bkt_trace
            
            # Calculate linear regression
            n = len(recent)
            x_values = list(range(n))
            y_values = recent
            
            # Compute slope using least squares
            sum_x = sum(x_values)
            sum_y = sum(y_values)
            sum_xy = sum(x * y for x, y in zip(x_values, y_values))
            sum_x2 = sum(x * x for x in x_values)
            
            # Slope = (n*sum_xy - sum_x*sum_y) / (n*sum_x2 - sum_x^2)
            denominator = n * sum_x2 - sum_x * sum_x
            if denominator == 0:
                slope = 0.0
            else:
                slope = (n * sum_xy - sum_x * sum_y) / denominator
            
            # Determine trend direction
            # Slope threshold: 0.02 per step = meaningful change
            if slope > 0.02:
                trend = 'improving'
            elif slope < -0.02:
                trend = 'declining'
            else:
                trend = 'stable'
            
            # Determine confidence based on data points and consistency
            if n >= 8:
                confidence = 'high'
            elif n >= 5:
                confidence = 'medium'
            else:
                confidence = 'low'
            
            # Check consistency (how many steps follow the trend)
            if n >= 3:
                consistent_steps = 0
                for i in range(1, n):
                    change = y_values[i] - y_values[i-1]
                    if slope > 0 and change > 0:
                        consistent_steps += 1
                    elif slope < 0 and change < 0:
                        consistent_steps += 1
                
                consistency_ratio = consistent_steps / (n - 1)
                if consistency_ratio < 0.5:
                    confidence = 'low'
            
            return {
                'concept_tag': concept_tag,
                'trend': trend,
                'slope': round(slope, 4),
                'confidence': confidence,
                'data_points': n,
                'recent_values': recent
            }
            
        except ConceptMastery.DoesNotExist:
            return {
                'concept_tag': concept_tag,
                'trend': 'stable',
                'slope': 0.0,
                'confidence': 'none',
                'data_points': 0
            }
    
    def get_trend_summary(self, user_id: int = None) -> Dict:
        """
        Get trend summary for all concepts.
        
        Returns:
            Dict with improving, stable, declining topics
        """
        user_id = user_id or self.user_id
        
        masteries = ConceptMastery.objects.filter(user_id=user_id)
        
        improving = []
        stable = []
        declining = []
        
        for mastery in masteries:
            trend_data = self.compute_trend(user_id, mastery.concept_tag)
            
            topic_info = {
                'concept_tag': mastery.concept_tag,
                'mastery_score': mastery.mastery_score,
                'trend': trend_data['trend'],
                'slope': trend_data['slope'],
                'confidence': trend_data['confidence']
            }
            
            if trend_data['trend'] == 'improving':
                improving.append(topic_info)
            elif trend_data['trend'] == 'declining':
                declining.append(topic_info)
            else:
                stable.append(topic_info)
        
        # Sort each category by mastery_score
        improving.sort(key=lambda x: x['mastery_score'])
        stable.sort(key=lambda x: x['mastery_score'])
        declining.sort(key=lambda x: x['mastery_score'])
        
        return {
            'improving': improving,
            'stable': stable,
            'declining': declining,
            'total_concepts': len(masteries),
            'improving_count': len(improving),
            'stable_count': len(stable),
            'declining_count': len(declining)
        }
    
    def get_weak_topic_trends(self, user_id: int = None) -> List[Dict]:
        """
        Get trends specifically for weak topics.
        
        Args:
            user_id: User ID
            
        Returns:
            List of weak topics with trend data
        """
        user_id = user_id or self.user_id
        
        # Get weak topics
        weak_masteries = ConceptMastery.objects.filter(
            user_id=user_id,
            is_struggling=True
        )
        
        weak_trends = []
        for mastery in weak_masteries:
            trend_data = self.compute_trend(user_id, mastery.concept_tag)
            weak_trends.append({
                'concept_tag': mastery.concept_tag,
                'mastery_score': mastery.mastery_score,
                'trend': trend_data['trend'],
                'slope': trend_data['slope'],
                'confidence': trend_data['confidence'],
                'is_struggling': mastery.is_struggling,
                'attempts': mastery.quiz_attempts + mastery.coding_attempts
            })
        
        # Sort by trend (declining first) then by mastery_score
        weak_trends.sort(key=lambda x: (
            0 if x['trend'] == 'declining' else (1 if x['trend'] == 'stable' else 2),
            x['mastery_score']
        ))
        
        return weak_trends
    
    def get_topic_velocity(self, user_id: int, concept_tag: str) -> float:
        """
        Calculate learning velocity for a topic (mastery change per week).
        
        Args:
            user_id: User ID
            concept_tag: Concept tag
            
        Returns:
            float: Velocity (positive = improving, negative = declining)
        """
        mastery = ConceptMastery.objects.filter(user_id=user_id, concept_tag=concept_tag).first()
        
        if not mastery or not mastery.bkt_trace or len(mastery.bkt_trace) < 2:
            return 0.0
        
        # Get timestamps from recent events
        from tracking.models import LearnerEvent
        
        week_ago = timezone.now() - timedelta(weeks=4)
        events = LearnerEvent.objects.filter(
            user_id=user_id,
            metadata__concept_tag=concept_tag,
            timestamp__gte=week_ago
        ).order_by('timestamp')[:20]
        
        if events.count() < 2:
            return 0.0
        
        # Calculate average change per event
        changes = []
        for i in range(1, len(events)):
            # Approximate mastery change from event types
            prev_event = events[i-1]
            curr_event = events[i]
            
            # Simple heuristic: passed events increase mastery
            if curr_event.event_type in ['QUIZ_PASSED', 'CODE_PASSED']:
                changes.append(0.05)
            elif curr_event.event_type in ['QUIZ_FAILED', 'CODE_FAILED']:
                changes.append(-0.02)
        
        if not changes:
            return 0.0
        
        avg_change = sum(changes) / len(changes)
        
        # Convert to weekly velocity (assuming ~5 events per week)
        weekly_velocity = avg_change * 5
        
        return round(weekly_velocity, 4)


def compute_trend(user_id: int, concept_tag: str) -> Dict:
    """Convenience function to compute trend for a concept."""
    tracker = TopicTrendTracker(user_id)
    return tracker.compute_trend(user_id, concept_tag)


def get_trend_summary(user_id: int) -> Dict:
    """Convenience function to get trend summary."""
    tracker = TopicTrendTracker(user_id)
    return tracker.get_trend_summary()