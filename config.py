
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.path.join(BASE_DIR, "data")
MODELS_DIR = os.path.join(BASE_DIR, "models")

NSE_SYMBOLS_CSV = os.path.join(DATA_DIR, "nse_symbols.csv")
BSE_SYMBOLS_CSV = os.path.join(DATA_DIR, "bse_symbols.csv")

TOP_N = 5
LOOKBACK_DAYS = 180

TRAIN_YEARS = 3
TRAIN_SYMBOL_LIMIT = 200

ANALYSIS_SYMBOL_LIMIT = 300

EMAIL_ENABLED = False
EMAIL_SENDER = "your_email@example.com"
EMAIL_PASSWORD = "your_email_app_password"
EMAIL_SMTP_SERVER = "smtp.gmail.com"
EMAIL_SMTP_PORT = 465
EMAIL_RECIPIENT = "target_email@example.com"

TELEGRAM_ENABLED = False
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID = "YOUR_TELEGRAM_CHAT_ID"

SCHEDULE_HOUR = 17
SCHEDULE_MINUTE = 0
