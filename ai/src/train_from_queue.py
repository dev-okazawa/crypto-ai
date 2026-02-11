from ai.src.train_queue import pop_next, mark_done
from ai.src.fetch_data import fetch_klines
from ai.src.train_price import train_price_model
from ai.src.train_direction import train_direction_model
import os

RAW_DIR = "ai/data/raw"

def ensure_csv(symbol, interval):
    path = f"{RAW_DIR}/{symbol}_{interval}.csv"
    if os.path.exists(path):
        return
    df = fetch_klines(symbol, interval, 1000)
    df.to_csv(path, index=False)


def main():
    while True:
        item = pop_next()
        if not item:
            break

        symbol = item["symbol"]
        interval = item["interval"]
        h = item["horizon"]

        ensure_csv(symbol, interval)
        train_price_model(symbol, interval, h)
        train_direction_model(symbol, interval, h)

        mark_done(item)


if __name__ == "__main__":
    main()
