import ssl
import smtplib
import requests
from typing import List, Dict

from config import (
    EMAIL_ENABLED, EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_SMTP_SERVER,
    EMAIL_SMTP_PORT, EMAIL_RECIPIENT,
    TELEGRAM_ENABLED, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
)

# -------------------------
# EMAIL NOTIFICATION
# -------------------------
def send_email(subject: str, body: str) -> None:
    if not EMAIL_ENABLED:
        return
    if not EMAIL_SENDER or not EMAIL_PASSWORD or not EMAIL_RECIPIENT:
        return

    try:
        msg = f"Subject: {subject}\n\n{body}"
        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL(EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT, context=ctx) as s:
            s.login(EMAIL_SENDER, EMAIL_PASSWORD)
            s.sendmail(EMAIL_SENDER, EMAIL_RECIPIENT, msg)
    except Exception as e:
        print("❌ Email notification failed:", e)

# -------------------------
# TELEGRAM NOTIFICATION
# -------------------------
def send_telegram(message: str) -> None:
    if not TELEGRAM_ENABLED:
        return
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }

    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code != 200:
            print("❌ Telegram send failed:", r.text)
    except Exception as e:
        print("❌ Telegram exception:", e)

# -------------------------
# MAIN NOTIFIER
# -------------------------
# def notify_analysis_done(top_list: List[Dict]) -> None:
    """
    Send notification when analysis is completed
    # """
    # if not top_list:
    #     msg = (
    #         "📊 *SwingBot Analysis Completed*\n\n"
    #         "No stocks matched the criteria in this run."
    #     )
    # else:
    #     lines = ["📈 *SwingBot – Top Momentum Stocks*"]
    #     for s in top_list:
    #         lines.append(
    #             f"\n*{s['symbol']}*\n"
    #             f"Price: ₹{s['last_price']}\n"
    #             f"15D: {s['upside_15d']}%\n"
    #             f"30D: {s['upside_30d']}%\n"
    #             f"60D: {s['upside_60d']}%\n"
    #             f"90D: {s['upside_90d']}%\n"
    #             f"Target(90D): ₹{s['target_90d']}\n"
    #             f"Stop Loss: ₹{s['stop_loss']}"
    #         )

    #     msg = "\n".join(lines)

    # # Send via all enabled channels
    # send_email("SwingBot analysis done", msg)
    # send_telegram(msg)
def notify_analysis_done(stocks: List[Dict], chunk_size: int = 5) -> None:
    """
    Send notification when analysis is completed.
    Sends ALL stocks in safe Telegram-sized chunks.
    """
    if not stocks:
        msg = (
            "📊 *SwingBot Analysis Completed*\n\n"
            "No stocks matched the criteria in this run."
        )
        send_email("SwingBot analysis done", msg)
        send_telegram(msg)
        return

    total = len(stocks)

    # Summary message
    summary_msg = (
        "📊 *SwingBot Analysis Completed*\n\n"
        f"Total stocks analyzed: *{total}*"
    )

    send_email("SwingBot analysis done", summary_msg)
    send_telegram(summary_msg)

    # Send detailed stock data in chunks
    for i in range(0, total, chunk_size):
        chunk = stocks[i:i + chunk_size]

        lines = [
            f"📈 *Stocks {i+1}–{min(i+chunk_size, total)}*"
        ]

        for s in chunk:
            lines.append(
                f"\n*{s['symbol']}*\n"
                f"Price: ₹{s['last_price']}\n"
                f"15D: {s['upside_15d']}%\n"
                f"30D: {s['upside_30d']}%\n"
                f"60D: {s['upside_60d']}%\n"
                f"90D: {s['upside_90d']}%\n"
                f"Target(90D): ₹{s.get('target_90d', '-')}\n"
                f"Stop Loss: ₹{s.get('stop_loss', '-')}"
            )

        chunk_msg = "\n".join(lines)
        send_telegram(chunk_msg)
    # send_telegram("✨ Better luck next candle 😉\n— DT 🤖")
    # send_telegram("📉 Market was moody today 😄\n— DT 🤖")
    send_telegram("📊 📉 Data checked. Emotions ignored.📊 📉 \n \n —✨ Thank's From D.T.")

