import json
import sqlite3
from contextlib import closing
from pathlib import Path
from uuid import uuid4

from src.models import (
    AssessmentDetailResponse,
    AssessmentList,
    AssessmentResultsSummary,
    AssessmentSummary,
    AssessmentWithSections,
    ClassList,
    ClassResponse,
    ClassResultsResponse,
    ClassSummary,
    QuestionAnswer,
    ScoringSection,
    SectionPerformance,
    SectionScoreResponse,
    SectionSummary,
    StudentResults,
    StudentSummary,
    SubmissionResponse,
    SubmissionResponseList,
)

_DB_PATH = Path(__file__).parent.parent / "data" / "assessments.db"
_SEED_PATH = Path(__file__).parent.parent / "data" / "seed.sql"


def _connect(db_path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: str | Path = _DB_PATH) -> None:
    seed_sql = _SEED_PATH.read_text()
    with closing(_connect(db_path)) as conn:
        conn.executescript(seed_sql)


def get_assessment_with_sections(
    assessment_id: str, db_path: str | Path = _DB_PATH
) -> AssessmentWithSections | None:
    with closing(_connect(db_path)) as conn:
        row = conn.execute(
            "SELECT id, name FROM assessments WHERE id = ?", (assessment_id,)
        ).fetchone()
        if row is None:
            return None

        section_rows = conn.execute(
            "SELECT id, name, weight FROM sections WHERE assessment_id = ? ORDER BY id",
            (assessment_id,),
        ).fetchall()

        sections = []
        for sec_row in section_rows:
            question_rows = conn.execute(
                "SELECT id, correct_answer FROM questions WHERE section_id = ? ORDER BY id",
                (sec_row["id"],),
            ).fetchall()
            sections.append(
                ScoringSection(
                    id=sec_row["id"],
                    name=sec_row["name"],
                    weight=sec_row["weight"],
                    questions=[
                        QuestionAnswer(id=q["id"], correct_answer=q["correct_answer"])
                        for q in question_rows
                    ],
                )
            )

        return AssessmentWithSections(id=row["id"], name=row["name"], sections=sections)


def save_submission(
    student_id: str,
    assessment_id: str,
    section_scores: list[SectionScoreResponse],
    overall_percentage: float,
    passed: bool,
    db_path: str | Path = _DB_PATH,
) -> str:
    section_scores_json = json.dumps([s.model_dump() for s in section_scores])
    with closing(_connect(db_path)) as conn:
        existing = conn.execute(
            "SELECT id FROM submissions WHERE student_id = ? AND assessment_id = ?",
            (student_id, assessment_id),
        ).fetchone()

        if existing:
            conn.execute(
                "UPDATE submissions SET section_scores = ?, overall_percentage = ?, passed = ?"
                " WHERE id = ?",
                (section_scores_json, overall_percentage, int(passed), existing["id"]),
            )
            conn.commit()
            return existing["id"]
        else:
            submission_id = f"sub-{uuid4().hex[:8]}"
            conn.execute(
                "INSERT INTO submissions"
                " (id, student_id, assessment_id, section_scores, overall_percentage, passed)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (submission_id, student_id, assessment_id,
                 section_scores_json, overall_percentage, int(passed)),
            )
            conn.commit()
            return submission_id


def get_submissions_for_student(
    student_id: str, db_path: str | Path = _DB_PATH
) -> SubmissionResponseList:
    with closing(_connect(db_path)) as conn:
        rows = conn.execute(
            "SELECT id, student_id, assessment_id, section_scores, overall_percentage, passed"
            " FROM submissions WHERE student_id = ?",
            (student_id,),
        ).fetchall()

    return SubmissionResponseList(
        responses=[
            SubmissionResponse(
                submission_id=row["id"],
                student_id=row["student_id"],
                assessment_id=row["assessment_id"],
                section_scores=[
                    SectionScoreResponse.model_validate(score)
                    for score in json.loads(row["section_scores"])
                ],
                overall_percentage=row["overall_percentage"],
                passed=bool(row["passed"]),
            )
            for row in rows
        ]
    )


def get_classes(db_path: str | Path = _DB_PATH) -> ClassList:
    with closing(_connect(db_path)) as conn:
        rows = conn.execute("SELECT id, name FROM classes ORDER BY id").fetchall()
    return ClassList(
        classes=[ClassSummary(id=row["id"], name=row["name"]) for row in rows]
    )


def get_class_with_students(
    class_id: str, db_path: str | Path = _DB_PATH
) -> ClassResponse | None:
    with closing(_connect(db_path)) as conn:
        row = conn.execute(
            "SELECT id, name, teacher_name FROM classes WHERE id = ?", (class_id,)
        ).fetchone()
        if row is None:
            return None

        student_rows = conn.execute(
            "SELECT s.id, s.name FROM students s"
            " JOIN class_students cs ON s.id = cs.student_id"
            " WHERE cs.class_id = ? ORDER BY s.id",
            (class_id,),
        ).fetchall()

    return ClassResponse(
        id=row["id"],
        name=row["name"],
        teacher_name=row["teacher_name"],
        students=[StudentSummary(id=s["id"], name=s["name"]) for s in student_rows],
    )


def get_assessments(db_path: str | Path = _DB_PATH) -> AssessmentList:
    with closing(_connect(db_path)) as conn:
        rows = conn.execute("SELECT id, name FROM assessments ORDER BY id").fetchall()
    return AssessmentList(
        assessments=[AssessmentSummary(id=row["id"], name=row["name"]) for row in rows]
    )


def get_assessment_detail(
    assessment_id: str, db_path: str | Path = _DB_PATH
) -> AssessmentDetailResponse | None:
    with closing(_connect(db_path)) as conn:
        row = conn.execute(
            "SELECT id, name FROM assessments WHERE id = ?", (assessment_id,)
        ).fetchone()
        if row is None:
            return None

        section_rows = conn.execute(
            "SELECT id, name, weight FROM sections WHERE assessment_id = ? ORDER BY id",
            (assessment_id,),
        ).fetchall()

    return AssessmentDetailResponse(
        id=row["id"],
        name=row["name"],
        sections=[
            SectionSummary(id=s["id"], name=s["name"], weight=s["weight"])
            for s in section_rows
        ],
    )


def get_class_results(
    class_id: str,
    assessment_id: str | None,
    db_path: str | Path = _DB_PATH,
) -> ClassResultsResponse | None:
    with closing(_connect(db_path)) as conn:
        row = conn.execute(
            "SELECT id, name, teacher_name FROM classes WHERE id = ?", (class_id,)
        ).fetchone()
        if row is None:
            return None

        rows = conn.execute(
            """
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
            """,
            (assessment_id, assessment_id, class_id),
        ).fetchall()

    students: dict[str, dict] = {}
    assessments: dict[str, dict] = {}

    for r in rows:
        student_id = r["student_id"]
        if student_id not in students:
            students[student_id] = {
                "id": student_id,
                "name": r["student_name"],
                "submissions": [],
            }

        if r["submission_id"] is None:
            continue

        parsed_sections = json.loads(r["section_scores"])
        students[student_id]["submissions"].append(
            SubmissionResponse(
                submission_id=r["submission_id"],
                student_id=student_id,
                assessment_id=r["assessment_id"],
                section_scores=[
                    SectionScoreResponse.model_validate(sec) for sec in parsed_sections
                ],
                overall_percentage=r["overall_percentage"],
                passed=bool(r["passed"]),
            )
        )

        a_id = r["assessment_id"]
        if a_id not in assessments:
            assessments[a_id] = {
                "id": a_id,
                "name": r["assessment_name"],
                "submitted_student_ids": [],
                "passed_student_ids": [],
                "sections": {},
            }
        assessments[a_id]["submitted_student_ids"].append(student_id)
        if bool(r["passed"]):
            assessments[a_id]["passed_student_ids"].append(student_id)

        for sec in parsed_sections:
            sec_acc = assessments[a_id]["sections"].setdefault(
                sec["id"],
                {"name": sec["name"], "percentages": [], "passing_ids": [], "failing_ids": []},
            )
            sec_acc["percentages"].append(sec["percentage"])
            if sec["passed"]:
                sec_acc["passing_ids"].append(student_id)
            else:
                sec_acc["failing_ids"].append(student_id)

    roster_size = len(students)

    assessment_summaries = []
    for a_id in sorted(assessments):
        acc = assessments[a_id]
        students_submitted = len(acc["submitted_student_ids"])
        submitted_ids = set(acc["submitted_student_ids"])
        not_submitted_ids = [sid for sid in students if sid not in submitted_ids]
        section_performances = [
            SectionPerformance(
                id=sec_id,
                name=acc["sections"][sec_id]["name"],
                average_percentage=round(
                    sum(acc["sections"][sec_id]["percentages"])
                    / len(acc["sections"][sec_id]["percentages"]),
                    4,
                ),
                submitted_count=len(acc["sections"][sec_id]["percentages"]),
                passed_count=len(acc["sections"][sec_id]["passing_ids"]),
                passing_student_ids=acc["sections"][sec_id]["passing_ids"],
                failing_student_ids=acc["sections"][sec_id]["failing_ids"],
            )
            for sec_id in sorted(acc["sections"])
        ]
        assessment_summaries.append(
            AssessmentResultsSummary(
                id=a_id,
                name=acc["name"],
                students_submitted=students_submitted,
                students_not_submitted=roster_size - students_submitted,
                students_not_submitted_ids=not_submitted_ids,
                students_passed=len(acc["passed_student_ids"]),
                sections=section_performances,
            )
        )

    return ClassResultsResponse(
        id=row["id"],
        name=row["name"],
        teacher_name=row["teacher_name"],
        students=[
            StudentResults(id=s["id"], name=s["name"], submissions=s["submissions"])
            for s in students.values()
        ],
        assessment_summaries=assessment_summaries,
    )
