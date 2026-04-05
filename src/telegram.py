"""src/telegram.py — 텔레그램 발송"""
import requests
from src.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from src.formatter import split_messages


def send(text: str) -> bool:
    url  = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    ok_all = True
    for part in split_messages(text):
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": part,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        try:
            r = requests.post(url, json=payload, timeout=20)
            if r.status_code == 200:
                print("  ✅ 텔레그램 발송 성공")
            else:
                # HTML 파싱 실패 시 plain text 재시도
                import re
                plain = re.sub(r"<[^>]+>", "", part)
                payload["text"] = plain
                payload["parse_mode"] = ""
                r2 = requests.post(url, json=payload, timeout=20)
                ok = r2.status_code == 200
                print(f"  {'✅' if ok else '❌'} plain text 재시도")
                ok_all = ok_all and ok
        except Exception as e:
            print(f"  ❌ 발송 오류: {e}")
            ok_all = False
    return ok_all
