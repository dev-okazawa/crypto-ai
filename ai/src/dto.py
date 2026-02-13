from pathlib import Path
from datetime import datetime, timezone
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "ai" / "data" / "raw"


def load_price_history(symbol: str, interval: str, points: int = 30):
    path = DATA_DIR / f"{symbol}_{interval}.csv"

    if not path.exists():
        raise FileNotFoundError(f"CSV not found: {path}")

    df = pd.read_csv(path)

    if df.empty:
        raise ValueError("Not enough price history")

    prices = df["close"].astype(float).tolist()

    if len(prices) < 2:
        raise ValueError("Not enough price history")

    return prices[-points:]


def build_candles_with_time(symbol: str, interval: str, points: int = 30):
    """
    CSVの open_time をそのまま使用し、
    実ローソク足時間と完全一致させる版
    """

    path = DATA_DIR / f"{symbol}_{interval}.csv"

    if not path.exists():
        raise FileNotFoundError(f"CSV not found: {path}")

    df = pd.read_csv(path)

    if df.empty:
        raise ValueError("CSV is empty")

    df = df.tail(points)

    candles = []

    for _, row in df.iterrows():
        # open_time は ISO UTC 文字列
        ts = int(pd.Timestamp(row["open_time"]).timestamp() * 1000)

        candles.append({
            "time": ts,
            "open": float(row["open"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
            "close": float(row["close"]),
            "volume": float(row["volume"]),
        })

    return candles


def build_prediction_dto(result: dict):

    history = load_price_history(
        result["symbol"],
        result["interval"]
    )

    current = result["current_price"]
    predicted = result["predicted_price"]

    # 最新価格は現在値で上書き
    history[-1] = current

    diff = predicted - current
    pct_change = round(diff / current * 100, 2)

    trend = (
        "UP" if diff > 0 else
        "DOWN" if diff < 0 else
        "FLAT"
    )

    current_price_at = result["current_price_at"]

    candles = build_candles_with_time(
        result["symbol"],
        result["interval"]
    )

    interval_map = {
        "1h": 3600000,
        "4h": 14400000,
        "1d": 86400000,
        "1w": 604800000,
    }

    step = interval_map.get(result["interval"], 3600000)

    last_time = candles[-1]["time"]
    future_time = last_time + step

    chart_data = {
        "candles": candles,
        "prediction": {
            "future": [{
                "time": future_time,
                "value": predicted,
            }]
        }
    }

    return {
        "symbol": result["symbol"],

        "prices": {
            "past": history,
            "future": [predicted],
        },

        "chart": chart_data,

        "trend": trend,
        "confidence": result["confidence"],

        "metrics": {
            "current": current,
            "predicted": predicted,
            "diff": diff,
            "pct_change": pct_change,
            "current_price_at": current_price_at,
        },

        "direction_internal": result.get("direction_internal"),

        "meta": {
            "interval": result["interval"],
            "horizon": result["horizon"],
            "generated_at": result["generated_at"],
        },
    }
