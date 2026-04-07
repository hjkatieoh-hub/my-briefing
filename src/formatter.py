"""src/formatter.py — 텔레그램 메시지 포맷터 (HTML 모드)"""
import re
from datetime import datetime
from src.config import KST
from src.storage import streak, list_dates

DAYS_KO = ["월", "화", "수", "목", "금", "토", "일"]


def _esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _clean(content: str) -> str:
    """Claude 응답을 텔레그램 HTML로 변환"""
    lines = content.strip().split("\n")
    out = []
    for line in lines:
        s = line.strip()
        if not s:
            out.append("")
            continue
        # 메타 발언/면책 제거
        if re.match(r"^(검색|정리|종합|확인|수집|죄송|⚠️|※|데이터를|아래는|위 포맷|다만|정확한 정보|추가 검색|참고로).*", s):
            continue
        if re.search(r"(직접 조회|확인 권장|확인하시|권장합니다|주의.*표기|검색 결과에서 확인 불가)", s):
            continue
        # --- 구분선 제거
        if re.match(r"^-{3,}$", s):
            continue
        # ## 헤딩 → 볼드
        if s.startswith("#"):
            s = re.sub(r"^#+\s*", "", s)
        # 테이블 구분선 스킵
        if re.match(r"^\|[\s\-:]+\|", s):
            continue
        # 테이블 행 → bullet
        if s.startswith("|") and s.endswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|") if c.strip()]
            s = " · ".join(cells)
        # **bold** → <b>
        s = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", s)
        # HTML 이스케이프 (태그 보존)
        parts = re.split(r"(</?b>)", s)
        s = "".join(_esc(p) if p not in ("<b>", "</b>") else p for p in parts)
        out.append(s)

    result = "\n".join(out)
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip()


def _sec(emoji: str, title: str, content: str) -> str:
    body = _clean(content)
    return f"<b>{emoji} {title}</b>\n{body}"


def format_daily(sections: list[dict]) -> str:
    now = datetime.now(KST)
    s = streak()
    days = len(list_dates("daily", 9999))
    dow = DAYS_KO[now.weekday()]
    head = (
        f"<b>📋 데일리 브리핑</b> | {now.month}/{now.day} {dow}\n"
        f"연속 {s}일 · 총 {days}일"
    )
    divider = "\n\n"
    body = divider.join(_sec(sec["emoji"], sec["title"], sec["content"]) for sec in sections)
    foot = f"\n\n<a href='https://hjkatieoh-hub.github.io/my-briefing/'>📊 대시보드</a>"
    return head + "\n\n" + body + foot


def format_weekly(sections: list[dict]) -> str:
    now = datetime.now(KST)
    head = (
        f"<b>📊 위클리 리포트</b> | {now.month}월 {now.day}일 주차"
    )
    divider = "\n\n"
    body = divider.join(_sec(sec["emoji"], sec["title"], sec["content"]) for sec in sections)
    foot = f"\n\n<a href='https://hjkatieoh-hub.github.io/my-briefing/'>📊 대시보드</a>"
    return head + "\n\n" + body + foot


def split_messages(text: str, limit: int = 4000) -> list[str]:
    if len(text) <= limit:
        return [text]
    # 섹션 단위로 분할 (빈 줄 2개 = 섹션 구분)
    blocks = re.split(r"\n\n(?=<b>)", text)
    parts, buf = [], ""
    for block in blocks:
        chunk = ("\n\n" + block) if buf else block
        if len(buf) + len(chunk) > limit:
            if buf:
                parts.append(buf)
            buf = block
        else:
            buf += chunk
    if buf:
        parts.append(buf)
    return parts or [text[:limit]]
