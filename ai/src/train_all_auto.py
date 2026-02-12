from pathlib import Path

from ai.src.train_price import train_price_model
from ai.src.train_direction import train_direction_model
from ai.src.market_cap import load_trained_symbols

# =====================
# Paths
# =====================

BASE_DIR = Path(__file__).resolve().parents[2]
AI_DIR = BASE_DIR / "ai"

STATE_DIR = AI_DIR / "state"
TRAINED_DIR = STATE_DIR / "trained"

TRAINED_DIR.mkdir(parents=True, exist_ok=True)

# =====================
# Config
# =====================

INTERVALS = ["1h", "1d", "1w"]
HORIZONS = [1]

# =====================
# Train
# =====================

def train_symbol_all(symbol: str):
    print(f"[TRAIN] {symbol}")

    # fetch は cron 側で実行される設計なのでここでは呼ばない

    for interval in INTERVALS:
        for h in HORIZONS:
            train_price_model(symbol, interval, h)
            train_direction_model(symbol, interval, h)

    trained_path = TRAINED_DIR / symbol
    trained_path.mkdir(exist_ok=True)

    print(f"[TRAINED] {symbol}")


# =====================
# Entry Point
# =====================

if __name__ == "__main__":
    symbols = sorted(load_trained_symbols())

    print(f"[AUTO TRAIN] symbols={len(symbols)}")

    for symbol in symbols:
        train_symbol_all(symbol)
