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
# 텔레그램 수신자 목록: BOT_TOKEN:CHAT_ID 쌍
# TELEGRAM_RECIPIENTS="token1:chatid1,token2:chatid2"
# 하위 호환: TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID도 지원
def _build_recipients():
    recipients = []
    raw = os.environ.get("TELEGRAM_RECIPIENTS", "")
    if raw:
        for pair in raw.split(","):
            pair = pair.strip()
            if ":" in pair:
                token, chat_id = pair.split(":", 1)
                # bot token has format "number:hash" so re-join properly
                parts = pair.split(":")
                # format: botid:bothash:chatid → token=botid:bothash, chatid=chatid
                token = ":".join(parts[:-1])
                chat_id = parts[-1]
                recipients.append((token, chat_id))
    # fallback: 기존 환경변수
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

def prompt_weather(p: dict) -> str:
    loc = p["user"]["location"]
    return f"""오늘 {loc}의 날씨를 웹에서 검색해서 알려줘.
반드시 아래 항목을 포함해:
- 아침 최저 기온 (°C)
- 낮 최고 기온 (°C)
- 날씨 상태 (맑음/흐림/비/눈 등)
- 강수확률 (%)
- 이번 주말 날씨 한 줄 예보

또한 아침 기온 기준으로 오늘 옷차림을 구체적으로 추천해줘:
- 상의 (구체적 아이템명)
- 하의 (구체적 아이템명)
- 신발
- 기타 소품 (있으면)
- 실용 팁 한 줄

서두 없이 위 내용만 간결하게."""

def prompt_stocks(p: dict) -> str:
    port = p["stocks"]["portfolio_man"] // 100
    return f"""오늘 미국 주식시장(어제 밤~오늘 새벽 마감 기준) S&P500, 나스닥, 달러/원 환율, 미국 10년물 국채금리를 알려줘.

다음 내용을 포함해:
1. 각 지수/환율 수치와 등락률
2. 오늘 시장을 움직인 핵심 이유 2가지 (각 1문장)
3. 주목할 종목 또는 섹터 동향 1가지
4. 해외주식 {port}억 보유 기준 오늘 지수 변동의 수익/손실 추정 (원화 기준)
5. 핵심 인사이트 1~2문장

서두 없이 바로."""

def prompt_realestate(p: dict) -> str:
    cap   = p["real_estate"]["capital_man"] // 100
    ltv   = int(p["real_estate"]["ltv_rate"] * 100)
    regs  = ", ".join(p["real_estate"]["watch_regions"][:4])
    return f"""오늘 기준 다음 정보를 알려줘:
1. 5대 은행 주택담보대출 최저 금리 (%)
2. 서울 아파트 매수심리지수 (최신치)
3. {regs} 지역 최근 가격 동향 각 1줄

그리고 다음을 계산해줘:
- 자본 {cap}억, LTV {ltv}% 적용 시 최대 매수 가능 금액
- 현재 금리 기준 30년 원리금균등상환 월 상환액
- 현재 매수 타이밍 판단: 🟢관심 / 🟡관망 / 🔴비추 + 이유 한 줄

서두 없이 바로."""

def prompt_toss(p: dict) -> str:
    comps = ", ".join(p["fintech"]["competitors"])
    return f"""오늘 핀테크 뉴스를 우선순위 순으로 짧게 알려줘.

**최우선** 토스인컴(토스 보험) 관련 뉴스
**그 다음** 토스·토스뱅크·토스증권·비바리퍼블리카 관련
**마지막** {comps} / 금융위·금감원 핀테크 정책

각 뉴스: 제목 + 핵심 1~2줄 + 인사이트 한 줄.
최대 5건. 없으면 생략. 서두 없이 바로."""

def prompt_industry(p: dict) -> str:
    domestic = ", ".join(p["tech_companies"])
    global_  = ", ".join(p["global_tech"][:5])
    return f"""오늘(또는 최근 24시간) 다음 기업들의 뉴스를 검색해서 각 1건씩 알려줘.
국내: {domestic}
글로벌(국내 IT·핀테크에 영향 있는 것만): {global_}

각 기업명으로 "네이버 뉴스", "카카오 뉴스" 등으로 검색해.
각 1~2줄. 뉴스가 없는 기업은 생략. 서두/사과 없이 바로."""

def prompt_ai(p: dict) -> str:
    return """오늘 AI/인공지능 분야 주목할 뉴스 또는 릴리즈 2~3건.
LLM, AI 에이전트, 핀테크 AI 적용 관련 위주.
각 2~3문장. 서두 없이 바로."""

def prompt_daily_insight(p: dict) -> str:
    return f"""오늘 경제/시장/업계 흐름을 종합한 핵심 인사이트 1~2개를 뽑아줘.

이 사람의 상황:
- {p["user"]["job"]}
- 미국 해외주식 {p["stocks"]["portfolio_man"]//100}억 투자 중
- 자본 {p["real_estate"]["capital_man"]//100}억으로 {p["real_estate"]["target_years"]}년 내 서울 아파트 매수 계획

오늘 뉴스들의 연결고리를 찾아서, 이 사람에게 의미 있는 인사이트만.
마지막 줄에 "내일/이번 주 주목할 시그널" 한 줄 예고.
총 3~4문장."""

# ── 위클리 섹션 프롬프트 ─────────────────────────────────────────

def prompt_weekly_market(p: dict) -> str:
    port = p["stocks"]["portfolio_man"] // 100
    return f"""지난 1주일 미국 주식시장 주간 성과를 요약해줘.
1. S&P500, 나스닥 주간 등락률
2. 강세 섹터 Top 2 / 약세 섹터 Top 2
3. 해외주식 {port}억 기준 주간 추정 수익/손실 (원화)
4. 이번 주 주목할 실적 발표 일정 (요일별로)
5. 다음 주 핵심 매크로 이벤트 1~2개

간결하게. 서두 없이 바로."""

def prompt_weekly_realestate(p: dict) -> str:
    cap  = p["real_estate"]["capital_man"] // 100
    regs = ", ".join(p["real_estate"]["watch_regions"][:4])
    return f"""지난 1주일 서울 아파트 시장 주간 동향을 알려줘.
1. 서울 주간 거래량 (전주 대비)
2. {regs} 지역별 가격 변동
3. 전세가율 변화
4. 주담대 금리 주간 변동
5. 자본 {cap}억, 5년 내 매수 계획 기준 이번 주 타이밍 신호: 🟢관심 / 🟡관망 / 🔴비추 + 근거 2줄

서두 없이 바로."""

def prompt_weekly_fintech(p: dict) -> str:
    entities = ", ".join(p["fintech"]["entities"])
    comps    = ", ".join(p["fintech"]["competitors"])
    return f"""지난 1주일 핀테크 업계 흐름을 요약해줘.
1. {entities} 주간 주요 동향
2. {comps} 경쟁 구도 변화
3. 금융 규제/정책 변화 중 핀테크에 영향 있는 것
4. 업계 전체 분위기와 다음 주 주목 포인트

4~6줄. 서두 없이 바로."""

def prompt_weekly_calendar(p: dict) -> str:
    return """이번 주(월~금) 주요 경제 이벤트 일정을 요일별로 알려줘.
한국: 한국은행 발표, 정부 정책, 주요 기업 실적
미국: FOMC, CPI/PPI, 고용지표, 주요 기업 실적
각 이벤트마다 중요도(★★★/★★/★)와 예상 영향 한 줄.
서두 없이 바로."""

def prompt_weekly_events(p: dict) -> str:
    loc = p["user"]["location"]
    return f"""이번 주말과 다음 주말에 {loc} 및 서울 근교에서 열리는 축제, 문화 행사, 전시, 공연을 알려줘.
각 행사: 행사명 / 날짜 / 장소 / 한줄 설명
5~7개. 입장료 있으면 포함. 서두 없이 바로 목록으로."""

def prompt_weekly_concept(p: dict) -> str:
    return f"""이번 주 뉴스와 가장 연관된 경제·투자 개념 1개를 골라 쉽게 설명해줘.

대상: 경제 공부 시작 단계 / 미국 해외주식 {p["stocks"]["portfolio_man"]//100}억 투자 중 / 서울 아파트 매수 계획

설명 순서:
1. 개념 정의 (1~2줄)
2. 실생활 예시 (1~2줄)  
3. 지금 시장에서의 의미 (1~2줄)
4. 내 투자/자산과의 연관성 (1줄)

친근하고 명확하게."""

def prompt_weekly_signal(p: dict) -> str:
    return f"""다음 주 주목해야 할 핵심 시그널 3가지를 예고해줘.
1. 해외주식 관련 (지수/이벤트/실적)
2. 부동산 관련 (금리/거래량/정책)
3. 핀테크/토스 업계 관련

각 시그널: 무엇을 봐야 하는지 + 왜 중요한지 + 어떤 방향 예상인지.
3~4줄씩. 서두 없이 바로."""

# ── 섹션 메타 ────────────────────────────────────────────────────

DAILY_SECTIONS = [
    {"id": "weather",        "emoji": "🌤",  "title": "오늘 날씨 & 옷차림",    "prompt_fn": prompt_weather},
    {"id": "stocks",         "emoji": "📈",  "title": "해외주식 & 환율",        "prompt_fn": prompt_stocks},
    {"id": "realestate",     "emoji": "🏠",  "title": "부동산 시그널",          "prompt_fn": prompt_realestate},
    {"id": "toss",           "emoji": "💙",  "title": "토스 & 핀테크",          "prompt_fn": prompt_toss},
    {"id": "industry",       "emoji": "🏢",  "title": "네카라쿠배 & 빅테크",    "prompt_fn": prompt_industry},
    {"id": "ai",             "emoji": "🤖",  "title": "AI 트렌드",              "prompt_fn": prompt_ai},
    {"id": "daily_insight",  "emoji": "💡",  "title": "오늘의 인사이트",        "prompt_fn": prompt_daily_insight},
]

WEEKLY_SECTIONS = [
    {"id": "weekly_market",    "emoji": "📊",  "title": "주간 시장 리뷰",      "prompt_fn": prompt_weekly_market},
    {"id": "weekly_realestate","emoji": "🏠",  "title": "부동산 주간 리포트",   "prompt_fn": prompt_weekly_realestate},
    {"id": "weekly_fintech",   "emoji": "💙",  "title": "핀테크 업계 흐름",     "prompt_fn": prompt_weekly_fintech},
    {"id": "weekly_calendar",  "emoji": "📅",  "title": "이번 주 경제 일정",    "prompt_fn": prompt_weekly_calendar},
    {"id": "weekly_events",    "emoji": "🎉",  "title": "이번 주말 행사",        "prompt_fn": prompt_weekly_events},
    {"id": "weekly_concept",   "emoji": "🧠",  "title": "이번 주 배울 개념",    "prompt_fn": prompt_weekly_concept},
    {"id": "weekly_signal",    "emoji": "🔭",  "title": "다음 주 시그널",        "prompt_fn": prompt_weekly_signal},
]
