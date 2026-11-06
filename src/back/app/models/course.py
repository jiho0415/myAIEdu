from sqlalchemy import JSON, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Course(Base):
    __tablename__ = "courses"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)
    total_weeks: Mapped[int] = mapped_column(default=8)
    weeks: Mapped[list["Week"]] = relationship(order_by="Week.week_no", back_populates="course")


class Week(Base):
    __tablename__ = "weeks"
    __table_args__ = (UniqueConstraint("course_id", "week_no"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))
    week_no: Mapped[int]
    stage: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(100))
    summary: Mapped[str] = mapped_column(Text)
    course: Mapped[Course] = relationship(back_populates="weeks")
    practices: Mapped[list["Practice"]] = relationship(order_by="Practice.order_no")


class Practice(Base):
    __tablename__ = "practices"
    id: Mapped[int] = mapped_column(primary_key=True)
    week_id: Mapped[int] = mapped_column(ForeignKey("weeks.id"))
    title: Mapped[str] = mapped_column(String(100))
    steps: Mapped[list] = mapped_column(JSON)
    order_no: Mapped[int] = mapped_column(default=1)
