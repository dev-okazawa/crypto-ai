from datetime import datetime
from ai.src.market_cap import get_supported
from ai.src.fetch_data import fetch_klines
from ai.src.train_price import train_price_model
from ai.src.train_direction import train_direction_model
import os

RAW_DIR = "ai/data/raw"

INTERVALS = {
    "1h": 1000,
    "1d": 1000,
}

HORIZONS = [1, 7]


def ensure_csv(symbol, interval, limit):
    path = f"{RAW_DIR}/{symbol}_{interval}.csv"
    if os.path.exists(path):
        return
    df = fetch_klines(symbol, interval, limit)
    df.to_csv(path, index=False)
    print(f"[FETCH] {path}")


def main():
    print("=" * 60)
    print("[NIGHTLY] Top20 training start:", datetime.now())
    print("=" * 60)

    # Top20（未学習含む）
    coins = get_supported("1h")[:20]

    for c in coins:
        symbol = c["symbol"]
        for interval, limit in INTERVALS.items():
            ensure_csv(symbol, interval, limit)

            for h in HORIZONS:
                print(f"[TRAIN] {symbol} {interval} h={h}")
                train_price_model(symbol, interval, h)
                train_direction_model(symbol, interval, h)

    print("[NIGHTLY] done")


if __name__ == "__main__":
    main()
