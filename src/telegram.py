"""src/telegram.py — 텔레그램 발송 (다중 봇·수신자 지원)"""
import re
import requests
from src.config import TELEGRAM_RECIPIENTS
from src.formatter import split_messages


def send(text: str) -> bool:
    ok_all = True

    for bot_token, chat_id in TELEGRAM_RECIPIENTS:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        for part in split_messages(text):
            payload = {
                "chat_id": chat_id,
                "text": part,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            }
            try:
                r = requests.post(url, json=payload, timeout=20)
                if r.status_code == 200:
                    print(f"  ✅ 발송 성공 ({chat_id})")
                else:
                    # HTML 파싱 실패 시 plain text 재시도
                    plain = re.sub(r"<[^>]+>", "", part)
                    payload["text"] = plain
                    payload["parse_mode"] = ""
                    r2 = requests.post(url, json=payload, timeout=20)
                    ok = r2.status_code == 200
                    print(f"  {'✅' if ok else '❌'} plain text 재시도 ({chat_id})")
                    ok_all = ok_all and ok
            except Exception as e:
                print(f"  ❌ 발송 오류 ({chat_id}): {e}")
                ok_all = False
    return ok_all
