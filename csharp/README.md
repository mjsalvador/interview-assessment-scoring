# Assessment Scoring Service — C#

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) with Docker Compose

## Getting started

```bash
docker compose up
```

The API will be available at `http://localhost:8080`.

## Running the tests

```bash
docker compose run test
```

Before you implement the scoring function, 8 tests pass and 8 fail. All 16 should pass once your implementation is correct.

To run only the scoring unit tests:

```bash
docker compose run test --filter "Category=Scoring"
```

## API reference

### Submit an assessment

```bash
curl -X POST http://localhost:8080/assessments/assess-001/submit \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "student-001",
    "answers": {
      "q-001": "author",
      "q-002": "setting",
      "q-004": "main idea"
    }
  }'
```

### Get a student's scores

```bash
curl http://localhost:8080/students/student-001/scores
```

### List classes

```bash
curl http://localhost:8080/classes
```

### Get a class with its students

```bash
curl http://localhost:8080/classes/class-001
```

### List assessments

```bash
curl http://localhost:8080/assessments
```

### Get assessment detail

```bash
curl http://localhost:8080/assessments/assess-001
```

## What to implement

**Part 1 — Scoring function:** Open `src/AssessmentScoring/Services/ScoringService.cs`. The method `Calculate` is stubbed out — read the XML doc comment carefully, then implement it. The tests in `tests/AssessmentScoring.Tests/ScoringTests.cs` define exactly what it should do.

**Part 2 — Class results feature:** The `GET /classes/{class_id}` endpoint returns a class roster but no assessment data. Extend the API so it also returns each student's latest score for a given assessment. Design the API shape yourself.

## What to submit

Fill in `../NOTES.md.template` and bring it to the live session.
