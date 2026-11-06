from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Enrollment


class EnrollmentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, enrollment_id: int) -> Enrollment | None:
        return self.db.get(Enrollment, enrollment_id)

    def find(self, user_id: int, cohort_id: int) -> Enrollment | None:
        return self.db.scalar(select(Enrollment).where(
            Enrollment.user_id == user_id, Enrollment.cohort_id == cohort_id))

    def list_by_user(self, user_id: int) -> Sequence[Enrollment]:
        return self.db.scalars(select(Enrollment).where(Enrollment.user_id == user_id)
                               .order_by(Enrollment.id.desc())).all()

    def add(self, enrollment: Enrollment) -> Enrollment:
        self.db.add(enrollment)
        return enrollment

    def commit(self) -> None:
        self.db.commit()

    def refresh(self, enrollment: Enrollment) -> None:
        self.db.refresh(enrollment)
