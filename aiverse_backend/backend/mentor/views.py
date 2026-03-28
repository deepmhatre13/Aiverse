from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.throttling import UserRateThrottle
from rest_framework.exceptions import NotFound, PermissionDenied
from django.shortcuts import get_object_or_404
from django.utils import timezone
from celery.result import AsyncResult
import logging

from .models import MentorSession, MentorMessage
from .serializers import MentorSessionSerializer, MentorMessageSerializer, AskMentorSerializer
from .tasks import process_mentor_query
from .llm import generate_mentor_response, SYSTEM_INSTRUCTION, build_full_prompt

logger = logging.getLogger(__name__)


# ============================================================================
# CLASS-BASED VIEWS (for frontend's singular 'session' routes)
# ============================================================================

class MentorMessageListCreateView(generics.ListCreateAPIView):
    """
    GET /api/mentor/session/<session_id>/messages/ - Fetch all messages in session
    POST /api/mentor/session/<session_id>/messages/ - Create new message in session
    """
    serializer_class = MentorMessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        session_id = self.kwargs['session_id']
        try:
            session = MentorSession.objects.get(id=session_id)
        except MentorSession.DoesNotExist:
            raise NotFound({'detail': 'Session does not exist'})
        if session.user != self.request.user:
            raise PermissionDenied({'detail': 'Not your session'})
        return MentorMessage.objects.filter(session=session).order_by('created_at')

    def perform_create(self, serializer):
        session_id = self.kwargs['session_id']
        try:
            session = MentorSession.objects.get(id=session_id)
        except MentorSession.DoesNotExist:
            raise NotFound({'detail': 'Session does not exist'})
        if session.user != self.request.user:
            raise PermissionDenied({'detail': 'Not your session'})
        serializer.save(session=session)


# ============================================================================
# RATE THROTTLING
# ============================================================================

class MentorRateThrottle(UserRateThrottle):
    """Rate throttle: 20 requests per hour per authenticated user."""
    rate = '20/hour'


# ============================================================================
# FUNCTION-BASED VIEWS (Frontend-facing endpoints)
# ============================================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_session(request):
    """
    POST /api/mentor/session/start/ - Create new session for authenticated user.
    
    Returns:
    {
      "id": "uuid-string",
      "title": "Chat",
      "created_at": "iso-timestamp"
    }
    
    Non-blocking: returns immediately without waiting for LLM.
    """
    try:
        session = MentorSession.objects.create(user=request.user)
        serializer = MentorSessionSerializer(session)
        logger.info(f"[Mentor] Created session {session.id} for user {request.user.id}")
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    except Exception as e:
        logger.error(f"[Mentor] Error creating session: {e}", exc_info=True)
        return Response(
            {'error': 'Failed to create session'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_sessions(request):
    """
    GET /api/mentor/sessions/ - Fetch all sessions for authenticated user.
    
    Returns:
    [
      {
        "id": "uuid-string",
        "title": "Chat",
        "created_at": "iso",
        "last_active_at": "iso",
        "messages": [...]
      },
      ...
    ]
    """
    try:
        sessions = MentorSession.objects.filter(user=request.user).order_by('-last_active_at')
        serializer = MentorSessionSerializer(sessions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"[Mentor] Error fetching sessions for user {request.user.id}: {e}", exc_info=True)
        return Response(
            {'error': 'Failed to fetch sessions'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_session_detail(request, session_id):
    """GET /api/mentor/sessions/{id}/ - Fetch a single session."""
    try:
        session = get_object_or_404(MentorSession, id=session_id, user=request.user)
        serializer = MentorSessionSerializer(session)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"[Mentor] Error fetching session {session_id}: {e}", exc_info=True)
        return Response(
            {'error': 'Failed to fetch session'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_messages(request, session_id):
    """GET /api/mentor/sessions/{id}/messages/ - Fetch all messages in session."""
    session = get_object_or_404(MentorSession, id=session_id, user=request.user)
    
    try:
        messages = session.messages.all().order_by('created_at')
        serializer = MentorMessageSerializer(messages, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"[Mentor] Error fetching messages for session {session_id}: {e}", exc_info=True)
        return Response(
            {'error': 'Failed to fetch messages'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([MentorRateThrottle])
def ask_mentor(request, session_id):
    """
    POST /api/mentor/sessions/{id}/ask/ (plural route - backward compat)
    
    1. Validate question
    2. Save user message IMMEDIATELY
    3. Enqueue Celery task
    4. Return 202 with task_id
    
    Frontend polls /task/{task_id}/status/ until completion.
    """
    print(request.user)
    # Ownership check
    session = get_object_or_404(MentorSession, id=session_id, user=request.user)
    
    # Validate input
    serializer = AskMentorSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    question = serializer.validated_data['question']
    
    try:
        # Save user message IMMEDIATELY (optimistic update)
        user_message = MentorMessage.objects.create(
            session=session,
            role='user',
            content=question
        )
        logger.info(f"[Mentor] User message {user_message.id} created for session {session_id}")
        
        # Update session timestamp
        session.last_active_at = timezone.now()
        session.save(update_fields=['last_active_at'])
        
        # Enqueue Celery task (fire and forget)
        try:
            task = process_mentor_query.delay(str(session_id), question)
            print("Task created:", task.id)
            logger.info(f"[Mentor] Task {task.id} enqueued for session {session_id}")
        except Exception as celery_err:
            logger.error(f"[Mentor] Celery enqueue failed: {celery_err}", exc_info=True)
            return Response(
                {'error': 'AI service unavailable. Ensure Redis and Celery are running.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        # Return 202 immediately (non-blocking)
        return Response(
            {'task_id': str(task.id)},
            status=status.HTTP_202_ACCEPTED
        )
    
    except Exception as e:
        logger.error(f"[Mentor] Error in ask_mentor: {e}", exc_info=True)
        return Response(
            {'error': 'Failed to process question'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([MentorRateThrottle])
def ask_mentor_v2(request, session_id):
    """
    POST /api/mentor/session/{id}/ask/ (singular route - FRONTEND EXPECTED)
    
    Same as ask_mentor but for singular URL path.
    
    1. Validate question
    2. Save user message IMMEDIATELY
    3. Enqueue Celery task
    4. Return 202 with task_id
    
    Frontend polls /task/{task_id}/status/ until completion.
    """
    print(request.user)
    # Ownership check
    session = get_object_or_404(MentorSession, id=session_id, user=request.user)
    
    # Validate input
    serializer = AskMentorSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    question = serializer.validated_data['question']
    logger.info("[Mentor] request.user=%s", request.user)
    logger.info(
        "[Mentor] ask_mentor_v2 user=%s authenticated=%s session=%s",
        getattr(request.user, 'id', None),
        bool(getattr(request.user, 'is_authenticated', False)),
        session_id,
    )
    
    try:
        # Save user message IMMEDIATELY (optimistic update)
        user_message = MentorMessage.objects.create(
            session=session,
            role='user',
            content=question
        )
        logger.info(f"[Mentor] User message {user_message.id} created for session {session_id}")
        
        # Update session timestamp
        session.last_active_at = timezone.now()
        session.save(update_fields=['last_active_at'])
        
        # Enqueue Celery task (fire and forget)
        try:
            task = process_mentor_query.delay(str(session_id), question)
            print("Task created:", task.id)
            logger.info(f"[Mentor] Task {task.id} enqueued for session {session_id}")
        except Exception as celery_err:
            logger.error(f"[Mentor] Celery enqueue failed: {celery_err}", exc_info=True)
            return Response(
                {'error': 'AI service unavailable. Ensure Redis and Celery are running.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        # Return 202 immediately (non-blocking)
        return Response(
            {'task_id': str(task.id)},
            status=status.HTTP_202_ACCEPTED
        )
    
    except Exception as e:
        logger.error(f"[Mentor] Error in ask_mentor_v2: {e}", exc_info=True)
        return Response(
            {'error': 'Failed to process question'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_task_status(request, task_id):
    """
    Check if Celery mentor task is complete.
    
    CRITICAL: This endpoint determines whether frontend continues polling or stops.
    It MUST return accurate status to prevent infinite "Mentor is thinking..." loops.
    
    Requires authentication.
    Task completion is checked via Celery AsyncResult, not the database.
    
    Returns:
    - {"status": "processing", "state": "PENDING|RUNNING|RETRY"}
    - {"status": "completed", "state": "SUCCESS|FAILURE"}
    - {"status": "error", "state": "UNKNOWN"} if task cannot be found
    
    Frontend behavior:
    - If status === "completed": Stop polling, fetch messages
    - If status === "processing": Continue polling (wait 1 second, try again)
    - If status === "error": Stop polling, show error to user
    
    Celery States:
    - PENDING: Task waiting to execute (not yet picked up by worker)
    - RUNNING: Task currently executing
    - RETRY: Task failed, retrying
    - SUCCESS: Task completed successfully
    - FAILURE: Task failed and will not retry
    - REVOKED: Task was cancelled
    """
    try:
        print("Task status checked")
        logger.info("[Mentor] status request.user=%s", request.user)
        logger.info(
            "[Mentor] check_task_status user=%s authenticated=%s task=%s",
            getattr(request.user, 'id', None),
            bool(getattr(request.user, 'is_authenticated', False)),
            task_id,
        )
        # Check Celery task state directly
        result = AsyncResult(task_id)
        
        # Get actual Celery state
        # state can be: PENDING, RUNNING, SUCCESS, FAILURE, RETRY, REVOKED, STARTED, etc.
        state = result.state
        is_ready = result.ready()  # True if SUCCESS or FAILURE, False otherwise
        
        # Map Celery states to frontend-friendly status
        if state in ('SUCCESS', 'FAILURE'):
            # Task finished (success or error)
            # Frontend will stop polling and fetch messages
            return Response({
                "status": "completed",
                "state": state
            }, status=200)
        
        elif state in ('PENDING', 'RUNNING', 'RETRY', 'STARTED'):
            # Task still processing
            # Frontend will continue polling
            return Response({
                "status": "processing",
                "state": state
            }, status=200)
        
        else:
            # Unknown state (REVOKED, etc.)
            # Treat as still processing
            return Response({
                "status": "processing",
                "state": state
            }, status=200)
    
    except Exception as e:
        # If we can't check task status (e.g., Redis down, invalid task ID),
        # return "error" not "processing" to prevent infinite polling
        logger.error(f"[Mentor] Error checking task {task_id}: {e}", exc_info=True)
        return Response({
            "status": "error",
            "state": "UNKNOWN",
            "error": str(e)
        }, status=200)  # Still 200 so frontend doesn't retry on network errors


@api_view(['GET'])
@permission_classes([AllowAny])
def test_gemini(request):
    """
    GET /api/mentor/test-gemini/ - Diagnostic endpoint to test Google Gemini connectivity.
    
    No authentication required.
    No database writes.
    Fail fast if Gemini API is unreachable or API key is invalid.
    
    Success = Gemini responds in <15s with valid API key.
    Failure = Missing API key, auth error, rate limit, or timeout.
    """
    try:
        logger.info("[Mentor] Testing Google Gemini 2.5 Flash connectivity...")
        
        # Hardcoded test prompt (same as before for consistency)
        test_prompt = (
            f"{SYSTEM_INSTRUCTION}\n\n"
            "Student: Explain gradient descent intuitively with one real-world example.\n"
            "Mentor:"
        )
        
        # Call Gemini (synchronous, fail fast)
        # generate_mentor_response returns (response_text, latency_ms)
        response, latency_ms = generate_mentor_response(test_prompt)
        
        # Log response
        logger.info(f"[Mentor] Gemini test passed ({latency_ms}ms). Response ({len(response)} chars):\n{response}")
        
        return Response(
            {
                'status': 'ok',
                'message': 'Google Gemini 2.5 Flash is reachable and responding',
                'response': response,
                'latency_ms': latency_ms,
                'prompt_length': len(test_prompt)
            },
            status=status.HTTP_200_OK
        )
    
    except Exception as e:
        logger.error(f"[Mentor] Gemini test failed: {e}", exc_info=True)
        return Response(
            {
                'status': 'error',
                'error': str(e),
                'message': 'Google Gemini is unreachable, API key invalid, or rate limited'
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
