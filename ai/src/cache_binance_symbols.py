# ai/src/cache_binance_symbols.py

import json
import requests
from pathlib import Path

OUTPUT = Path("ai/data/binance_symbols.json")
BINANCE_EXCHANGE_INFO = "https://api.binance.com/api/v3/exchangeInfo"


def main():
    print("[BINANCE] fetching exchangeInfo")

    r = requests.get(BINANCE_EXCHANGE_INFO, timeout=30)
    r.raise_for_status()

    data = r.json()

    symbols = [
        s["symbol"]
        for s in data["symbols"]
        if s["status"] == "TRADING"
        and s["quoteAsset"] == "USDT"
        and s["symbol"].endswith("USDT")
    ]

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(
            {
                "count": len(symbols),
                "symbols": symbols,
            },
            indent=2,
        )
    )

    print(f"[BINANCE] cached {len(symbols)} USDT symbols")
    print(f"[BINANCE] output => {OUTPUT}")


if __name__ == "__main__":
    main()
