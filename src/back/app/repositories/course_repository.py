from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Cohort, Course, Week


class CourseRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_courses(self) -> Sequence[Course]:
        return self.db.scalars(select(Course)).all()

    def get_course(self, course_id: int) -> Course | None:
        return self.db.get(Course, course_id)

    def get_week(self, course_id: int, week_no: int) -> Week | None:
        return self.db.scalar(
            select(Week).where(Week.course_id == course_id, Week.week_no == week_no))

    def list_cohorts(self, status: str | None = None) -> Sequence[Cohort]:
        q = select(Cohort).order_by(Cohort.start_date)
        if status:
            q = q.where(Cohort.status == status)
        return self.db.scalars(q).all()

    def get_cohort(self, cohort_id: int) -> Cohort | None:
        return self.db.get(Cohort, cohort_id)
