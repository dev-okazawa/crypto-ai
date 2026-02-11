import os
import pandas as pd
import requests

BINANCE_URL = "https://api.binance.com/api/v3/klines"

DATA_DIR = "ai/data/raw"
os.makedirs(DATA_DIR, exist_ok=True)

# interval → 取得本数
INTERVAL_LIMITS = {
    "1h": 1000,
    "1d": 1000,
}


def fetch_klines(symbol: str, interval: str, limit: int):
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit,
    }
    r = requests.get(BINANCE_URL, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()

    if not data:
        raise ValueError("No kline data returned")

    df = pd.DataFrame(
        data,
        columns=[
            "open_time", "open", "high", "low", "close", "volume",
            "close_time", "qav", "trades",
            "taker_base", "taker_quote", "ignore",
        ],
    )

    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    df["close"] = df["close"].astype(float)
    df["volume"] = df["volume"].astype(float)

    return df[["open_time", "close", "volume"]]


def fetch_symbol(symbol: str):
    """
    1通貨分の CSV を生成（存在すればスキップ）
    """
    print(f"[FETCH] {symbol}")

    for interval, limit in INTERVAL_LIMITS.items():
        path = f"{DATA_DIR}/{symbol}_{interval}.csv"

        if os.path.exists(path):
            continue

        df = fetch_klines(symbol, interval, limit)
        df.to_csv(path, index=False)
        print(f"[OK] saved {path}")
