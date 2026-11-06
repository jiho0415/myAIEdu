"""실습 공통 AI 호출 모듈.

수강생 PC에 API 키가 없어도 수업이 멈추지 않도록, 키나 SDK가 없으면
'연습 모드'(미리 준비한 예시 답변)로 자동 전환한다.
"""

import os
import sys

MODEL = os.environ.get("CLAUDE_MODEL", "claude-opus-5-5")
# 실습 과제는 대부분 짧은 문서 작업이라 기본 노력 수준을 낮춰 비용과 대기 시간을 줄인다.
EFFORT = os.environ.get("AI_EFFORT", "low")
MOCK_ENV = "MYAIEDU_MOCK"


def is_mock_mode() -> bool:
    if os.environ.get(MOCK_ENV) == "1":
        return True
    try:
        import anthropic  # noqa: F401
    except ImportError:
        return True
    return False


def ask(prompt: str, system: str | None = None, mock_answer: str | None = None) -> str:
    """AI에게 한 번 묻고 답변 텍스트를 돌려준다."""
    if is_mock_mode():
        return _mock(prompt, mock_answer)
    try:
        return _call_claude(prompt, system)
    except Exception as exc:  # 수업 중 네트워크/인증 오류로 실습이 끊기지 않게 연습 모드로 넘긴다
        print(f"[알림] AI 호출 실패({type(exc).__name__}). 연습 모드 답변으로 대신합니다.", file=sys.stderr)
        return _mock(prompt, mock_answer)


def _call_claude(prompt: str, system: str | None) -> str:
    import anthropic

    client = anthropic.Anthropic()
    params: dict = {
        "model": MODEL,
        "max_tokens": 16000,
        "thinking": {"type": "adaptive"},
        "output_config": {"effort": EFFORT},
        "messages": [{"role": "user", "content": prompt}],
        # 안전 분류기가 요청을 거절하면 서버가 권장 모델로 자동 재시도한다.
        "betas": ["server-side-fallback-2026-07-01"],
        "fallbacks": "default",
    }
    if system:
        params["system"] = system
    response = client.beta.messages.create(**params)
    if response.stop_reason == "refusal":
        return "(AI가 이 요청에는 답하지 않았습니다. 질문을 바꿔 다시 시도해 보세요.)"
    return "".join(block.text for block in response.content if block.type == "text").strip()


def _mock(prompt: str, mock_answer: str | None) -> str:
    if mock_answer:
        return f"[연습 모드]\n{mock_answer}"
    preview = prompt.strip().splitlines()[0][:60] if prompt.strip() else ""
    return f"[연습 모드] 실제 AI 대신 예시 답변입니다. 받은 요청 첫 줄: \"{preview}\""
