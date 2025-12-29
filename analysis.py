"""Run inference: scan stocks from CSV only,
predict upsides using trained ML model,
return 1 highest positive & 1 highest negative momentum stock.
"""
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Tuple

import pandas as pd
import yfinance as yf
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange
import joblib

from config import (
    LOOKBACK_DAYS,
    MODELS_DIR
)
from sentiment import get_sentiment_for_symbol

# =======================
# MODEL LOADING
# =======================
MODEL_PATH = os.path.join(MODELS_DIR, "swing_model.pkl")

if not os.path.exists(MODEL_PATH):
    raise RuntimeError("Model not found. Run model_train.py first.")

MODEL = joblib.load(MODEL_PATH)

FEATURE_COLS = [
    "Close", "ret_1d", "ma_5", "ma_10", "ma_20",
    "ma_ratio_5_20", "rsi_14", "atr_14",
]

# =======================
# SYMBOL LOADING (CSV ONLY)
# =======================

def load_symbols() -> List[str]:
    df = pd.read_csv("data/nse_symbols.csv")
    symbols = []

    for s in df["SYMBOL"].dropna().unique():
        s = str(s).strip().upper()

        # Auto-append NSE suffix if missing
        if not s.endswith(".NS") and not s.endswith(".BO"):
            s = s + ".NS"

        symbols.append(s)

    return symbols


# =======================
# DATA FETCHING
# =======================

def fetch_recent_history(symbol: str, days: int) -> pd.DataFrame:
    end = pd.Timestamp.today()
    start = end - pd.Timedelta(days=days)

    # Try methods in order
    methods = [
        ("download", symbol),
        ("ticker", symbol),
    ]

    for method, sym in methods:
        try:
            if method == "download":
                df = yf.download(
                    sym,
                    start=start,
                    end=end,
                    progress=False,
                    auto_adjust=False,
                    group_by=False,
                    threads=False
                )
            else:
                df = yf.Ticker(sym).history(
                    start=start,
                    end=end,
                    auto_adjust=False
                )

            if df is not None and not df.empty:
                return df[["Open", "High", "Low", "Close", "Volume"]].dropna()

        except Exception:
            pass

    # Fallback to BSE if NSE fails
    if symbol.endswith(".NS"):
        return fetch_recent_history(symbol.replace(".NS", ".BO"), days)

    return pd.DataFrame()

# =======================
# FEATURE ENGINEERING
# =======================
def build_features_latest(df: pd.DataFrame):
    df = df.copy()

    df["ret_1d"] = df["Close"].pct_change()
    df["ma_5"] = df["Close"].rolling(5).mean()
    df["ma_10"] = df["Close"].rolling(10).mean()
    df["ma_20"] = df["Close"].rolling(20).mean()
    df["ma_ratio_5_20"] = df["ma_5"] / df["ma_20"]

    rsi = RSIIndicator(df["Close"], window=14)
    df["rsi_14"] = rsi.rsi()

    atr = AverageTrueRange(
        df["High"], df["Low"], df["Close"], window=14
    )
    df["atr_14"] = atr.average_true_range()

    df = df.dropna()
    if df.empty:
        return None

    last = df.iloc[-1]
    return last[FEATURE_COLS], float(last["Close"]), float(last["atr_14"])

# =======================
# SINGLE SYMBOL ANALYSIS
# =======================

def analyze_symbol(symbol: str) -> Dict:
    print(f"Analyzing: {symbol}")

    df = fetch_recent_history(symbol, LOOKBACK_DAYS)
    if df.empty:
        print(f"❌ No price data for {symbol}")
        return {}

    res = build_features_latest(df)
    if not res:
        print(f"❌ Feature build failed for {symbol}")
        return {}

    features, last_price, atr_last = res
    X = pd.DataFrame([features])

    try:
        preds = MODEL.predict(X)[0]
    except Exception as e:
        print(f"❌ Model prediction failed for {symbol}: {e}")
        return {}

    # ML predicted upsides (%)
    up_15 = preds[0] * 100
    up_30 = preds[1] * 100
    up_60 = preds[2] * 100
    up_90 = preds[3] * 100

    # Sentiment
    sentiment = get_sentiment_for_symbol(symbol)

    # -----------------------------
    # Target & Stop Loss (ATR based)
    # -----------------------------
    target_90d = round(last_price * (1 + up_90 / 100), 2)
    stop_loss = round(last_price - (1.5 * atr_last), 2)

    # Safety check
    if stop_loss <= 0:
        stop_loss = round(last_price * 0.9, 2)

    # -----------------------------
    # Rationale (simple & explainable)
    # -----------------------------
    if up_30 > 0:
        rationale = "Positive ML momentum with upward trend"
    else:
        rationale = "Negative ML momentum with downside risk"

    print(f"✅ Success for {symbol}")

    return {
        "symbol": symbol,
        "last_price": round(last_price, 2),
        "upside_15d": round(up_15, 2),
        "upside_30d": round(up_30, 2),
        "upside_60d": round(up_60, 2),
        "upside_90d": round(up_90, 2),
        "target_90d": target_90d,
        "stop_loss": stop_loss,
        "sentiment": round(sentiment, 3),
        "rationale": rationale,
    }

# =======================
# MAIN ANALYSIS (CSV → 2 STOCKS)
# =======================
def analyze_all_stocks() -> Tuple[List[Dict], List[Dict]]:
    symbols = load_symbols()
    results: List[Dict] = []

    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {executor.submit(analyze_symbol, s): s for s in symbols}
        for fut in as_completed(futures):
            try:
                r = fut.result()
                if r:
                    results.append(r)
            except Exception:
                continue

    if not results:
        return [], []
    top_positive = max(results, key=lambda x: x["upside_30d"])
    top_negative = min(results, key=lambda x: x["upside_30d"])
    top_positive["rationale"] = "Strongest positive ML momentum 30 Days (relative)"
    top_negative["rationale"] = "Weakest / negative ML momentum 30 Days (relative)"
    return [top_positive, top_negative], results

if __name__ == "__main__":
    top, _ = analyze_all_stocks()
    print("Top picks:")
    for r in top:
        print(r)