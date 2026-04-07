"""src/formatter.py — 텔레그램 메시지 포맷터 (HTML 모드)"""
import re
from datetime import datetime
from src.config import KST
from src.storage import streak, list_dates

DAYS_KO = ["월", "화", "수", "목", "금", "토", "일"]

def _date_str(dt: datetime) -> str:
    return f"{dt.month}월 {dt.day}일 {DAYS_KO[dt.weekday()]}요일"

def _esc(text: str) -> str:
    """HTML 특수문자 이스케이프"""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

# Claude 응답에 자주 섞이는 메타/서두 패턴
_META_PATTERNS = [
    r"^검색 결과를? .*",
    r"^.*데이터를? .*정리.*",
    r"^.*충분한 정보.*",
    r"^.*답변드립니다.*",
    r"^.*기반으로 정리.*",
    r"^.*구성합니다.*",
    r"^.*추가 검색.*",
    r"^.*진행합니다.*",
    r"^⚠️ \*상세 수치는.*",
]

def _clean(content: str) -> str:
    """마크다운 → 텔레그램 HTML 변환 및 정리"""
    lines = content.strip().split("\n")
    out = []
    in_table = False
    table_rows = []

    for line in lines:
        stripped = line.strip()

        # 빈 줄
        if not stripped:
            if in_table and table_rows:
                out.extend(_format_table(table_rows))
                table_rows = []
                in_table = False
            out.append("")
            continue

        # 메타/서두 제거
        if any(re.match(p, stripped) for p in _META_PATTERNS):
            continue

        # --- 구분선 제거
        if re.match(r"^-{3,}$", stripped):
            continue

        # 테이블 구분선 (|---|---|)
        if re.match(r"^\|[\s\-:]+\|", stripped):
            in_table = True
            continue

        # 테이블 행
        if stripped.startswith("|") and stripped.endswith("|"):
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            table_rows.append(cells)
            in_table = True
            continue

        # 테이블 끝
        if in_table and table_rows:
            out.extend(_format_table(table_rows))
            table_rows = []
            in_table = False

        # ## / ### 헤딩 → 볼드
        if stripped.startswith("#"):
            heading = re.sub(r"^#+\s*", "", stripped)
            heading = _convert_bold(heading)
            out.append(f"\n<b>{_esc_keep_tags(heading)}</b>")
            continue

        # > 인용문
        if stripped.startswith(">"):
            quote = stripped.lstrip("> ").strip()
            quote = _convert_bold(quote)
            out.append(f"  💬 {_esc_keep_tags(quote)}")
            continue

        # 일반 줄
        stripped = _convert_bold(stripped)
        out.append(_esc_keep_tags(stripped))

    # 남은 테이블
    if table_rows:
        out.extend(_format_table(table_rows))

    # 연속 빈 줄 정리
    result = "\n".join(out)
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip()


def _format_table(rows: list[list[str]]) -> list[str]:
    """마크다운 테이블 → 깔끔한 텍스트 목록"""
    if not rows:
        return []
    out = []
    # 첫 행이 헤더인지 판단 (보통 그렇다)
    header = rows[0] if len(rows) > 1 else None
    data_rows = rows[1:] if header else rows

    for row in data_rows:
        if len(row) >= 2:
            key = _convert_bold(row[0].strip())
            val = " · ".join(c.strip() for c in row[1:] if c.strip())
            val = _convert_bold(val)
            out.append(f"  • {_esc_keep_tags(key)}: {_esc_keep_tags(val)}")
        else:
            out.append(f"  • {_esc_keep_tags(row[0])}")
    return out


def _convert_bold(text: str) -> str:
    """**text** → <b>text</b>"""
    return re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)


def _esc_keep_tags(text: str) -> str:
    """HTML 이스케이프하되 <b></b> <i></i> <a> 태그는 보존"""
    # 태그를 임시 치환
    tags = []
    def save_tag(m):
        tags.append(m.group(0))
        return f"\x00TAG{len(tags)-1}\x00"
    text = re.sub(r"</?(?:b|i|a|code)[^>]*>", save_tag, text)
    text = _esc(text)
    # 태그 복원
    for i, tag in enumerate(tags):
        text = text.replace(f"\x00TAG{i}\x00", tag)
    return text


def _sec(emoji: str, title: str, content: str) -> str:
    body = _clean(content)
    return f"\n<b>{emoji} {title}</b>\n\n{body}"


def format_daily(sections: list[dict]) -> str:
    now  = datetime.now(KST)
    s    = streak()
    days = len(list_dates("daily", 9999))
    head = (
        f"<b>📋 데일리 브리핑</b>  {_date_str(now)}\n"
        f"<i>연속 {s}일 · 총 {days}일 발행 · 오전 5:00</i>"
    )
    divider = "\n\n─────────────────"
    body = divider.join(_sec(sec["emoji"], sec["title"], sec["content"]) for sec in sections)
    foot = f"\n\n─────────────────\n📊 <a href='https://hjkatieoh-hub.github.io/my-briefing/'>전체 분석 대시보드</a>"
    return head + divider + body + foot


def format_weekly(sections: list[dict]) -> str:
    now  = datetime.now(KST)
    head = (
        f"<b>📊 위클리 리포트</b>  {now.month}월 {now.day}일 주차\n"
        f"<i>매주 월요일 오전 5:05 발송</i>"
    )
    divider = "\n\n─────────────────"
    body = divider.join(_sec(sec["emoji"], sec["title"], sec["content"]) for sec in sections)
    foot = f"\n\n─────────────────\n📊 <a href='https://hjkatieoh-hub.github.io/my-briefing/'>심층 분석 대시보드</a>"
    return head + divider + body + foot


def split_messages(text: str, limit: int = 4000) -> list[str]:
    """4096자 텔레그램 제한에 맞게 분할"""
    if len(text) <= limit:
        return [text]
    parts, buf = [], ""
    for block in text.split("\n\n─────────────────"):
        chunk = "\n\n─────────────────" + block if buf else block
        if len(buf) + len(chunk) > limit:
            if buf:
                parts.append(buf)
            buf = chunk
        else:
            buf += chunk
    if buf:
        parts.append(buf)
    return parts or [text[:limit]]
