
"""Train RandomForest multi-output model for swing returns."""
import os
import time
from typing import List, Tuple

import pandas as pd
import yfinance as yf
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange

from sklearn.ensemble import RandomForestRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import joblib

from config import (
    NSE_SYMBOLS_CSV, BSE_SYMBOLS_CSV, MODELS_DIR,
    TRAIN_YEARS, TRAIN_SYMBOL_LIMIT
)
from auto_symbols import fetch_nse_symbols

# def load_symbols() -> List[str]:
    # print("Fetching ALL NSE symbols for training...")
    # try:
    #     nse_df = fetch_nse_symbols()
    #     print(f"Fetched {len(nse_df)} NSE symbols from API.")
    # except Exception as e:
    #     print("NSE auto-fetch failed, falling back to CSV:", e)
    #     nse_df = pd.read_csv(NSE_SYMBOLS_CSV)
    # symbols = [s.strip() + ".NS" for s in nse_df["SYMBOL"].dropna().unique()]
    # if os.path.exists(BSE_SYMBOLS_CSV):
    #     bse_df = pd.read_csv(BSE_SYMBOLS_CSV)
    #     col = "SYMBOL" if "SYMBOL" in bse_df.columns else bse_df.columns[0]
    #     for s in bse_df[col].dropna().unique():
    #         symbols.append(str(s).strip() + ".BO")
    # symbols = sorted(list(set(symbols)))
    # return symbols

def load_symbols() -> List[str]:
    print("Loading NSE symbols from local CSV only...")

    # --- USE ONLY LOCAL CSV ---
    if not os.path.exists(NSE_SYMBOLS_CSV):
        raise FileNotFoundError(f"NSE symbols CSV not found at: {NSE_SYMBOLS_CSV}")

    # Load CSV
    nse_df = pd.read_csv(NSE_SYMBOLS_CSV)

    # Auto-detect SYMBOL column
    col = "SYMBOL" if "SYMBOL" in nse_df.columns else nse_df.columns[0]

    # Build NSE symbol list
    symbols = [
        str(s).strip() + ".NS"
        for s in nse_df[col].dropna().unique()
        if str(s).strip() != ""
    ]

    # Sort + remove duplicates
    symbols = sorted(list(set(symbols)))

    print(f"Loaded {len(symbols)} NSE symbols from CSV.")
    return symbols

def fetch_history(symbol: str, years: int) -> pd.DataFrame:
    end = pd.Timestamp.today()
    start = end - pd.DateOffset(years=years)

    try:
        df = yf.download(symbol, start=start, end=end, progress=False, auto_adjust=False)

        if df is None or df.empty:
            return pd.DataFrame()

        if isinstance(df.columns, pd.MultiIndex):
            df = df.swaplevel(axis=1)
            df = df.loc[:, (symbol, ["Open", "High", "Low", "Close", "Volume"])]
            df.columns = ["Open", "High", "Low", "Close", "Volume"]

        for col in ["Open", "High", "Low", "Close", "Volume"]:
            if col in df and hasattr(df[col], "values") and df[col].values.ndim > 1:
                df[col] = df[col].iloc[:, 0]  # take the first column

        return df[["Open", "High", "Low", "Close", "Volume"]].dropna()

    except Exception as e:
        print("fetch_history FAILED for", symbol, ":", e)
        return pd.DataFrame()


def build_features(df):
    df = df.copy()
    df["Close"] = pd.to_numeric(df["Close"], errors='coerce')
    df["Open"] = pd.to_numeric(df["Open"], errors='coerce')
    df["High"] = pd.to_numeric(df["High"], errors='coerce')
    df["Low"] = pd.to_numeric(df["Low"], errors='coerce')

    df = df.dropna()

    df["ret_1d"] = df["Close"].pct_change()
    df["ma_5"] = df["Close"].rolling(5).mean()
    df["ma_10"] = df["Close"].rolling(10).mean()
    df["ma_20"] = df["Close"].rolling(20).mean()
    df["ma_ratio_5_20"] = df["ma_5"] / df["ma_20"]

    rsi = RSIIndicator(close=df["Close"].astype(float), window=14)
    df["rsi_14"] = rsi.rsi()

    atr = AverageTrueRange(
        high=df["High"].astype(float),
        low=df["Low"].astype(float),
        close=df["Close"].astype(float),
        window=14
    )
    df["atr_14"] = atr.average_true_range()
    return df.dropna()


def add_targets(df: pd.DataFrame, horizons=(15, 30, 60, 90)) -> pd.DataFrame:
    df = df.copy()
    for h in horizons:
        df[f"fwd_ret_{h}"] = df["Close"].shift(-h) / df["Close"] - 1.0
    return df.dropna()

def build_dataset(symbols: List[str]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    X_list, Y_list = [], []
    horizons = (15, 30, 60, 90)
    total = len(symbols)
    for i, sym in enumerate(symbols, 1):
        print(f"[{i}/{total}] {sym} - fetching history")
        df = fetch_history(sym, TRAIN_YEARS)
        if df.empty:
            continue
        df_feat = build_features(df)
        df_full = add_targets(df_feat, horizons)
        feature_cols = [
            "Close", "ret_1d", "ma_5", "ma_10", "ma_20",
            "ma_ratio_5_20", "rsi_14", "atr_14",
        ]
        target_cols = [f"fwd_ret_{h}" for h in horizons]
        X_list.append(df_full[feature_cols])
        Y_list.append(df_full[target_cols])
        time.sleep(0.1)
    if not X_list:
        raise RuntimeError("No training data collected.")
    X_all = pd.concat(X_list, axis=0)
    Y_all = pd.concat(Y_list, axis=0)
    return X_all, Y_all

def main():
    symbols = load_symbols()
    print(f"Loaded {len(symbols)} symbols.")
    if TRAIN_SYMBOL_LIMIT:
        symbols = symbols[:TRAIN_SYMBOL_LIMIT]
        print(f"Using first {len(symbols)} symbols (TRAIN_SYMBOL_LIMIT).")
    X, Y = build_dataset(symbols)
    print(f"Dataset: X={X.shape}, Y={Y.shape}")
    X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2, shuffle=False)
    base = RandomForestRegressor(
        n_estimators=300, max_depth=8, n_jobs=-1, random_state=42
    )
    model = MultiOutputRegressor(base)
    print("Training model...")
    model.fit(X_train, Y_train)
    Y_pred = model.predict(X_test)
    for i, h in enumerate((15, 30, 60, 90)):
        mse = mean_squared_error(Y_test.iloc[:, i], Y_pred[:, i])
        rmse = mse ** 0.5
        r2 = r2_score(Y_test.iloc[:, i], Y_pred[:, i])
        print(f"H{h}: RMSE={rmse:.4f}, R2={r2:.4f}")
    os.makedirs(MODELS_DIR, exist_ok=True)
    path = os.path.join(MODELS_DIR, "swing_model.pkl")
    joblib.dump(model, path)
    print("Model saved to", path)

if __name__ == "__main__":
    main()
