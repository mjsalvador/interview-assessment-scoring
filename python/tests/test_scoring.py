import pytest
from src.scoring import calculate_score
from src.config import MASTERY_THRESHOLD

SECTIONS = [
    {
        "id": "sec-vocab",
        "name": "Vocabulary",
        "weight": 0.4,
        "questions": {"q1": "author", "q2": "setting", "q3": "plot"}
    },
    {
        "id": "sec-comp",
        "name": "Comprehension",
        "weight": 0.6,
        "questions": {"q4": "main idea", "q5": "inference", "q6": "evidence"}
    }
]


def test_all_sections_pass_returns_passed():
    answers = {"q1": "author", "q2": "setting", "q3": "plot",
               "q4": "main idea", "q5": "inference", "q6": "evidence"}
    result = calculate_score(answers, SECTIONS)
    assert result["passed"] is True
    assert result["overall_percentage"] == pytest.approx(1.0)
    assert all(s["passed"] for s in result["section_scores"])


def test_failed_section_fails_overall_even_if_weighted_average_passes():
    # vocab: 0/3 = 0% (fails); comp: 3/3 = 100% (passes)
    # weighted avg: 0*0.4 + 1.0*0.6 = 0.6 — below threshold
    answers = {"q4": "main idea", "q5": "inference", "q6": "evidence"}
    result = calculate_score(answers, SECTIONS)
    assert result["passed"] is False
    vocab = next(s for s in result["section_scores"] if s["id"] == "sec-vocab")
    assert vocab["passed"] is False


def test_weighted_average_below_threshold_fails_overall():
    # vocab: 3/3 (100%), comp: 2/3 (66.7% — fails threshold)
    answers = {"q1": "author", "q2": "setting", "q3": "plot",
               "q4": "main idea", "q5": "inference"}
    result = calculate_score(answers, SECTIONS)
    comp = next(s for s in result["section_scores"] if s["id"] == "sec-comp")
    assert comp["passed"] is False
    assert result["passed"] is False


def test_weights_applied_correctly_to_overall_percentage():
    # vocab: 2/3, comp: 3/3
    # weighted: (2/3)*0.4 + (3/3)*0.6 = 0.267 + 0.6 = 0.867
    answers = {"q1": "author", "q2": "setting",
               "q4": "main idea", "q5": "inference", "q6": "evidence"}
    result = calculate_score(answers, SECTIONS)
    assert result["overall_percentage"] == pytest.approx(0.867, abs=0.001)


def test_unanswered_questions_score_zero_in_their_section():
    answers = {"q4": "main idea", "q5": "inference", "q6": "evidence"}
    result = calculate_score(answers, SECTIONS)
    vocab = next(s for s in result["section_scores"] if s["id"] == "sec-vocab")
    assert vocab["points_earned"] == 0
    assert vocab["points_possible"] == 3


def test_empty_submission_scores_zero_everywhere():
    result = calculate_score({}, SECTIONS)
    assert result["overall_percentage"] == pytest.approx(0.0)
    assert result["passed"] is False
    for section in result["section_scores"]:
        assert section["points_earned"] == 0
        assert section["percentage"] == pytest.approx(0.0)
