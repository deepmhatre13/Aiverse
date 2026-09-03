"""
Run: python manage.py shell < scripts/generate_synthetic_data.py
Generates 50 synthetic learners with realistic event histories.
"""
import django
import os
import random
import uuid
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from tracking.models import LearnerEvent
from learner.models import ConceptMastery
from learner.services import LearnerProfileService
from django.utils import timezone

User = get_user_model()

CONCEPTS = ['python_ml','numpy_pandas','statistics','linear_algebra',
            'regression','classification','evaluation_metrics',
            'gradient_descent','neural_networks','cnn']

LEARNER_ARCHETYPES = {
    'fast_learner': {'quiz_pass_rate': 0.85, 'completion_rate': 0.9, 'activity': 15},
    'average': {'quiz_pass_rate': 0.55, 'completion_rate': 0.6, 'activity': 8},
    'struggling': {'quiz_pass_rate': 0.3, 'completion_rate': 0.4, 'activity': 5},
    'dropout_risk': {'quiz_pass_rate': 0.25, 'completion_rate': 0.2, 'activity': 2},
}

for i in range(50):
    archetype_name = random.choice(list(LEARNER_ARCHETYPES.keys()))
    archetype = LEARNER_ARCHETYPES[archetype_name]

    username = f"synthetic_user_{i+1}_{archetype_name[:3]}"
    user, created = User.objects.get_or_create(username=username)
    if created:
        user.set_password('synthetic123')
        user.save()

    # Generate events over past 30 days
    for day in range(archetype['activity']):
        ts = timezone.now() - timedelta(days=random.randint(0, 30))
        session_id = str(uuid.uuid4())

        # Lesson events
        lesson_id = random.randint(1, 20)
        LearnerEvent.objects.create(
            user=user, event_type='LESSON_OPENED',
            content_type='lesson', content_id=lesson_id,
            session_id=session_id, timestamp=ts,
            metadata={'source': 'synthetic'}
        )
        if random.random() < archetype['completion_rate']:
            LearnerEvent.objects.create(
                user=user, event_type='LESSON_COMPLETED',
                content_type='lesson', content_id=lesson_id,
                session_id=session_id,
                timestamp=ts + timedelta(minutes=random.randint(10, 40)),
                metadata={'time_spent': random.randint(600, 2400), 'source': 'synthetic'}
            )

        # Quiz events
        quiz_id = random.randint(1, 15)
        score = random.uniform(0.6, 1.0) if random.random() < archetype['quiz_pass_rate'] else random.uniform(0.1, 0.5)
        passed = score >= 0.7
        LearnerEvent.objects.create(
            user=user, event_type='QUIZ_SUBMITTED',
            content_type='quiz', content_id=quiz_id,
            session_id=session_id,
            timestamp=ts + timedelta(minutes=45),
            metadata={'score': round(score * 100, 1), 'source': 'synthetic'}
        )
        LearnerEvent.objects.create(
            user=user, event_type='QUIZ_PASSED' if passed else 'QUIZ_FAILED',
            content_type='quiz', content_id=quiz_id,
            session_id=session_id,
            timestamp=ts + timedelta(minutes=46),
            metadata={'score': round(score * 100, 1), 'source': 'synthetic'}
        )

        # Generate mastery for random concepts
        concept = random.choice(CONCEPTS)
        mastery_score = score * 0.8 + random.uniform(0, 0.2)
        mastery_obj, _ = ConceptMastery.objects.get_or_create(user=user, concept_tag=concept)
        mastery_obj.quiz_mastery = round(min(1.0, mastery_score), 4)
        mastery_obj.quiz_attempts += 1
        mastery_obj.recompute_mastery()

    # Recompute full profile
    LearnerProfileService.recompute(user.id)
    print(f"Generated: {username} | Archetype: {archetype_name}")

print("Done. 50 synthetic learners created.")
