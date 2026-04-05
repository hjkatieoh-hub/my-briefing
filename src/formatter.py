"""src/formatter.py — 텔레그램 메시지 포맷터 (HTML 모드)"""
from datetime import datetime
from src.config import KST
from src.storage import streak, list_dates

DAYS_KO = ["월", "화", "수", "목", "금", "토", "일"]

def _date_str(dt: datetime) -> str:
    return f"{dt.month}월 {dt.day}일 {DAYS_KO[dt.weekday()]}요일"

def _esc(text: str) -> str:
    """HTML 특수문자 이스케이프"""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def _sec(emoji: str, title: str, content: str) -> str:
    lines = []
    for line in content.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        # 번호 목록
        import re
        if re.match(r"^\d+[.。]", line):
            line = re.sub(r"^(\d+[.。])\s*", r"\1 ", line)
        # 볼드 변환 **text**
        line = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", line)
        lines.append(_esc(line).replace("&lt;b&gt;", "<b>").replace("&lt;/b&gt;", "</b>"))
    body = "\n".join(lines)
    return f"\n<b>{emoji} {title}</b>\n{body}"

def format_daily(sections: list[dict]) -> str:
    now  = datetime.now(KST)
    s    = streak()
    days = len(list_dates("daily", 9999))
    head = (
        f"<b>📋 데일리 브리핑</b>  {_date_str(now)}\n"
        f"<i>연속 {s}일 · 총 {days}일 발행 · 오전 5:00</i>"
    )
    divider = "\n─────────────────"
    body = divider.join(_sec(sec["emoji"], sec["title"], sec["content"]) for sec in sections)
    foot = f"\n─────────────────\n📊 <a href='https://your-username.github.io/my-briefing/'>전체 분석 대시보드</a>"
    return head + divider + body + foot


def format_weekly(sections: list[dict]) -> str:
    now  = datetime.now(KST)
    head = (
        f"<b>📊 위클리 리포트</b>  {now.month}월 {now.day}일 주차\n"
        f"<i>매주 월요일 오전 5:05 발송</i>"
    )
    divider = "\n─────────────────"
    body = divider.join(_sec(sec["emoji"], sec["title"], sec["content"]) for sec in sections)
    foot = f"\n─────────────────\n📊 <a href='https://your-username.github.io/my-briefing/'>심층 분석 대시보드</a>"
    return head + divider + body + foot


def split_messages(text: str, limit: int = 4000) -> list[str]:
    """4096자 텔레그램 제한에 맞게 분할"""
    if len(text) <= limit:
        return [text]
    parts, buf = [], ""
    for block in text.split("\n─────────────────"):
        chunk = "\n─────────────────" + block if buf else block
        if len(buf) + len(chunk) > limit:
            if buf:
                parts.append(buf)
            buf = chunk
        else:
            buf += chunk
    if buf:
        parts.append(buf)
    return parts or [text[:limit]]
