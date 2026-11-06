"""의존성 조립(Composition Root): Session → Repository → Service → 현재 사용자."""
from collections.abc import Iterator

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.exceptions import UnauthorizedError
from app.models import User
from app.repositories.course_repository import CourseRepository
from app.repositories.enrollment_repository import EnrollmentRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.course_service import CourseService
from app.services.enrollment_service import EnrollmentService


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(UserRepository(db))


def get_course_service(db: Session = Depends(get_db)) -> CourseService:
    return CourseService(CourseRepository(db))


def get_enrollment_service(db: Session = Depends(get_db)) -> EnrollmentService:
    return EnrollmentService(EnrollmentRepository(db), CourseRepository(db))


def get_current_user(
    authorization: str | None = Header(default=None),
    auth: AuthService = Depends(get_auth_service),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedError("로그인이 필요합니다.")
    return auth.authenticate(authorization[7:])


def require_admin(user: User = Depends(get_current_user)) -> User:
    return AuthService.ensure_admin(user)
