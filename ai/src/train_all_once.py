# ai/src/train_all_once.py
"""
Train ALL eligible symbols in one run.
Intended to be executed once per day via cron.
"""

from datetime import datetime

from ai.src.market_cap import get_train_candidates
from ai.src.train_all_auto import train_symbol_all


def main():
    print("=" * 60)
    print("[TRAIN-ALL] start", datetime.utcnow().isoformat())
    print("=" * 60)

    # 件数制限なし（実質：Top200）
    symbols = get_train_candidates(max_per_night=10_000)

    print(f"[SELECT] {len(symbols)} symbols")
    if not symbols:
        print("[TRAIN-ALL] nothing to train")
        return

    trained = 0
    failed = 0

    for symbol in symbols:
        try:
            print(f"[TRAIN] {symbol}")
            train_symbol_all(symbol)
            trained += 1
        except Exception as e:
            print(f"[ERROR] {symbol}: {e}")
            failed += 1

    print("-" * 60)
    print(f"[TRAIN-ALL] done")
    print(f"  trained : {trained}")
    print(f"  failed  : {failed}")
    print(f"  total   : {len(symbols)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
