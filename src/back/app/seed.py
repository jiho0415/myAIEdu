from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import ADMIN_EMAIL, ADMIN_PASSWORD
from app.core.security import hash_password
from app.models import Cohort, Course, Practice, User, Week

WEEKS = [
    (1, "basic", "AI와 친해지기", "생성형 AI가 무엇인지 알고, 첫 대화를 직접 해봅니다."),
    (2, "basic", "질문 잘하는 법 (프롬프트 기초)", "원하는 답을 얻는 요청문의 기본 공식을 익힙니다."),
    (3, "practice", "업무 보고서·공문서 초안 10분 완성", "내 실제 업무로 문서 초안을 만들고 다듬습니다."),
    (4, "practice", "이메일·회의록·제안서", "반복되는 업무 문서를 AI로 빠르게 처리합니다."),
    (5, "practice", "홍보 문구·SNS 콘텐츠", "가게·서비스 홍보용 글과 이미지 문구를 만듭니다."),
    (6, "practice", "홍보 콘텐츠 실전 제작", "블로그·카톡 채널용 콘텐츠를 한 세트로 완성합니다."),
    (7, "automation", "나만의 자동화 루틴 설계", "반복 업무를 AI 루틴으로 묶어 설계합니다."),
    (8, "automation", "개인 프로젝트 발표", "내 일에 적용한 결과를 발표하고 피드백을 받습니다."),
]


def seed(db: Session) -> None:
    if not db.scalar(select(Course).limit(1)):
        course = Course(title="4050 실전 AI 클래스 (8주)",
                        description="어렵지 않게 시작해서 당장 내 일에 쓰는 실용 AI 교육")
        for no, stage, title, summary in WEEKS:
            w = Week(week_no=no, stage=stage, title=title, summary=summary)
            if no == 3:
                w.practices.append(Practice(
                    title="보고서 초안 10분 완성", order_no=1,
                    steps=["내 실제 업무 소재 입력하기", "초안 생성 후 다듬기",
                           "나만의 프롬프트 템플릿으로 저장하기"]))
            course.weeks.append(w)
        db.add(course)
        db.flush()
        db.add_all([
            Cohort(course_id=course.id, name="2026년 12월 1기", start_date=date(2026, 12, 7), capacity=20),
            Cohort(course_id=course.id, name="2027년 1월 1기", start_date=date(2027, 1, 11), capacity=20),
        ])
    if not db.scalar(select(User).where(User.email == ADMIN_EMAIL)):
        db.add(User(email=ADMIN_EMAIL, password_hash=hash_password(ADMIN_PASSWORD),
                    name="관리자", role="admin"))
    db.commit()
