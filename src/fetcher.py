"""src/fetcher.py — Claude API + 웹검색으로 각 섹션 수집"""
from __future__ import annotations
import anthropic
from src.config import ANTHROPIC_API_KEY

SYSTEM_PROMPT = """텔레그램 브리핑 봇. 반드시 지켜야 할 규칙:

금지: 마크다운 테이블, ##헤딩, ---, > 인용, 서두, 맺음말, 사과, 면책, "검색하겠습니다", "정리합니다" 등 메타 발언
필수: 사용자가 지정한 포맷을 정확히 따를 것. 한 항목당 1줄. 데이터 없으면 생략.
볼드: **텍스트** 형태만 사용.
핵심만 초축약. 장황하면 실패."""

SECTION_MODELS = {
    "weather":    "claude-haiku-4-5-20251001",
}
DEFAULT_MODEL = "claude-sonnet-4-6"

NO_SEARCH_SECTIONS = {"daily_insight"}

SEARCH_MAX_USES = {
    "weather": 1,
    "ai": 2,
    "industry_ai": 3,
    "stocks": 2,
    "realestate": 2,
    "toss": 3,
    "daily_insight": 0,
}

# 합쳐서 1회 호출할 섹션 그룹
MERGE_GROUPS = {
    "industry_ai": ["industry", "ai"],
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


def fetch_merged(client: anthropic.Anthropic, sections: list[dict], profile: dict) -> list[dict]:
    """여러 섹션을 하나의 API 호출로 합쳐서 수집"""
    group_id = None
    for gid, sids in MERGE_GROUPS.items():
        if [s["id"] for s in sections] == sids:
            group_id = gid
            break

    prompts = []
    for sec in sections:
        prompts.append(f"[{sec['emoji']} {sec['title']}]\n{sec['prompt_fn'](profile)}")
    combined_prompt = "아래 섹션들을 각각 답해줘. 섹션 구분은 === 로 해.\n\n" + "\n\n===\n\n".join(prompts)

    model = DEFAULT_MODEL
    max_uses = SEARCH_MAX_USES.get(group_id, 3)

    try:
        resp = client.messages.create(
            model=model,
            max_tokens=1200,
            system=SYSTEM_PROMPT,
            tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": max_uses}],
            messages=[{"role": "user", "content": combined_prompt}],
        )
        text = "\n".join(b.text for b in resp.content if hasattr(b, "text")).strip()

        usage = resp.usage
        sec_names = "+".join(s["title"] for s in sections)
        print(f"[{model.split('-')[1][:3]} in:{usage.input_tokens} out:{usage.output_tokens}]", end=" ")

        # === 로 분할
        parts = [p.strip() for p in text.split("===") if p.strip()]
        results = []
        for i, sec in enumerate(sections):
            content = parts[i] if i < len(parts) else "(내용 없음)"
            results.append({**sec, "content": content, "ok": True})
        return results
    except Exception as e:
        return [{**sec, "content": f"수집 오류: {e}", "ok": False} for sec in sections]


def fetch_all(sections: list, profile: dict) -> list:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    results = []
    skip_ids = set()

    # 먼저 merge 그룹 처리
    for group_id, member_ids in MERGE_GROUPS.items():
        group_sections = [s for s in sections if s["id"] in member_ids]
        if len(group_sections) == len(member_ids):
            names = " + ".join(s["emoji"] + " " + s["title"] for s in group_sections)
            print(f"  {names} ...", end=" ", flush=True)
            merged = fetch_merged(client, group_sections, profile)
            print("✓" if all(r["ok"] for r in merged) else "✗")
            results.extend(merged)
            skip_ids.update(member_ids)

    # 나머지 개별 처리
    for sec in sections:
        if sec["id"] in skip_ids:
            continue
        print(f"  {sec['emoji']} {sec['title']} ...", end=" ", flush=True)
        result = fetch_section(client, sec, profile)
        print("✓" if result["ok"] else "✗")
        results.append(result)

    # 원래 섹션 순서로 정렬
    order = {s["id"]: i for i, s in enumerate(sections)}
    results.sort(key=lambda r: order.get(r["id"], 99))
    return results
