CREATE TABLE IF NOT EXISTS assessments (
    id   TEXT PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sections (
    id            TEXT PRIMARY KEY,
    assessment_id TEXT NOT NULL REFERENCES assessments(id),
    name          TEXT NOT NULL,
    weight        REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS questions (
    id             TEXT PRIMARY KEY,
    section_id     TEXT NOT NULL REFERENCES sections(id),
    correct_answer TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS students (
    id   TEXT PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS classes (
    id           TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    teacher_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS class_students (
    class_id   TEXT NOT NULL REFERENCES classes(id),
    student_id TEXT NOT NULL REFERENCES students(id),
    PRIMARY KEY (class_id, student_id)
);

CREATE TABLE IF NOT EXISTS submissions (
    id                 TEXT PRIMARY KEY,
    student_id         TEXT NOT NULL,
    assessment_id      TEXT NOT NULL REFERENCES assessments(id),
    section_scores     TEXT NOT NULL,
    overall_percentage REAL NOT NULL,
    passed             INTEGER NOT NULL
);

-- Assessments

INSERT OR IGNORE INTO assessments VALUES ('assess-001', 'Grade 3 Reading');
INSERT OR IGNORE INTO assessments VALUES ('assess-002', 'Grade 3 Math');

-- Sections

INSERT OR IGNORE INTO sections VALUES ('sec-001', 'assess-001', 'Vocabulary',    0.4);
INSERT OR IGNORE INTO sections VALUES ('sec-002', 'assess-001', 'Comprehension', 0.6);
INSERT OR IGNORE INTO sections VALUES ('sec-003', 'assess-002', 'Computation',   0.5);
INSERT OR IGNORE INTO sections VALUES ('sec-004', 'assess-002', 'Word Problems', 0.5);

-- Questions

INSERT OR IGNORE INTO questions VALUES ('q-001', 'sec-001', 'author');
INSERT OR IGNORE INTO questions VALUES ('q-002', 'sec-001', 'setting');
INSERT OR IGNORE INTO questions VALUES ('q-003', 'sec-001', 'plot');

INSERT OR IGNORE INTO questions VALUES ('q-004', 'sec-002', 'main idea');
INSERT OR IGNORE INTO questions VALUES ('q-005', 'sec-002', 'inference');
INSERT OR IGNORE INTO questions VALUES ('q-006', 'sec-002', 'evidence');
INSERT OR IGNORE INTO questions VALUES ('q-007', 'sec-002', 'summary');

INSERT OR IGNORE INTO questions VALUES ('q-008', 'sec-003', '12');
INSERT OR IGNORE INTO questions VALUES ('q-009', 'sec-003', '25');
INSERT OR IGNORE INTO questions VALUES ('q-010', 'sec-003', '144');

INSERT OR IGNORE INTO questions VALUES ('q-011', 'sec-004', '8 apples');
INSERT OR IGNORE INTO questions VALUES ('q-012', 'sec-004', '15 minutes');
INSERT OR IGNORE INTO questions VALUES ('q-013', 'sec-004', '$3.50');

-- Students

INSERT OR IGNORE INTO students VALUES ('student-001', 'Maya Chen');
INSERT OR IGNORE INTO students VALUES ('student-002', 'Jordan Williams');
INSERT OR IGNORE INTO students VALUES ('student-003', 'Priya Patel');
INSERT OR IGNORE INTO students VALUES ('student-004', 'Alex Thompson');
INSERT OR IGNORE INTO students VALUES ('student-005', 'Sam Rivera');
INSERT OR IGNORE INTO students VALUES ('student-006', 'Casey Kim');
INSERT OR IGNORE INTO students VALUES ('student-007', 'Riley Johnson');
INSERT OR IGNORE INTO students VALUES ('student-008', 'Morgan Davis');
INSERT OR IGNORE INTO students VALUES ('student-009', 'Taylor Brown');
INSERT OR IGNORE INTO students VALUES ('student-010', 'Jamie Lee');

-- Classes

INSERT OR IGNORE INTO classes VALUES ('class-001', 'Room 12A', 'Ms. Rivera');
INSERT OR IGNORE INTO classes VALUES ('class-002', 'Room 12B', 'Mr. Chen');
INSERT OR IGNORE INTO classes VALUES ('class-003', 'Room 12C', 'Ms. Johnson');

-- Class rosters

INSERT OR IGNORE INTO class_students VALUES ('class-001', 'student-001');
INSERT OR IGNORE INTO class_students VALUES ('class-001', 'student-002');
INSERT OR IGNORE INTO class_students VALUES ('class-001', 'student-003');
INSERT OR IGNORE INTO class_students VALUES ('class-001', 'student-004');
INSERT OR IGNORE INTO class_students VALUES ('class-001', 'student-005');

INSERT OR IGNORE INTO class_students VALUES ('class-002', 'student-004');
INSERT OR IGNORE INTO class_students VALUES ('class-002', 'student-005');
INSERT OR IGNORE INTO class_students VALUES ('class-002', 'student-006');
INSERT OR IGNORE INTO class_students VALUES ('class-002', 'student-007');
INSERT OR IGNORE INTO class_students VALUES ('class-002', 'student-008');

INSERT OR IGNORE INTO class_students VALUES ('class-003', 'student-006');
INSERT OR IGNORE INTO class_students VALUES ('class-003', 'student-007');
INSERT OR IGNORE INTO class_students VALUES ('class-003', 'student-009');
INSERT OR IGNORE INTO class_students VALUES ('class-003', 'student-010');

-- Pre-seeded submissions

INSERT OR IGNORE INTO submissions VALUES (
    'sub-001', 'student-001', 'assess-001',
    '[{"id":"sec-001","name":"Vocabulary","points_earned":3,"points_possible":3,"percentage":1.0,"passed":true},{"id":"sec-002","name":"Comprehension","points_earned":4,"points_possible":4,"percentage":1.0,"passed":true}]',
    1.0, 1
);

INSERT OR IGNORE INTO submissions VALUES (
    'sub-002', 'student-002', 'assess-001',
    '[{"id":"sec-001","name":"Vocabulary","points_earned":3,"points_possible":3,"percentage":1.0,"passed":true},{"id":"sec-002","name":"Comprehension","points_earned":4,"points_possible":4,"percentage":1.0,"passed":true}]',
    1.0, 1
);

INSERT OR IGNORE INTO submissions VALUES (
    'sub-003', 'student-003', 'assess-001',
    '[{"id":"sec-001","name":"Vocabulary","points_earned":3,"points_possible":3,"percentage":1.0,"passed":true},{"id":"sec-002","name":"Comprehension","points_earned":2,"points_possible":4,"percentage":0.5,"passed":false}]',
    0.7, 0
);

INSERT OR IGNORE INTO submissions VALUES (
    'sub-004', 'student-004', 'assess-001',
    '[{"id":"sec-001","name":"Vocabulary","points_earned":1,"points_possible":3,"percentage":0.333,"passed":false},{"id":"sec-002","name":"Comprehension","points_earned":4,"points_possible":4,"percentage":1.0,"passed":true}]',
    0.733, 0
);

INSERT OR IGNORE INTO submissions VALUES (
    'sub-005', 'student-006', 'assess-001',
    '[{"id":"sec-001","name":"Vocabulary","points_earned":2,"points_possible":3,"percentage":0.667,"passed":false},{"id":"sec-002","name":"Comprehension","points_earned":3,"points_possible":4,"percentage":0.75,"passed":false}]',
    0.717, 0
);

INSERT OR IGNORE INTO submissions VALUES (
    'sub-006', 'student-007', 'assess-001',
    '[{"id":"sec-001","name":"Vocabulary","points_earned":0,"points_possible":3,"percentage":0.0,"passed":false},{"id":"sec-002","name":"Comprehension","points_earned":1,"points_possible":4,"percentage":0.25,"passed":false}]',
    0.15, 0
);

INSERT OR IGNORE INTO submissions VALUES (
    'sub-007', 'student-009', 'assess-001',
    '[{"id":"sec-001","name":"Vocabulary","points_earned":3,"points_possible":3,"percentage":1.0,"passed":true},{"id":"sec-002","name":"Comprehension","points_earned":4,"points_possible":4,"percentage":1.0,"passed":true}]',
    1.0, 1
);

INSERT OR IGNORE INTO submissions VALUES (
    'sub-008', 'student-010', 'assess-001',
    '[{"id":"sec-001","name":"Vocabulary","points_earned":3,"points_possible":3,"percentage":1.0,"passed":true},{"id":"sec-002","name":"Comprehension","points_earned":3,"points_possible":4,"percentage":0.75,"passed":false}]',
    0.85, 0
);

INSERT OR IGNORE INTO submissions VALUES (
    'sub-009', 'student-001', 'assess-002',
    '[{"id":"sec-003","name":"Computation","points_earned":3,"points_possible":3,"percentage":1.0,"passed":true},{"id":"sec-004","name":"Word Problems","points_earned":3,"points_possible":3,"percentage":1.0,"passed":true}]',
    1.0, 1
);

INSERT OR IGNORE INTO submissions VALUES (
    'sub-010', 'student-009', 'assess-002',
    '[{"id":"sec-003","name":"Computation","points_earned":2,"points_possible":3,"percentage":0.667,"passed":false},{"id":"sec-004","name":"Word Problems","points_earned":2,"points_possible":3,"percentage":0.667,"passed":false}]',
    0.667, 0
);
