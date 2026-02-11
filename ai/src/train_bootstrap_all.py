# 初回ブート用：全通貨を一度だけ学習する
# 途中で落ちても再実行可能

import time
from datetime import datetime

from ai.src.market_cap import load_coingecko_top
from ai.src.binance_symbols import load_binance_symbols
from ai.src.train_all_auto import train_symbol_all
from ai.src.market_cap import load_trained_symbols


MAX_TARGET = 200          # 上限（実質130〜160）
SLEEP_SEC = 5             # API / CPU 保護


def main():
    print("=" * 60)
    print("[BOOTSTRAP] start", datetime.utcnow().isoformat())
    print("=" * 60)

    coins = load_coingecko_top(200)
    binance = load_binance_symbols()
    trained = load_trained_symbols()

    targets = []

    for c in coins:
        symbol = f"{c['symbol'].upper()}USDT"

        if symbol not in binance:
            continue

        if symbol in trained:
            continue  # すでに学習済みはスキップ

        targets.append(symbol)

        if len(targets) >= MAX_TARGET:
            break

    print(f"[BOOTSTRAP] targets: {len(targets)}")

    for i, symbol in enumerate(targets, 1):
        print(f"[{i}/{len(targets)}] TRAIN {symbol}")

        try:
            train_symbol_all(symbol)
        except Exception as e:
            print(f"[ERROR] {symbol}: {e}")
            continue

        time.sleep(SLEEP_SEC)

    print("=" * 60)
    print("[BOOTSTRAP] done", datetime.utcnow().isoformat())
    print("=" * 60)


if __name__ == "__main__":
    main()

