from fastapi import APIRouter, Depends

from app.api.deps import get_course_service
from app.schemas.course import CohortOut, CourseDetailOut, CourseSummaryOut, WeekOut
from app.services.course_service import CourseService

router = APIRouter(tags=["courses"])


@router.get("/courses", response_model=list[CourseSummaryOut])
def list_courses(svc: CourseService = Depends(get_course_service)):
    return svc.list_courses()


@router.get("/courses/{course_id}", response_model=CourseDetailOut)
def get_course(course_id: int, svc: CourseService = Depends(get_course_service)):
    return svc.get_course(course_id)


@router.get("/courses/{course_id}/weeks/{week_no}", response_model=WeekOut)
def get_week(course_id: int, week_no: int, svc: CourseService = Depends(get_course_service)):
    return svc.get_week(course_id, week_no)


@router.get("/cohorts", response_model=list[CohortOut])
def list_cohorts(status: str | None = None, svc: CourseService = Depends(get_course_service)):
    return svc.list_cohorts(status)
