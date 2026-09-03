"""
Spaced Repetition Revision Scheduler

Calculates optimal review intervals using SM-2 algorithm adapted for BKT decay.
"""

from datetime import datetime, timedelta
from typing import Optional
from django.utils import timezone
from learner.models import ConceptMastery
from tracking.models import LearnerEvent
import logging

logger = logging.getLogger(__name__)


class RevisionScheduler:
    """
    Calculates when a concept should be reviewed next based on mastery and review history.
    
    Uses SM-2 algorithm adapted for BKT decay rates.
    """
    
    def __init__(self, concept_mastery: ConceptMastery):
        self.mastery = concept_mastery
        self.user_id = concept_mastery.user_id
        self.concept_tag = concept_mastery.concept_tag
    
    def calculate_next_review(self) -> Optional[datetime]:
        """
        Calculate next review date for this concept.
        
        Returns:
            datetime: When to review next, or None if no review needed
        """
        # Get review history from LearnerEvent
        review_events = self._get_review_history()
        
        # Get current mastery
        mastery_score = self.mastery.mastery_score
        bkt_trace = self.mastery.bkt_trace or []
        
        # Calculate decay rate from bkt_trace
        decay_rate = self._calculate_decay_rate(bkt_trace)
        
        # Calculate days since last review
        days_since_last_review = self._days_since_last_review(review_events)
        
        # SM-2 adapted algorithm
        if mastery_score >= 0.9:
            # Mastered: review after 30 days
            interval = 30
        elif mastery_score >= 0.8:
            # Strong: review after 14 days
            interval = 14
        elif mastery_score >= 0.7:
            # Approaching mastery: review after 7 days
            interval = 7
        elif mastery_score >= 0.4:
            # Unmastered: review after 3 days
            interval = 3
        else:
            # Struggling: review after 1 day
            interval = 1
        
        # Adjust interval based on decay rate
        # Higher decay = shorter interval
        if decay_rate > 0.1:  # Rapid decay
            interval = max(1, int(interval * 0.5))
        elif decay_rate > 0.05:  # Moderate decay
            interval = max(1, int(interval * 0.7))
        
        # Adjust based on number of reviews (more reviews = longer interval)
        review_count = len(review_events)
        if review_count > 5:
            interval = int(interval * 1.2)
        elif review_count > 10:
            interval = int(interval * 1.5)
        
        # If last review was recent and mastery is high, extend interval
        if days_since_last_review < interval and mastery_score >= 0.7:
            remaining_days = interval - days_since_last_review
            return timezone.now() + timedelta(days=remaining_days)
        
        # If overdue or first review, schedule immediately
        return timezone.now() + timedelta(days=interval)
    
    def _get_review_history(self) -> list:
        """Get history of review events for this concept."""
        return LearnerEvent.objects.filter(
            user_id=self.user_id,
            event_type__in=['QUIZ_PASSED', 'CODE_PASSED', 'LESSON_COMPLETED'],
            metadata__concept_tag=self.concept_tag
        ).order_by('-timestamp')[:20]
    
    def _calculate_decay_rate(self, bkt_trace: list) -> float:
        """
        Calculate decay rate from BKT trace.
        
        Decay rate = average slope of last 5 mastery estimates.
        Positive slope = improving, negative = decaying.
        """
        if len(bkt_trace) < 2:
            return 0.0
        
        # Get last 5 trace values
        recent = bkt_trace[-5:] if len(bkt_trace) >= 5 else bkt_trace
        
        # Calculate average change per step
        changes = []
        for i in range(1, len(recent)):
            change = recent[i] - recent[i-1]
            changes.append(change)
        
        if not changes:
            return 0.0
        
        avg_change = sum(changes) / len(changes)
        # Return decay rate (negative change = positive decay rate)
        return max(0.0, -avg_change)
    
    def _days_since_last_review(self, review_events: list) -> int:
        """Calculate days since last review event."""
        if not review_events:
            return 999  # Never reviewed
        
        last_review = review_events[0].timestamp
        delta = timezone.now() - last_review
        return delta.days


def schedule_revision_for_user(user_id: int):
    """
    Schedule revision recommendations for all concepts needing review.
    
    Args:
        user_id: User ID
    """
    from recommendations.models import Recommendation
    
    masteries = ConceptMastery.objects.filter(user_id=user_id)
    
    for mastery in masteries:
        scheduler = RevisionScheduler(mastery)
        next_review = scheduler.calculate_next_review()
        
        if next_review:
            # Check if revision is due within next 24 hours
            time_until_review = (next_review - timezone.now()).total_seconds() / 3600
            
            if time_until_review <= 24:
                # Create or update revision recommendation
                rec, created = Recommendation.objects.get_or_create(
                    user_id=user_id,
                    recommendation_type='revision',
                    content_type='lesson',
                    content_id=mastery.concept_tag,
                    defaults={
                        'score': 0.9,
                        'reason': f"Revision due: {mastery.concept_tag}",
                        'source': 'ml_model',
                        'expires_at': next_review
                    }
                )
                
                if not created:
                    # Update existing
                    rec.expires_at = next_review
                    rec.is_dismissed = False
                    rec.save(update_fields=['expires_at', 'is_dismissed'])