"""
ELO-based rating system for ML problem solving.

Problem difficulty ratings:
- Easy: 800
- Medium: 1200
- Hard: 1600
- Expert: 2000

On ACCEPTED submission:
- If user rating < problem rating: large gain
- If user rating > problem rating: small gain
- If user rating == problem rating: moderate gain

K-factor = 32 (standard competitive)
"""


def calculate_elo_change(user_rating: int, problem_rating: int, solved: bool, k_factor: int = 32) -> int:
    """
    Calculate ELO rating change after attempting a problem.

    Args:
        user_rating: Current user rating
        problem_rating: Problem difficulty rating
        solved: Whether the user solved the problem (ACCEPTED)
        k_factor: ELO K-factor (default 32)

    Returns:
        Rating change (positive for gain, negative for loss)
    """
    # Expected probability of solving based on rating difference
    expected = 1.0 / (1.0 + 10 ** ((problem_rating - user_rating) / 400.0))

    # Actual outcome
    actual = 1.0 if solved else 0.0

    # Rating change
    change = int(round(k_factor * (actual - expected)))

    # Minimum change on solve: +1
    if solved and change < 1:
        change = 1

    # Don't go below 0 rating
    if user_rating + change < 0:
        change = -user_rating

    return change


def update_user_rating(user, problem_slug: str, solved: bool):
    """
    Update user's ELO rating after a submission.

    Args:
        user: User model instance
        problem_slug: Problem identifier
        solved: Whether submission was ACCEPTED
    """
    from ml.registry import get_problem_definition

    try:
        problem_def = get_problem_definition(problem_slug)
    except ValueError:
        return

    problem_rating = problem_def.difficulty_rating
    current_rating = user.rating

    change = calculate_elo_change(current_rating, problem_rating, solved)

    user.rating = max(0, current_rating + change)

    if solved:
        # Count unique problems solved
        from ml.models import Submission
        unique_solved = Submission.objects.filter(
            user=user, status='ACCEPTED'
        ).values('problem__slug').distinct().count()
        user.problems_solved = unique_solved

    user.save(update_fields=['rating', 'problems_solved'])
