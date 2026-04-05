from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from src.config import BRIEFINGS, KST


def _clean(sections: list) -> list:
    """JSON 직렬화 불가 항목 제거"""
    result = []
    for s in sections:
        result.append({k: v for k, v in s.items() if k != "prompt_fn"})
    return result


def save(mode: str, sections: list) -> Path:
    now  = datetime.now(KST)
    date = now.strftime("%Y-%m-%d")
    out  = BRIEFINGS / now.strftime("%Y") / now.strftime("%m")
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{date}-{mode}.json"
    path.write_text(
        json.dumps({"date": date, "mode": mode, "generated_at": now.isoformat(),
                    "sections": _clean(sections)}, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"  저장: {path.relative_to(BRIEFINGS.parent)}")
    return path


def load(date: str, mode: str):
    y, m, _ = date.split("-")
    p = BRIEFINGS / y / m / f"{date}-{mode}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def list_dates(mode: str = "daily", limit: int = 30) -> list:
    files = sorted(BRIEFINGS.rglob(f"*-{mode}.json"), reverse=True)
    return [f.stem.replace(f"-{mode}", "") for f in files[:limit]]


def streak() -> int:
    dates = set(list_dates("daily", 60))
    today = datetime.now(KST).date()
    from datetime import timedelta
    s = 0
    for i in range(60):
        if (today - timedelta(days=i)).strftime("%Y-%m-%d") in dates:
            s += 1
        else:
            break
    return s
