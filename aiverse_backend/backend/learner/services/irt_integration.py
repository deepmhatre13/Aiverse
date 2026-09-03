"""
IRT (Item Response Theory) Integration Service

Integrates with ML service to estimate learner ability and select problems by difficulty.
"""

from typing import List, Dict, Optional
from django.contrib.auth import get_user_model
from django.core.cache import cache
from tracking.models import LearnerEvent
from learn.models import CodingProblem
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)
User = get_user_model()


class IRTIntegrationService:
    """Service for integrating with IRT ML service."""
    
    def __init__(self):
        self.ml_service_url = getattr(settings, 'ML_SERVICE_URL', 'http://localhost:8001')
        self.cache_ttl = 3600  # 1 hour
    
    def get_learner_ability(self, user_id: int, events: List[LearnerEvent] = None) -> float:
        """
        Get learner ability estimate (theta) from IRT model.
        
        Args:
            user_id: User ID
            events: Optional list of recent LearnerEvents. If None, fetches from DB.
            
        Returns:
            float: Theta estimate (typically -3 to 3)
        """
        # Check cache first
        cache_key = f"learner_ability:{user_id}"
        cached_ability = cache.get(cache_key)
        if cached_ability is not None:
            return cached_ability
        
        try:
            # Fetch recent events if not provided
            if events is None:
                from django.utils import timezone
                from datetime import timedelta
                events = LearnerEvent.objects.filter(
                    user_id=user_id,
                    timestamp__gte=timezone.now() - timedelta(days=30)
                ).order_by('-timestamp')[:50]
            
            # Prepare request data
            event_data = []
            for event in events:
                event_data.append({
                    'event_type': event.event_type,
                    'content_type': event.content_type,
                    'content_id': event.content_id,
                    'metadata': event.metadata or {}
                })
            
            # Call ML service
            response = requests.post(
                f"{self.ml_service_url}/ml/irt/estimate-ability",
                json={
                    'user_id': user_id,
                    'events': event_data
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                theta = data.get('theta', 0.0)
                
                # Cache result
                cache.set(cache_key, theta, self.cache_ttl)
                
                logger.info(f"Estimated ability for user {user_id}: {theta}")
                return theta
            else:
                logger.error(f"IRT service error: {response.status_code} - {response.text}")
                return 0.0
                
        except Exception as e:
            logger.error(f"Error estimating ability for user {user_id}: {str(e)}")
            return 0.0
    
    def select_problem_by_difficulty(self, ability: float, concept_tag: str, 
                                      difficulty_tolerance: float = 0.5) -> Optional[Dict]:
        """
        Select a problem matching learner's ability level.
        
        Args:
            ability: Learner's theta estimate
            concept_tag: Concept tag to filter by
            difficulty_tolerance: How far from ability to select (+/-)
            
        Returns:
            Dict with problem info, or None if no match
        """
        try:
            # Get problems for concept
            problems = CodingProblem.objects.filter(
                concept_tag=concept_tag,
                is_active=True
            )
            
            if not problems.exists():
                return None
            
            # Try to use IRT difficulty if available
            problems_with_irt = problems.filter(irt_difficulty__isnull=False)
            
            if problems_with_irt.exists():
                # Use IRT difficulty
                target_difficulty = ability
                min_diff = target_difficulty - difficulty_tolerance
                max_diff = target_difficulty + difficulty_tolerance
                
                # Filter by difficulty range
                candidates = problems_with_irt.filter(
                    irt_difficulty__gte=min_diff,
                    irt_difficulty__lte=max_diff
                )
                
                if candidates.exists():
                    # Select closest to target
                    best = min(candidates, key=lambda p: abs(p.irt_difficulty - target_difficulty))
                    return {
                        'problem_id': best.id,
                        'title': best.title,
                        'difficulty': best.difficulty,
                        'irt_difficulty': best.irt_difficulty,
                        'concept_tag': best.concept_tag
                    }
            
            # Fallback: use static difficulty mapping
            # Map ability to difficulty level
            if ability < -1.0:
                target_level = 'easy'
            elif ability < 0.5:
                target_level = 'medium'
            elif ability < 1.5:
                target_level = 'hard'
            else:
                target_level = 'expert'
            
            fallback = problems.filter(difficulty=target_level).first()
            if fallback:
                return {
                    'problem_id': fallback.id,
                    'title': fallback.title,
                    'difficulty': fallback.difficulty,
                    'irt_difficulty': None,
                    'concept_tag': fallback.concept_tag
                }
            
            # Ultimate fallback: any problem
            return {
                'problem_id': problems.first().id,
                'title': problems.first().title,
                'difficulty': problems.first().difficulty,
                'irt_difficulty': None,
                'concept_tag': problems.first().concept_tag
            }
            
        except Exception as e:
            logger.error(f"Error selecting problem by difficulty: {str(e)}")
            return None


def get_learner_ability(user_id: int, events: List[LearnerEvent] = None) -> float:
    """
    Convenience function to get learner ability.
    
    Args:
        user_id: User ID
        events: Optional list of recent events
        
    Returns:
        float: Theta estimate
    """
    service = IRTIntegrationService()
    return service.get_learner_ability(user_id, events)


def select_problem_by_difficulty(ability: float, concept_tag: str) -> Optional[Dict]:
    """
    Convenience function to select problem by difficulty.
    
    Args:
        ability: Learner's theta estimate
        concept_tag: Concept tag
        
    Returns:
        Dict with problem info
    """
    service = IRTIntegrationService()
    return service.select_problem_by_difficulty(ability, concept_tag)