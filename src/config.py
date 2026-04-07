"""src/config.py — 설정 & 프롬프트 중앙 관리"""
import os, json
from pathlib import Path
from datetime import timezone, timedelta
from dotenv import load_dotenv

ROOT         = Path(__file__).parent.parent
load_dotenv(ROOT / ".env", override=True)
BRIEFINGS    = ROOT / "briefings"
PROFILE_PATH = ROOT / "profile.json"
KST          = timezone(timedelta(hours=9))

ANTHROPIC_API_KEY  = os.environ.get("ANTHROPIC_API_KEY", "")

def _build_recipients():
    recipients = []
    raw = os.environ.get("TELEGRAM_RECIPIENTS", "")
    if raw:
        for pair in raw.split(","):
            pair = pair.strip()
            if ":" in pair:
                parts = pair.split(":")
                token = ":".join(parts[:-1])
                chat_id = parts[-1]
                recipients.append((token, chat_id))
    if not recipients:
        token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        chat_ids = os.environ.get("TELEGRAM_CHAT_ID", "")
        if token and chat_ids:
            for cid in chat_ids.split(","):
                if cid.strip():
                    recipients.append((token, cid.strip()))
    return recipients

TELEGRAM_RECIPIENTS = _build_recipients()
GITHUB_USER        = os.environ.get("GITHUB_USER", "your-username")
GITHUB_REPO        = os.environ.get("GITHUB_REPO", "my-briefing")

def load_profile() -> dict:
    return json.loads(PROFILE_PATH.read_text(encoding="utf-8"))

# ── 데일리 섹션 프롬프트 ─────────────────────────────────────────
# 모든 프롬프트는 "정확히 이 포맷으로" 출력을 강제합니다.

def prompt_weather(p: dict) -> str:
    loc = p["user"]["location"]
    return f"""오늘 {loc} 날씨를 검색해서 정확히 아래 포맷으로만 답해.

최저 __°C / 최고 __°C / 날씨상태 / 강수 __%
주말: (한 줄 예보)
👔 상의: __ / 하의: __ / 신발: __
💡 (실용 팁 한 줄)

위 4줄만 출력. 다른 말 하지 마."""

def prompt_stocks(p: dict) -> str:
    port = p["stocks"]["portfolio_man"] // 100
    return f"""어제 미국 주식시장 마감 기준, 정확히 아래 포맷으로만 답해.

S&P _____ ▲/▼_.__% | 나스닥 _____ ▲/▼_.__%
원/달러 _,___원 ▲/▼__ | 10Y ____% | WTI유가 $___
📌 핵심1: (시장 움직인 이유 1문장)
📌 핵심2: (시장 움직인 이유 1문장)
🔍 주목: (종목/섹터 동향 1문장)
💰 {port}억 기준: 약 ▲/▼___만원 추정
💡 (인사이트 1문장)

위 포맷만 출력. 서두/맺음/면책 없이."""

def prompt_realestate(p: dict) -> str:
    cap   = p["real_estate"]["capital_man"] // 100
    ltv   = int(p["real_estate"]["ltv_rate"] * 100)
    regs  = ", ".join(p["real_estate"]["watch_regions"][:4])
    return f"""오늘 기준 부동산 정보를 정확히 아래 포맷으로만 답해.

주담대 최저 _.__% | 매수심리 ___
{regs} 각 1줄씩:
성동: (동향)
마포: (동향)
용산: (동향)
강남: (동향)
🧮 자본{cap}억+LTV{ltv}% → 최대매수 __억 / 월상환 ___만
⏱️ 🟢관심/🟡관망/🔴비추 + 이유 한 줄

위 포맷만 출력. 계산 과정/면책 없이."""

def prompt_toss(p: dict) -> str:
    comps = ", ".join(p["fintech"]["competitors"])
    return f"""오늘 핀테크 뉴스를 검색해서 아래 포맷으로만 답해.
우선순위: ①토스인컴 ②토스계열 ③{comps}/정책

각 뉴스를 이렇게:
① (회사명) 제목
→ 핵심 1줄
💡 인사이트 1줄

최대 4건. 없으면 생략. 서두/사과/면책 없이 바로."""

def prompt_industry(p: dict) -> str:
    domestic = ", ".join(p["tech_companies"])
    global_  = ", ".join(p["global_tech"][:5])
    return f"""오늘(최근 24시간) 기업 뉴스를 검색해서 아래 포맷으로만 답해.

각 기업 1줄씩:
네이버: (뉴스 핵심 1줄)
카카오: (뉴스 핵심 1줄)
...

국내: {domestic}
글로벌: {global_}
뉴스 없는 기업은 생략. 서두/사과 절대 없이 바로."""

def prompt_ai(p: dict) -> str:
    return """오늘 AI 분야 뉴스 2~3건을 검색해서 아래 포맷으로만 답해.

① (제목)
→ 핵심 1~2줄

② (제목)
→ 핵심 1~2줄

서두 없이 바로."""

def prompt_daily_insight(p: dict) -> str:
    return f"""오늘 경제/시장/업계 흐름 종합 인사이트. 정확히 아래 포맷으로만 답해.

💡 (인사이트 제목)
(2~3문장으로 핵심만)

🔭 내일/이번 주 주목: (시그널 1줄)

이 사람: {p["user"]["job"]} / 해외주식 {p["stocks"]["portfolio_man"]//100}억 / 서울 아파트 {p["real_estate"]["target_years"]}년 내 매수 계획
위 포맷만. 서두/맺음 없이."""

# ── 위클리 섹션 프롬프트 ─────────────────────────────────────────

def prompt_weekly_market(p: dict) -> str:
    port = p["stocks"]["portfolio_man"] // 100
    return f"""지난 1주일 미국 시장 요약. 정확히 아래 포맷으로만 답해.

S&P 주간 ▲/▼_.__% | 나스닥 ▲/▼_.__%
강세: __, __ | 약세: __, __
💰 {port}억 기준 주간: ▲/▼___만원
📅 이번 주 실적: (요일별 1줄씩)
🔭 다음 주: (매크로 이벤트 1~2개)

서두 없이 바로."""

def prompt_weekly_realestate(p: dict) -> str:
    cap  = p["real_estate"]["capital_man"] // 100
    regs = ", ".join(p["real_estate"]["watch_regions"][:4])
    return f"""지난 1주일 서울 아파트 주간 동향. 아래 포맷으로만 답해.

거래량: ___건 (전주比 ▲/▼)
{regs}: 각 1줄 가격 변동
전세가율: __%  (▲/▼)
주담대: _.__% (▲/▼)
⏱️ 🟢/🟡/🔴 + 근거 1줄

서두 없이 바로."""

def prompt_weekly_fintech(p: dict) -> str:
    entities = ", ".join(p["fintech"]["entities"])
    comps    = ", ".join(p["fintech"]["competitors"])
    return f"""지난 1주일 핀테크 업계 흐름. 아래 포맷으로만 답해.

토스: (주간 동향 1~2줄)
경쟁사: (구도 변화 1줄)
정책: (규제 변화 1줄)
🔭 다음 주: (주목 포인트 1줄)

서두 없이 바로."""

def prompt_weekly_calendar(p: dict) -> str:
    return """이번 주 경제 일정. 아래 포맷으로만 답해.

월: (이벤트) ★~★★★
화: (이벤트) ★~★★★
...금요일까지

한국+미국 합쳐서 요일별 1~2개만. 서두 없이 바로."""

def prompt_weekly_events(p: dict) -> str:
    loc = p["user"]["location"]
    return f"""이번 주말~다음 주말 {loc}/서울 근교 행사. 아래 포맷으로만 답해.

① 행사명 | 날짜 | 장소
(한줄 설명, 입장료)

5개 이내. 서두 없이 바로."""

def prompt_weekly_concept(p: dict) -> str:
    return f"""이번 주 뉴스 관련 경제 개념 1개. 아래 포맷으로만 답해.

📖 (개념명)
정의: (1줄)
예시: (1줄)
시장: (1줄)
내 자산: (1줄)

서두 없이 바로."""

def prompt_weekly_signal(p: dict) -> str:
    return """다음 주 핵심 시그널 3가지. 아래 포맷으로만 답해.

📈 주식: (무엇을 + 왜 + 예상 방향, 2줄)
🏠 부동산: (무엇을 + 왜 + 예상 방향, 2줄)
💙 핀테크: (무엇을 + 왜 + 예상 방향, 2줄)

서두 없이 바로."""

# ── 섹션 메타 ────────────────────────────────────────────────────

DAILY_SECTIONS = [
    {"id": "weather",        "emoji": "🌤",  "title": "날씨",              "prompt_fn": prompt_weather},
    {"id": "stocks",         "emoji": "📈",  "title": "주식 & 환율",       "prompt_fn": prompt_stocks},
    {"id": "realestate",     "emoji": "🏠",  "title": "부동산",            "prompt_fn": prompt_realestate},
    {"id": "toss",           "emoji": "💙",  "title": "토스 & 핀테크",     "prompt_fn": prompt_toss},
    {"id": "industry",       "emoji": "🏢",  "title": "네카라쿠배 & 빅테크","prompt_fn": prompt_industry},
    {"id": "ai",             "emoji": "🤖",  "title": "AI",               "prompt_fn": prompt_ai},
    {"id": "daily_insight",  "emoji": "💡",  "title": "인사이트",          "prompt_fn": prompt_daily_insight},
]

WEEKLY_SECTIONS = [
    {"id": "weekly_market",    "emoji": "📊",  "title": "주간 시장",       "prompt_fn": prompt_weekly_market},
    {"id": "weekly_realestate","emoji": "🏠",  "title": "부동산 주간",     "prompt_fn": prompt_weekly_realestate},
    {"id": "weekly_fintech",   "emoji": "💙",  "title": "핀테크 주간",     "prompt_fn": prompt_weekly_fintech},
    {"id": "weekly_calendar",  "emoji": "📅",  "title": "경제 일정",       "prompt_fn": prompt_weekly_calendar},
    {"id": "weekly_events",    "emoji": "🎉",  "title": "주말 행사",       "prompt_fn": prompt_weekly_events},
    {"id": "weekly_concept",   "emoji": "🧠",  "title": "경제 개념",       "prompt_fn": prompt_weekly_concept},
    {"id": "weekly_signal",    "emoji": "🔭",  "title": "다음 주 시그널",   "prompt_fn": prompt_weekly_signal},
]
