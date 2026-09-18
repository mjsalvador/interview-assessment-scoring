import pytest


def test_results_without_assessment_id_includes_every_assessment_with_submissions(test_client):
    response = test_client.get("/classes/class-001/results")
    assert response.status_code == 200
    assessment_ids = {a["id"] for a in response.json()["assessment_summaries"]}
    assert assessment_ids == {"assess-001", "assess-002"}


def test_results_with_assessment_id_filters_to_that_assessment(test_client):
    response = test_client.get("/classes/class-001/results?assessment_id=assess-001")
    assert response.status_code == 200
    data = response.json()

    assessment_ids = {a["id"] for a in data["assessment_summaries"]}
    assert assessment_ids == {"assess-001"}

    for student in data["students"]:
        assert all(sub["assessment_id"] == "assess-001" for sub in student["submissions"])


def test_student_with_no_submission_has_empty_submissions_list(test_client):
    response = test_client.get("/classes/class-001/results")
    data = response.json()
    student = next(s for s in data["students"] if s["id"] == "student-005")
    assert student["submissions"] == []


def test_section_averages_and_pass_counts_match_seed_data(test_client):
    # class-001 on assess-001: sec-001 percentages [1.0, 1.0, 1.0, 0.333], 3 passing
    # sec-002 percentages [1.0, 1.0, 0.5, 1.0], 3 passing
    response = test_client.get("/classes/class-001/results?assessment_id=assess-001")
    sections = response.json()["assessment_summaries"][0]["sections"]
    vocab = next(s for s in sections if s["id"] == "sec-001")
    comprehension = next(s for s in sections if s["id"] == "sec-002")

    assert vocab["average_percentage"] == pytest.approx(0.8333, abs=0.0001)
    assert vocab["submitted_count"] == 4
    assert vocab["passed_count"] == 3

    assert comprehension["average_percentage"] == pytest.approx(0.875, abs=0.0001)
    assert comprehension["submitted_count"] == 4
    assert comprehension["passed_count"] == 3


def test_passing_and_failing_student_ids_for_one_section(test_client):
    response = test_client.get("/classes/class-001/results?assessment_id=assess-001")
    sections = response.json()["assessment_summaries"][0]["sections"]
    vocab = next(s for s in sections if s["id"] == "sec-001")

    assert set(vocab["passing_student_ids"]) == {"student-001", "student-002", "student-003"}
    assert set(vocab["failing_student_ids"]) == {"student-004"}


def test_students_not_submitted_is_correct(test_client):
    response = test_client.get("/classes/class-001/results")
    summaries = {a["id"]: a for a in response.json()["assessment_summaries"]}

    assert summaries["assess-001"]["students_not_submitted"] == 1
    assert summaries["assess-001"]["students_not_submitted_ids"] == ["student-005"]

    assert summaries["assess-002"]["students_not_submitted"] == 4
    assert set(summaries["assess-002"]["students_not_submitted_ids"]) == {
        "student-002", "student-003", "student-004", "student-005",
    }
