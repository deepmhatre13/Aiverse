"""
Views for learner app.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db.models import QuerySet
from typing import Dict, List
from learner.models import ConceptMastery, LearnerProfile
from learner.services.path_generator import get_learning_path_for_user
from learner.services.weak_topic_analyzer import WeakTopicAnalyzer
from learner.serializers import (
    LearningPathSerializer,
    KnowledgeGapSerializer,
    KnowledgeGapWidgetSerializer,
    ConceptMasterySerializer,
    LearnerProfileSerializer,
    MasteryHistorySerializer,
    PrerequisiteResolutionSerializer,
)
import logging

logger = logging.getLogger(__name__)


class LearningPathView(APIView):
    """
    Get personalized learning path for authenticated user.
    
    Returns ordered lessons, current focus concept, estimated completion time,
    and mastery vector across all concept tags.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            user_id = request.user.id
            path_data = get_learning_path_for_user(user_id)
            
            serializer = LearningPathSerializer(path_data)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Error generating learning path for user {request.user.id}: {str(e)}")
            return Response(
                {"error": "Failed to generate learning path"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class KnowledgeGapView(APIView):
    """
    List all knowledge gaps for authenticated user.
    
    Knowledge gaps are concepts where:
    - mastery_score < 0.4
    - Total attempts (quiz + coding) >= 3
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            user = request.user
            
            # Get concept masteries where gap is detected
            gaps = ConceptMastery.objects.filter(
                user=user,
                gap_detected=True
            ).order_by('mastery_score')  # Worst first
            
            if not gaps.exists():
                return Response({
                    "gaps": [],
                    "total_gaps": 0,
                    "message": "No knowledge gaps detected. Keep learning!"
                })
            
            # Build response with suggested actions
            gap_data = []
            for mastery in gaps:
                suggested_actions = self._get_suggested_actions(mastery)
                priority = self._get_priority(mastery)
                
                gap_data.append({
                    "concept_tag": mastery.concept_tag,
                    "mastery_score": mastery.mastery_score,
                    "quiz_attempts": mastery.quiz_attempts,
                    "coding_attempts": mastery.coding_attempts,
                    "suggested_actions": suggested_actions,
                    "priority": priority
                })
            
            serializer = KnowledgeGapSerializer(gap_data, many=True)
            return Response({
                "gaps": serializer.data,
                "total_gaps": len(gap_data)
            })
        
        except Exception as e:
            logger.error(f"Error fetching knowledge gaps for user {request.user.id}: {str(e)}")
            return Response(
                {"error": "Failed to fetch knowledge gaps"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_suggested_actions(self, mastery: ConceptMastery) -> list:
        """Generate suggested actions based on attempt patterns."""
        actions = []
        
        # Always suggest reviewing the lesson first
        actions.append("review_lesson")
        
        # If more quiz attempts, suggest coding practice
        if mastery.quiz_attempts > mastery.coding_attempts:
            actions.append("practice_coding_problems")
        # If more coding attempts, suggest more quizzes and lessons
        elif mastery.coding_attempts > mastery.quiz_attempts:
            actions.append("take_quiz")
            actions.append("review_related_lessons")
        else:
            # Balanced: suggest both
            actions.append("practice_coding_problems")
            actions.append("take_quiz")
        
        # Always suggest mentor session for struggling concepts
        actions.append("mentor_session")
        
        return actions
    
    def _get_priority(self, mastery: ConceptMastery) -> str:
        """Determine priority level based on mastery and attempts."""
        if mastery.mastery_score < 0.2 or mastery.quiz_attempts + mastery.coding_attempts >= 7:
            return "critical"
        elif mastery.mastery_score < 0.3 or mastery.quiz_attempts + mastery.coding_attempts >= 5:
            return "high"
        else:
            return "medium"


class KnowledgeGapWidgetView(APIView):
    """
    Dashboard widget data for knowledge gaps.
    
    Returns simplified gap data optimized for frontend widgets.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            user = request.user
            
            # Get top 5 knowledge gaps
            gaps = ConceptMastery.objects.filter(
                user=user,
                gap_detected=True
            ).order_by('mastery_score')[:5]
            
            gap_data = []
            for mastery in gaps:
                gap_data.append({
                    "concept_tag": mastery.concept_tag,
                    "mastery_score": mastery.mastery_score,
                    "quiz_attempts": mastery.quiz_attempts,
                    "coding_attempts": mastery.coding_attempts,
                    "suggested_actions": self._get_suggested_actions(mastery),
                    "priority": self._get_priority(mastery)
                })
            
            serializer = KnowledgeGapWidgetSerializer({
                "gaps": gap_data,
                "total_gaps": ConceptMastery.objects.filter(user=user, gap_detected=True).count()
            })
            
            return Response(serializer.data)
        
        except Exception as e:
            logger.error(f"Error fetching knowledge gap widget for user {request.user.id}: {str(e)}")
            return Response(
                {"error": "Failed to fetch widget data"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_suggested_actions(self, mastery: ConceptMastery) -> list:
        """Generate suggested actions based on attempt patterns."""
        actions = []
        
        if mastery.quiz_attempts > mastery.coding_attempts:
            actions.append("practice_coding_problems")
        elif mastery.coding_attempts > mastery.quiz_attempts:
            actions.append("take_quiz")
        else:
            actions.append("practice_coding_problems")
            actions.append("take_quiz")
        
        actions.append("mentor_session")
        return actions
    
    def _get_priority(self, mastery: ConceptMastery) -> str:
        """Determine priority level."""
        if mastery.mastery_score < 0.2 or mastery.quiz_attempts + mastery.coding_attempts >= 7:
            return "critical"
        elif mastery.mastery_score < 0.3 or mastery.quiz_attempts + mastery.coding_attempts >= 5:
            return "high"
        else:
            return "medium"


class ConceptMasteryListView(APIView):
    """
    List all concept mastery records for authenticated user.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            user = request.user
            masteries = ConceptMastery.objects.filter(user=user).order_by('concept_tag')
            
            serializer = ConceptMasterySerializer(masteries, many=True)
            return Response(serializer.data)
        
        except Exception as e:
            logger.error(f"Error fetching concept mastery for user {request.user.id}: {str(e)}")
            return Response(
                {"error": "Failed to fetch concept mastery"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TopicAnalysisView(APIView):
    """
    Get comprehensive topic analysis for authenticated user.
    
    Returns weak topics, strong topics, overall mastery, and trend analysis.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            user = request.user
            analyzer = WeakTopicAnalyzer(user.id)
            
            # Get weak and strong topics
            weak_topics = analyzer.analyze_user_weak_topics()
            strong_topics = analyzer.analyze_user_strengths()
            
            # Get trend summary
            trend_summary = analyzer.get_trend_summary()
            
            # Get overall mastery from LearnerProfile or calculate
            try:
                profile = LearnerProfile.objects.get(user=user)
                overall_mastery = profile.overall_mastery
            except LearnerProfile.DoesNotExist:
                overall_mastery = analyzer.update_learner_profile()['overall_mastery']
            
            # Count concepts
            total_concepts = ConceptMastery.objects.filter(user=user).count()
            mastered_count = len(strong_topics)
            struggling_count = len([t for t in weak_topics if t['is_struggling']])
            
            return Response({
                "weak_topics": weak_topics,
                "strong_topics": strong_topics,
                "overall_mastery": overall_mastery,
                "total_concepts": total_concepts,
                "mastered_count": mastered_count,
                "struggling_count": struggling_count,
                "trend_summary": {
                    "improving": len(trend_summary['improving']),
                    "stable": len(trend_summary['stable']),
                    "declining": len(trend_summary['declining'])
                }
            })
        
        except Exception as e:
            logger.error(f"Error analyzing topics for user {request.user.id}: {str(e)}")
            return Response(
                {"error": "Failed to analyze topics"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class WeakTopicWidgetView(APIView):
    """
    Dashboard widget data for weak topics.
    
    Returns top 5 weak topics with trends and suggested actions.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            user = request.user
            analyzer = WeakTopicAnalyzer(user.id)
            
            # Get top 5 weak topics
            weak_topics = analyzer.analyze_user_weak_topics()[:5]
            
            # Add suggested actions
            widget_data = []
            for topic in weak_topics:
                suggested_actions = self._get_suggested_actions(topic)
                widget_data.append({
                    "concept_tag": topic['concept_tag'],
                    "mastery_score": topic['mastery_score'],
                    "trend": topic['trend'],
                    "quiz_attempts": topic['quiz_attempts'],
                    "coding_attempts": topic['coding_attempts'],
                    "suggested_actions": suggested_actions,
                    "priority": self._get_priority(topic)
                })
            
            return Response({
                "weak_topics": widget_data,
                "total_weak": len(analyzer.analyze_user_weak_topics())
            })
        
        except Exception as e:
            logger.error(f"Error fetching weak topic widget for user {request.user.id}: {str(e)}")
            return Response(
                {"error": "Failed to fetch widget data"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_suggested_actions(self, topic: Dict) -> list:
        """Generate suggested actions based on topic data."""
        actions = []
        
        # Always suggest reviewing lesson
        actions.append("review_lesson")
        
        # Based on attempt patterns
        if topic['quiz_attempts'] > topic['coding_attempts']:
            actions.append("practice_coding_problems")
        elif topic['coding_attempts'] > topic['quiz_attempts']:
            actions.append("take_quiz")
        else:
            actions.append("practice_coding_problems")
            actions.append("take_quiz")
        
        # Suggest mentor session for struggling topics
        if topic['is_struggling']:
            actions.append("mentor_session")
        
        return actions
    
    def _get_priority(self, topic: Dict) -> str:
        """Determine priority level."""
        if topic['mastery_score'] < 0.2 or topic['total_attempts'] >= 7:
            return "critical"
        elif topic['mastery_score'] < 0.3 or topic['total_attempts'] >= 5:
            return "high"
        else:
            return "medium"
class LearnerProfileView(APIView):
    """
    Aggregated learner profile for the authenticated user (frontend dashboard).

    Returns the canonical LearnerProfile (skill level, overall mastery,
    weak/strong concepts, engagement & risk signals) via the existing
    LearnerProfileSerializer. No recomputation is forced on-read; the
    aggregate is refreshed asynchronously by Celery tasks. A user with no
    history receives the deterministic default (beginner / zero mastery),
    which satisfies the new-user contract without fabricating data.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile, _ = LearnerProfile.objects.get_or_create(user=request.user)
            serializer = LearnerProfileSerializer(profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching learner profile for user {request.user.id}: {str(e)}")
            return Response(
                {"error": "Failed to fetch learner profile"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class MasteryHistoryView(APIView):
    """
    Per-concept BKT mastery history used by the frontend mastery-over-time chart.

    GET /api/learner/mastery-history/?concept=<concept_tag>

    Returns the persisted BKT probability trace. For a concept with no
    history, returns an empty trace (deterministic; not fabricated).
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        concept = request.query_params.get("concept")
        if not concept:
            return Response(
                {"error": "concept query parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        current_mastery = 0.0
        trace = []
        try:
            mastery = ConceptMastery.objects.get(user=request.user, concept_tag=concept)
            trace = mastery.bkt_trace or []
            current_mastery = mastery.mastery_score
        except ConceptMastery.DoesNotExist:
            # No history — deterministic empty state, not an error.
            pass
        except Exception as e:
            logger.error(f"Error fetching mastery history for user {request.user.id}: {str(e)}")
            return Response(
                {"error": "Failed to fetch mastery history"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        serializer = MasteryHistorySerializer({
            "trace": trace,
            "concept_tag": concept,
            "current_mastery": current_mastery,
        })
        return Response(serializer.data, status=status.HTTP_200_OK)


class PrerequisiteView(APIView):
    """
    Resolve prerequisite status for a concept.

    GET /api/learner/prerequisites/?concept=<concept_tag>

    Returns, for the requested concept, each declared prerequisite's status
    (satisfied / partially mastered / missing) plus the recommended next
    prerequisite to tackle. Reuses the existing PREREQUISITE_MAP and
    ConceptMastery records as the single source of truth.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        concept = request.query_params.get("concept")
        if not concept:
            return Response(
                {"error": "concept query parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            from learner.services.prerequisites import resolve_prerequisites
            data = resolve_prerequisites(request.user.id, concept)
            serializer = PrerequisiteResolutionSerializer(data)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error resolving prerequisites for user {request.user.id}: {str(e)}")
            return Response(
                {"error": "Failed to resolve prerequisites"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
