from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import ActivityEvent, PerformanceSnapshot


@receiver(post_save, sender='problems.Submission')
def log_submission_activity(sender, instance, created, **kwargs):
    """Log submission activity events"""
    
    if created:
        # Log submission attempt
        ActivityEvent.objects.create(
            user=instance.user,
            event_type='submission',
            reference_id=instance.id,
            metadata={
                'problem_id': instance.problem.id,
                'problem_title': instance.problem.title,
                'status': instance.status
            }
        )
    
    elif instance.status == 'completed':
        # Log submission result
        if instance.score >= 70:
            event_type = 'submission_success'
            
            # Check if this is first solve
            from ml.models import Submission
            is_first_solve = not Submission.objects.filter(
                user=instance.user,
                problem=instance.problem,
                status='completed',
                score__gte=70
            ).exclude(id=instance.id).exists()
            
            if is_first_solve:
                ActivityEvent.objects.create(
                    user=instance.user,
                    event_type='problem_solved',
                    reference_id=instance.problem.id,
                    score_delta=instance.score,
                    metadata={
                        'problem_id': instance.problem.id,
                        'problem_title': instance.problem.title,
                        'score': instance.score,
                        'submission_id': instance.id
                    }
                )
        else:
            event_type = 'submission_fail'
        
        ActivityEvent.objects.create(
            user=instance.user,
            event_type=event_type,
            reference_id=instance.id,
            score_delta=instance.score,
            metadata={
                'problem_id': instance.problem.id,
                'problem_title': instance.problem.title,
                'score': instance.score
            }
        )
        
        # Update daily snapshot
        PerformanceSnapshot.generate_for_date(
            user=instance.user,
            date=instance.submitted_at.date()
        )


@receiver(post_save, sender='learn.VideoProgress')
def log_video_completion(sender, instance, created, **kwargs):
    """Log video completion events"""
    if instance.completed and not created:
        # Check if event already logged
        exists = ActivityEvent.objects.filter(
            user=instance.user,
            event_type='video_completed',
            reference_id=instance.video.id
        ).exists()
        
        if not exists:
            ActivityEvent.objects.create(
                user=instance.user,
                event_type='video_completed',
                reference_id=instance.video.id,
                metadata={
                    'video_id': instance.video.id,
                    'video_title': instance.video.title
                }
            )


@receiver(post_save, sender='mentor.MentorMessage')
def log_mentor_usage(sender, instance, created, **kwargs):
    """Log mentor usage events"""
    if created and instance.role == 'user':
        ActivityEvent.objects.create(
            user=instance.session.user,
            event_type='mentor_used',
            reference_id=instance.session.id,
            metadata={
                'session_id': instance.session.id,
                'question_preview': instance.content[:100]
            }
        )


@receiver(post_save, sender='payments.Payment')
def log_course_purchase(sender, instance, created, **kwargs):
    """Log course purchase events"""
    if created and instance.status == 'completed' and instance.course:
        ActivityEvent.objects.create(
            user=instance.user,
            event_type='course_purchased',
            reference_id=instance.course.id,
            metadata={
                'course_id': instance.course.id,
                'course_title': instance.course.title,
                'amount': float(instance.amount)
            }
        )