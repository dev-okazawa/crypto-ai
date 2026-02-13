"""
Cron / CLI entry point for daily full training.

Design:
- No trained / untrained distinction
- Always retrain ALL symbols
- Models are overwritten every run
"""

from pathlib import Path
from datetime import datetime

from ai.src.train_all_auto import train_symbol_all

# =====================
# Paths
# =====================

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "ai" / "data" / "raw"

# =====================
# Helpers
# =====================

def load_all_symbols():
    """
    学習対象の定義：
    ai/data/raw に CSV が存在する通貨
    （fetch が成功している = 学習可能）
    """
    symbols = set()

    for p in DATA_DIR.glob("*_1h.csv"):
        # 例: BTCUSDT_1h.csv → BTCUSDT
        symbol = p.name.split("_")[0]
        symbols.add(symbol)

    return sorted(symbols)

# =====================
# Main
# =====================

def main():
    print("=" * 60)
    print("[TRAIN-ALL] start", datetime.utcnow().isoformat())
    print("=" * 60)

    symbols = load_all_symbols()
    print(f"[SELECT] {len(symbols)} symbols")

    if not symbols:
        print("[TRAIN-ALL] no symbols found")
        return

    for symbol in symbols:
        try:
            print(f"[TRAIN] {symbol}")
            train_symbol_all(symbol)
        except Exception as e:
            print(f"[ERROR] {symbol}: {e}")

    print("=" * 60)
    print("[TRAIN-ALL] done", datetime.utcnow().isoformat())
    print("=" * 60)

if __name__ == "__main__":
    main()
