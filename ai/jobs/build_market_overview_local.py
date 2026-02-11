import json
from pathlib import Path
from datetime import datetime

# === ローカル専用設定 ===
BASE_DIR = Path(__file__).resolve().parent.parent.parent
CACHE_DIR = BASE_DIR / "cache"
OUT_PATH = CACHE_DIR / "market_overview.json"

# UI が期待する最小構造を作る
def dummy_item(symbol, rank, current, predicted):
    pct_change = ((predicted - current) / current) * 100

    return {
        "symbol": symbol,
        "prices": {
            "past": [
                round(current * 0.98, 4),
                round(current * 0.99, 4),
                round(current, 4),
            ],
            "future": [round(predicted, 4)],
        },
        "direction": "UP" if predicted > current else "DOWN",
        "confidence": 90,
        "metrics": {
            "current": current,
            "predicted": predicted,
            "pct_change": round(pct_change, 2),
        },
        "rank": rank,
    }

def main():
    items = [
        dummy_item("BTCUSDT", 1, 43000, 43500),
        dummy_item("ETHUSDT", 2, 2300, 2380),
        dummy_item("SOLUSDT", 3, 98, 104),
    ]

    data = {
        "items": items,
        "meta": {
            "interval": "1h",
            "horizon": 1,
            "count": len(items),
            "generated_at": datetime.utcnow().isoformat(),
            "source": "local_dummy",
        },
    }

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(data, indent=2))
    print(f"[OK] market overview generated at: {OUT_PATH}")

if __name__ == "__main__":
    main()

