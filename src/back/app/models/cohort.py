from datetime import date

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Cohort(Base):
    __tablename__ = "cohorts"
    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))
    name: Mapped[str] = mapped_column(String(50))
    start_date: Mapped[date]
    capacity: Mapped[int]
    status: Mapped[str] = mapped_column(String(20), default="open")
    enrollments: Mapped[list["Enrollment"]] = relationship(back_populates="cohort")  # noqa: F821

    @property
    def is_open(self) -> bool:
        return self.status == "open"

    @property
    def seats_left(self) -> int:
        used = sum(1 for e in self.enrollments if e.status != "canceled")
        return max(self.capacity - used, 0)
