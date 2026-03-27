"""
Google Gemini 2.5 Flash LLM Integration - Problem-Aware ML Mentor

This module provides a simple, testable interface to Google's Gemini API.
Replaces Ollama with official Google Generative AI library.

Design:
- Pure function (no DB access, no side effects)
- Can be tested from Django shell independently
- Always returns string (never raises exceptions to caller)
- Handles all network/timeout errors gracefully
- Used by Celery task (async) to avoid blocking
- Optimized for fast response time with streaming disabled (get full response in one call)
- Problem-aware: when a problem_context is provided, the mentor understands
  the specific ML challenge the user is working on and tailors guidance accordingly

Setup:
1. Get API key from Google AI Studio: https://aistudio.google.com/app/apikeys
2. Set GEMINI_API_KEY in .env
3. Install: pip install google-generativeai

Gemini API Documentation:
- Model: gemini-2.5-flash (fast, reliable, cost-effective)
- Timeout: 10-15 seconds (much faster than Ollama)
- No streaming (full response in one call for deterministic UX)

Performance Improvements over Ollama:
- Ollama 2b: 5-30 seconds average latency (CPU-bound, variable quality)
- Gemini 2.5 Flash: 1-3 seconds average latency (cloud-optimized, consistent quality)
- ~10x faster responses with better answer quality
"""

import logging
import os
import time
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# Gemini API Configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_TIMEOUT = 15  # 15 second hard limit (much faster than Ollama's 120s)

# Lazy load google.generativeai (only when needed)
_genai = None
def _get_genai():
    global _genai
    if _genai is None:
        try:
            import google.generativeai as genai
            _genai = genai
            _genai.configure(api_key=GEMINI_API_KEY)
        except ImportError:
            logger.error("[Gemini] google-generativeai not installed. Install with: pip install google-generativeai")
            raise
    return _genai

# System prompt that defines mentor behavior
SYSTEM_INSTRUCTION = """You are an expert Artificial Intelligence mentor and practitioner.

Your role is to help users LEARN, APPLY, and THINK like real ML engineers and researchers.

Your responsibilities:

1) Teaching Style
- Start with intuition and real-world motivation.
- Explain concepts step-by-step, assuming no hidden knowledge.
- Gradually increase depth based on the user's question quality.
- Avoid unnecessary math unless it adds clarity.
- When math is used, explain what it means in plain language.
- Never hallucinate formulas, results, or citations.

2) Practical Orientation
- Always connect theory to implementation.
- Clearly explain:
  - Why this concept exists
  - When it is used
  - When it should NOT be used
- Provide small, illustrative code snippets (Python / NumPy / scikit-learn / PyTorch / TensorFlow) when helpful.
- Prefer minimal examples over long boilerplate.

3) Learning Progression
- Treat the user as someone learning AI systematically.
- If a concept depends on prerequisites, briefly mention them.
- When appropriate, suggest:
  - "Next concept to learn"
  - "Common mistakes beginners make here"
  - "How this appears in real projects or interviews"

4) Real-World ML Mindset
- Think like a production ML engineer, not a textbook.
- Emphasize:
  - Data quality
  - Assumptions
  - Trade-offs
  - Bias-variance
  - Overfitting vs underfitting
  - Evaluation metrics
- Use real examples like:
  - Spam detection
  - Recommendation systems
  - Medical diagnosis
  - Computer vision
  - NLP
  - Time-series forecasting

5) Code Critique Capability
- When the user shares code or describes their approach, analyze it critically.
- Identify potential issues such as:
  - Data leakage (e.g., fitting scaler on full data before split)
  - Incorrect metric usage (e.g., using accuracy on imbalanced data)
  - Missing preprocessing steps (e.g., no imputation for NaN values)
  - Suboptimal model choice for the task type
  - Hyperparameter values that are clearly wrong
- Provide specific, actionable feedback on what to fix and why.

6) Overfitting Detection and Guidance
- When the user reports high training scores but low test scores, diagnose overfitting.
- Suggest concrete remedies based on the situation:
  - Regularization (L1/L2, dropout, early stopping)
  - Reducing model complexity (fewer features, simpler model)
  - Increasing training data or using data augmentation
  - Cross-validation instead of single train/test split
  - Feature selection to remove noise features
- Explain the bias-variance tradeoff in context of their specific problem.

7) Feature Engineering Suggestions
- When discussing a dataset or problem, proactively suggest feature engineering ideas:
  - Interaction terms between correlated features
  - Polynomial features for non-linear relationships
  - Log transforms for skewed distributions
  - Binning continuous variables when appropriate
  - Domain-specific derived features
  - Handling categorical variables (one-hot, ordinal, target encoding)
- Explain WHY each feature transformation helps, not just what to do.

8) Metric Explanation
- When a specific evaluation metric is used, explain:
  - What the metric measures in plain language
  - Why this metric was chosen for this type of problem
  - How to interpret the score (what is good vs. bad)
  - Common pitfalls (e.g., accuracy is misleading with imbalanced classes)
  - How to improve the metric score with specific strategies
- For regression metrics (RMSE, MAE, R2): explain scale dependence and interpretation.
- For classification metrics (accuracy, F1, AUC-ROC): explain precision/recall tradeoffs.

9) Response Constraints
- Keep responses concise and structured (2-4 short sections).
- Use bullet points where clarity improves.
- Avoid unnecessary verbosity.
- Do not repeat the user's question.
- Do not use emojis.
- Do not include meta commentary about being an AI.

10) CRITICAL: No Full Solutions
- NEVER provide complete, ready-to-submit solution code.
- Instead, provide:
  - Conceptual hints about the right approach
  - Pseudo-code or partial code showing the technique
  - Specific function names or library references to look up
  - Step-by-step strategy without full implementation
- If the user explicitly asks for the full solution, politely decline and redirect:
  - "I can guide you through the approach, but writing the full solution would defeat the learning purpose."
  - Offer to explain any specific part they are stuck on.
- Small illustrative snippets (e.g., showing how StandardScaler works) are fine.
- Full train_and_predict implementations are NOT fine.

11) Adaptation Rule
- If the question is basic: explain simply.
- If the question is advanced: go deeper and be precise.
- If the question is vague: clarify assumptions and give a clean explanation.
- If the question is wrong: correct it politely but firmly.

Goal:
Help the user become capable of building, debugging, evaluating, and improving real AI systems -- not just understanding definitions.
IMPORTANT:
- Always complete your explanation fully.
- If a list is started, finish all items.
- Do not stop mid-sentence or mid-point.
- If the answer is long, summarize at the end instead of cutting off.
"""


# Problem-aware context template injected when a problem_slug is provided
PROBLEM_CONTEXT_TEMPLATE = """
--- ACTIVE PROBLEM CONTEXT ---
The student is currently working on the following ML challenge:

Problem: {title}
Type: {task_type}
Difficulty: {difficulty} (Rating: {difficulty_rating})
Category: {category}
Evaluation Metric: {metric}
Metric Direction: {metric_direction}
Submission Threshold: {threshold}

Problem Description (summary):
{description_summary}

IMPORTANT CONTEXT RULES:
- Tailor your guidance to THIS specific problem.
- Reference the evaluation metric ({metric}) when discussing performance.
- When suggesting improvements, frame them in terms of improving {metric}.
- Remember the threshold is {threshold} -- help the student understand what that means.
- For {metric_direction} metrics, explain whether the student needs to go higher or lower.
- Do NOT give away the full solution. Guide the student toward discovering it themselves.
- If the student's approach is fundamentally wrong for this problem type, say so clearly.
--- END PROBLEM CONTEXT ---
"""


SCORE_ANALYSIS_TEMPLATE = """
--- STUDENT'S LAST SUBMISSION ---
The student's most recent submission scored: {score} (metric: {metric})
The required threshold is: {threshold}
Status: {status}
Gap: {gap_description}

When responding, consider:
- Acknowledge their current score and what it means.
- If the score is close to the threshold, suggest fine-tuning strategies.
- If the score is far from the threshold, suggest fundamental approach changes.
- If the score indicates overfitting (very low despite reasonable approach), diagnose it.
- Be encouraging but honest about what needs to improve.
--- END SUBMISSION CONTEXT ---
"""


def build_problem_context_block(problem_context: Dict) -> str:
    """
    Build the problem-aware context block to inject into the prompt.

    Args:
        problem_context: Dict with keys:
            - title (str)
            - task_type (str): "classification" or "regression"
            - difficulty (str): "easy", "medium", "hard", "expert"
            - difficulty_rating (int): 800, 1200, 1600, 2000
            - category (str)
            - metric (str): e.g., "accuracy", "f1", "rmse", "mae"
            - threshold (float): submission threshold
            - description (str): full problem description markdown

    Returns:
        Formatted context string to prepend to conversation.
    """
    metric = problem_context.get("metric", "accuracy")

    # Determine metric direction
    lower_is_better_metrics = {"rmse", "mae", "mse"}
    if metric.lower() in lower_is_better_metrics:
        metric_direction = "lower is better"
    else:
        metric_direction = "higher is better"

    # Truncate description to first 500 chars for prompt efficiency
    full_description = problem_context.get("description", "")
    if len(full_description) > 500:
        description_summary = full_description[:500] + "..."
    else:
        description_summary = full_description

    return PROBLEM_CONTEXT_TEMPLATE.format(
        title=problem_context.get("title", "Unknown"),
        task_type=problem_context.get("task_type", "unknown"),
        difficulty=problem_context.get("difficulty", "unknown"),
        difficulty_rating=problem_context.get("difficulty_rating", "N/A"),
        category=problem_context.get("category", "general"),
        metric=metric,
        metric_direction=metric_direction,
        threshold=problem_context.get("threshold", "N/A"),
        description_summary=description_summary,
    )


def build_score_analysis_block(
    last_score: float,
    metric: str,
    threshold: float,
    task_type: str = "classification",
) -> str:
    """
    Build the score analysis block when the user has a recent submission.

    Analyzes the score relative to the threshold and provides context
    for the mentor to give targeted improvement advice.

    Args:
        last_score: The user's most recent submission score.
        metric: The evaluation metric name (e.g., "accuracy", "rmse").
        threshold: The required threshold for acceptance.
        task_type: "classification" or "regression".

    Returns:
        Formatted score analysis string.
    """
    lower_is_better_metrics = {"rmse", "mae", "mse"}
    is_lower_better = metric.lower() in lower_is_better_metrics

    if is_lower_better:
        passed = last_score <= threshold
        gap = last_score - threshold
        if passed:
            status = "PASSING (score is at or below threshold)"
            gap_description = f"Score {last_score:.4f} is {abs(gap):.4f} below the threshold {threshold} (good)."
        else:
            status = "NOT PASSING (score is above threshold)"
            gap_description = f"Score {last_score:.4f} is {gap:.4f} above the threshold {threshold}. Needs to decrease by {gap:.4f}."
    else:
        passed = last_score >= threshold
        gap = threshold - last_score
        if passed:
            status = "PASSING (score meets or exceeds threshold)"
            gap_description = f"Score {last_score:.4f} is {abs(gap):.4f} above the threshold {threshold} (good)."
        else:
            status = "NOT PASSING (score is below threshold)"
            gap_description = f"Score {last_score:.4f} is {gap:.4f} below the threshold {threshold}. Needs to improve by {gap:.4f}."

    return SCORE_ANALYSIS_TEMPLATE.format(
        score=f"{last_score:.4f}",
        metric=metric,
        threshold=threshold,
        status=status,
        gap_description=gap_description,
    )


def build_full_prompt(
    conversation_history: list,
    problem_context: Optional[Dict] = None,
    last_score: Optional[float] = None,
) -> str:
    """
    Build the complete prompt with system instruction, optional problem context,
    optional score analysis, and conversation history.

    This is the central prompt builder used by the Celery task.

    Args:
        conversation_history: List of (role, content) tuples.
            role is "user" or "assistant".
        problem_context: Optional dict with problem details.
            Keys: title, task_type, difficulty, difficulty_rating, category,
                  metric, threshold, description
        last_score: Optional float of the user's most recent submission score.

    Returns:
        Complete prompt string ready for Gemini API.
    """
    prompt_parts = [SYSTEM_INSTRUCTION]

    # Inject problem context if available
    if problem_context:
        prompt_parts.append(build_problem_context_block(problem_context))

    # Inject score analysis if both score and problem context are available
    if last_score is not None and problem_context:
        metric = problem_context.get("metric", "accuracy")
        threshold = problem_context.get("threshold", 0.0)
        task_type = problem_context.get("task_type", "classification")
        prompt_parts.append(build_score_analysis_block(
            last_score=last_score,
            metric=metric,
            threshold=threshold,
            task_type=task_type,
        ))

    # Add conversation history
    prompt_parts.append("\n\n--- Conversation ---\n")

    for role, content in conversation_history:
        prefix = "Student:" if role == "user" else "Mentor:"
        prompt_parts.append(f"{prefix} {content}\n")

    # Signal to Gemini to generate mentor response
    prompt_parts.append("Mentor:")

    return "".join(prompt_parts)


def generate_mentor_response(prompt: str) -> Tuple[str, float]:
    """
    Call Google Gemini 2.5 Flash and return mentor response.

    Pure function: decoupled from Celery, database, and HTTP layer.

    Design principles:
    - Always returns (text, latency_ms) tuple (never raises exceptions to caller)
    - Gracefully handles all failure modes (timeout, auth, parse errors)
    - Logs all errors for debugging
    - Callers can assume a non-empty string is always returned

    Args:
        prompt: Complete prompt = SYSTEM_INSTRUCTION + optional context + conversation history
                Example: "You are an expert ML mentor.\n\nStudent: What is gradient descent?\nMentor:"

    Returns:
        Tuple of (response_text, latency_milliseconds)
        - response_text: String response from Gemini, or error message prefixed with [ERROR]
        - latency_ms: Time taken in milliseconds (for performance monitoring)

        Examples:
        - ("Gradient descent is an optimization algorithm that...", 2345)
        - ("[ERROR] API key invalid or not set", 0)
        - ("[ERROR] Request timed out (>15s)", 15000)

    Testing from Django shell:
        >>> from mentor.llm import generate_mentor_response, build_full_prompt
        >>> prompt = build_full_prompt([("user", "What is ML?")])
        >>> response, latency = generate_mentor_response(prompt)
        >>> print(f"Response: {response[:100]}")
        >>> print(f"Latency: {latency}ms")
    """
    start_time = time.time()

    try:
        # Validate API key
        if not GEMINI_API_KEY:
            logger.error("[Gemini] GEMINI_API_KEY not set in environment")
            return "[ERROR] API key not configured. Contact administrator.", 0

        logger.debug(f"[Gemini] Calling {GEMINI_MODEL} for {len(prompt)} chars")

        # Initialize Gemini client
        genai = _get_genai()

        # Create model instance with safety settings
        model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            generation_config={
                "temperature": 0.7,  # Balanced: creative but not hallucinating
                "top_p": 0.9,        # Nucleus sampling for diversity
                "top_k": 40,         # Limit vocabulary diversity
                "max_output_tokens": 2048,  # Reasonable limit for mentor responses
            },
            safety_settings=[
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE",
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE",
                },
            ]
        )

        # Call Gemini API with timeout
        response = model.generate_content(prompt)


        # Extract response text
        response_text = response.text.strip() if response.text else ""

        if not response_text:
            logger.warning("[Gemini] Model returned empty response")
            latency_ms = int((time.time() - start_time) * 1000)
            return "[ERROR] Model returned empty response. Please try again.", latency_ms

        latency_ms = int((time.time() - start_time) * 1000)
        logger.debug(f"[Gemini] Got response ({len(response_text)} chars) in {latency_ms}ms")
        return response_text, latency_ms

    except TimeoutError:
        latency_ms = int((time.time() - start_time) * 1000)
        logger.error(f"[Gemini] Request timeout (>{GEMINI_TIMEOUT}s)")
        return f"[ERROR] Request timed out (>{GEMINI_TIMEOUT}s). Please try again.", latency_ms

    except Exception as e:
        latency_ms = int((time.time() - start_time) * 1000)
        error_msg = str(e)

        # Provide helpful error messages for common issues
        if "API key" in error_msg or "authentication" in error_msg.lower():
            logger.error("[Gemini] Authentication error - check GEMINI_API_KEY")
            return "[ERROR] API authentication failed. Contact administrator.", latency_ms
        elif "rate limit" in error_msg.lower():
            logger.warning("[Gemini] Rate limited by API")
            return "[ERROR] Service rate limited. Please wait a moment and try again.", latency_ms
        elif "invalid_request" in error_msg.lower():
            logger.error(f"[Gemini] Invalid request: {error_msg}")
            return "[ERROR] Request format error. Please try a different question.", latency_ms
        else:
            logger.error(f"[Gemini] Unexpected error: {error_msg}", exc_info=True)
            return f"[ERROR] Service error: {error_msg}", latency_ms
