import sys

from ai.src.train_price import train_price_model
from ai.src.train_direction import train_direction_model
from ai.src.market_cap import get_supported

INTERVALS = ["1h", "1d", "1w"]
DEFAULT_HORIZON = 1


def train_symbol_all(symbol: str, horizons):
    print(f"[TRAIN] {symbol}")

    for interval in INTERVALS:
        for h in horizons:
            print(f"  -> interval={interval} horizon={h}")
            train_price_model(symbol, interval, h)
            train_direction_model(symbol, interval, h)

    print(f"[TRAINED] {symbol}")


if __name__ == "__main__":

    if len(sys.argv) > 1:
        horizons = [int(sys.argv[1])]
    else:
        horizons = [DEFAULT_HORIZON]

    # 🔥 ここが最重要
    symbols_data = get_supported("1h")
    symbols = [s["symbol"] for s in symbols_data]

    print(f"[AUTO TRAIN] symbols={len(symbols)} horizons={horizons}")

    for symbol in symbols:
        train_symbol_all(symbol, horizons)