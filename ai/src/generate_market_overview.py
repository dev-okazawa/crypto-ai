import json
from datetime import datetime, timezone

from ai.src.market_cap import get_supported
from ai.src.predict import predict

OUTPUT_PATH = "ai/data/market_overview.json"

INTERVAL = "1d"
HORIZON = 7


def main():
    symbols = get_supported(INTERVAL)

    results = []

    for c in symbols:
        symbol = c["symbol"] if isinstance(c, dict) else c

        try:
            data = predict(symbol, INTERVAL, HORIZON)

            diff = data["predicted_price"] - data["current_price"]
            pct = diff / data["current_price"] * 100

            results.append({
                "symbol": symbol,
                "current_price": data["current_price"],
                "predicted_price": data["predicted_price"],
                "pct_change": round(pct, 2),
                "direction": data["direction"],
                "confidence": data["confidence"],
            })

        except Exception as e:
            # ★ ここで理由を出す
            print(f"[SKIP] {symbol}: {e}")
            continue

    # トレンド強度順（全件）
    results.sort(
        key=lambda x: abs(x["pct_change"]) * x["confidence"],
        reverse=True
    )

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "interval": INTERVAL,
        "horizon": HORIZON,
        "items": [
            dict(rank=i + 1, **item)
            for i, item in enumerate(results)
        ]
    }

    with open(OUTPUT_PATH, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"[OK] saved {OUTPUT_PATH} ({len(results)} items)")


if __name__ == "__main__":
    main()
