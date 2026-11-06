from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models import Enrollment


class EnrollIn(BaseModel):
    cohort_id: int


class ProgressIn(BaseModel):
    current_week: int = Field(ge=0, le=8)


class EnrollmentOut(BaseModel):
    id: int
    cohort_id: int
    cohort_name: str
    start_date: date
    status: str
    current_week: int
    enrolled_at: datetime

    @classmethod
    def from_entity(cls, e: Enrollment) -> "EnrollmentOut":
        return cls(id=e.id, cohort_id=e.cohort.id, cohort_name=e.cohort.name,
                   start_date=e.cohort.start_date, status=e.status,
                   current_week=e.current_week, enrolled_at=e.enrolled_at)
