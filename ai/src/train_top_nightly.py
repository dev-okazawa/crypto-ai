# ai/src/train_top_nightly.py

import os
from datetime import datetime

from ai.src.market_cap import get_train_candidates
from ai.src.train_all_auto import train_symbol_all

MAX_PER_NIGHT = int(os.getenv("MAX_PER_NIGHT", 5))


def main():
    print("[NIGHTLY] start", datetime.utcnow().isoformat())

    symbols = get_train_candidates(MAX_PER_NIGHT)
    print(f"[SELECT] {symbols}")

    for symbol in symbols:
        try:
            print(f"[TRAIN] {symbol}")
            train_symbol_all(symbol)
        except Exception as e:
            print(f"[ERROR] {symbol}: {e}")

    print(f"[NIGHTLY] done: trained {len(symbols)} symbols")


if __name__ == "__main__":
    main()
