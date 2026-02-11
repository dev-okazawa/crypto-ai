import requests
import json
from pathlib import Path

OUTPUT_PATH = Path("ai/data/top300_usdt.json")
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

BINANCE_TICKER_URL = "https://api.binance.com/api/v3/ticker/24hr"


def fetch_all_tickers():
    print("Fetching 24h ticker data from Binance...")
    res = requests.get(BINANCE_TICKER_URL, timeout=30)
    res.raise_for_status()
    return res.json()


def filter_usdt_pairs(tickers):
    usdt = []
    for t in tickers:
        symbol = t["symbol"]
        if symbol.endswith("USDT"):
            try:
                quote_volume = float(t["quoteVolume"])
            except:
                quote_volume = 0.0

            usdt.append({
                "symbol": symbol,
                "quoteVolume": quote_volume
            })

    return usdt


def main():
    tickers = fetch_all_tickers()

    usdt_pairs = filter_usdt_pairs(tickers)

    print(f"Found {len(usdt_pairs)} USDT pairs")

    # 24h出来高順にソート
    usdt_sorted = sorted(
        usdt_pairs,
        key=lambda x: x["quoteVolume"],
        reverse=True
    )

    top300 = usdt_sorted[:300]

    symbols_only = [x["symbol"] for x in top300]

    OUTPUT_PATH.write_text(json.dumps(symbols_only, indent=2))

    print(f"[OK] Saved top 300 symbols → {OUTPUT_PATH}")
    print(f"Top 10 preview: {symbols_only[:10]}")


if __name__ == "__main__":
    main()
