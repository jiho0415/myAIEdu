# myAIEdu 아키텍처 규칙 (필수 준수)

모든 코드는 아래 구조와 규칙을 따른다. 어긋나는 요청이 오면 먼저 이 규칙을 알리고 대안을 제시한다.

## 1. 최상위 구조
```
myAiEdu/
├─ src/back/    FastAPI 백엔드 (패키지명 `app`, 실행 위치 src/back)
└─ src/front/   정적 프론트엔드 (index.html, css/, js/)
```
- 백엔드/프론트 코드는 **반드시 `src/back`, `src/front` 아래에만** 둔다. 루트에 소스 파일(main.py, index.html 등)을 만들지 않는다.
- 백↔프론트는 **HTTP API(JSON)로만** 통신한다. 서로의 파일을 import/참조하지 않는다.
- API 계약의 단일 기준은 FastAPI `/openapi.json`이다. 응답 필드 변경 시 프론트(`js/api.js`, `js/app.js`)를 함께 수정한다.

## 2. 백엔드 계층 (src/back/app)
의존 방향은 **단방향**: `api → services → repositories → models`

| 계층 | 위치 | 책임 | 금지 |
|---|---|---|---|
| 라우터 | `api/routers/` | 요청 파싱, 서비스 호출, 응답 모델 반환 | 비즈니스 규칙, DB 쿼리 |
| 의존성 | `api/deps.py` | Session→Repository→Service 조립, 인증/권한 의존성 | 비즈니스 로직 |
| 서비스 | `services/` | 비즈니스 규칙, 트랜잭션(commit) 경계 | `fastapi`/HTTPException import, SQL 직접 작성 |
| 리포지토리 | `repositories/` | SQLAlchemy 쿼리만 | 비즈니스 판단, HTTP 개념 |
| 모델 | `models/` | ORM 엔티티, 엔티티 자체 규칙(메서드/프로퍼티) | 서비스·리포지토리 import |
| 스키마 | `schemas/` | 요청/응답 DTO (Pydantic) | DB 접근 |
| 코어 | `core/` | 설정, DB, 보안, 도메인 예외 | 상위 계층 import |

규칙:
- 하위 계층이 상위 계층을 import 하면 안 된다 (예: service가 router import 금지).
- 서비스는 HTTP를 모른다. 오류는 `core/exceptions.py`의 도메인 예외(`NotFoundError`, `ConflictError`, `BadRequestError`, `UnauthorizedError`, `ForbiddenError`)만 던지고, 변환은 `main.py` 핸들러가 한다.
- 모든 라우트에 `response_model`을 지정한다. ORM 객체를 그대로 반환하지 않는다.
- 새 기능 추가 순서: `models → schemas → repositories → services → api/routers → api/deps.py 연결 → main.py 라우터 등록 → tests`.
- 파일은 도메인별로 나눈다 (`user_*`, `course_*`, `enrollment_*`). 한 파일이 약 200줄을 넘으면 분할을 검토한다.
- 임포트는 `app.` 절대경로만 사용한다 (상대 임포트 금지).
- 설정값/비밀값은 `core/config.py`에서 환경변수로 읽는다. 코드·프론트에 하드코딩 금지 (개발용 기본값 제외).
- 인증/권한 검사는 `api/deps.py`의 의존성(`get_current_user`, `require_admin`)으로 처리한다.

## 3. 프론트엔드 (src/front)
- 구조: `index.html`, `css/`, `js/`. 빌드 도구 없이 정적 서빙(`python -m http.server 5500`)으로 동작해야 한다.
- 서버 통신은 `js/api.js`에만 둔다. 화면 로직(`js/app.js` 등)에서 `fetch`를 직접 호출하지 않는다.
- 화면이 커지면 `js/`를 `api/`, `pages/`, `components/`로 분할한다.
- `API_BASE`는 한 곳에서만 정의한다. 백엔드 CORS 허용 오리진(`CORS_ORIGINS`)과 맞춘다.
- 사용자 입력/서버 응답을 `innerHTML`에 넣을 때는 반드시 이스케이프한다 (XSS 방지).
- 토큰 등 민감정보를 콘솔/URL에 노출하지 않는다.

## 4. 코딩 컨벤션
- Python: 타입 힌트 필수, `str | None` 스타일, 함수는 작게(한 가지 책임), 한글 사용자 메시지는 서비스의 예외 메시지로만 정의.
- 네이밍: 파일/함수/변수 `snake_case`, 클래스 `PascalCase`, JS는 `camelCase`.
- 주석은 "왜"가 필요한 곳에만. 죽은 코드/주석 처리된 코드는 남기지 않는다.
- 새 의존성은 `src/back/requirements.txt`에 추가하고 추가 이유를 PR/커밋에 남긴다.

## 5. 테스트
- 위치: `src/back/tests/`. 실행: `cd src/back; .\.venv\Scripts\python.exe -m pytest -q`.
- API 변경/추가 시 테스트를 함께 작성한다. 서비스 규칙(정원, 중복 신청, 권한 등)은 정상/예외 케이스를 모두 검증한다.
- 테스트는 임시 DB(`DATABASE_URL` 환경변수)를 쓰고 운영/개발 DB(`myaiedu.db`)를 건드리지 않는다.
- 변경 완료 전 테스트 전체 통과를 확인한다.

## 6. 보안·운영 기본
- 비밀번호는 bcrypt 해시만 저장, 평문 로깅 금지.
- `ADMIN_PASSWORD`, `SECRET_KEY`는 운영 배포 전 반드시 환경변수로 교체.
- `.venv/`, `*.db`, `__pycache__/`는 커밋하지 않는다 (`.gitignore` 유지).

## 7. 체크리스트 (코드 작성/리뷰 시)
- [ ] 파일이 `src/back` 또는 `src/front` 안에 있는가
- [ ] 라우터에 비즈니스 로직/쿼리가 없는가
- [ ] 서비스에 `fastapi` import가 없는가
- [ ] 의존 방향이 단방향인가
- [ ] `response_model`과 테스트를 추가했는가
- [ ] 프론트 변경 시 `api.js` 경유로 통신하는가
