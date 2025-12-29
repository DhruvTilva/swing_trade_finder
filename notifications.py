
import ssl
import smtplib
import requests
from typing import List, Dict

from config import (
    EMAIL_ENABLED, EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_SMTP_SERVER,
    EMAIL_SMTP_PORT, EMAIL_RECIPIENT,
    TELEGRAM_ENABLED, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
)

def send_email(subject: str, body: str) -> None:
    if not EMAIL_ENABLED:
        return
    if not EMAIL_SENDER or not EMAIL_PASSWORD or not EMAIL_RECIPIENT:
        return

    msg = f"Subject: {subject}\n\n{body}"
    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL(EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT, context=ctx) as s:
        s.login(EMAIL_SENDER, EMAIL_PASSWORD)
        s.sendmail(EMAIL_SENDER, EMAIL_RECIPIENT, msg)

def send_telegram(message: str) -> None:
    if not TELEGRAM_ENABLED:
        return
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    params = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
    except Exception:
        return

def notify_analysis_done(top_list: List[Dict]) -> None:
    if not top_list:
        msg = "SwingBot: analysis completed. No stocks matched criteria."
    else:
        lines = ["SwingBot: latest top candidates:"]
        for s in top_list:
            lines.append(
                f"{s['symbol']}: 15d {s['upside_15d']}%, 30d {s['upside_30d']}%, "
                f"60d {s['upside_60d']}%, 90d {s['upside_90d']}%, "
                f"Tgt90 ₹{s['target_90d']}, SL ₹{s['stop_loss']}"
            )
        msg = "\n".join(lines)
    send_email("SwingBot analysis done", msg)
    send_telegram(msg)
