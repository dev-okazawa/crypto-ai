import json
from datetime import datetime, timezone

from ai.src.market_cap import get_supported
from ai.src.predict import predict

OUTPUT_TEMPLATE = "ai/data/cache/market_overview_{interval}.json"

HORIZON_MAP = {
    "1h": 1,
    "1d": 1,
    "1w": 1,
}


def build(interval):

    horizon = HORIZON_MAP[interval]
    symbols = get_supported(interval)

    results = []

    for c in symbols:
        symbol = c["symbol"] if isinstance(c, dict) else c

        try:
            data = predict(symbol, interval, horizon)

            diff = data["predicted_price"] - data["current_price"]
            pct = diff / data["current_price"] * 100

            results.append({
                "symbol": symbol,
                "current_price": data["current_price"],
                "predicted_price": data["predicted_price"],
                "pct_change": round(pct, 2),
                "direction": data["trend"],
                "confidence": float(data["confidence"]),
            })

        except Exception as e:
            print(f"[SKIP] {symbol}: {e}")
            continue

    results.sort(
        key=lambda x: abs(x["pct_change"]) * x["confidence"],
        reverse=True
    )

    payload = {
        "meta": {
            "interval": interval,
            "horizon": horizon,
            "count": len(results),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
        "items": [
            dict(rank=i + 1, **item)
            for i, item in enumerate(results)
        ]
    }

    path = OUTPUT_TEMPLATE.format(interval=interval)

    with open(path, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"[OK] saved {path} ({len(results)} items)")


if __name__ == "__main__":
    for interval in ["1h", "1d", "1w"]:
        build(interval)