# ai/jobs/fetch_prices.py

import sys
import pandas as pd
import requests
from pathlib import Path
from datetime import datetime, timedelta

from ai.src.market_cap import load_trained_symbols

# =====================
# Args
# =====================
if len(sys.argv) < 3:
    print("Usage: fetch_prices <SYMBOL|all> <INTERVAL>", flush=True)
    sys.exit(1)

TARGET = sys.argv[1]   # SYMBOL or "all"
INTERVAL = sys.argv[2] # "1h" or "1d" or "1w"

# =====================
# Paths
# =====================
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "ai" / "data" / "raw"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# =====================
# Binance
# =====================
BINANCE_INTERVAL_MAP = {
    "1h": "1h",
    "1d": "1d",
    "1w": "1w",
}

INTERVAL_DELTA = {
    "1h": timedelta(hours=1),
    "1d": timedelta(days=1),
    "1w": timedelta(weeks=1),
}

# =====================
# Binance API
# =====================
def fetch_klines(symbol, interval, start_time=None, limit=1000):
    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": BINANCE_INTERVAL_MAP[interval],
        "limit": limit,
    }

    if start_time:
        params["startTime"] = int(start_time.timestamp() * 1000)

    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    return r.json()

# =====================
# Fetch one symbol
# =====================
def fetch_one(symbol: str):
    path = DATA_DIR / f"{symbol}_{INTERVAL}.csv"

    # ---- load existing ----
    if path.exists():
        df_old = pd.read_csv(path)
        last_open = str(df_old.iloc[-1]["open_time"])

        if INTERVAL in ("1d", "1w"):
            last_time = datetime.strptime(last_open, "%Y-%m-%d")
        else:
            last_time = datetime.strptime(last_open, "%Y-%m-%d %H:%M:%S")

        start_time = last_time + INTERVAL_DELTA[INTERVAL]
    else:
        df_old = None
        start_time = None

    # ---- fetch ----
    if df_old is None:
        # 初回は直近1000本取得
        klines = fetch_klines(symbol, INTERVAL, start_time=None, limit=1000)
    else:
        klines = fetch_klines(symbol, INTERVAL, start_time=start_time, limit=1000)

    if not klines:
        print(f"[SKIP] {symbol}: no new klines", flush=True)
        return

    # ---- build rows ----
    rows = []
    for k in klines:
        ts = datetime.utcfromtimestamp(k[0] / 1000)

        if INTERVAL in ("1d", "1w"):
            open_time = ts.strftime("%Y-%m-%d")
        else:
            open_time = ts.strftime("%Y-%m-%d %H:%M:%S")

        close = float(k[4])
        volume = float(k[5])
        rows.append([open_time, close, volume])

    df_new = pd.DataFrame(rows, columns=["open_time", "close", "volume"])

    # ---- merge & dedupe ----
    if df_old is not None:
        df = pd.concat([df_old, df_new], ignore_index=True)
        df = df.drop_duplicates(subset=["open_time"]).sort_values("open_time")
    else:
        df = df_new

    df.to_csv(path, index=False)
    print(f"[OK] {symbol}: appended {len(df_new)} rows", flush=True)

# =====================
# Entry point
# =====================
def main():
    if TARGET == "all":
        symbols = sorted(load_trained_symbols())
        print(f"[FETCH ALL] symbols={len(symbols)}, interval={INTERVAL}", flush=True)
    else:
        symbols = [TARGET]
        print(f"[FETCH ONE] {TARGET}, interval={INTERVAL}", flush=True)

    for symbol in symbols:
        fetch_one(symbol)

if __name__ == "__main__":
    main()
