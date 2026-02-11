# ai/src/cache_coingecko.py
import json
import requests
from datetime import datetime, timezone
from pathlib import Path

OUTPUT = Path("ai/data/coingecko_top.json")

def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    r = requests.get(
        "https://api.coingecko.com/api/v3/coins/markets",
        params={
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": 200,
            "page": 1,
        },
        timeout=15,
    )
    r.raise_for_status()

    payload = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "items": r.json(),
    }

    with open(OUTPUT, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"[OK] cached CoinGecko top coins -> {OUTPUT}")

if __name__ == "__main__":
    main()

