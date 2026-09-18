# Codebase Report: Assessment Scoring Service

## 1. Executive Summary

A small HTTP API for student assessments. Students belong to classes. A student submits answers to a sectioned assessment; the service scores each section against the correct answers, computes a weighted overall score, decides pass/fail against a mastery threshold, and stores the result. Teachers can read a student's stored scores, list classes and assessments, and view a class roster.

The repo ships two functionally identical implementations: `python/` (FastAPI) and `csharp/` (.NET). This report covers `python/`, the implementation being used for the exercise.

Key functionality:

- Submit answers and receive a scored result (`POST /assessments/{assessment_id}/submit`)
- Read all stored results for a student (`GET /students/{student_id}/scores`)
- List classes, and read one class with its student roster (`GET /classes`, `GET /classes/{class_id}`)
- List assessments, and read one assessment with its sections and weights (`GET /assessments`, `GET /assessments/{assessment_id}`)

Current state:

- `calculate_score` in `src/scoring.py` is a stub that raises `NotImplementedError`
- The class endpoint returns a roster only, with no assessment results
- Test baseline: 16 tests, 8 pass and 8 fail (verified locally)

## 2. High-Level Architecture

### Directory map

```
interview-assessment-scoring/
├── README.md                  # Exercise overview, pick a language
├── NOTES.md.template          # Submission notes template
├── csharp/                    # .NET implementation (not in use)
└── python/
    ├── Dockerfile             # python:3.12-slim, copies src/tests/data at build time
    ├── docker-compose.yml     # `api` service (:8000) and `test` service (pytest)
    ├── requirements.txt       # fastapi, uvicorn, pydantic, pytest, httpx, pytest-asyncio (unpinned)
    ├── pytest.ini             # pythonpath = .
    ├── data/
    │   └── seed.sql           # Schema + seed data, run on every startup
    ├── src/
    │   ├── app.py             # FastAPI app, routes, lifespan (DB init)
    │   ├── database.py        # SQLite access functions, row -> model mapping
    │   ├── models.py          # Pydantic request/response/internal models
    │   ├── scoring.py         # calculate_score (stub)
    │   └── config.py          # MASTERY_THRESHOLD = 0.8
    └── tests/
        ├── conftest.py        # TestClient fixture with temp DB path
        ├── test_api.py        # 10 HTTP-level tests
        └── test_scoring.py    # 6 unit tests for calculate_score
```

### Layers

```
HTTP request
   │
   ▼
app.py            Route handlers: validation via Pydantic, 404 handling, orchestration
   │
   ├──► database.py   Raw SQL via sqlite3, maps rows to Pydantic models
   │        │
   │        ▼
   │     data/assessments.db  (SQLite file, created and seeded from seed.sql)
   │
   └──► scoring.py    Pure function, plain dicts in and out, no I/O
            │
            ▼
         config.py    MASTERY_THRESHOLD
```

### Submit flow (the main write path)

```
POST /assessments/{assessment_id}/submit   body: { student_id, answers: {question_id: answer} }
  1. FastAPI validates body against SubmitRequest (missing student_id -> 422)
  2. database.get_assessment_with_sections -> AssessmentWithSections (unknown id -> 404)
  3. app.py reshapes models into plain dicts:
       [{ id, name, weight, questions: {question_id: correct_answer} }, ...]
  4. scoring.calculate_score(answers, sections) -> dict
       { section_scores: [...], overall_percentage, passed }
  5. Each section score validated into SectionScoreResponse
  6. database.save_submission -> upsert keyed on (student_id, assessment_id), returns submission_id
  7. Return SubmissionResponse
```

### Read flows

```
GET /students/{id}/scores   -> get_submissions_for_student   -> list[SubmissionResponse] (empty list if none)
GET /classes                -> get_classes                   -> list[ClassSummary]
GET /classes/{id}           -> get_class_with_students       -> ClassResponse (404 if missing)
GET /assessments            -> get_assessments               -> list[AssessmentSummary]
GET /assessments/{id}       -> get_assessment_detail         -> AssessmentDetailResponse (404 if missing)
```

### Entry points

- Runtime: `uvicorn src.app:app` (Dockerfile `CMD`), started with `docker compose up`
- Startup: FastAPI `lifespan` calls `init_db(_DB_PATH)`, which executes `seed.sql` every boot (idempotent via `CREATE TABLE IF NOT EXISTS` and `INSERT OR IGNORE`)
- Tests: `pytest tests/ -v` via `docker compose run test`

## 3. Core Modules & Responsibilities

### `src/app.py`
- Defines the FastAPI app and all six routes
- Owns the module-level `_DB_PATH` and passes it explicitly to every database call
- Translates `None` from the database layer into 404s
- Bridges models and scoring: converts `ScoringSection` models to the dict shape `calculate_score` expects, then validates the result back into `SectionScoreResponse`

### `src/database.py`
- One function per query use case; each opens and closes its own connection (`contextlib.closing`)
- Connections enable `PRAGMA foreign_keys = ON` and use `sqlite3.Row`
- Every function takes a `db_path` argument (defaults to its own module-level `_DB_PATH`)
- `get_assessment_with_sections`: one query for sections, then one query per section for questions
- `save_submission`: SELECT then UPDATE or INSERT on (student_id, assessment_id); overwrites prior results rather than keeping history
- `get_submissions_for_student`: no ordering, deserializes `section_scores` JSON
- `get_class_with_students`: roster via join on `class_students`, ordered by student id

### `src/models.py`
- Request: `SubmitRequest` (`student_id` required, `answers: dict[str, str]` defaults to empty)
- Responses: `SubmissionResponse`, `SectionScoreResponse`, `ClassResponse`, `ClassSummary`, `StudentSummary`, `AssessmentSummary`, `AssessmentDetailResponse`, `SectionSummary`
- List wrappers used only between database and app: `SubmissionResponseList`, `ClassList`, `AssessmentList`
- Internal scoring input: `AssessmentWithSections` -> `ScoringSection` -> `QuestionAnswer`

### `src/scoring.py`
- `calculate_score(submitted_answers, sections) -> dict`, currently unimplemented
- Pure function with no database or HTTP dependency
- Docstring contract:
  - Per section: `points_earned`, `points_possible`, `percentage` (0.0 to 1.0), `passed` (percentage >= threshold)
  - `overall_percentage`: weighted average of section percentages
  - `passed`: overall >= threshold AND every section passed
  - Unanswered questions are incorrect; answers to unknown questions are ignored; comparison is case-insensitive; empty submission is valid; weights sum to 1.0

### `src/config.py`
- `MASTERY_THRESHOLD = 0.8`, shared by scoring and tests

### `data/seed.sql`
- Schema and seed data (see Data Model below)

### `tests/`
- `conftest.py`: `test_client` fixture sets `src.app._DB_PATH` to a per-test temp file, then starts `TestClient` (which runs lifespan, so each test gets a freshly seeded DB)
- `test_scoring.py`: 6 unit tests against a local two-section fixture (weights 0.4 / 0.6)
- `test_api.py`: 10 endpoint tests covering validation, 404s, list endpoints, submit, and read-after-submit
- Currently failing: all 6 scoring tests, `test_submit_returns_score_result`, `test_get_scores_returns_submission_after_submit`

## 4. Dependencies & Integration

### Libraries
- **FastAPI**: routing, request validation, response serialization via return type annotations
- **Pydantic v2**: models, `model_validate`, `model_dump`
- **Uvicorn**: ASGI server
- **pytest / httpx**: tests via FastAPI `TestClient`
- **pytest-asyncio**: installed, unused (all routes and tests are synchronous)
- **sqlite3** (standard library): no ORM, no migrations
- All dependencies are unpinned

### Data model

```
assessments (id, name)
  └── sections (id, assessment_id FK, name, weight)
        └── questions (id, section_id FK, correct_answer)

students (id, name)
classes (id, name, teacher_name)
class_students (class_id FK, student_id FK)   PK (class_id, student_id)

submissions (id, student_id, assessment_id FK, section_scores TEXT(JSON), overall_percentage, passed)
```

- `submissions.student_id` has no foreign key to `students`
- No unique constraint on `submissions (student_id, assessment_id)`; uniqueness is enforced only in application code
- No timestamps on any table
- No relationship between classes and assessments
- `section_scores` stores a JSON array of section results, including a copy of the section name at submit time

### Seed data
- 2 assessments: Grade 3 Reading (Vocabulary 0.4, Comprehension 0.6; 3 + 4 questions), Grade 3 Math (Computation 0.5, Word Problems 0.5; 3 + 3 questions)
- 10 students, 3 classes of 4 to 5 students; some students are in two classes (student-004, 005, 006, 007)
- 10 pre-seeded submissions: 8 for Reading, 2 for Math; stored percentages are rounded to 3 decimals
- Some rostered students have no submissions (for example student-005 in class-001, student-008 in class-002)

### Docker and runtime notes
- The image copies `src/`, `tests/`, and `data/` at build time; compose mounts only `./data`. Code changes require an image rebuild before `docker compose run test` or `docker compose up` reflect them, and uvicorn `--reload` has no source changes to detect
- The SQLite file is written to `python/data/assessments.db` on the host through the volume mount (ignored by `.gitignore`)

### Test harness notes
- The fixture overrides `_DB_PATH` on `src.app` only. Database functions called without an explicit `db_path` fall back to `src.database._DB_PATH`, the real data file
- `test_submit_returns_500_before_scoring_implemented` asserts the pre-implementation failure and will fail once scoring works
- `test_get_class_returns_students_without_scores` asserts that `scores` and `submissions` keys are absent from `GET /classes/{id}`
