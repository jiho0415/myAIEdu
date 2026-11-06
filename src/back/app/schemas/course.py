from datetime import date

from pydantic import BaseModel, ConfigDict


class PracticeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    title: str
    steps: list


class WeekOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    week_no: int
    stage: str
    title: str
    summary: str
    practices: list[PracticeOut]


class CourseSummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    description: str
    total_weeks: int


class CourseDetailOut(CourseSummaryOut):
    weeks: list[WeekOut]


class CohortOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    course_id: int
    name: str
    start_date: date
    capacity: int
    seats_left: int
    status: str
