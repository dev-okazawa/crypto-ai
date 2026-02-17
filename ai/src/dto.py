from pathlib import Path
from datetime import datetime, timezone
import pandas as pd
from ai.src.repository.db import get_connection

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "ai" / "data" / "raw"

def get_actual_performance(symbol: str, interval: str):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    
    try:
        # カラム指定をせず * で取得し、コード側で安全に処理する
        cur.execute("""
            SELECT *
            FROM predictions
            WHERE symbol = %s AND timeframe = %s AND evaluated = TRUE 
            ORDER BY id DESC
        """, (symbol, interval))
        
        rows = cur.fetchall()
        if not rows:
            return 0.0, 0, 0.0

        hits = 0
        total_mae_pct = 0.0
        count = len(rows)

        for row in rows:
            pred = float(row.get('predicted_price') or 0)
            actual = float(row.get('actual_price') or 0)
            
            # 優先順位をつけて基準価格を取得 (current_priceがない対策)
            base = float(row.get('current_price') or row.get('initial_price') or actual)

            # 方向判定
            if (pred - base) * (actual - base) >= 0:
                hits += 1
            
            # MAE算出
            if actual > 0:
                total_mae_pct += (abs(pred - actual) / actual) * 100
        
        accuracy = round((hits / count) * 100, 2)
        avg_mae = round(total_mae_pct / count, 2)

        return accuracy, count, avg_mae
    except Exception as e:
        print(f"DTO Logic Error for {symbol}: {e}")
        return 0.0, 0, 0.0
    finally:
        cur.close()
        conn.close()

# --- 以下の関数は変更なし ---
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
    path = DATA_DIR / f"{symbol}_{interval}.csv"
    if not path.exists():
        raise FileNotFoundError(f"CSV not found: {path}")
    df = pd.read_csv(path)
    if df.empty:
        raise ValueError("CSV is empty")
    df = df.tail(points)
    candles = []
    for _, row in df.iterrows():
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
    history = load_price_history(result["symbol"], result["interval"])
    current = result["current_price"]
    predicted = result["predicted_price"]
    history[-1] = current

    diff = predicted - current
    pct_change = round(diff / current * 100, 2)
    trend = "UP" if diff > 0 else "DOWN" if diff < 0 else "FLAT"

    current_price_at = result["current_price_at"]
    candles = build_candles_with_time(result["symbol"], result["interval"])

    interval_map = {"1h": 3600000, "4h": 14400000, "1d": 86400000, "1w": 604800000}
    step = interval_map.get(result["interval"], 3600000)
    last_time = candles[-1]["time"]
    future_time = last_time + step

    chart_data = {
        "candles": candles,
        "prediction": {
            "future": [{"time": future_time, "value": predicted}]
        }
    }

    accuracy, count, mae = get_actual_performance(result["symbol"], result["interval"])

    return {
        "symbol": result["symbol"],
        "prices": {"past": history, "future": [predicted]},
        "chart": chart_data,
        "trend": trend,
        "confidence": result["confidence"],
        "metrics": {
            "current": current,
            "predicted": predicted,
            "diff": diff,
            "pct_change": pct_change,
            "current_price_at": current_price_at,
            "accuracy": accuracy,
            "count": count,
            "mae": mae,
        },
        "direction_internal": result.get("direction_internal"),
        "meta": {
            "interval": result["interval"],
            "horizon": result["horizon"],
            "generated_at": result["generated_at"],
        },
    }