"""
Celery tasks for learner app.
"""

from celery import shared_task
from django.contrib.auth import get_user_model
from learner.models import ConceptMastery, LearnerProfile
from learner.services.path_generator import get_learning_path_for_user
from recommendations.models import Recommendation
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task
def recalculate_learning_path(user_id: int):
    """
    Recalculate learning path for a user.
    
    Triggered on:
    - LearnerEvent: QUIZ_PASSED, CODE_PASSED, CODE_FAILED
    - Manual trigger
    
    Args:
        user_id: User ID
    """
    try:
        logger.info(f"Recalculating learning path for user {user_id}")
        
        # Recompute all concept masteries
        masteries = ConceptMastery.objects.filter(user_id=user_id)
        for mastery in masteries:
            mastery.recompute_mastery()
        
        # Generate new learning path
        path_data = get_learning_path_for_user(user_id)
        
        # Update or create LearningPath model
        learning_path, created = LearningPath.objects.update_or_create(
            user_id=user_id,
            defaults={
                'ordered_lesson_ids': [lesson['lesson_id'] for lesson in path_data['ordered_lessons']],
                'is_adaptive': True
            }
        )
        
        # Invalidate old next_lesson recommendations
        Recommendation.objects.filter(
            user_id=user_id,
            recommendation_type='next_lesson',
            is_dismissed=False
        ).update(is_dismissed=True)
        
        # Create new next_lesson recommendations
        for lesson in path_data['ordered_lessons'][:5]:  # Top 5
            Recommendation.objects.create(
                user_id=user_id,
                recommendation_type='next_lesson',
                content_type='lesson',
                content_id=lesson['lesson_id'],
                score=1.0,
                reason=f"Personalized path: {lesson['concept_tag']}",
                source='ml_model'
            )
        
        logger.info(f"Learning path recalculated for user {user_id}: {len(path_data['ordered_lessons'])} lessons")
        return {"status": "success", "user_id": user_id, "lessons_count": len(path_data['ordered_lessons'])}
        
    except Exception as e:
        logger.error(f"Error recalculating learning path for user {user_id}: {str(e)}")
        return {"status": "error", "user_id": user_id, "error": str(e)}


@shared_task
def generate_revision_recommendations(user_id: int):
    """
    Generate spaced repetition revision recommendations for a user.
    
    Runs daily for all active users.
    """
    try:
        from learner.services.revision_scheduler import RevisionScheduler
        
        logger.info(f"Generating revision recommendations for user {user_id}")
        
        # Get all concept masteries
        masteries = ConceptMastery.objects.filter(user_id=user_id)
        
        revision_count = 0
        for mastery in masteries:
            # Check if revision is due
            if mastery.gap_detected or mastery.mastery_score < 0.6:
                scheduler = RevisionScheduler(mastery)
                next_review = scheduler.calculate_next_review()
                
                if next_review and next_review <= timezone.now():
                    # Create revision recommendation
                    Recommendation.objects.create(
                        user_id=user_id,
                        recommendation_type='revision',
                        content_type='lesson',
                        content_id=mastery.concept_tag,  # Will be resolved to actual lesson
                        score=0.9,
                        reason=f"Revision due: {mastery.concept_tag}",
                        source='ml_model',
                        expires_at=next_review
                    )
                    revision_count += 1
        
        logger.info(f"Generated {revision_count} revision recommendations for user {user_id}")
        return {"status": "success", "user_id": user_id, "revisions_created": revision_count}
        
    except Exception as e:
        logger.error(f"Error generating revision recommendations for user {user_id}: {str(e)}")
        return {"status": "error", "user_id": user_id, "error": str(e)}


@shared_task
def process_event_for_mastery(event_id: str):
    """
    Process a learner event and update concept mastery.
    
    Triggered after every quiz/code event.
    """
    from tracking.models import LearnerEvent
    from django.utils import timezone
    
    try:
        logger.info(f"Processing event {event_id} for mastery update")
        
        event = LearnerEvent.objects.get(id=event_id)
        user_id = event.user_id
        event_type = event.event_type
        metadata = event.metadata or {}
        concept_tag = metadata.get('concept_tag')
        
        if not concept_tag:
            logger.warning(f"No concept_tag in event {event_id}")
            return {"status": "skipped", "reason": "no concept_tag"}
        
        # Get or create ConceptMastery
        mastery, created = ConceptMastery.objects.get_or_create(
            user_id=user_id,
            concept_tag=concept_tag
        )
        
        # Update attempt counts
        if event_type in ['QUIZ_PASSED', 'QUIZ_FAILED', 'QUIZ_SUBMITTED']:
            mastery.quiz_attempts += 1
        elif event_type in ['CODE_PASSED', 'CODE_FAILED', 'CODE_SUBMITTED']:
            mastery.coding_attempts += 1
        
        # Recompute mastery
        mastery.recompute_mastery()

        # Persist the attempt counters: recompute_mastery() saves via
        # update_fields (which excludes quiz/coding_attempts), so a fresh
        # get_or_create row would otherwise leave the counter at its DB
        # default (0) even after the increment above. Save it explicitly.
        mastery.save(update_fields=["quiz_attempts", "coding_attempts"])

        # Close the live intelligence loop: event -> ConceptMastery ->
        # canonical LearnerProfile (weak/strong/overall/skill). Previously the
        # profile was only refreshed by the nightly batch, so the
        # /api/learner/profile/ view lagged behind the latest mastery. Running
        # the existing WeakTopicAnalyzer sync here keeps it current without an
        # extra broker hop (this task already runs inside a worker).
        try:
            from learner.services.weak_topic_analyzer import (
                update_learner_profile_topics as _update_profile,
            )
            _update_profile(user_id)
        except Exception as exc:  # never break event processing over a hiccup
            logger.warning(
                f"process_event_for_mastery: profile sync failed for user {user_id}: {exc}"
            )
        
        logger.info(f"Updated mastery for user {user_id}, concept {concept_tag}: {mastery.mastery_score}")
        
        # Trigger learning path recalculation for key events
        if event_type in ['QUIZ_PASSED', 'CODE_PASSED', 'CODE_FAILED']:
            recalculate_learning_path.delay(user_id)
        
        return {
            "status": "success",
            "user_id": user_id,
            "concept_tag": concept_tag,
            "mastery_score": mastery.mastery_score,
            "is_struggling": mastery.is_struggling
        }
        
    except LearnerEvent.DoesNotExist:
        logger.error(f"Event {event_id} not found")
        return {"status": "error", "reason": "event_not_found"}
    except Exception as e:
        logger.error(f"Error processing event {event_id}: {str(e)}")
        return {"status": "error", "error": str(e)}


@shared_task
def update_learner_ability(user_id: int):
    """
    Update learner ability estimate using IRT.
    
    Triggered periodically and after key events.
    """
    try:
        from tracking.models import LearnerEvent
        from learner.services.irt_integration import get_learner_ability
        
        logger.info(f"Updating learner ability for user {user_id}")
        
        # Get recent events
        recent_events = LearnerEvent.objects.filter(
            user_id=user_id,
            timestamp__gte=timezone.now() - timezone.timedelta(days=30)
        ).order_by('-timestamp')[:50]
        
        if not recent_events:
            logger.warning(f"No recent events for user {user_id}")
            return {"status": "skipped", "reason": "no_events"}
        
        # Get ability estimate
        ability = get_learner_ability(user_id, recent_events)
        
        # Update LearnerProfile
        profile, created = LearnerProfile.objects.get_or_create(user_id=user_id)
        profile.learner_ability = ability
        profile.save(update_fields=['learner_ability'])
        
        logger.info(f"Updated learner ability for user {user_id}: {ability}")
        return {"status": "success", "user_id": user_id, "ability": ability}
        
    except Exception as e:
        logger.error(f"Error updating learner ability for user {user_id}: {str(e)}")
        return {"status": "error", "error": str(e)}


@shared_task
def calibrate_difficulty_irt():
    """
    Nightly task to calibrate problem/question difficulties using IRT.
    
    Updates CodingProblem and Quiz models with computed difficulty parameters.
    """
    try:
        from ml.models import Submission
        from aiverse_ml_service.routers.irt import IRTModel
        import numpy as np
        
        logger.info("Starting IRT difficulty calibration")
        
        # Get submissions from past week
        week_ago = timezone.now() - timezone.timedelta(days=7)
        submissions = Submission.objects.filter(
            created_at__gte=week_ago
        ).select_related('problem', 'user')
        
        # Group by problem
        from collections import defaultdict
        problem_responses = defaultdict(list)
        for sub in submissions:
            problem_responses[sub.problem_id].append({
                'user_id': sub.user_id,
                'score': sub.score
            })
        
        calibrated_count = 0
        for problem_id, responses in problem_responses.items():
            if len(responses) < 5:  # Need minimum responses
                continue
            
            # Fit IRT model (simplified)
            # In production, use proper IRT calibration
            correct = [1 if r['score'] >= 70 else 0 for r in responses]
            
            # Placeholder: compute difficulty as 1 - success rate
            difficulty = 1.0 - (sum(correct) / len(correct))
            discrimination = 0.5  # Placeholder
            
            # Update CodingProblem
            from learn.models import CodingProblem
            try:
                problem = CodingProblem.objects.get(id=problem_id)
                problem.irt_difficulty = difficulty
                problem.irt_discrimination = discrimination
                problem.irt_guessing = 0.25  # 4-choice MCQ guessing
                problem.save(update_fields=['irt_difficulty', 'irt_discrimination', 'irt_guessing'])
                calibrated_count += 1
            except CodingProblem.DoesNotExist:
                pass
        
        logger.info(f"Calibrated IRT difficulty for {calibrated_count} problems")
        return {"status": "success", "calibrated_count": calibrated_count}
        
    except Exception as e:
        logger.error(f"Error in IRT calibration: {str(e)}")
        return {"status": "error", "error": str(e)}


@shared_task
def batch_recalculate_learning_paths():
    """
    Nightly batch task to recalculate learning paths for all active users.
    
    Only processes users active in the last 7 days.
    """
    try:
        from django.utils import timezone
        
        logger.info("Starting batch learning path recalculation")
        
        week_ago = timezone.now() - timezone.timedelta(days=7)
        active_users = User.objects.filter(
            last_login__gte=week_ago
        ).values_list('id', flat=True)
        
        count = 0
        for user_id in active_users:
            recalculate_learning_path.delay(user_id)
            count += 1
        
        logger.info(f"Queued learning path recalculation for {count} users")
        return {"status": "success", "users_queued": count}
        
    except Exception as e:
        logger.error(f"Error in batch recalculation: {str(e)}")
        return {"status": "error", "error": str(e)}


@shared_task
def update_learner_profile_topics(user_id: int):
    """
    Update learner profile with weak/strong topics and overall mastery.
    
    Triggered after learning path recalculation.
    """
    try:
        from learner.services.weak_topic_analyzer import update_learner_profile_topics as update_profile
        
        logger.info(f"Updating learner profile topics for user {user_id}")
        
        result = update_profile(user_id)
        
        logger.info(
            f"Updated profile for user {user_id}: "
            f"mastery={result['overall_mastery']:.2f}, "
            f"level={result['estimated_skill_level']}"
        )
        
        return {
            "status": "success",
            "user_id": user_id,
            "overall_mastery": result['overall_mastery'],
            "weak_count": result['weak_count'],
            "strong_count": result['strong_count']
        }
        
    except Exception as e:
        logger.error(f"Error updating learner profile for user {user_id}: {str(e)}")
        return {"status": "error", "user_id": user_id, "error": str(e)}


@shared_task
def batch_update_learner_profiles():
    """
    Nightly batch task to update learner profiles for all active users.
    """
    try:
        from django.utils import timezone
        from datetime import timedelta
        
        logger.info("Starting batch learner profile update")
        
        week_ago = timezone.now() - timedelta(days=7)
        active_users = User.objects.filter(
            last_login__gte=week_ago
        ).values_list('id', flat=True)
        
        count = 0
        for user_id in active_users:
            update_learner_profile_topics.delay(user_id)
            count += 1
        
        logger.info(f"Queued profile update for {count} users")
        return {"status": "success", "users_queued": count}
        
    except Exception as e:
        logger.error(f"Error in batch profile update: {str(e)}")
        return {"status": "error", "error": str(e)}
