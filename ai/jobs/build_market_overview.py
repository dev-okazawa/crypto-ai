import json
from pathlib import Path
from datetime import datetime, timezone

from ai.src.predict import predict
from ai.src.market_cap import get_top100_with_status
from ai.src.dto import build_prediction_dto


BASE_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = BASE_DIR / "data" / "cache"

INTERVALS = ["1h", "1d", "1w"]
HORIZON = 1


def build_cache(interval: str):

    print(f"Building market overview cache ({interval})...")

    items = []

    coins = get_top100_with_status(interval)

    for coin in coins:

        if coin.get("status") != "trained":
            continue

        try:
            result = predict(coin["symbol"], interval, HORIZON)

            if result.get("status") != "ok":
                continue

            dto = build_prediction_dto(result)

            wrapped = {
                "meta": {
                    "symbol": dto["symbol"],
                    "interval": dto["meta"]["interval"],
                    "timezone": "UTC",
                    "last_update": int(
                        datetime.now(timezone.utc).timestamp() * 1000
                    ),
                },
                "data": dto,
            }

            items.append(wrapped)

        except Exception as e:
            print("Skip:", coin["symbol"], e)
            continue

    # pct_change でソート
    items.sort(
        key=lambda x: x["data"]["metrics"]["pct_change"],
        reverse=True
    )

    # rank付与（全件）
    for i, item in enumerate(items, start=1):
        item["rank"] = i

    data = {
        "meta": {
            "interval": interval,
            "horizon": HORIZON,
            "count": len(items),
            "sort": "pct_change_desc",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
        "items": items,
    }

    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    output_path = CACHE_DIR / f"market_overview_{interval}.json"

    output_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2)
    )

    print(f"Market overview cache updated ({interval})")


if __name__ == "__main__":

    for interval in INTERVALS:
        build_cache(interval)
