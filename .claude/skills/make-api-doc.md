---
name: make-api-doc
description: 백엔드 FastAPI 라우터·스키마·서비스를 분석해 docs/api.md API 문서를 생성/갱신한다. 코드는 수정하지 않는다.
---

# make-api-doc: API 문서 자동 생성

`src/back/app`의 코드를 근거로 `docs/api.md`를 생성한다. **쓰기 대상은 `docs/api.md` 하나뿐**이며 소스 코드는 수정하지 않는다. 코드에서 확인되지 않는 내용은 추측하지 말고 `확인 필요`로 표기한다.

## 1. 분석 절차

### 1-1. 라우터 등록 확인 (`src/back/app/main.py`)
- `include_router`로 등록된 모듈 목록을 확인한다. (현재: `auth`, `courses`, `enrollments`)
- `main.py`에 직접 선언된 라우트(`@app.get(...)`, 예: `/health`)도 엔드포인트로 포함한다.
- `@app.exception_handler`에서 에러 응답 형식을 확인한다. (현재: `{"detail": "<메시지>"}`, 상태 코드는 `exc.status_code`)
- 등록되지 않은 라우터 파일은 문서에서 제외하고 문서 끝에 "미등록 라우터"로 적는다.

### 1-2. 엔드포인트 수집 (`src/back/app/api/routers/*.py`)
각 파일에서 다음을 추출한다. (Grep 패턴: `@router\.(get|post|put|patch|delete)`)

| 항목 | 추출 위치 | 비고 |
|---|---|---|
| 메서드 | 데코레이터 이름 | 대문자로 표기 |
| 경로 | `APIRouter(prefix=...)` + 데코레이터 인자 | prefix가 없는 라우터는 데코레이터 경로가 전체 경로 (예: `auth.py`, `courses.py`). prefix가 있으면 합친다 (예: `/enrollments` + `/me`). 빈 문자열 `""`은 prefix 자체 |
| 성공 상태 코드 | `status_code=` | 없으면 200 |
| 응답 스키마 | `response_model=` | `list[X]`는 "X 배열"로 표기 |
| 태그(도메인) | `APIRouter(tags=[...])` | 섹션 분류에 사용 |
| 경로 파라미터 | 경로의 `{name}` + 함수 인자 타입 | |
| 쿼리 파라미터 | 경로에 없고 Pydantic 모델도 아닌 단순 타입 인자 (`status: str \| None = None`) | 기본값이 있으면 선택 |
| 요청 본문 | Pydantic 모델 타입 인자 (`body: XxxIn`) | 스키마 파일에서 필드 조회 |
| 설명 | 함수 docstring, 없으면 함수명과 서비스 호출로 한 줄 요약 | |

### 1-3. 인증 수준 분류 (`src/back/app/api/deps.py`)
엔드포인트 함수 인자의 `Depends(...)`로 판정한다.

| Depends | 인증 수준 | 문서 표기 |
|---|---|---|
| 없음 (`get_*_service`만) | 공개 | `공개` |
| `get_current_user` | 로그인 필요 | `로그인 (Bearer)` |
| `require_admin` | 관리자 전용 | `관리자 (Bearer)` |

`deps.py`에서 헤더 형식(`Authorization: Bearer <token>`)과 실패 시 예외를 확인해 "공통 사항"에 반영한다.

### 1-4. 스키마 필드 정리 (`src/back/app/schemas/*.py`)
- 요청/응답에 쓰인 클래스만 조회한다. 중첩 모델(예: `TokenOut.user: UserOut`)은 재귀적으로 펼치거나 별도 표로 링크한다.
- 필드마다: 이름, 타입(`str | None`은 "string, null 허용"), 필수 여부(기본값 없으면 필수), 제약(`Field(min_length/max_length/pattern/ge/le)` 등. 정규식 `pattern`은 원문 그대로 적는다), 설명.
- 같은 스키마가 여러 엔드포인트에 쓰이면 "스키마" 절에 한 번만 정의하고 엔드포인트에서는 이름으로 참조한다.

### 1-5. 에러 코드 수집 (`core/exceptions.py` + `services/*.py`)
1. `core/exceptions.py`에서 `AppError` 하위 클래스와 `status_code`를 읽는다. (현재: Bad 400, Unauthorized 401, Forbidden 403, NotFound 404, Conflict 409)
2. 엔드포인트가 호출하는 서비스 메서드를 따라가 `raise XxxError("메시지")`를 모두 수집한다.
   - 서비스가 호출하는 다른 서비스 메서드(`ensure_admin`, `authenticate` 등)의 `raise`도 포함한다.
   - 메시지는 코드에 적힌 한글 원문 그대로 옮긴다. 변수가 섞인 f-string이면 `{변수}`를 그대로 둔다.
   - 메시지가 모듈 상수(예: `enrollment_service.py`의 `_NOT_FOUND`)이면 같은 파일에서 상수 값을 찾아 원문으로 치환한다.
3. `Depends`에서 발생하는 예외도 해당 엔드포인트의 에러로 포함한다. (`get_current_user` → 401 "로그인이 필요합니다.", `require_admin` → 403)
4. 요청 본문/파라미터가 있는 엔드포인트에는 FastAPI 자동 검증 오류 **422**를 추가한다. (`detail`이 배열 형식임을 공통 사항에 설명)
5. 서비스를 따라가도 근거를 찾지 못한 코드는 쓰지 않는다.

### 1-6. openapi 대조 (선택)
- `http://localhost:8000/openapi.json`에 접속 가능하면 (`WebFetch` 또는 `curl`) 경로·메서드 목록을 코드 분석 결과와 비교한다. 서버가 없으면 이 단계를 건너뛰고 문서 상단에 "코드 기준 (openapi 대조 안 함)"이라고 적는다.
- 불일치 항목은 문서 끝 "확인 필요"에 나열한다.
- 서버를 직접 실행하지는 않는다.

## 2. 출력 템플릿 (`docs/api.md`)

아래 양식을 그대로 따른다. `<...>`는 분석 결과로 채우고, 해당 없는 항목은 `-`로 둔다. `docs/` 폴더가 없으면 만든다.

````markdown
# myAIEdu API 문서

> 생성일: <YYYY-MM-DD> · 기준: <코드 분석 | 코드 분석 + openapi 대조>
> 자동 생성 문서입니다. 수정은 코드에서 하고 `/make-api-doc`으로 다시 생성하세요.

## 공통 사항

| 항목 | 내용 |
|---|---|
| Base URL | `http://localhost:8000` (개발) |
| 데이터 형식 | JSON (`Content-Type: application/json`) |
| 인증 | `Authorization: Bearer <access_token>` |
| 에러 응답 | `{"detail": "<메시지>"}` |
| 검증 오류 (422) | `{"detail": [{"loc": [...], "msg": "...", "type": "..."}]}` |

### 에러 코드

| 코드 | 의미 | 도메인 예외 |
|---|---|---|
| 400 | 잘못된 요청 | `BadRequestError` |
| 401 | 인증 필요/실패 | `UnauthorizedError` |
| 403 | 권한 없음 | `ForbiddenError` |
| 404 | 대상 없음 | `NotFoundError` |
| 409 | 충돌(중복 등) | `ConflictError` |
| 422 | 요청 형식 검증 실패 (FastAPI 자동) | - |

## 엔드포인트 요약

| 메서드 | 경로 | 인증 | 설명 |
|---|---|---|---|
| <METHOD> | `<경로>` | <공개/로그인/관리자> | <한 줄 설명> |

## <도메인명: 태그 기준, 예: auth>

### <METHOD> `<경로>`

<한 줄 설명>

- **인증**: <공개 | 로그인 (Bearer) | 관리자 (Bearer)>
- **성공 응답**: <상태 코드> · <스키마명 | 스키마명 배열>

**경로 파라미터**

| 이름 | 타입 | 설명 |
|---|---|---|
| <name> | integer | <설명> |

**쿼리 파라미터**

| 이름 | 타입 | 필수 | 설명 |
|---|---|---|---|
| <name> | string | 아니오 | <설명> |

**요청 본문** (`<InSchemaName>`)

| 필드 | 타입 | 필수 | 제약/설명 |
|---|---|---|---|
| <field> | string | 예 | <제약> |

**응답 본문** (`<OutSchemaName>`)

| 필드 | 타입 | 설명 |
|---|---|---|
| <field> | integer | <설명> |

**에러**

| 코드 | 조건 | 메시지 |
|---|---|---|
| 401 | 토큰 없음/만료 | 로그인이 필요합니다. |

**예시**

```http
<METHOD> <경로> HTTP/1.1
Authorization: Bearer <token>
Content-Type: application/json

{ <요청 JSON 예시> }
```

```json
{ <응답 JSON 예시> }
```

(엔드포인트마다 위 블록을 반복한다. 해당 없는 소절(경로/쿼리 파라미터, 요청 본문 등)은 통째로 생략한다.)

## 스키마

### <SchemaName>

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| <field> | <type> | <예/아니오> | <설명> |

## 확인 필요

- <코드에서 근거를 찾지 못했거나 openapi와 불일치하는 항목. 없으면 "없음">
````

## 3. 작성 규칙
- 엔드포인트 순서는 라우터 등록 순서 → 파일 내 선언 순서를 따른다.
- 예시 JSON의 값은 스키마 타입에 맞는 현실적인 샘플을 쓴다. 실제 토큰·비밀번호·운영 데이터는 쓰지 않는다. (`"access_token": "<jwt>"` 형태)
- 문서의 설명 문장은 한국어로 쓴다.
- 기존 `docs/api.md`가 있으면 덮어쓰기 전에 읽고, 사람이 손으로 추가한 절(템플릿에 없는 제목)이 있으면 문서 끝 "추가 메모"로 보존한다.

## 4. 완료 보고
작업을 마치면 다음만 짧게 보고한다.
- 생성/갱신한 `docs/api.md` 경로
- 엔드포인트 수 (도메인별)
- "확인 필요" 항목 수와 핵심 내용
- 코드는 수정하지 않았다는 확인
