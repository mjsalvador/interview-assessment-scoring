from src.config import MASTERY_THRESHOLD


def calculate_score(
    submitted_answers: dict[str, str],
    sections: list[dict],
) -> dict:
    """
    Score a student's submitted answers across a sectioned assessment.

    Each section has a weight and its own set of questions. The student must
    meet the mastery threshold both overall (weighted) and in each section
    individually to pass.

    Args:
        submitted_answers: maps question_id -> student's answer string
        sections: list of section dicts, each with:
            - id        (str):            section identifier
            - name      (str):            display name
            - weight    (float):          contribution to overall score (all weights sum to 1.0)
            - questions (dict[str, str]): maps question_id -> correct answer string

    Returns a dict with:
        section_scores     (list): one entry per section, each with:
            - id               (str)
            - name             (str)
            - points_earned    (int)
            - points_possible  (int)
            - percentage       (float): 0.0 to 1.0
            - passed           (bool):  True if percentage >= MASTERY_THRESHOLD
        overall_percentage  (float): weighted average across all sections
        passed              (bool):  True only if overall_percentage >= MASTERY_THRESHOLD
                                     AND every individual section passed

    Rules:
        - Questions not answered by the student count as incorrect
        - Answers submitted for questions not in any section are ignored
        - Comparison is case-insensitive
        - An empty submission is valid and scores 0 in all sections
        - Section weights are guaranteed to sum to 1.0

    TODO: Implement this function.
    The tests in tests/test_scoring.py define the expected behavior.
    Run: docker compose run test
    """
    raise NotImplementedError
