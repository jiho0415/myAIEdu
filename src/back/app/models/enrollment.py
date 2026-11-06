from datetime import datetime

from sqlalchemy import ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.cohort import Cohort


class Enrollment(Base):
    __tablename__ = "enrollments"
    __table_args__ = (UniqueConstraint("user_id", "cohort_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    cohort_id: Mapped[int] = mapped_column(ForeignKey("cohorts.id"))
    status: Mapped[str] = mapped_column(String(20), default="applied")
    current_week: Mapped[int] = mapped_column(default=0)
    enrolled_at: Mapped[datetime] = mapped_column(server_default=func.now())
    cohort: Mapped[Cohort] = relationship(back_populates="enrollments")

    @property
    def is_canceled(self) -> bool:
        return self.status == "canceled"

    def reapply(self) -> None:
        """취소했던 신청을 다시 신청 상태로 되돌린다."""
        self.status, self.current_week = "applied", 0

    def cancel(self) -> None:
        self.status = "canceled"
