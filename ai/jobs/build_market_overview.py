import json
from pathlib import Path
from datetime import datetime, timezone

from ai.src.predict import predict
from ai.src.market_cap import get_top100_with_status
from ai.src.dto import build_prediction_dto


BASE_DIR = Path(__file__).resolve().parent.parent
CACHE_PATH = BASE_DIR / "data" / "cache" / "market_overview.json"

INTERVAL = "1h"
HORIZON = 1
LIMIT = 10


def build_cache():
    items = []

    coins = get_top100_with_status(INTERVAL)

    for coin in coins:
        if coin["status"] != "trained":
            continue

        try:
            result = predict(coin["symbol"], INTERVAL, HORIZON)
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

    # pct_change でソート（dtoの中にある）
    items.sort(
        key=lambda x: x["data"]["metrics"]["pct_change"],
        reverse=True
    )

    items = items[:LIMIT]

    # rank付与
    for i, item in enumerate(items, start=1):
        item["rank"] = i

    data = {
        "meta": {
            "interval": INTERVAL,
            "horizon": HORIZON,
            "count": len(items),
            "sort": "pct_change_desc",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
        "items": items,
    }

    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2)
    )

    print("Market overview cache updated")


if __name__ == "__main__":
    build_cache()
