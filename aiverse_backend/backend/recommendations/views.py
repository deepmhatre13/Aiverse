from datetime import timedelta

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from learner.models import ConceptMastery, LearnerProfile
from learn.models import CodingProblem, Enrollment, Lesson
from tracking.models import LearnerEvent

from .models import Recommendation
from .serializers import RecommendationSerializer
from .services import RuleBasedRecommender
from .ml_client import call_ml_service


class RecommendationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        recs = Recommendation.objects.filter(
            user=request.user,
            is_dismissed=False
        ).order_by('-score')[:10]

        if not recs.exists():
            # Generate on-demand if none exist
            recommender = RuleBasedRecommender(request.user.id)
            recommender.generate_and_cache()
            recs = Recommendation.objects.filter(
                user=request.user, is_dismissed=False
            ).order_by('-score')[:10]

        serializer = RecommendationSerializer(recs, many=True)
        return Response(serializer.data)


def _compute_learning_pace(user) -> float:
    four_weeks_ago = timezone.now() - timedelta(weeks=4)
    count = LearnerEvent.objects.filter(
        user=user,
        event_type="LESSON_COMPLETED",
        timestamp__gte=four_weeks_ago,
    ).count()
    return round(count / 4.0, 2)


def _enrich_ml_recommendations(ml_recs: list) -> list:
    lesson_ids = [r["content_id"] for r in ml_recs if r.get("content_type") == "lesson"]
    lessons = {l.id: l for l in Lesson.objects.filter(id__in=lesson_ids).select_related("course")}
    enriched = []
    for rec in ml_recs:
        lesson = lessons.get(rec["content_id"])
        if not lesson:
            continue
        enriched.append({
            "id": rec["content_id"],
            "content_id": rec["content_id"],
            "content_type": "lesson",
            "course_id": lesson.course_id,
            "title": lesson.title,
            "slug": lesson.slug,
            "concept_tag": rec.get("concept_tag") or lesson.concept_tag,
            "difficulty": rec.get("difficulty") or lesson.difficulty,
            "course_slug": lesson.course.slug if lesson.course_id else None,
            "recommendation_type": rec.get("recommendation_type", "next"),
            "final_score": rec.get("final_score", 0),
            "score": rec.get("final_score", 0),
            "explanation": rec.get("explanation", ""),
            "why_badge": rec.get("why_badge", ""),
            "reason": rec.get("explanation", ""),
            "mastery_after": rec.get("mastery_after"),
        })
    return enriched


class PersonalisedRecommendationsView(APIView):
    """GET /api/recommendations/personalised/ — ML-driven recommendations."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        profile, _ = LearnerProfile.objects.get_or_create(user=user)
        masteries = ConceptMastery.objects.filter(user=user)

        completed_lessons = list(
            LearnerEvent.objects.filter(
                user=user, event_type="LESSON_COMPLETED", content_type="lesson"
            ).values_list("content_id", flat=True).distinct()
        )
        completed_problems = list(
            LearnerEvent.objects.filter(
                user=user,
                event_type__in=["CODE_PASSED", "PROBLEM_SOLVED"],
                content_type="problem",
            ).values_list("content_id", flat=True).distinct()
        )

        bkt_histories = {}
        quiz_events = LearnerEvent.objects.filter(
            user=user,
            content_type="quiz",
            event_type__in=["QUIZ_PASSED", "QUIZ_FAILED"],
        ).order_by("timestamp")
        for event in quiz_events:
            concept = (event.metadata or {}).get("concept_tag")
            if concept:
                bkt_histories.setdefault(concept, []).append(
                    event.event_type == "QUIZ_PASSED"
                )
        problem_responses = [
            {
                "problem_id": e.content_id,
                "correct": e.event_type == "CODE_PASSED",
            }
            for e in LearnerEvent.objects.filter(
                user=user,
                content_type="problem",
                event_type__in=["CODE_PASSED", "CODE_FAILED"],
            ).order_by("-timestamp")[:100]
            if e.content_id
        ]
        payload = {
            "user_id": user.id,
            "skill_level": profile.estimated_skill_level,
            "completed_lesson_ids": completed_lessons,
            "completed_problem_ids": completed_problems,
            "weak_concepts": profile.weak_concepts or [],
            "mastery_scores": {m.concept_tag: m.mastery_score for m in masteries},
            "bkt_histories": bkt_histories,
            "enrolled_course_ids": list(
                Enrollment.objects.filter(user=user, status="active").values_list("course_id", flat=True)
            ),
            "days_inactive": (
                (timezone.now() - profile.last_active).days if profile.last_active else 0
            ),
            "learning_pace": _compute_learning_pace(user),
            "problem_responses": problem_responses,
            "n_recommendations": 10,
        }

        ml_result = call_ml_service("/ml/recommend/", payload)
        if ml_result and ml_result.get("recommendations"):
            learner_ability = float(ml_result.get("learner_ability", 0.0))
            if learner_ability != 0.0:
                profile.learner_ability = learner_ability
                profile.save(update_fields=["learner_ability", "last_updated"])
            return Response({
                "recommendations": _enrich_ml_recommendations(ml_result["recommendations"]),
                "model_version": ml_result.get("model_version", "unknown"),
                "is_personalised": ml_result.get("is_personalised", False),
                "learner_ability": learner_ability,
            })

        recommender = RuleBasedRecommender(user.id)
        recs = recommender.generate_and_cache()
        payload = build_personalized_learn_response(user)
        return Response({
            "recommendations": RecommendationSerializer(recs, many=True).data,
            "model_version": payload.get('model_version', 'rule_based_fallback'),
            "is_personalised": payload.get('is_personalised', True),
            "learner_ability": profile.learner_ability,
            "continue_learning": payload.get('continue_learning', []),
            "recommended_for_you": payload.get('recommended_for_you', []),
            "missing_prerequisites": payload.get('missing_prerequisites', []),
            "strengthen_weak_areas": payload.get('strengthen_weak_areas', []),
            "next_best_lesson": payload.get('next_best_lesson'),
            "current_learning_path": payload.get('current_learning_path', []),
        })


class ProblemNextRecommendationsView(APIView):
    """GET /api/recommendations/after-problem/<slug>/"""

    permission_classes = [IsAuthenticated]

    def get(self, request, slug):
        problem = get_object_or_404(CodingProblem, slug=slug, is_active=True)
        user = request.user

        try:
            mastery = ConceptMastery.objects.get(user=user, concept_tag=problem.concept_tag)
            p_known = mastery.mastery_score
        except ConceptMastery.DoesNotExist:
            p_known = 0.0

        ml_map = call_ml_service("/ml/graph/problem-lessons/", {"problem_id": problem.id})
        if ml_map and ml_map.get("related"):
            related_lesson_ids = [r["lesson_id"] for r in ml_map["related"]]
        else:
            related_lesson_ids = list(
                Lesson.objects.filter(concept_tag=problem.concept_tag, is_active=True)
                .values_list("id", flat=True)[:3]
            )

        related_lessons = Lesson.objects.filter(id__in=related_lesson_ids)
        difficulty_order = ["easy", "medium", "hard", "expert"]
        try:
            idx = difficulty_order.index(problem.difficulty)
            next_difficulty = difficulty_order[min(idx + (1 if p_known >= 0.6 else 0), 3)]
        except ValueError:
            next_difficulty = problem.difficulty

        next_problems = CodingProblem.objects.filter(
            concept_tag=problem.concept_tag,
            difficulty=next_difficulty,
            is_active=True,
        ).exclude(id=problem.id).order_by("order")[:2]

        label = problem.concept_tag.replace("_", " ")
        if p_known < 0.35:
            message = (
                f"Your mastery of {label} is at {round(p_known * 100)}%. "
                "Review the linked lessons before attempting harder problems."
            )
        elif p_known < 0.65:
            message = (
                f"Good progress on {label} ({round(p_known * 100)}% mastery). "
                "Try the next problem or revise with the linked lesson."
            )
        else:
            message = (
                f"Strong mastery of {label} ({round(p_known * 100)}%). "
                "You're ready for a harder challenge."
            )

        return Response({
            "current_problem": {
                "slug": problem.slug,
                "title": problem.title,
                "concept_tag": problem.concept_tag,
            },
            "user_mastery_on_concept": round(p_known * 100),
            "related_lessons": [
                {
                    "id": l.id,
                    "title": l.title,
                    "slug": l.slug,
                    "concept_tag": l.concept_tag,
                    "difficulty": l.difficulty,
                    "course_slug": l.course.slug,
                }
                for l in related_lessons
            ],
            "next_problems": [
                {
                    "id": p.id,
                    "slug": p.slug,
                    "title": p.title,
                    "difficulty": p.difficulty,
                    "points": p.points,
                    "concept_tag": p.concept_tag,
                }
                for p in next_problems
            ],
            "message": message,
        })


class DismissRecommendationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, rec_id):
        try:
            rec = Recommendation.objects.get(id=rec_id, user=request.user)
            rec.is_dismissed = True
            rec.save()
            return Response({'status': 'dismissed'})
        except Recommendation.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)


class DKTMasteryView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        events = LearnerEvent.objects.filter(
            user=user,
            event_type__in=["QUIZ_PASSED", "QUIZ_FAILED", "CODE_PASSED", "CODE_FAILED"],
        ).order_by("timestamp")

        sequence = []
        for event in events:
            concept = (event.metadata or {}).get("concept_tag")
            if not concept:
                continue
            correct = event.event_type in ("QUIZ_PASSED", "CODE_PASSED")
            sequence.append({"concept": concept, "correct": correct})

        if len(sequence) < 3:
            return Response(
                {"error": "Not enough events for DKT estimate"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = call_ml_service("/ml/dkt/estimate", {
            "user_id": user.id,
            "sequence": sequence,
        })
        if not result:
            return Response(
                {"error": "ML service unavailable"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        mastery_by_concept = result.get("mastery_by_concept", {})
        updated = []
        for concept_tag, score in mastery_by_concept.items():
            obj, _ = ConceptMastery.objects.get_or_create(
                user=user, concept_tag=concept_tag
            )
            obj.mastery_score = round(score, 4)
            obj.is_struggling = score < 0.4
            obj.save(update_fields=["mastery_score", "is_struggling"])
            updated.append({"concept_tag": concept_tag, "mastery": score})

        return Response({
            "model_used": result.get("model_used"),
            "updated_concepts": updated,
        })


class IRTAbilityView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        profile, _ = LearnerProfile.objects.get_or_create(user=user)

        code_events = LearnerEvent.objects.filter(
            user=user,
            content_type="problem",
            event_type__in=["CODE_PASSED", "CODE_FAILED", "PROBLEM_SOLVED"],
        ).order_by("-timestamp")[:100]

        if not code_events.exists():
            return Response({
                "estimated_ability": profile.learner_ability,
                "model_used": "cached",
            })

        responses = [
            {
                "problem_id": e.content_id,
                "correct": e.event_type in ("CODE_PASSED", "PROBLEM_SOLVED"),
            }
            for e in code_events if e.content_id
        ]

        result = call_ml_service("/ml/irt/ability", {
            "user_id": user.id,
            "responses": responses,
        })
        if not result:
            return Response({
                "estimated_ability": profile.learner_ability,
                "model_used": "cached",
            })

        ability = result.get("estimated_ability", 0.0)
        profile.learner_ability = ability
        profile.save(update_fields=["learner_ability", "last_updated"])

        return Response({
            "estimated_ability": ability,
            "model_used": result.get("model_used"),
        })
