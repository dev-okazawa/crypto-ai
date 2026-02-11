import os
import time
import requests
import pandas as pd

RAW_DIR = "ai/data/raw"
BASE_URL = "https://api.binance.com/api/v3/klines"
EXCHANGE_INFO_URL = "https://api.binance.com/api/v3/exchangeInfo"

os.makedirs(RAW_DIR, exist_ok=True)


def get_all_usdt_symbols():
    response = requests.get(EXCHANGE_INFO_URL)
    data = response.json()

    symbols = []
    for s in data["symbols"]:
        if s["quoteAsset"] == "USDT" and s["status"] == "TRADING":
            symbols.append(s["symbol"])

    print(f"Found {len(symbols)} USDT trading pairs")
    return symbols


def fetch_weekly(symbol: str):
    params = {
        "symbol": symbol,
        "interval": "1w",
        "limit": 1000
    }

    response = requests.get(BASE_URL, params=params)
    data = response.json()

    if not isinstance(data, list) or len(data) == 0:
        print(f"[SKIP] {symbol} no weekly data")
        return

    df = pd.DataFrame(data, columns=[
        "open_time","open","high","low","close","volume",
        "close_time","qav","num_trades",
        "taker_base_vol","taker_quote_vol","ignore"
    ])

    df = df[["open_time","open","high","low","close","volume"]]
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)

    for col in ["open","high","low","close","volume"]:
        df[col] = df[col].astype(float)

    path = f"{RAW_DIR}/{symbol}_1w.csv"
    df.to_csv(path, index=False)

    print(f"[OK] {symbol} 1w → {len(df)} rows")


def main():
    symbols = get_all_usdt_symbols()

    for symbol in symbols:
        try:
            fetch_weekly(symbol)
            time.sleep(0.1)  # API負荷軽減
        except Exception as e:
            print(f"[ERROR] {symbol}: {e}")

    print("\nWeekly fetch completed.")


if __name__ == "__main__":
    main()
