import json
import sys
from pathlib import Path
from ai.src.predict import predict

TOP300_PATH = Path("ai/data/top300_usdt.json")

TIMEFRAME = "1h"
DEFAULT_HORIZON = 1


def load_symbols(limit=200):

    if not TOP300_PATH.exists():
        raise FileNotFoundError(
            "top300_usdt.json not found. Run get_top300_symbols first."
        )

    symbols = json.loads(TOP300_PATH.read_text())
    return symbols[:limit]


def run_all(horizon):

    symbols = load_symbols(limit=200)

    print(f"[PREDICT ALL] symbols={len(symbols)} horizon={horizon}")

    for symbol in symbols:
        try:
            result = predict(symbol, TIMEFRAME, horizon)
            print(f"OK: {symbol} confidence={result['confidence']}")
        except Exception as e:
            print(f"SKIP: {symbol} {e}")


if __name__ == "__main__":

    # 🔥 シェル引数対応
    if len(sys.argv) > 1:
        horizon = int(sys.argv[1])
    else:
        horizon = DEFAULT_HORIZON

    run_all(horizon)
