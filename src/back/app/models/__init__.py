"""모든 모델을 import 해서 Base.metadata에 테이블을 등록한다."""
from app.models.cohort import Cohort
from app.models.course import Course, Practice, Week
from app.models.enrollment import Enrollment
from app.models.user import User

__all__ = ["Cohort", "Course", "Enrollment", "Practice", "User", "Week"]
