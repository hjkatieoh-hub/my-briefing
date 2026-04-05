"""src/fetcher.py — Claude API + 웹검색으로 각 섹션 수집"""
from __future__ import annotations
import anthropic
from src.config import ANTHROPIC_API_KEY


def fetch_section(client: anthropic.Anthropic, section: dict, profile: dict) -> dict:
    prompt = section["prompt_fn"](profile)
    try:
        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
            messages=[{"role": "user", "content": prompt}],
        )
        text = "\n".join(b.text for b in resp.content if hasattr(b, "text")).strip()
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
