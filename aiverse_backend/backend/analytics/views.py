from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from tracking.models import LearnerEvent
from learner.models import ConceptMastery, LearnerProfile
from learner.services.thresholds import classify_mastery_score
from django.db.models import Count, Avg
from django.utils import timezone
from datetime import timedelta


class LearnerDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        profile, _ = LearnerProfile.objects.get_or_create(user=user)
        masteries = ConceptMastery.objects.filter(user=user)
        events = LearnerEvent.objects.filter(user=user)

        # Activity last 7 days
        week_ago = timezone.now() - timedelta(days=7)
        daily_activity = (
            events.filter(timestamp__gte=week_ago)
            .extra(select={'day': "date(timestamp)"})
            .values('day')
            .annotate(count=Count('id'))
            .order_by('day')
        )

        # Mastery breakdown
        mastery_data = [
            {
                'concept': m.concept_tag,
                'score': m.mastery_score,
                'struggling': m.is_struggling,
                'readiness': classify_mastery_score(m.mastery_score),
            }
            for m in masteries
        ]
        weak_concepts = [
            m.concept_tag for m in masteries
            if classify_mastery_score(m.mastery_score) in {'missing', 'partially_mastered'}
        ]
        strong_concepts = [
            m.concept_tag for m in masteries
            if classify_mastery_score(m.mastery_score) == 'satisfied'
        ]

        # Recent events
        recent = events.order_by('-timestamp')[:20]
        recent_data = [{'type': e.event_type, 'time': e.timestamp} for e in recent]

        return Response({
            'profile': {
                'skill_level': profile.estimated_skill_level,
                'overall_mastery': profile.overall_mastery,
                'engagement_score': profile.engagement_score,
                'frustration_score': profile.frustration_score,
                'dropout_risk': profile.dropout_risk,
                'weak_concepts': weak_concepts,
                'strong_concepts': strong_concepts,
                'total_lessons': profile.total_lessons_completed,
                'total_problems': profile.total_problems_solved,
                'total_quizzes': profile.total_quizzes_passed,
            },
            'mastery_breakdown': mastery_data,
            'daily_activity': list(daily_activity),
            'recent_events': recent_data,
        })
