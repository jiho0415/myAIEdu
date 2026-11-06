from collections.abc import Sequence

from app.core.exceptions import NotFoundError
from app.models import Cohort, Course, Week
from app.repositories.course_repository import CourseRepository


class CourseService:
    def __init__(self, courses: CourseRepository):
        self.courses = courses

    def list_courses(self) -> Sequence[Course]:
        return self.courses.list_courses()

    def get_course(self, course_id: int) -> Course:
        course = self.courses.get_course(course_id)
        if not course:
            raise NotFoundError("과정을 찾을 수 없습니다.")
        return course

    def get_week(self, course_id: int, week_no: int) -> Week:
        week = self.courses.get_week(course_id, week_no)
        if not week:
            raise NotFoundError("주차를 찾을 수 없습니다.")
        return week

    def list_cohorts(self, status: str | None = None) -> Sequence[Cohort]:
        return self.courses.list_cohorts(status)
