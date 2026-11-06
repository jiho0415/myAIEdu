from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, get_enrollment_service, require_admin
from app.models import User
from app.schemas.enrollment import EnrollIn, EnrollmentOut, ProgressIn
from app.services.enrollment_service import EnrollmentService

router = APIRouter(prefix="/enrollments", tags=["enrollments"])


@router.post("", status_code=201, response_model=EnrollmentOut)
def enroll(body: EnrollIn, user: User = Depends(get_current_user),
           svc: EnrollmentService = Depends(get_enrollment_service)):
    return EnrollmentOut.from_entity(svc.enroll(user, body.cohort_id))


@router.get("/me", response_model=list[EnrollmentOut])
def my_enrollments(user: User = Depends(get_current_user),
                   svc: EnrollmentService = Depends(get_enrollment_service)):
    return [EnrollmentOut.from_entity(e) for e in svc.list_for_user(user)]


@router.patch("/{enrollment_id}/cancel", response_model=EnrollmentOut)
def cancel(enrollment_id: int, user: User = Depends(get_current_user),
           svc: EnrollmentService = Depends(get_enrollment_service)):
    return EnrollmentOut.from_entity(svc.cancel(user, enrollment_id))


@router.patch("/{enrollment_id}/progress", response_model=EnrollmentOut)
def progress(enrollment_id: int, body: ProgressIn, _: User = Depends(require_admin),
             svc: EnrollmentService = Depends(get_enrollment_service)):
    return EnrollmentOut.from_entity(svc.set_progress(enrollment_id, body.current_week))
