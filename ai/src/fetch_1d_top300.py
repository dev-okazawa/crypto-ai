import os
import json
import time
import requests
import pandas as pd

RAW_DIR = "ai/data/raw"
TOP300_PATH = "ai/data/top300_usdt.json"
BASE_URL = "https://api.binance.com/api/v3/klines"

os.makedirs(RAW_DIR, exist_ok=True)


def fetch_klines(symbol, interval="1d", limit=1000):

    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }

    response = requests.get(BASE_URL, params=params, timeout=15)

    if response.status_code != 200:
        raise Exception(f"HTTP {response.status_code} {response.text}")

    data = response.json()
    if not data:
        return None

    df = pd.DataFrame(data, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "num_trades",
        "taker_buy_base", "taker_buy_quote", "ignore"
    ])

    df = df[["open_time", "open", "high", "low", "close", "volume"]]

    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)

    numeric_cols = ["open", "high", "low", "close", "volume"]
    df[numeric_cols] = df[numeric_cols].astype(float)

    return df


def main():

    if not os.path.exists(TOP300_PATH):
        print("top300_usdt.json not found")
        return

    with open(TOP300_PATH, "r") as f:
        symbols = json.load(f)

    print(f"\nFetching 1d OHLCV for {len(symbols)} symbols...\n")

    for i, symbol in enumerate(symbols, 1):

        try:
            print(f"[{i}/{len(symbols)}] {symbol} 1d...")

            df = fetch_klines(symbol, "1d", 1000)

            if df is None or len(df) == 0:
                print(f"[SKIP] {symbol} (no data)")
                continue

            path = f"{RAW_DIR}/{symbol}_1d.csv"
            df.to_csv(path, index=False)

            print(f"[OK] Saved {path} ({len(df)} rows)")

            time.sleep(0.2)

        except Exception as e:
            print(f"[ERROR] {symbol}: {e}")
            time.sleep(0.5)

    print("\n1d fetch completed.")


if __name__ == "__main__":
    main()
