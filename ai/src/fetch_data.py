import os
import time
import requests
import pandas as pd
from datetime import datetime

RAW_DIR = "ai/data/raw"
BASE_URL = "https://api.binance.com/api/v3/klines"

os.makedirs(RAW_DIR, exist_ok=True)


def fetch_all_klines(symbol: str, interval: str):
    print(f"\nFetching {symbol} {interval} full history...")

    all_data = []
    start_time = None

    while True:
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": 1000
        }

        if start_time:
            params["startTime"] = start_time

        response = requests.get(BASE_URL, params=params)
        data = response.json()

        if not isinstance(data, list) or len(data) == 0:
            break

        all_data.extend(data)

        print(f"Fetched {len(all_data)} rows...")

        # 次の取得開始時刻
        last_open_time = data[-1][0]
        start_time = last_open_time + 1

        # 1000未満なら終了
        if len(data) < 1000:
            break

        time.sleep(0.2)  # API制限対策

    if not all_data:
        print("No data.")
        return

    df = pd.DataFrame(all_data, columns=[
        "open_time",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "close_time",
        "qav",
        "num_trades",
        "taker_base_vol",
        "taker_quote_vol",
        "ignore"
    ])

    df = df[["open_time", "open", "high", "low", "close", "volume"]]

    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)

    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = df[col].astype(float)

    path = f"{RAW_DIR}/{symbol}_{interval}.csv"
    df.to_csv(path, index=False)

    print(f"[OK] Saved {path} ({len(df)} rows)")


def main():
    symbols = ["BTCUSDT", "ETHUSDT"]  # ← 最初はテスト用

    for symbol in symbols:
        for interval in ["1h", "1d", "1w"]:
            try:
                fetch_all_klines(symbol, interval)
            except Exception as e:
                print(f"[ERROR] {symbol} {interval}: {e}")


if __name__ == "__main__":
    main()
