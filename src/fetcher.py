"""src/fetcher.py — Claude API + 웹검색으로 각 섹션 수집"""
from __future__ import annotations
import anthropic
from src.config import ANTHROPIC_API_KEY

SYSTEM_PROMPT = """텔레그램 브리핑 봇. 반드시 지켜야 할 규칙:

금지: 마크다운 테이블, ##헤딩, ---, > 인용, 서두, 맺음말, 사과, 면책, "검색하겠습니다", "정리합니다" 등 메타 발언
필수: 사용자가 지정한 포맷을 정확히 따를 것. 한 항목당 1줄. 데이터 없으면 생략.
볼드: **텍스트** 형태만 사용.
핵심만 초축약. 장황하면 실패."""

# 단순 정보 조회는 haiku, 분석·종합은 sonnet
SECTION_MODELS = {
    "weather":    "claude-haiku-4-5-20251001",
}
DEFAULT_MODEL = "claude-sonnet-4-6"

# 웹검색이 불필요한 섹션 (이전 섹션 종합)
NO_SEARCH_SECTIONS = {"daily_insight"}

# 섹션별 웹검색 최대 횟수
SEARCH_MAX_USES = {
    "weather": 1,
    "ai": 2,
    "industry": 5,
    "stocks": 2,
    "realestate": 2,
    "toss": 3,
    "daily_insight": 0,
}


def fetch_section(client: anthropic.Anthropic, section: dict, profile: dict) -> dict:
    prompt = section["prompt_fn"](profile)
    model = SECTION_MODELS.get(section["id"], DEFAULT_MODEL)
    max_uses = SEARCH_MAX_USES.get(section["id"], 2)

    tools = []
    if section["id"] not in NO_SEARCH_SECTIONS:
        tool = {"type": "web_search_20250305", "name": "web_search", "max_uses": max_uses}
        tools.append(tool)

    try:
        kwargs = {
            "model": model,
            "max_tokens": 800,
            "system": SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": prompt}],
        }
        if tools:
            kwargs["tools"] = tools

        resp = client.messages.create(**kwargs)
        text = "\n".join(b.text for b in resp.content if hasattr(b, "text")).strip()

        usage = resp.usage
        print(f"[{model.split('-')[1][:3]} in:{usage.input_tokens} out:{usage.output_tokens}]", end=" ")

        return {**section, "content": text or "(내용 없음)", "ok": True}
    except Exception as e:
        return {**section, "content": f"수집 오류: {e}", "ok": False}


def fetch_all(sections: list, profile: dict) -> list:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    results = []
    for sec in sections:
        print(f"  {sec['emoji']} {sec['title']} ...", end=" ", flush=True)
        result = fetch_section(client, sec, profile)
        print("✓" if result["ok"] else "✗")
        results.append(result)
    return results
