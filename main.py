"""main.py — 데일리/위클리 브리핑 파이프라인

사용법:
  python main.py daily            # 데일리 브리핑
  python main.py weekly           # 위클리 리포트
  python main.py daily --dry-run  # API 없이 구조 테스트
  python main.py daily --no-send  # 텔레그램 발송 없이 저장만
"""
import sys
from datetime import datetime
from src.config import load_profile, KST, DAILY_SECTIONS, WEEKLY_SECTIONS
from src.fetcher import fetch_all
from src.storage import save
from src.formatter import format_daily, format_weekly
from src.telegram import send

def banner(mode: str):
    now = datetime.now(KST)
    bar = "=" * 48
    print(f"\n{bar}")
    print(f"  나의 브리핑 봇 — {mode.upper()}")
    print(f"  {now.strftime('%Y-%m-%d %H:%M')} KST")
    print(f"{bar}\n")

def dummy(sections):
    return [{**s, "content": f"[DRY-RUN] {s['title']} 샘플 내용입니다.", "ok": True}
            for s in sections]

def run(mode: str, dry: bool, no_send: bool):
    banner(mode)
    profile  = load_profile()
    sections = DAILY_SECTIONS if mode == "daily" else WEEKLY_SECTIONS
    label    = "데일리" if mode == "daily" else "위클리"

    print(f"[ 1/3 ] {label} 섹션 수집 ({len(sections)}개)")
    results = dummy(sections) if dry else fetch_all(sections, profile)

    print(f"\n[ 2/3 ] 히스토리 저장")
    save(mode, results)

    print(f"\n[ 3/3 ] 텔레그램 발송")
    if no_send:
        print("  --no-send 플래그 — 발송 건너뜀")
        msg = format_daily(results) if mode == "daily" else format_weekly(results)
        print("\n" + "─" * 40)
        print(msg[:800] + "..." if len(msg) > 800 else msg)
    else:
        msg = format_daily(results) if mode == "daily" else format_weekly(results)
        send(msg)

    print(f"\n{'=' * 48}")
    print(f"  완료! ({'dry-run' if dry else '실제 실행'})")
    print(f"{'=' * 48}\n")

if __name__ == "__main__":
    args    = sys.argv[1:]
    mode    = args[0] if args else "daily"
    dry     = "--dry-run" in args
    no_send = "--no-send" in args
    if mode not in ("daily", "weekly"):
        print("사용법: python main.py [daily|weekly] [--dry-run] [--no-send]")
        sys.exit(1)
    run(mode, dry, no_send)
