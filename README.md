# myAIEdu

4050 AI 교육 서비스 MVP. FastAPI 백엔드 + 정적 프론트엔드.

## 로컬 실행 (PowerShell, 터미널 2개)

**터미널 1 - 백엔드 (http://localhost:8000, API 문서 /docs)**
```
cd src/back
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

**터미널 2 - 프론트엔드 (http://localhost:5500)**
```
cd src/front
python -m http.server 5500
```

첫 실행 시 SQLite(`src/back/myaiedu.db`)가 만들어지고 8주 커리큘럼과 기수 2개가 자동 입력됩니다.

## 테스트
```
cd src/back
.\.venv\Scripts\python.exe -m pytest -q
```

## 개발용 관리자 계정
`admin@myaiedu.local` / `admin1234` (진행 주차 갱신 API용). 운영 전 `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `SECRET_KEY` 환경변수로 반드시 교체하세요.

## 구조
- `src/back/app/` 계층형(클린) 구조 — 의존 방향: `api → services → repositories → models`
  - `api/routers/` HTTP 라우터(얇게), `api/deps.py` 의존성 조립·인증
  - `services/` 비즈니스 규칙(정원·중복신청·권한), HTTP 비의존, 도메인 예외(`core/exceptions.py`)만 발생
  - `repositories/` DB 접근(SQLAlchemy 쿼리)
  - `models/` ORM 엔티티, `schemas/` 요청·응답 DTO, `core/` 설정·DB·보안, `seed.py`
- `src/front/` index.html, css, js(api.js 호출, app.js 화면)
