import requests


def get_aggregated_price(symbol: str):
    """
    Get current price from multiple exchanges and return the average price.

    Returns:
        price (float)
        sources (list[str])
    """

    prices = []
    sources = []

    # --------------------
    # Binance
    # --------------------
    try:
        r = requests.get(
            "https://api.binance.com/api/v3/ticker/price",
            params={"symbol": symbol},
            timeout=5
        )
        r.raise_for_status()
        data = r.json()
        prices.append(float(data["price"]))
        sources.append("Binance")
    except Exception:
        pass

    # --------------------
    # Coinbase
    # --------------------
    try:
        base = symbol.replace("USDT", "")
        r = requests.get(
            f"https://api.coinbase.com/v2/prices/{base}-USD/spot",
            timeout=5
        )
        r.raise_for_status()
        data = r.json()
        prices.append(float(data["data"]["amount"]))
        sources.append("Coinbase")
    except Exception:
        pass

    # --------------------
    # Kraken
    # --------------------
    try:
        base = symbol.replace("USDT", "")
        pair = base + "USD"
        r = requests.get(
            "https://api.kraken.com/0/public/Ticker",
            params={"pair": pair},
            timeout=5
        )
        r.raise_for_status()
        data = r.json()
        price = list(data["result"].values())[0]["c"][0]
        prices.append(float(price))
        sources.append("Kraken")
    except Exception:
        pass

    # --------------------
    # Validation
    # --------------------
    if not prices:
        raise RuntimeError("Failed to fetch price from all exchanges")

    avg_price = sum(prices) / len(prices)
    return avg_price, sources


# --------------------
# Local test
# --------------------
if __name__ == "__main__":
    price, src = get_aggregated_price("BTCUSDT")
    print("Price:", price)
    print("Sources:", src)
