# Implementation Plan and Handoff

Planned in a separate AI session before implementation. This file is the agreed plan; follow it as written. If something in it turns out to be wrong or impossible, stop and raise it instead of improvising.

## Context

- Exercise repo for Ellevation. Work in `python/` only. Ignore `csharp/`.
- Two deliverables: implement `calculate_score`, and expose class assessment results. Then fill in `NOTES.md` from `NOTES.md.template`.
- `CODEBASE_REPORT.md` in this directory describes the existing service, its data model, and known rough edges.
- Baseline before any changes: 16 tests, 8 pass and 8 fail.

## Working agreement

- Plan-then-implement. The plan below is already agreed. Follow it precisely.
- Do not run git commands. Committing is the developer's call.
- Do not restructure the codebase (no router or service layer split). That is deliberately deferred and recorded in NOTES.
- Do not break existing tests. One existing test gets skipped, by prior decision, and that is the only change to existing tests.
- Keep boilerplate changes to a minimum.
- Every new `database.py` function takes a `db_path` argument, and every route passes `_DB_PATH` explicitly. The test fixture overrides `_DB_PATH` on `src.app` only, so a missing argument sends tests at the real database file.

## Environment

- Virtual environment lives at `interview-assessment-scoring/.venv` (Python 3.12.12), one level above `python/`.
- Run commands from `python/`:
  - `source ../.venv/bin/activate`
  - `pytest tests/ -v`
  - `uvicorn src.app:app --reload --port 8000`
- Docker is the final check, not the development loop. The image copies `src/` and `tests/` at build time and compose mounts only `data/`, so edits need a rebuild: `docker compose run --build test`.

## Part 1: `calculate_score` in `src/scoring.py`

Single function. No helper functions.

### Step by step

1. Create an empty list `section_scores`.
2. Set `overall` to `0.0`, which accumulates the raw weighted score.
3. For each `section` in `sections`:
   1. Read the section's `questions` dict.
   2. If `questions` is empty, raise `ValueError` with a message naming the section id.
   3. Set `points_possible` to the number of questions.
   4. Set `points_earned` to `0`.
   5. For each `question_id, correct_answer` in the questions dict:
      1. Look up the student's answer with `submitted_answers.get(question_id)`.
      2. If there is no answer, continue. It counts as incorrect.
      3. Compare `submitted.strip().casefold() == correct_answer.strip().casefold()`.
      4. If equal, add 1 to `points_earned`.
   6. Set `percentage` to `points_earned / points_possible`, kept raw (unrounded).
   7. Set the section's `passed` to `percentage >= MASTERY_THRESHOLD`, using the raw value.
   8. Add `percentage * section["weight"]` to `overall`.
   9. Append a dict with `id`, `name`, `points_earned`, `points_possible`, `percentage` rounded to 4 decimals, and `passed`.
4. After the loop, set `all_sections_passed` to whether every entry in `section_scores` has `passed` true.
5. Set `overall_passed` to `round(overall, 9) >= MASTERY_THRESHOLD`.
6. Set `passed` to `overall_passed and all_sections_passed`.
7. Return `{"section_scores": section_scores, "overall_percentage": round(overall, 4), "passed": passed}`.

### Decisions behind it

- **Iterate the section's questions, not the submitted answers.** This makes unanswered questions count as incorrect and answers to unknown questions get ignored, both required by the docstring.
- **No early exit on a failed section.** Every section must still produce a score; a teacher needs the breakdown for failing students, and Part 2 depends on it.
- **`casefold()` plus `strip()` on both sides.** Case-insensitivity is in the docstring. Trimming leading and trailing spaces goes slightly beyond it and is a deliberate choice. Internal spaces are preserved ("main idea" stays two words). No Unicode normalization and no accent stripping: whether "café" should match "cafe" is a grading policy question for the product team, not a decision to make silently.
- **Zero-question section raises `ValueError`.** Any score picked for an empty section is arbitrary: 1.0 hands out free credit weighted into the overall score, 0.0 makes the assessment impossible to pass, and excluding it silently rewrites the assessment's weights. The input is invalid, so it surfaces as an error (a 500 from the submit endpoint).
- **`round(overall, 9)` in the pass check.** This removes floating-point error only. With weights 0.7/0.3 and 4/5 correct in both sections, every section passes at exactly 0.8 but the raw sum is `0.7999999999999999`, which would fail. It changes no real grade: 0.7996 still fails. Rounding to tenths or hundredths was rejected because it lowers the effective mastery threshold, which is a grading policy decision.
- **Pass/fail computed from raw values, rounding applied only to output.** Rounding first would compound error into the overall score and, in edge cases, flip a result.
- **4 decimals in the output.** The seed data stores 3. Harmless, since nothing compares stored percentages, and the stored `passed` flag is computed at submit time. Noted in NOTES.
- **Weights are trusted to sum to 1.0**, per the docstring guarantee. Not validated. Noted in NOTES.

### Tests

Existing:

- `tests/test_api.py::test_submit_returns_500_before_scoring_implemented`: add `@pytest.mark.skip(reason="...")` with a reason saying the test only described behavior before `calculate_score` was implemented. Skip rather than delete, so the change stays visible in test output. No other existing test changes.

No new tests added to `tests/test_scoring.py`. The existing suite there already defines the expected behavior; `calculate_score` is implemented to satisfy it as written.

### Definition of done

All scoring tests pass, all API tests pass, one test skipped. Verified locally, then with `docker compose run --build test`.

## Part 2: class assessment results

New endpoint: `GET /classes/{class_id}/results`, with an optional `assessment_id` query parameter.

Chosen over extending `GET /classes/{class_id}` because that response is contract-tested to contain no `scores` or `submissions` key, and because a class resource returning per-student assessment results widens what the endpoint means. A query parameter (rather than the assessment in the path) allows one endpoint to serve both "how did this class do on this assessment" and "how is this class doing across assessments".

### New models in `src/models.py`

```python
class StudentResults(StudentSummary):            # inherits id, name
    submissions: list[SubmissionResponse]

class SectionPerformance(BaseModel):
    id: str
    name: str
    average_percentage: float
    submitted_count: int
    passed_count: int
    passing_student_ids: list[str]
    failing_student_ids: list[str]

class AssessmentResultsSummary(BaseModel):
    id: str
    name: str
    students_submitted: int
    students_not_submitted: int
    students_passed: int
    sections: list[SectionPerformance]

class ClassResultsResponse(BaseModel):
    id: str
    name: str
    teacher_name: str
    students: list[StudentResults]
    assessment_summaries: list[AssessmentResultsSummary]
```

`AssessmentSummary` and `SectionSummary` already exist with different meanings (plain id/name, and id/name/weight). Do not reuse or change them.

`SubmissionResponse` is reused inside `StudentResults` even though it repeats `student_id`, and repeats `assessment_id` on every row when filtered. Deliberate: one shape clients already know, less code. Noted in NOTES.

### `database.py`: `get_class_results(class_id, assessment_id, db_path)` step by step

1. Open a connection.
2. Query `classes` for `id`, `name`, `teacher_name` where `id = class_id`. If there is no row, return `None`.
3. Run one query for the roster and any results:

```sql
SELECT s.id AS student_id, s.name AS student_name,
       sub.id AS submission_id, sub.assessment_id, a.name AS assessment_name,
       sub.section_scores, sub.overall_percentage, sub.passed
FROM class_students cs
JOIN students s ON s.id = cs.student_id
LEFT JOIN submissions sub
       ON sub.student_id = s.id
      AND (? IS NULL OR sub.assessment_id = ?)
LEFT JOIN assessments a ON a.id = sub.assessment_id
WHERE cs.class_id = ?
ORDER BY s.id, sub.assessment_id
```

- The assessment filter belongs in the `ON` clause. In `WHERE` it turns the `LEFT JOIN` into an inner join and drops students who never submitted.
- Bind `assessment_id` twice, then `class_id`.
- The join to `assessments` supplies the assessment name, which `submissions` does not store.
- Section names come from the stored `section_scores` JSON, so the `sections` table is not queried. Section weights are not surfaced.

4. Assemble and return `ClassResultsResponse` as follows.

#### Assembly step by step

1. Start an ordered mapping of students keyed by `student_id`, each holding `id`, `name`, and an empty `submissions` list.
2. Start an ordered mapping of assessments keyed by `assessment_id`.
3. For each row:
   1. Add the student to the student mapping if not present.
   2. If `submission_id` is null, this student has no submission in scope. Continue.
   3. Parse `section_scores` from JSON into a list of section dicts.
   4. Append a `SubmissionResponse` to that student's `submissions`.
   5. Add the assessment to the assessment mapping if not present, with its id, name, and an empty per-section accumulator.
   6. For each parsed section, record under that assessment and section id: the section name, the student's `percentage`, and whether the student passed that section, tagged with the student id.
4. Roster size is the number of students in the student mapping.
5. For each assessment in the mapping:
   1. `students_submitted`: number of students with a submission for it.
   2. `students_not_submitted`: roster size minus `students_submitted`.
   3. `students_passed`: number of those students whose submission `passed` is true.
   4. Per section: `average_percentage` is the mean of that section's percentages across submitted students, rounded to 4 decimals; `submitted_count` is how many students that section covers; `passing_student_ids` and `failing_student_ids` come from the tags; `passed_count` is the length of the passing list. Order sections by section id.
   5. Build an `AssessmentResultsSummary`.
6. Build `ClassResultsResponse` with the class fields, students in roster order (student id), and assessment summaries ordered by assessment id.

Averages and pass counts cover submitted students only. A student who never submitted is not averaged in; missing a test is not an evaluation of their understanding. `students_not_submitted` carries that information separately.

Assembly lives in `database.py` to match the existing pattern of returning response models from that layer. Splitting SQL and assembly into separate layers is recorded in NOTES as a future improvement.

### Route step by step (`src/app.py`)

1. `@app.get("/classes/{class_id}/results")`, signature `get_class_results(class_id: str, assessment_id: str | None = None) -> ClassResultsResponse`. Give the route function a distinct name from the database function it calls.
2. If `assessment_id` is provided, verify the assessment exists (reuse `get_assessment_detail`). If it does not, raise `HTTPException(404, "Assessment not found")`. A typo should not return a page of empty results that reads as total class failure.
3. Call the database function, passing `_DB_PATH` explicitly.
4. If it returns `None`, raise `HTTPException(404, "Class not found")`.
5. Return the response.

A class and assessment that both exist with no submissions is a 200 with empty `submissions` lists, not an error.

### Tests to add (`tests/test_api.py`)

- Unknown class returns 404.
- Unknown `assessment_id` returns 404.
- Without `assessment_id`: every assessment the class has submissions for appears in `assessment_summaries`, and no others.
- With `assessment_id`: only that assessment appears in submissions and summaries.
- A rostered student with no submission appears with an empty `submissions` list (`student-005` in `class-001`).
- Section averages and pass counts match hand-checked seed values for `class-001` on `assess-001`.
- `passing_student_ids` and `failing_student_ids` contain the right students for one section.
- `students_not_submitted` is correct.
- `GET /classes/{class_id}` still has no `scores` or `submissions` key.

### Definition of done

Full suite green locally and under `docker compose run --build test`, plus a manual check with curl:

```bash
curl "http://localhost:8000/classes/class-001/results"
curl "http://localhost:8000/classes/class-001/results?assessment_id=assess-001"
```