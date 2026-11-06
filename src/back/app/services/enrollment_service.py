from collections.abc import Sequence

from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.models import Enrollment, User
from app.repositories.course_repository import CourseRepository
from app.repositories.enrollment_repository import EnrollmentRepository

_NOT_FOUND = "신청 내역을 찾을 수 없습니다."


class EnrollmentService:
    def __init__(self, enrollments: EnrollmentRepository, courses: CourseRepository):
        self.enrollments = enrollments
        self.courses = courses

    def enroll(self, user: User, cohort_id: int) -> Enrollment:
        cohort = self.courses.get_cohort(cohort_id)
        if not cohort:
            raise NotFoundError("기수를 찾을 수 없습니다.")
        if not cohort.is_open:
            raise BadRequestError("모집 중인 기수가 아닙니다.")
        existing = self.enrollments.find(user.id, cohort.id)
        if existing and not existing.is_canceled:
            raise ConflictError("이미 신청한 기수입니다.")
        if cohort.seats_left <= 0:
            raise ConflictError("정원이 마감되었습니다.")
        if existing:  # 취소했던 신청을 재신청
            existing.reapply()
            enrollment = existing
        else:
            enrollment = self.enrollments.add(Enrollment(user_id=user.id, cohort_id=cohort.id))
        self.enrollments.commit()
        self.enrollments.refresh(enrollment)
        return enrollment

    def list_for_user(self, user: User) -> Sequence[Enrollment]:
        return self.enrollments.list_by_user(user.id)

    def cancel(self, user: User, enrollment_id: int) -> Enrollment:
        enrollment = self.enrollments.get(enrollment_id)
        # 본인 소유(또는 관리자)가 아니면 존재 여부를 노출하지 않도록 404
        if not enrollment or (enrollment.user_id != user.id and user.role != "admin"):
            raise NotFoundError(_NOT_FOUND)
        enrollment.cancel()
        self.enrollments.commit()
        return enrollment

    def set_progress(self, enrollment_id: int, current_week: int) -> Enrollment:
        enrollment = self.enrollments.get(enrollment_id)
        if not enrollment:
            raise NotFoundError(_NOT_FOUND)
        enrollment.current_week = current_week
        self.enrollments.commit()
        return enrollment
