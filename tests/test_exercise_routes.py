import pytest

from src.exercises.app import create_app
from src.exercises.extensions import db
from src.exercises.models import Assignment, Student, Grade


@pytest.fixture()
def app():
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    })
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


# ===== HEALTH =====

def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.get_json()["status"] == "ok"


# ===== STUDENTS CRUD =====

def test_create_student(client):
    res = client.post("/students", json={"name": "Alice", "email": "alice@example.com"})
    assert res.status_code == 201
    data = res.get_json()
    assert data["name"] == "Alice"
    assert data["email"] == "alice@example.com"
    assert "id" in data


def test_create_student_missing_name(client):
    res = client.post("/students", json={"email": "alice@example.com"})
    assert res.status_code == 400
    assert "error" in res.get_json()


def test_create_student_missing_email(client):
    res = client.post("/students", json={"name": "Alice"})
    assert res.status_code == 400
    assert "error" in res.get_json()


def test_create_student_duplicate_email(client):
    client.post("/students", json={"name": "Alice", "email": "alice@example.com"})
    res = client.post("/students", json={"name": "Bob", "email": "alice@example.com"})
    assert res.status_code == 409
    assert "error" in res.get_json()


def test_list_students(client):
    client.post("/students", json={"name": "Charlie", "email": "charlie@example.com"})
    client.post("/students", json={"name": "Alice", "email": "alice@example.com"})
    client.post("/students", json={"name": "Bob", "email": "bob@example.com"})

    res = client.get("/students")
    assert res.status_code == 200
    students = res.get_json()
    assert len(students) == 3
    assert students[0]["name"] == "Alice"  # ordered by name


def test_list_students_empty(client):
    res = client.get("/students")
    assert res.status_code == 200
    assert res.get_json() == []


def test_get_student(client):
    create_res = client.post("/students", json={"name": "Alice", "email": "alice@example.com"})
    student_id = create_res.get_json()["id"]

    res = client.get(f"/students/{student_id}")
    assert res.status_code == 200
    data = res.get_json()
    assert data["name"] == "Alice"
    assert data["id"] == student_id


def test_get_student_not_found(client):
    res = client.get("/students/999")
    assert res.status_code == 404
    assert "error" in res.get_json()


def test_update_student_email(client):
    create_res = client.post("/students", json={"name": "Alice", "email": "alice@example.com"})
    student_id = create_res.get_json()["id"]

    res = client.patch(f"/students/{student_id}", json={"email": "alice.new@example.com"})
    assert res.status_code == 200
    data = res.get_json()
    assert data["email"] == "alice.new@example.com"


def test_update_student_email_missing(client):
    create_res = client.post("/students", json={"name": "Alice", "email": "alice@example.com"})
    student_id = create_res.get_json()["id"]

    res = client.patch(f"/students/{student_id}", json={})
    assert res.status_code == 400


def test_update_student_email_not_found(client):
    res = client.patch("/students/999", json={"email": "new@example.com"})
    assert res.status_code == 404


def test_update_student_email_duplicate(client):
    client.post("/students", json={"name": "Alice", "email": "alice@example.com"})
    create_res = client.post("/students", json={"name": "Bob", "email": "bob@example.com"})
    student_id = create_res.get_json()["id"]

    res = client.patch(f"/students/{student_id}", json={"email": "alice@example.com"})
    assert res.status_code == 409


def test_delete_student(client):
    create_res = client.post("/students", json={"name": "Alice", "email": "alice@example.com"})
    student_id = create_res.get_json()["id"]

    res = client.delete(f"/students/{student_id}")
    assert res.status_code == 204

    # Verify deletion
    get_res = client.get(f"/students/{student_id}")
    assert get_res.status_code == 404


def test_delete_student_not_found(client):
    res = client.delete("/students/999")
    assert res.status_code == 404


# ===== ASSIGNMENTS CRUD =====

def test_create_assignment(client):
    res = client.post("/assignments", json={"title": "Quiz 1", "max_points": 10})
    assert res.status_code == 201
    data = res.get_json()
    assert data["title"] == "Quiz 1"
    assert data["max_points"] == 10
    assert "id" in data


def test_create_assignment_missing_title(client):
    res = client.post("/assignments", json={"max_points": 10})
    assert res.status_code == 400


def test_create_assignment_missing_max_points(client):
    res = client.post("/assignments", json={"title": "Quiz 1"})
    assert res.status_code == 400


def test_create_assignment_invalid_max_points(client):
    res = client.post("/assignments", json={"title": "Quiz 1", "max_points": "invalid"})
    assert res.status_code == 400


def test_create_assignment_zero_max_points(client):
    res = client.post("/assignments", json={"title": "Quiz 1", "max_points": 0})
    assert res.status_code == 400


def test_create_assignment_negative_max_points(client):
    res = client.post("/assignments", json={"title": "Quiz 1", "max_points": -5})
    assert res.status_code == 400


def test_create_assignment_duplicate_title(client):
    client.post("/assignments", json={"title": "Quiz 1", "max_points": 10})
    res = client.post("/assignments", json={"title": "Quiz 1", "max_points": 20})
    assert res.status_code == 409


def test_list_assignments(client):
    client.post("/assignments", json={"title": "Quiz 1", "max_points": 10})
    client.post("/assignments", json={"title": "HW 1", "max_points": 100})

    res = client.get("/assignments")
    assert res.status_code == 200
    assignments = res.get_json()
    assert len(assignments) == 2
    assert assignments[0]["title"] == "HW 1"  # ordered by title


def test_list_assignments_empty(client):
    res = client.get("/assignments")
    assert res.status_code == 200
    assert res.get_json() == []


def test_get_assignment(client):
    create_res = client.post("/assignments", json={"title": "Quiz 1", "max_points": 10})
    assignment_id = create_res.get_json()["id"]

    res = client.get(f"/assignments/{assignment_id}")
    assert res.status_code == 200
    data = res.get_json()
    assert data["title"] == "Quiz 1"
    assert data["id"] == assignment_id


def test_get_assignment_not_found(client):
    res = client.get("/assignments/999")
    assert res.status_code == 404


def test_delete_assignment(client):
    create_res = client.post("/assignments", json={"title": "Quiz 1", "max_points": 10})
    assignment_id = create_res.get_json()["id"]

    res = client.delete(f"/assignments/{assignment_id}")
    assert res.status_code == 204

    # Verify deletion
    get_res = client.get(f"/assignments/{assignment_id}")
    assert get_res.status_code == 404


def test_delete_assignment_not_found(client):
    res = client.delete("/assignments/999")
    assert res.status_code == 404


# ===== GRADES CRUD =====

def test_create_grade(client):
    a_res = client.post("/assignments", json={"title": "Quiz 1", "max_points": 10})
    assignment_id = a_res.get_json()["id"]
    s_res = client.post("/students", json={"name": "Alice", "email": "alice@example.com"})
    student_id = s_res.get_json()["id"]

    res = client.post("/grades", json={
        "student_id": student_id,
        "assignment_id": assignment_id,
        "score": 9
    })
    assert res.status_code == 201
    data = res.get_json()
    assert data["score"] == 9
    assert data["student_id"] == student_id
    assert data["assignment_id"] == assignment_id


def test_create_grade_missing_student_id(client):
    a_res = client.post("/assignments", json={"title": "Quiz 1", "max_points": 10})
    assignment_id = a_res.get_json()["id"]

    res = client.post("/grades", json={"assignment_id": assignment_id, "score": 9})
    assert res.status_code == 400


def test_create_grade_missing_assignment_id(client):
    s_res = client.post("/students", json={"name": "Alice", "email": "alice@example.com"})
    student_id = s_res.get_json()["id"]

    res = client.post("/grades", json={"student_id": student_id, "score": 9})
    assert res.status_code == 400


def test_create_grade_missing_score(client):
    a_res = client.post("/assignments", json={"title": "Quiz 1", "max_points": 10})
    assignment_id = a_res.get_json()["id"]
    s_res = client.post("/students", json={"name": "Alice", "email": "alice@example.com"})
    student_id = s_res.get_json()["id"]

    res = client.post("/grades", json={"student_id": student_id, "assignment_id": assignment_id})
    assert res.status_code == 400


def test_create_grade_invalid_score(client):
    a_res = client.post("/assignments", json={"title": "Quiz 1", "max_points": 10})
    assignment_id = a_res.get_json()["id"]
    s_res = client.post("/students", json={"name": "Alice", "email": "alice@example.com"})
    student_id = s_res.get_json()["id"]

    res = client.post("/grades", json={
        "student_id": student_id,
        "assignment_id": assignment_id,
        "score": "invalid"
    })
    assert res.status_code == 400


def test_create_grade_negative_score(client):
    a_res = client.post("/assignments", json={"title": "Quiz 1", "max_points": 10})
    assignment_id = a_res.get_json()["id"]
    s_res = client.post("/students", json={"name": "Alice", "email": "alice@example.com"})
    student_id = s_res.get_json()["id"]

    res = client.post("/grades", json={
        "student_id": student_id,
        "assignment_id": assignment_id,
        "score": -5
    })
    assert res.status_code == 400


def test_create_grade_missing_student(client):
    a_res = client.post("/assignments", json={"title": "Quiz 1", "max_points": 10})
    assignment_id = a_res.get_json()["id"]

    res = client.post("/grades", json={
        "student_id": 999,
        "assignment_id": assignment_id,
        "score": 9
    })
    assert res.status_code == 404


def test_create_grade_missing_assignment(client):
    s_res = client.post("/students", json={"name": "Alice", "email": "alice@example.com"})
    student_id = s_res.get_json()["id"]

    res = client.post("/grades", json={
        "student_id": student_id,
        "assignment_id": 999,
        "score": 9
    })
    assert res.status_code == 404


def test_create_grade_duplicate(client):
    a_res = client.post("/assignments", json={"title": "Quiz 1", "max_points": 10})
    assignment_id = a_res.get_json()["id"]
    s_res = client.post("/students", json={"name": "Alice", "email": "alice@example.com"})
    student_id = s_res.get_json()["id"]

    client.post("/grades", json={
        "student_id": student_id,
        "assignment_id": assignment_id,
        "score": 9
    })
    res = client.post("/grades", json={
        "student_id": student_id,
        "assignment_id": assignment_id,
        "score": 10
    })
    assert res.status_code == 409


def test_list_grades(client):
    a_res = client.post("/assignments", json={"title": "Quiz 1", "max_points": 10})
    assignment_id = a_res.get_json()["id"]
    s_res = client.post("/students", json={"name": "Alice", "email": "alice@example.com"})
    student_id = s_res.get_json()["id"]

    client.post("/grades", json={
        "student_id": student_id,
        "assignment_id": assignment_id,
        "score": 9
    })

    res = client.get("/grades")
    assert res.status_code == 200
    grades = res.get_json()
    assert len(grades) == 1
    assert grades[0]["score"] == 9


def test_list_grades_empty(client):
    res = client.get("/grades")
    assert res.status_code == 200
    assert res.get_json() == []


def test_get_grade(client):
    a_res = client.post("/assignments", json={"title": "Quiz 1", "max_points": 10})
    assignment_id = a_res.get_json()["id"]
    s_res = client.post("/students", json={"name": "Alice", "email": "alice@example.com"})
    student_id = s_res.get_json()["id"]

    g_res = client.post("/grades", json={
        "student_id": student_id,
        "assignment_id": assignment_id,
        "score": 9
    })
    grade_id = g_res.get_json()["id"]

    res = client.get(f"/grades/{grade_id}")
    assert res.status_code == 200
    data = res.get_json()
    assert data["score"] == 9


def test_get_grade_not_found(client):
    res = client.get("/grades/999")
    assert res.status_code == 404


def test_delete_grade(client):
    a_res = client.post("/assignments", json={"title": "Quiz 1", "max_points": 10})
    assignment_id = a_res.get_json()["id"]
    s_res = client.post("/students", json={"name": "Alice", "email": "alice@example.com"})
    student_id = s_res.get_json()["id"]

    g_res = client.post("/grades", json={
        "student_id": student_id,
        "assignment_id": assignment_id,
        "score": 9
    })
    grade_id = g_res.get_json()["id"]

    res = client.delete(f"/grades/{grade_id}")
    assert res.status_code == 204

    # Verify deletion
    get_res = client.get(f"/grades/{grade_id}")
    assert get_res.status_code == 404


def test_delete_grade_not_found(client):
    res = client.delete("/grades/999")
    assert res.status_code == 404


# ===== ANALYTICS ROUTES =====

def test_student_average(client):
    a1_res = client.post("/assignments", json={"title": "Quiz 1", "max_points": 10})
    a1_id = a1_res.get_json()["id"]
    a2_res = client.post("/assignments", json={"title": "HW 1", "max_points": 100})
    a2_id = a2_res.get_json()["id"]
    s_res = client.post("/students", json={"name": "Alice", "email": "alice@example.com"})
    s_id = s_res.get_json()["id"]

    client.post("/grades", json={"student_id": s_id, "assignment_id": a1_id, "score": 10})  # 100%
    client.post("/grades", json={"student_id": s_id, "assignment_id": a2_id, "score": 90})  # 90%

    res = client.get(f"/students/{s_id}/average")
    assert res.status_code == 200
    data = res.get_json()
    assert data["student_id"] == s_id
    assert data["average_percent"] == 95.0


def test_student_average_not_found(client):
    res = client.get("/students/999/average")
    assert res.status_code == 404


def test_student_grades(client):
    a_res = client.post("/assignments", json={"title": "Quiz 1", "max_points": 10})
    a_id = a_res.get_json()["id"]
    s_res = client.post("/students", json={"name": "Alice", "email": "alice@example.com"})
    s_id = s_res.get_json()["id"]

    client.post("/grades", json={"student_id": s_id, "assignment_id": a_id, "score": 9})

    res = client.get(f"/students/{s_id}/grades")
    assert res.status_code == 200
    data = res.get_json()
    assert data["student_id"] == s_id
    assert len(data["grades"]) == 1
    assert data["grades"][0]["score"] == 9


def test_student_grades_not_found(client):
    res = client.get("/students/999/grades")
    assert res.status_code == 404


def test_assignment_grades(client):
    a_res = client.post("/assignments", json={"title": "Quiz 1", "max_points": 10})
    a_id = a_res.get_json()["id"]
    s1_res = client.post("/students", json={"name": "Alice", "email": "alice@example.com"})
    s1_id = s1_res.get_json()["id"]
    s2_res = client.post("/students", json={"name": "Bob", "email": "bob@example.com"})
    s2_id = s2_res.get_json()["id"]

    client.post("/grades", json={"student_id": s1_id, "assignment_id": a_id, "score": 9})
    client.post("/grades", json={"student_id": s2_id, "assignment_id": a_id, "score": 8})

    res = client.get(f"/assignments/{a_id}/grades")
    assert res.status_code == 200
    data = res.get_json()
    assert data["assignment_id"] == a_id
    assert len(data["grades"]) == 2


def test_assignment_grades_not_found(client):
    res = client.get("/assignments/999/grades")
    assert res.status_code == 404


def test_assignment_highest_score(client):
    a_res = client.post("/assignments", json={"title": "Quiz 1", "max_points": 10})
    a_id = a_res.get_json()["id"]
    s1_res = client.post("/students", json={"name": "Alice", "email": "alice@example.com"})
    s1_id = s1_res.get_json()["id"]
    s2_res = client.post("/students", json={"name": "Bob", "email": "bob@example.com"})
    s2_id = s2_res.get_json()["id"]

    client.post("/grades", json={"student_id": s1_id, "assignment_id": a_id, "score": 9})
    client.post("/grades", json={"student_id": s2_id, "assignment_id": a_id, "score": 10})

    res = client.get(f"/assignments/{a_id}/highest-score")
    assert res.status_code == 200
    data = res.get_json()
    assert data["assignment_id"] == a_id
    assert data["highest_score"] == 10


def test_assignment_highest_score_no_grades(client):
    a_res = client.post("/assignments", json={"title": "Quiz 1", "max_points": 10})
    a_id = a_res.get_json()["id"]

    res = client.get(f"/assignments/{a_id}/highest-score")
    assert res.status_code == 200
    assert res.get_json()["highest_score"] is None


def test_assignment_highest_score_not_found(client):
    res = client.get("/assignments/999/highest-score")
    assert res.status_code == 404


def test_assignment_top_scorer(client):
    a_res = client.post("/assignments", json={"title": "Quiz 1", "max_points": 10})
    a_id = a_res.get_json()["id"]
    s1_res = client.post("/students", json={"name": "Alice", "email": "alice@example.com"})
    s1_id = s1_res.get_json()["id"]
    s2_res = client.post("/students", json={"name": "Bob", "email": "bob@example.com"})
    s2_id = s2_res.get_json()["id"]

    client.post("/grades", json={"student_id": s1_id, "assignment_id": a_id, "score": 9})
    client.post("/grades", json={"student_id": s2_id, "assignment_id": a_id, "score": 10})

    res = client.get(f"/assignments/{a_id}/top-scorer")
    assert res.status_code == 200
    data = res.get_json()
    assert data["assignment_id"] == a_id
    assert data["top_scorer"]["name"] == "Bob"


def test_assignment_top_scorer_no_grades(client):
    a_res = client.post("/assignments", json={"title": "Quiz 1", "max_points": 10})
    a_id = a_res.get_json()["id"]

    res = client.get(f"/assignments/{a_id}/top-scorer")
    assert res.status_code == 200
    assert res.get_json()["top_scorer"] is None


def test_assignment_top_scorer_not_found(client):
    res = client.get("/assignments/999/top-scorer")
    assert res.status_code == 404


def test_class_average(client):
    a_res = client.post("/assignments", json={"title": "Quiz 1", "max_points": 10})
    a_id = a_res.get_json()["id"]
    s1_res = client.post("/students", json={"name": "Alice", "email": "alice@example.com"})
    s1_id = s1_res.get_json()["id"]
    s2_res = client.post("/students", json={"name": "Bob", "email": "bob@example.com"})
    s2_id = s2_res.get_json()["id"]

    client.post("/grades", json={"student_id": s1_id, "assignment_id": a_id, "score": 10})  # 100%
    client.post("/grades", json={"student_id": s2_id, "assignment_id": a_id, "score": 5})  # 50%

    res = client.get("/class-average")
    assert res.status_code == 200
    data = res.get_json()
    assert data["class_average_percent"] == 75.0


def test_class_average_no_grades(client):
    res = client.get("/class-average")
    assert res.status_code == 200
    assert res.get_json()["class_average_percent"] == 0.0


def test_stats(client):
    a_res = client.post("/assignments", json={"title": "Quiz 1", "max_points": 10})
    a_id = a_res.get_json()["id"]
    s_res = client.post("/students", json={"name": "Alice", "email": "alice@example.com"})
    s_id = s_res.get_json()["id"]

    client.post("/grades", json={"student_id": s_id, "assignment_id": a_id, "score": 9})

    res = client.get("/stats")
    assert res.status_code == 200
    data = res.get_json()
    assert data["total_students"] == 1
    assert data["total_assignments"] == 1
    assert data["total_grades"] == 1
    assert "class_average_percent" in data


def test_stats_empty(client):
    res = client.get("/stats")
    assert res.status_code == 200
    data = res.get_json()
    assert data["total_students"] == 0
    assert data["total_assignments"] == 0
    assert data["total_grades"] == 0


def test_top_students_above_threshold(client):
    a_res = client.post("/assignments", json={"title": "Quiz 1", "max_points": 10})
    a_id = a_res.get_json()["id"]
    s1_res = client.post("/students", json={"name": "Alice", "email": "alice@example.com"})
    s1_id = s1_res.get_json()["id"]
    s2_res = client.post("/students", json={"name": "Bob", "email": "bob@example.com"})
    s2_id = s2_res.get_json()["id"]

    client.post("/grades", json={"student_id": s1_id, "assignment_id": a_id, "score": 10})  # 100%
    client.post("/grades", json={"student_id": s2_id, "assignment_id": a_id, "score": 5})  # 50%

    res = client.get("/students/top/above-threshold/80.0")
    assert res.status_code == 200
    data = res.get_json()
    assert data["threshold"] == 80.0
    assert len(data["students"]) == 1
    assert data["students"][0]["name"] == "Alice"


def test_top_students_above_threshold_none(client):
    a_res = client.post("/assignments", json={"title": "Quiz 1", "max_points": 10})
    a_id = a_res.get_json()["id"]
    s_res = client.post("/students", json={"name": "Alice", "email": "alice@example.com"})
    s_id = s_res.get_json()["id"]

    client.post("/grades", json={"student_id": s_id, "assignment_id": a_id, "score": 5})  # 50%

    res = client.get("/students/top/above-threshold/90.0")
    assert res.status_code == 200
    data = res.get_json()
    assert len(data["students"]) == 0


def test_assignments_without_grades(client):
    client.post("/assignments", json={"title": "Quiz 1", "max_points": 10})
    a2_res = client.post("/assignments", json={"title": "HW 1", "max_points": 100})
    a2_id = a2_res.get_json()["id"]
    s_res = client.post("/students", json={"name": "Alice", "email": "alice@example.com"})
    s_id = s_res.get_json()["id"]

    client.post("/grades", json={"student_id": s_id, "assignment_id": a2_id, "score": 95})

    res = client.get("/assignments/without-grades")
    assert res.status_code == 200
    data = res.get_json()
    assert len(data["assignments"]) == 1
    assert data["assignments"][0]["title"] == "Quiz 1"


def test_assignments_without_grades_all_graded(client):
    a_res = client.post("/assignments", json={"title": "Quiz 1", "max_points": 10})
    a_id = a_res.get_json()["id"]
    s_res = client.post("/students", json={"name": "Alice", "email": "alice@example.com"})
    s_id = s_res.get_json()["id"]

    client.post("/grades", json={"student_id": s_id, "assignment_id": a_id, "score": 9})

    res = client.get("/assignments/without-grades")
    assert res.status_code == 200
    assert res.get_json()["assignments"] == []


def test_assignments_without_grades_empty(client):
    res = client.get("/assignments/without-grades")
    assert res.status_code == 200
    assert res.get_json()["assignments"] == []

