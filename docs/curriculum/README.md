# 직장인을 위한 8주 생성형 AI 커리큘럼: 학습 자료

4050 직장인 대상 8주 과정의 강의록, 실습 가이드, 예시 코드입니다.
현재 **7주차와 8주차**가 준비되어 있습니다.

| 주차 | 주제 | 강의록 | 실습 가이드 | 예시 코드 |
|---|---|---|---|---|
| 7 | 퍼스널 브랜딩 완성형 | [lecture.md](week07/lecture.md) | [practice-guide.md](week07/practice-guide.md) | `brand_kit.py`, `profile_page.html` |
| 8 | 나의 경험, AI를 만나 비즈니스가 되다 | [lecture.md](week08/lecture.md) | [practice-guide.md](week08/practice-guide.md) | `business_plan.py`, `offer_landing.html` |

## 폴더 구조

```
docs/curriculum/
├─ README.md
├─ requirements.txt          실습 코드용 의존성 (선택: 실제 AI 호출 시)
├─ common/ai_client.py       AI 호출 공통 모듈 (키가 없으면 연습 모드)
├─ week07/
│  ├─ lecture.md, practice-guide.md
│  └─ examples/  brand_kit.py, my_profile.json, profile_page.html
└─ week08/
   ├─ lecture.md, practice-guide.md
   └─ examples/  business_plan.py, my_ideas.json, offer_landing.html
```

이 자료는 수강생에게 나눠 주는 교육 콘텐츠이며, 서비스 코드(`src/back`, `src/front`)와 별개입니다. 서로 import하지 않습니다.

## 실습 코드 실행

```bash
# 연습 모드(키 없이)로 바로 실행
cd docs/curriculum/week07/examples && python brand_kit.py my_profile.json
cd docs/curriculum/week08/examples && python business_plan.py my_ideas.json

# 실제 AI로 실행 (선택)
pip install -r docs/curriculum/requirements.txt
# ANTHROPIC_API_KEY 환경변수를 설정한 뒤 위 명령을 다시 실행
```

| 환경변수 | 기본값 | 설명 |
|---|---|---|
| `ANTHROPIC_API_KEY` | (없음) | 실제 AI 호출용 키. 코드에 직접 적지 않는다 |
| `CLAUDE_MODEL` | `claude-opus-5-5` | 사용할 모델 |
| `AI_EFFORT` | `low` | 답변 깊이 (`low`/`medium`/`high`) |
| `MYAIEDU_MOCK` | (없음) | `1`이면 키가 있어도 연습 모드로 실행 |

생성 결과는 각 `examples/output/`에 저장되며 git에 올라가지 않습니다.

## 서비스 DB와의 차이

서비스 초기 데이터(`src/back/app/seed.py`)의 7·8주차 제목은 아직 "나만의 자동화 루틴 설계", "개인 프로젝트 발표"입니다. 이 자료의 주제명으로 바꾸려면 `seed.py`를 함께 수정해야 합니다.
