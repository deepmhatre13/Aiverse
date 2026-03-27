from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType

from .models import UserActivity


@receiver(post_save, sender='problems.Submission')
def track_submission(sender, instance, created, **kwargs):
    """Track problem submission attempts and results"""
    if created:
        # Track problem attempted
        UserActivity.objects.create(
            user=instance.user,
            activity_type='problem_attempted',
            content_type=ContentType.objects.get_for_model(instance),
            object_id=instance.id
        )
    else:
        # Track submission evaluation result
        if instance.status == 'completed':
            if instance.score >= 70:  # Success threshold
                activity_type = 'submission_success'
            else:
                activity_type = 'submission_failed'
            
            UserActivity.objects.get_or_create(
                user=instance.user,
                activity_type=activity_type,
                content_type=ContentType.objects.get_for_model(instance),
                object_id=instance.id,
                defaults={'user': instance.user}
            )


@receiver(post_save, sender='learn.VideoProgress')
def track_video_completion(sender, instance, created, **kwargs):
    """Track when a user completes a video"""
    if instance.completed and not created:
        # Check if activity already exists to avoid duplicates
        exists = UserActivity.objects.filter(
            user=instance.user,
            activity_type='video_watched',
            content_type=ContentType.objects.get_for_model(instance.video),
            object_id=instance.video.id
        ).exists()
        
        if not exists:
            UserActivity.objects.create(
                user=instance.user,
                activity_type='video_watched',
                content_type=ContentType.objects.get_for_model(instance.video),
                object_id=instance.video.id
            )


@receiver(post_save, sender='payments.Payment')
def track_course_purchase(sender, instance, created, **kwargs):
    """Track course purchases"""
    if created and instance.status == 'completed' and instance.course:
        UserActivity.objects.create(
            user=instance.user,
            activity_type='course_purchased',
            content_type=ContentType.objects.get_for_model(instance.course),
            object_id=instance.course.id
        )


@receiver(post_save, sender='mentor.MentorMessage')
def track_mentor_question(sender, instance, created, **kwargs):
    """Track mentor questions"""
    if created and instance.role == 'user':
        UserActivity.objects.create(
            user=instance.session.user,
            activity_type='mentor_question',
            content_type=ContentType.objects.get_for_model(instance),
            object_id=instance.id
        )

        