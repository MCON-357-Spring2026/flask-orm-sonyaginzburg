"""Exercises: ORM fundamentals.


Implement the TODO functions. Autograder will test them.
"""


from __future__ import annotations


from typing import Optional
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func


from src.exercises.extensions import db
from src.exercises.models import Student, Grade, Assignment




# ===== BASIC CRUD =====


def create_student(name: str, email: str) -> Student:
    """ Create and commit a Student; handle duplicate email.
    If email is duplicate:
      - rollback
      - raise ValueError("duplicate email")
    """
    # instantiate new student ORM object
    student = Student(name = name, email=email)
    # this will stage the object, include in next commit
    db.session.add(student)
    try:
        # actual commit, writes staged changes to database permanently
        db.session.commit()
    except IntegrityError:
        # email has unique constraint so if rejected we must rollback
        db.session.rollback()
        raise ValueError("duplicate email")


    return student






def find_student_by_email(email: str) -> Optional[Student]:
    """ Return Student by email or None."""
    # filter_by() generates WHERE email = :email
    # .first() returns the first match, or None if no rows found
    return Student.query.filter_by(email=email).first()




def add_grade(student_id: int, assignment_id: int, score: int) -> Grade:
    """TODO: Add a Grade for the student+assignment and commit.


    If student doesn't exist: raise LookupError
    If assignment doesn't exist: raise LookupError
    If duplicate grade: raise ValueError("duplicate grade")
    """
    # .get() looks up a row by primary key if not found return None
    if not Student.query.get(student_id):
        raise LookupError


    if not Assignment.query.get(assignment_id):
        raise LookupError


    # Grade object
    grade = Grade(student_id=student_id, assignment_id=assignment_id, score=score)
    db.session.add(grade)


    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ValueError("duplicate grade")


    return grade




def average_percent(student_id: int) -> float:
    """ Return student's average percent across assignments.


    percent per grade = score / assignment.max_points * 100


    If student doesn't exist: raise LookupError
    If student has no grades: return 0.0
    Ai helped with this one
    """
    if not Student.query.get(student_id):
        raise LookupError


    # get all grades of student
    grades = Grade.query.filter_by(student_id=student_id).all()


    if not grades:
        return 0.0
    # computing the percentage of each grade
    percents = [
        g.score / Assignment.query.get(g.assignment_id).max_points * 100
        for g in grades
    ]
    # return the mean of all individual percentages
    return sum(percents) / len(percents)








# ===== QUERYING & FILTERING =====


def get_all_students() -> list[Student]:
    """ Return all students in database, ordered by name."""
    return Student.query.order_by(Student.name).all()




def get_assignment_by_title(title: str) -> Optional[Assignment]:
    """ Return assignment by title or None."""
    return Assignment.query.filter_by(title=title).first()




def get_student_grades(student_id: int) -> list[Grade]:
    """ Return all grades for a student, ordered by assignment title.


    If student doesn't exist: raise LookupError
    """
    if not Student.query.get(student_id):
        raise LookupError
    return (
        Grade.query.join(Assignment).filter(Grade.student_id == student_id).order_by(Assignment.title).all()
        # Notes:
        # JOIN Grade to Assignment so we can reference Assignment columns
        # WHERE student_id = :student_id
        # ORDER BY the joined table's title column
    )




def get_grades_for_assignment(assignment_id: int) -> list[Grade]:
    """ Return all grades for an assignment, ordered by student name.


    If assignment doesn't exist: raise LookupError
    """
    if not Assignment.query.get(assignment_id):
        raise LookupError
    return (
        Grade.query.join(Student).filter(Grade.assignment_id == assignment_id).order_by(Student.name).all()
    )




# ===== AGGREGATION =====


def total_student_grade_count() -> int:
    """ Return total number of grades in database."""
    # .count() is same as SELECT COUNT(*)
    return Grade.query.count()




def highest_score_on_assignment(assignment_id: int) -> Optional[int]:
    """ Return the highest score on an assignment, or None if no grades.


    If assignment doesn't exist: raise LookupError
    """
    if not Assignment.query.get(assignment_id):
        raise LookupError


    # Notes:
    # func.max() maps to SQL MAX() — an aggregate that scans all matching rows
    # .scalar() executes the query and returns the single value directly (or None if no rows)
    return (
        db.session.query(func.max(Grade.score))
        .filter_by(assignment_id=assignment_id)
        .scalar()
    )




def class_average_percent() -> float:
    """ Return average percent across all students and all assignments.


    percent per grade = score / assignment.max_points * 100
    Return average of all these percents.
    If no grades: return 0.0
    """
    grades = Grade.query.all()


    if not grades:
        return 0.0


    # compute individual percent and then  the average of all together
    percents = [
        g.score / Assignment.query.get(g.assignment_id).max_points * 100
        for g in grades
    ]
    return sum(percents)/ len(percents)




def student_grade_count(student_id: int) -> int:
    """ Return number of grades for a student.


    If student doesn't exist: raise LookupError
    """
    if not Student.query.get(student_id):
        raise LookupError
    return Grade.query.filter_by(student_id=student_id).count()




# ===== UPDATING & DELETION =====


def update_student_email(student_id: int, new_email: str) -> Student:
    """Update a student's email and commit.


    If student doesn't exist: raise LookupError
    If new email is duplicate: rollback and raise ValueError("duplicate email")
    Return the updated student.
    """
    student = Student.query.get(student_id)
    if not student:
        raise LookupError
    student.email = new_email


    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ValueError("duplicate email")


    return student




def delete_student(student_id: int) -> None:
    """ Delete a student and all their grades; commit.


    If student doesn't exist: raise LookupError
    """
    student = Student.query.get(student_id)
    if not student:
        raise LookupError


    # Notes:
    # Delete all of this student's grades first.
    # If we deleted the student first, any remaining Grade rows would have a dangling foreign key (student_id pointing to nothing), which the DB would reject.
    Grade.query.filter_by(student_id=student_id).delete()


    # Now safe to remove the parent row
    db.session.delete(student)
    db.session.commit()


def delete_grade(grade_id: int) -> None:
    """ Delete a grade by id; commit.


    If grade doesn't exist: raise LookupError
    """
    grade = Grade.query.get(grade_id)
    if not grade:
        raise LookupError


    db.session.delete(grade)
    db.session.commit()




# ===== FILTERING & FILTERING WITH AGGREGATION =====
#remember: WHERE vs HAVING —
# WHERE filters rows before grouping,
# HAVING filters after
# aggregates ex AVG() only exist after grouping, so they need HAVING


def students_with_average_above(threshold: float) -> list[Student]:
    """ Return students whose average percent is above threshold.
    (used AI help here)
    List should be ordered by average percent descending.
    percent per grade = score / assignment.max_points * 100
    """
    avg_expr = func.avg(Grade.score * 100.0 / Assignment.max_points)


    results = (
        db.session.query(Student, avg_expr)
        # JOIN Student → Grade → Assignment to reach all three tables
        .join(Grade, Grade.student_id == Student.id)
        .join(Assignment, Assignment.id == Grade.assignment_id)
        # GROUP BY collapses all of a student's rows into one,
        # so the aggregate (avg_expr) runs across each student's grades
        .group_by(Student.id)
        # HAVING filters on the aggregated value you can't use WHERE here
        # because WHERE runs before grouping and can't see AVG() results
        .having(avg_expr > threshold)
        # Sort highest average first
        .order_by(avg_expr.desc())
        .all()
    )
    # only returning Student objects
    return [row[0] for row in results]




def assignments_without_grades() -> list[Assignment]:
    """ Return assignments that have no grades yet, ordered by title."""
    return (
        Assignment.query.outerjoin(Grade).filter(Grade.id == None).order_by(Assignment.title).all()
    )
# LEFT OUTER JOIN keeps every Assignment row, even those with no matching Grade.
# After a left join, assignments with no grades will have NULL for Grade columns.
# Filtering for NULL grade ids isolates exactly those ungraded assignments.




def top_scorer_on_assignment(assignment_id: int) -> Optional[Student]:
    """ Return the Student with the highest score on an assignment.


    If assignment doesn't exist: raise LookupError
    If no grades on assignment: return None
    If tie (multiple students with same high score): return any one
    """
    if not Assignment.query.get(assignment_id):
        raise LookupError


    return (
        db.session.query(Student)
        # Join Student through Grade, scoped to just this assignment
        .join(Grade, Grade.student_id == Student.id)
        .filter(Grade.assignment_id == assignment_id)
        # Sort highest score to the top, then grab the first row
        .order_by(Grade.score.desc())
        # Returns None automatically if no grades exist for this assignment
        .first()
    )




