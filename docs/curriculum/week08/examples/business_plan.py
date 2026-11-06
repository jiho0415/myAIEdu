"""8주차 실습: 아이디어 후보를 점수화하고, 1등 아이디어로 기획서·인터뷰 질문·발표 대본을 만든다.

실행: python business_plan.py my_ideas.json
결과: output/ 폴더에 점수표, 가격 계산, 프롬프트, 기획서가 저장된다.
"""

import json
import math
import sys
from pathlib import Path

# 주차 폴더마다 공통 모듈을 복사하지 않도록 curriculum/common 경로를 추가한다.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "common"))
from ai_client import ask, is_mock_mode  # noqa: E402

# 강의록 5장의 기준과 같다. 수업에서 수강생이 직접 바꿔 보며 토론하는 값이다.
WEIGHTS = {
    "experience_fit": 0.30,
    "willingness_to_pay": 0.25,
    "ease_of_start": 0.20,
    "time_available": 0.15,
    "ai_leverage": 0.10,
}
CRITERIA_LABELS = {
    "experience_fit": "경험 적합도",
    "willingness_to_pay": "고객 지불 의사",
    "ease_of_start": "시작 용이성",
    "time_available": "시간 여건",
    "ai_leverage": "AI 활용도",
}

SYSTEM_PROMPT = (
    "너는 4050 직장인의 작은 부업·1인 비즈니스 기획을 돕는 코치다. "
    "사용자가 준 경험만 근거로 쓰고, 수익을 약속하거나 보장하는 표현은 쓰지 않는다. "
    "세무·법률 판단이 필요한 부분은 전문가 확인이 필요하다고만 안내한다."
)


def load_plan(path: Path) -> dict:
    plan = json.loads(path.read_text(encoding="utf-8"))
    for key in ("profile", "ideas", "pricing"):
        if key not in plan:
            raise ValueError(f"'{key}' 항목이 없습니다.")
    if not plan["ideas"]:
        raise ValueError("아이디어를 1개 이상 적어 주세요.")
    for idea in plan["ideas"]:
        for criterion in WEIGHTS:
            score = idea.get("scores", {}).get(criterion)
            if not isinstance(score, int) or not 1 <= score <= 5:
                raise ValueError(f"'{idea.get('title', '?')}'의 {CRITERIA_LABELS[criterion]} 점수는 1~5 정수여야 합니다.")
    return plan


def score_idea(scores: dict[str, int]) -> float:
    """가중 평균을 100점 만점으로 바꾼다."""
    weighted = sum(scores[c] * w for c, w in WEIGHTS.items())
    return round(weighted / 5 * 100, 1)


def rank_ideas(ideas: list[dict]) -> list[dict]:
    ranked = [{**idea, "total": score_idea(idea["scores"])} for idea in ideas]
    # 동점이면 고객 지불 의사가 높은 쪽을 먼저 둔다. (강의록 강사 노트 기준)
    return sorted(ranked, key=lambda i: (i["total"], i["scores"]["willingness_to_pay"]), reverse=True)


def calc_price(monthly_goal: int, monthly_hours: int, prep_hours: float, session_hours: float) -> dict[str, int]:
    if monthly_goal <= 0 or monthly_hours <= 0:
        raise ValueError("월 목표 수입과 월 투입 시간은 0보다 커야 합니다.")
    hourly = monthly_goal / monthly_hours
    # 고객에게 보여 줄 가격이므로 천 원 단위로 올림한다.
    price = math.ceil(hourly * (prep_hours + session_hours) / 1000) * 1000
    sessions_needed = math.ceil(monthly_goal / price)
    return {"hourly": round(hourly), "price": price, "sessions_needed": sessions_needed}


def format_score_table(ranked: list[dict]) -> str:
    header = "| 순위 | 아이디어 | " + " | ".join(CRITERIA_LABELS.values()) + " | 총점 |"
    divider = "|---" * (len(CRITERIA_LABELS) + 3) + "|"
    rows = [
        f"| {rank} | {idea['title']} | "
        + " | ".join(str(idea["scores"][c]) for c in WEIGHTS)
        + f" | **{idea['total']}** |"
        for rank, idea in enumerate(ranked, start=1)
    ]
    return "\n".join([header, divider, *rows])


def build_prompt(profile: dict, idea: dict, price: dict[str, int]) -> str:
    return f"""아래 정보로 작은 비즈니스 준비 자료를 만들어 줘.

[나의 브랜드]
- 포지셔닝: {profile['positioning']}
- 핵심 경험: {', '.join(profile['experiences'])}

[선택한 아이디어]
- 오퍼: {idea['title']}
- 대상 고객: {idea['customer']}
- 고객의 문제: {idea['problem']}
- 첫 가격: 1회 {price['price']:,}원 (시간당 목표 {price['hourly']:,}원 기준)

[작성 항목] 마크다운 제목(##)으로 구분
1. 1장 기획서: 고객 / 문제 / 해결책 / 차별점(내 경험) / 가격(무료·저가·본상품 3단) / 알리는 방법 3가지 / 30일 실행 계획(주별)
2. 고객 인터뷰 질문 7개: "쓰시겠어요?", "얼마면 사시겠어요?" 같은 가정형 질문은 빼고, 과거 행동을 묻는 질문으로
3. 사전 신청 랜딩페이지 문구: 제목, 부제, 이런 분께 필요해요(3개), 진행 방식, 신청 버튼 문구
4. 3분 발표 대본: 0:30 자기소개 / 0:45 문제 / 1:00 오퍼·가격·시연 / 0:30 30일 계획 / 0:15 받고 싶은 도움

[제약]
- 수익을 약속하거나 보장하는 표현은 쓰지 않는다.
- 위에 없는 경력·수치·후기는 만들지 않는다. 필요한 곳은 [직접 입력]으로 비워 둔다.
"""


def build_offline_plan(profile: dict, idea: dict, price: dict[str, int]) -> str:
    """API 없이도 수업을 진행할 수 있도록 템플릿으로 기본 자료를 만든다."""
    return f"""## 1. 1장 기획서
| 항목 | 내용 |
|---|---|
| 고객 | {idea['customer']} |
| 문제 | {idea['problem']} |
| 해결책 | {idea['title']} |
| 차별점 | {', '.join(profile['experiences'])} |
| 가격 | 무료: 체크리스트 / 저가: 소그룹 워크숍 [직접 입력] / 본상품: 1회 {price['price']:,}원 |
| 알리는 방법 | 카톡 프로필 링크, 블로그 첫 글, 지인 30명 직접 공유 |
| 30일 계획 | 1주 랜딩 공개 → 2주 인터뷰 5명 → 3주 무료 1회 → 4주 첫 유료 시도 |

## 2. 고객 인터뷰 질문
1. 최근에 "{idea['problem']}" 문제가 생겼던 때를 이야기해 주세요.
2. 그때 어떻게 해결하셨어요?
3. 그 방법에서 가장 불편했던 점은 무엇이었나요?
4. 이 문제에 지금 돈이나 시간을 얼마나 쓰고 계세요?
5. 이 문제를 해결하려고 찾아본 서비스나 사람이 있나요?
6. 그걸 쓰지 않은(또는 그만둔) 이유는 무엇인가요?
7. 이 문제로 고민하는 분을 한 명 더 소개해 주실 수 있을까요?

## 3. 랜딩페이지 문구
- 제목: {idea['title']}
- 부제: {idea['customer']}을(를) 위한 실전 도움
- 이런 분께 필요해요: [직접 입력 3개]
- 신청 버튼: 사전 신청하기

## 4. 3분 발표 대본
(연습 모드: 강의록 7장의 발표 구조에 맞춰 직접 작성해 보세요. 첫 문장은 포지셔닝 문장으로 시작합니다.)
"{profile['positioning']}"
"""


def write_outputs(out_dir: Path, score_table: str, price: dict[str, int], prompt: str, plan_text: str) -> None:
    out_dir.mkdir(exist_ok=True)
    (out_dir / "idea_scores.md").write_text(f"# 아이디어 점수표\n\n{score_table}\n", encoding="utf-8")
    (out_dir / "pricing.md").write_text(
        "# 첫 가격 계산\n\n"
        f"- 시간당 목표 단가: {price['hourly']:,}원\n"
        f"- 1회 가격: {price['price']:,}원\n"
        f"- 월 목표까지 필요한 판매 횟수: {price['sessions_needed']}회\n",
        encoding="utf-8",
    )
    (out_dir / "business_prompt.txt").write_text(prompt, encoding="utf-8")
    (out_dir / "business_plan.md").write_text(f"# 나의 작은 비즈니스 기획\n\n{plan_text}\n", encoding="utf-8")


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("사용법: python business_plan.py <아이디어 JSON 경로>")
        return 1
    try:
        plan = load_plan(Path(argv[1]))
        pricing = plan["pricing"]
        price = calc_price(pricing["monthly_goal"], pricing["monthly_hours"],
                           pricing["prep_hours"], pricing["session_hours"])
    except (OSError, ValueError, KeyError) as exc:
        print(f"입력 파일을 확인해 주세요: {exc}")
        return 1

    ranked = rank_ideas(plan["ideas"])
    best = ranked[0]
    prompt = build_prompt(plan["profile"], best, price)
    offline_plan = build_offline_plan(plan["profile"], best, price)
    plan_text = offline_plan if is_mock_mode() else ask(prompt, system=SYSTEM_PROMPT, mock_answer=offline_plan)

    out_dir = Path(__file__).resolve().parent / "output"
    write_outputs(out_dir, format_score_table(ranked), price, prompt, plan_text)

    print(f"1등 아이디어: {best['title']} ({best['total']}점)")
    print(f"첫 가격: 1회 {price['price']:,}원 · 월 목표까지 {price['sessions_needed']}회")
    print(f"결과 폴더: {out_dir}")
    if is_mock_mode():
        print("연습 모드로 실행했습니다. business_prompt.txt를 웹 AI에 붙여 넣으면 같은 결과를 받을 수 있습니다.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
