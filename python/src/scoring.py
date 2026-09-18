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

    """
    section_scores = []
    overall = 0.0

    for section in sections:
        questions = section["questions"]
        if not questions:
            raise ValueError(f"Section {section['id']} has no questions")

        points_possible = len(questions)
        points_earned = 0

        for question_id, correct_answer in questions.items():
            submitted = submitted_answers.get(question_id)
            if submitted is None:
                continue
            if submitted.strip().casefold() == correct_answer.strip().casefold():
                points_earned += 1

        percentage = points_earned / points_possible
        passed = percentage >= MASTERY_THRESHOLD
        overall += percentage * section["weight"]

        section_scores.append({
            "id": section["id"],
            "name": section["name"],
            "points_earned": points_earned,
            "points_possible": points_possible,
            "percentage": round(percentage, 4),
            "passed": passed,
        })

    all_sections_passed = all(s["passed"] for s in section_scores)
    overall_passed = round(overall, 9) >= MASTERY_THRESHOLD
    passed = overall_passed and all_sections_passed

    return {
        "section_scores": section_scores,
        "overall_percentage": round(overall, 4),
        "passed": passed,
    }
