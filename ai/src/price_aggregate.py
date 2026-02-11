import requests
import statistics


def aggregate_price(symbol: str):
    prices = []
    sources = []

    # Binance
    try:
        r = requests.get(
            "https://api.binance.com/api/v3/ticker/price",
            params={"symbol": symbol},
            timeout=5
        )
        r.raise_for_status()
        prices.append(float(r.json()["price"]))
        sources.append("Binance")
    except Exception:
        pass

    # Coinbase
    try:
        base = symbol.replace("USDT", "")
        r = requests.get(
            f"https://api.coinbase.com/v2/prices/{base}-USD/spot",
            timeout=5
        )
        r.raise_for_status()
        prices.append(float(r.json()["data"]["amount"]))
        sources.append("Coinbase")
    except Exception:
        pass

    # Kraken
    try:
        base = symbol.replace("USDT", "")
        r = requests.get(
            "https://api.kraken.com/0/public/Ticker",
            params={"pair": base + "USD"},
            timeout=5
        )
        r.raise_for_status()
        price = list(r.json()["result"].values())[0]["c"][0]
        prices.append(float(price))
        sources.append("Kraken")
    except Exception:
        pass

    # ---- SAFE fallback ----
    if not prices:
        return 0.0, []

    return statistics.median(prices), sources
