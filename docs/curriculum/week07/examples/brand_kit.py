"""7주차 실습: 경험 인벤토리(JSON)로 퍼스널 브랜드 키트를 만든다.

실행: python brand_kit.py my_profile.json
결과: output/ 폴더에 프롬프트, 브랜드 키트, 사실 검증 리포트가 저장된다.
"""

import json
import re
import sys
from pathlib import Path

# 주차 폴더마다 공통 모듈을 복사하지 않도록 curriculum/common 경로를 추가한다.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "common"))
from ai_client import ask, is_mock_mode  # noqa: E402

REQUIRED_FIELDS = ("name", "career_years", "role", "target", "problem", "experiences")
# 광고 표현으로 문제 될 수 있고 근거 확인이 어려운 최상급 표현
RISKY_WORDS = ("최고", "유일", "최초", "1위", "독보적", "완벽", "보장")

SYSTEM_PROMPT = (
    "너는 4050 직장인의 퍼스널 브랜딩을 돕는 카피라이터다. "
    "사용자가 준 사실만 사용하고, 경력·자격·수치를 절대 지어내지 않는다."
)


def load_profile(path: Path) -> dict:
    profile = json.loads(path.read_text(encoding="utf-8"))
    missing = [field for field in REQUIRED_FIELDS if not profile.get(field)]
    if missing:
        raise ValueError(f"프로필에 빠진 항목이 있습니다: {', '.join(missing)}")
    return profile


def positioning_statement(profile: dict) -> str:
    return (f"나는 {profile['target']}이(가) {profile['problem']} 문제를 "
            f"{profile['career_years']}년 {profile.get('field', '')} 경험으로 해결하도록 돕는 {profile['role']}다.")


def build_prompt(profile: dict) -> str:
    experiences = "\n".join(
        f"- 경험: {e['experience']} / 증거: {e['evidence']} / 필요한 사람: {e['audience']}"
        for e in profile["experiences"]
    )
    tone = ", ".join(profile.get("tone", ["신뢰감 있는", "따뜻한", "구체적인"]))
    banned = ", ".join(profile.get("banned_words", []) + list(RISKY_WORDS))
    return f"""아래 정보로 나의 퍼스널 브랜드 키트를 만들어 줘.

[기본 정보]
- 이름(호칭): {profile['name']}
- 경력: {profile.get('field', '')} 분야 {profile['career_years']}년
- 되고 싶은 역할: {profile['role']}
- 돕고 싶은 대상: {profile['target']}
- 대상이 겪는 문제: {profile['problem']}

[경험 인벤토리]
{experiences}

[작성 항목] 마크다운 제목(##)으로 구분해서 작성
1. 포지셔닝 문장: "나는 [대상]이 [문제]를 [경험]으로 [결과]하도록 돕는 [역할]이다." 형식 1개
2. 한 줄 소개: 30자 이내, 3안
3. 30초 자기소개: 150자 내외
4. 1분 자기소개: 300자 내외, 경험 인벤토리의 숫자 1개 이상 포함
5. 온라인 프로필: 헤드라인 1줄 + 소개 500자 이내
6. 콘텐츠 주제 기둥 3개: 기둥마다 첫 글 제목 5개
7. 톤앤매너: 형용사 3개와 쓰지 않을 표현 3개

[제약]
- 말투: {tone}
- 다음 표현은 쓰지 않는다: {banned}
- 위에 없는 경력, 자격증, 수치, 회사명은 만들지 않는다.
- 확인이 필요한 내용은 문장 끝에 (확인 필요)라고 표시한다.
"""


def build_offline_kit(profile: dict) -> str:
    """API 없이도 수업을 진행할 수 있도록 템플릿으로 기본 키트를 만든다."""
    first = profile["experiences"][0]
    topics = [e["experience"] for e in profile["experiences"][:3]]
    pillars = "\n".join(
        f"- **{topic}**: 「{topic}, 처음 시작할 때 꼭 알아야 할 3가지」 외 4편" for topic in topics
    )
    return f"""## 1. 포지셔닝 문장
{positioning_statement(profile)}

## 2. 한 줄 소개
- {profile['target']}의 든든한 {profile['role']}
- {profile['career_years']}년 현장 경험을 나누는 {profile['role']}
- "{profile['problem']}", 같이 풀어 드립니다

## 3. 30초 자기소개
안녕하세요, {profile['name']}입니다. {profile.get('field', '')} 분야에서 {profile['career_years']}년 일했습니다.
{first['experience']} 경험({first['evidence']})을 바탕으로, 지금은 {profile['target']}이(가) {profile['problem']} 문제를 풀도록 돕고 있습니다.

## 4. 1분 자기소개
(연습 모드: 3번 소개에 실패하거나 배운 경험 1개, 앞으로 하고 싶은 일 1개를 덧붙여 직접 완성해 보세요.)

## 5. 온라인 프로필
- 헤드라인: {profile['role']} | {profile['target']}의 "{profile['problem']}" 해결 | {profile.get('field', '')} {profile['career_years']}년
- 소개: (연습 모드: 3번 소개를 바탕으로 500자 이내로 늘려 보세요.)

## 6. 콘텐츠 주제 기둥
{pillars}

## 7. 톤앤매너
- 형용사: {', '.join(profile.get('tone', ['신뢰감 있는', '따뜻한', '구체적인']))}
- 쓰지 않을 표현: {', '.join(RISKY_WORDS[:3])}
"""


def strip_tone_section(kit: str) -> str:
    """톤앤매너 절은 '쓰지 않을 표현'을 일부러 나열하므로 점검 대상에서 뺀다."""
    return re.sub(r"##[^\n]*톤앤매너.*?(?=\n## |\Z)", "", kit, flags=re.S)


def fact_check(kit: str, profile: dict, prompt: str = "") -> list[str]:
    """생성 결과에서 사람이 꼭 다시 확인해야 할 부분을 찾는다."""
    warnings: list[str] = []
    kit = strip_tone_section(kit)
    # 프롬프트의 분량 지시(30자, 500자 등)에서 온 숫자는 지어낸 사실이 아니다.
    source_text = json.dumps(profile, ensure_ascii=False) + prompt
    for word in RISKY_WORDS + tuple(profile.get("banned_words", [])):
        if word in kit:
            warnings.append(f"근거 확인이 어려운 표현 '{word}'이(가) 있습니다. 지우거나 근거를 붙이세요.")
    # 프로필에 없는 숫자는 AI가 지어냈을 가능성이 있다.
    for number in sorted(set(re.findall(r"\d+(?:[.,]\d+)?", kit))):
        if number not in source_text and len(number) >= 2:
            warnings.append(f"프로필에 없는 숫자 '{number}'이(가) 있습니다. 사실인지 확인하세요.")
    if "(확인 필요)" in kit:
        warnings.append("AI가 '(확인 필요)'로 표시한 문장이 있습니다. 직접 확인 후 표시를 지우세요.")
    return warnings


def write_outputs(out_dir: Path, prompt: str, kit: str, warnings: list[str]) -> None:
    out_dir.mkdir(exist_ok=True)
    (out_dir / "brand_kit_prompt.txt").write_text(prompt, encoding="utf-8")
    (out_dir / "brand_kit.md").write_text(f"# 나의 브랜드 키트\n\n{kit}\n", encoding="utf-8")
    report = "\n".join(f"- [ ] {w}" for w in warnings) or "- 자동 점검에서 걸린 항목이 없습니다. 그래도 한 번 더 읽어 보세요."
    (out_dir / "fact_check.md").write_text(f"# 사실 검증 체크리스트\n\n{report}\n", encoding="utf-8")


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("사용법: python brand_kit.py <프로필 JSON 경로>")
        return 1
    try:
        profile = load_profile(Path(argv[1]))
    except (OSError, ValueError) as exc:
        print(f"프로필을 읽지 못했습니다: {exc}")
        return 1

    prompt = build_prompt(profile)
    offline_kit = build_offline_kit(profile)
    kit = offline_kit if is_mock_mode() else ask(prompt, system=SYSTEM_PROMPT, mock_answer=offline_kit)
    warnings = fact_check(kit, profile, prompt)

    out_dir = Path(__file__).resolve().parent / "output"
    write_outputs(out_dir, prompt, kit, warnings)
    print(f"브랜드 키트를 만들었습니다: {out_dir / 'brand_kit.md'}")
    print(f"확인할 항목 {len(warnings)}개: {out_dir / 'fact_check.md'}")
    if is_mock_mode():
        print("연습 모드로 실행했습니다. brand_kit_prompt.txt를 웹 AI에 붙여 넣으면 같은 결과를 받을 수 있습니다.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
