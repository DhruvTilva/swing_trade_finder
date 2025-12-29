import requests
import pandas as pd
import time

def fetch_nse_symbols():
    url = "https://www.nseindia.com/api/equity-master"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                      " AppleWebKit/537.36 (KHTML, like Gecko)"
                      " Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://www.nseindia.com/",
        "Origin": "https://www.nseindia.com"
    }

    s = requests.Session()

    # STEP 1 — get homepage cookies
    for _ in range(3):
        try:
            s.get("https://www.nseindia.com", headers=headers, timeout=10)
            break
        except:
            time.sleep(1)

    # STEP 2 — call equity-master with retries
    for _ in range(5):
        try:
            r = s.get(url, headers=headers, timeout=15)
            if r.status_code == 200:
                data = r.json()
                rec = data.get("data", [])
                df = pd.DataFrame(rec)
                if not df.empty:
                    return df[["symbol"]].rename(columns={"symbol":"SYMBOL"})
        except:
            pass
        time.sleep(1)

    # If still fails → fallback
    print("⚠ NSE API blocked. Falling back to CSV.")
    return pd.DataFrame({"SYMBOL": []})
