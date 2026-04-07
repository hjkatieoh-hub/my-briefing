"""src/fetcher.py — Claude API + 웹검색으로 각 섹션 수집"""
from __future__ import annotations
import anthropic
from src.config import ANTHROPIC_API_KEY

SYSTEM_PROMPT = """당신은 한국어 브리핑 봇입니다. 텔레그램으로 발송되는 메시지를 작성합니다.

규칙:
- 마크다운 테이블(| |) 사용 금지. 대신 "항목: 값" 형태로
- ##, ### 등 헤딩 대신 볼드(**텍스트**)만 사용
- --- 구분선 사용 금지
- > 인용문 사용 금지
- 서두/맺음말 없이 바로 본론
- 짧고 핵심만. 한 항목당 1~2줄 이내"""

# 단순 정보 조회는 haiku, 분석·종합은 sonnet
SECTION_MODELS = {
    "weather":    "claude-haiku-4-5-20251001",
    "ai":         "claude-haiku-4-5-20251001",
    "industry":   "claude-haiku-4-5-20251001",
}
DEFAULT_MODEL = "claude-sonnet-4-6"

# 웹검색이 불필요한 섹션 (이전 섹션 종합)
NO_SEARCH_SECTIONS = {"daily_insight"}

# 섹션별 웹검색 최대 횟수
SEARCH_MAX_USES = {
    "weather": 1,
    "ai": 2,
    "industry": 2,
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
            "max_tokens": 1500,
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
