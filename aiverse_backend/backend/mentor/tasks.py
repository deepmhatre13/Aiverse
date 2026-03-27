import logging
import time
from celery import shared_task
from django.utils import timezone
from django.db import transaction
from .models import MentorSession, MentorMessage
from .llm import generate_mentor_response, build_full_prompt

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=0, acks_late=True, time_limit=30)
def process_mentor_query(self, session_id, question, problem_context=None, last_score=None):
    """
    Async Celery task: Process mentor query via Google Gemini 2.5 Flash.

    CRITICAL: This task MUST:
    1. Fetch session and history
    2. Call Gemini API (with optional problem context and score)
    3. SAVE assistant message to DB (BEFORE returning)
    4. Update session timestamp
    5. Return SUCCESS ONLY AFTER DB writes are committed

    Architecture:
    - Fire-and-forget: Frontend polls /task/{task_id}/status/ for completion
    - Celery returns SUCCESS only after assistant message is persisted
    - If Gemini fails, save error message instead
    - No silent failures: all exceptions are caught and logged

    Performance:
    - Gemini 2.5 Flash: 1-3s average latency (consistent, reliable)
    - Task timeout: 30s (Gemini should complete in <15s)

    Args:
        session_id: UUID string of the MentorSession.
        question: The user's question text.
        problem_context: Optional dict with problem details for problem-aware mentoring.
            Keys: title (str), task_type (str), difficulty (str), difficulty_rating (int),
                  category (str), metric (str), threshold (float), description (str).
            When provided, the mentor tailors its guidance to the specific ML challenge.
        last_score: Optional float of the user's most recent submission score.
            When provided alongside problem_context, the mentor analyzes the score
            relative to the threshold and suggests targeted improvements.

    Returns: dict with success/error status and metrics
    """
    session = None
    task_start_time = time.time()
    assistant_msg_id = None

    try:
        # STEP 1: Fetch session (will raise DoesNotExist if deleted)
        session = MentorSession.objects.get(id=session_id)
        logger.info(f"[MentorTask] START - session {session_id}, user {session.user.id}")

        # STEP 2: Fetch conversation history (context window: last 10 messages)
        # This MUST include the user message that was just created in the view
        history_messages = list(
    MentorMessage.objects
    .filter(session=session)
    .order_by('-created_at')
    .values_list('role', 'content')[:10]
)[::-1]



        logger.debug(f"[MentorTask] Loaded {len(history_messages)} history messages")

        # STEP 3: Build prompt using the centralized prompt builder
        # build_full_prompt handles: system instruction + problem context +
        # score analysis + conversation history formatting
        has_problem = problem_context is not None
        has_score = last_score is not None

        prompt = build_full_prompt(
            conversation_history=history_messages,
            problem_context=problem_context,
            last_score=last_score,
        )

        logger.debug(
            f"[MentorTask] Built prompt ({len(prompt)} chars, "
            f"{len(history_messages)} messages, "
            f"problem_aware={has_problem}, has_score={has_score})"
        )

        # STEP 4: Call Gemini API
        # generate_mentor_response handles all network errors gracefully
        # Returns (response_text, latency_ms) - never raises exceptions
        assistant_response, gemini_latency_ms = generate_mentor_response(prompt)
        logger.info(f"[MentorTask] Gemini responded ({gemini_latency_ms}ms, {len(assistant_response)} chars)")

        # STEP 5: Save assistant message INSIDE explicit transaction
        # Use atomic() to ensure both the message save AND session update succeed together
        # or both rollback together (no partial writes)
        with transaction.atomic():
            assistant_msg = MentorMessage.objects.create(
                session=session,
                role="assistant",
                content=assistant_response
            )
            assistant_msg_id = assistant_msg.id
            logger.info(f"[MentorTask] Created assistant message {assistant_msg_id}")

            # Update session's last_active_at timestamp
            session.last_active_at = timezone.now()
            session.save(update_fields=["last_active_at"])
            logger.info(f"[MentorTask] Updated session {session_id} timestamp")

        # STEP 6: Calculate total task latency
        task_latency_ms = int((time.time() - task_start_time) * 1000)

        # Log successful completion
        logger.info(f"[MentorTask] SUCCESS - message {assistant_msg_id}, task time {task_latency_ms}ms")

        # Return SUCCESS with metrics (frontend will see task is complete)
        return {
            "success": True,
            "message_id": str(assistant_msg_id),
            "session_id": str(session_id),
            "gemini_latency_ms": gemini_latency_ms,
            "task_latency_ms": task_latency_ms,
            "response_length": len(assistant_response),
            "problem_aware": has_problem,
            "score_aware": has_score,
        }

    except MentorSession.DoesNotExist:
        # Session was deleted between view request and task execution
        logger.error(f"[MentorTask] FAIL - Session {session_id} not found (deleted)")
        return {"success": False, "error": "Session not found"}

    except Exception as e:
        # Catch-all for any unexpected errors
        # (Gemini errors are caught inside generate_mentor_response, not here)
        logger.error(f"[MentorTask] FAIL - Unexpected error: {type(e).__name__}: {e}", exc_info=True)

        # Try to save error message to ensure frontend never hangs
        if session:
            try:
                with transaction.atomic():
                    error_msg = MentorMessage.objects.create(
                        session=session,
                        role="assistant",
                        content=f"[ERROR] Failed to process query: {str(e)}"
                    )
                    assistant_msg_id = error_msg.id
                    session.last_active_at = timezone.now()
                    session.save(update_fields=["last_active_at"])

                task_latency_ms = int((time.time() - task_start_time) * 1000)
                logger.error(f"[MentorTask] Saved error message {assistant_msg_id}")

                return {
                    "success": False,
                    "error": str(e),
                    "message_id": str(assistant_msg_id),
                    "task_latency_ms": task_latency_ms
                }
            except Exception as save_error:
                # Even error saving failed - log and give up
                # Frontend will eventually timeout waiting for task completion
                logger.critical(f"[MentorTask] CRITICAL - Failed to save error message: {save_error}")
                return {"success": False, "error": str(e)}

        return {"success": False, "error": str(e)}
