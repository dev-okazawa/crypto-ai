import sys

from ai.src.train_price import train_price_model
from ai.src.train_direction import train_direction_model
from ai.src.market_cap import get_supported

# 時間軸の定義
INTERVALS = ["1h", "1d", "1w"]
DEFAULT_HORIZON = 1


def train_symbol_by_interval(symbol: str, interval: str, horizons: list):
    """
    特定の銘柄と時間軸に対して、指定された全ホライゾンの学習を実行する
    """
    for h in horizons:
        print(f"  -> {symbol} | interval={interval} | horizon={h}")
        try:
            train_price_model(symbol, interval, h)
            train_direction_model(symbol, interval, h)
        except Exception as e:
            print(f"    [ERROR] {symbol}_{interval} training failed: {e}")


if __name__ == "__main__":

    # コマンドライン引数から予測ホライゾンを取得
    if len(sys.argv) > 1:
        try:
            horizons = [int(sys.argv[1])]
        except ValueError:
            print("[ERROR] Horizon must be an integer.")
            sys.exit(1)
    else:
        horizons = [DEFAULT_HORIZON]

    print(f"🚀 Starting Auto Training Pipeline (Horizons: {horizons})")

    # 修正のポイント: インターバルを外側のループにする
    for interval in INTERVALS:
        print(f"\n--- Processing Interval: {interval} ---")
        
        # 各インターバルごとに、その時間軸でサポートされている銘柄リストを動的に取得
        # これにより 1h のリストに含まれない銘柄も 1w で救済される
        symbols_data = get_supported(interval)
        symbols = [s["symbol"] for s in symbols_data]
        
        print(f"[FETCHED] {len(symbols)} symbols for {interval}")

        for symbol in symbols:
            train_symbol_by_interval(symbol, interval, horizons)

    print("\n" + "="*50)
    print("🏁 [COMPLETED] All intervals processed.")
    print("="*50)