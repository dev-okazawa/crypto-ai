import os
import joblib
import pandas as pd
from datetime import datetime

from ai.src.features import make_features

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "ai", "data", "raw")
MODEL_DIR = os.path.join(BASE_DIR, "ai", "models")


def load_csv(symbol, interval):
    path = f"{DATA_DIR}/{symbol}_{interval}.csv"
    if not os.path.exists(path):
        raise FileNotFoundError(f"CSV not found: {path}")
    return pd.read_csv(path)


def load_model(symbol, interval, kind, horizon):
    path = f"{MODEL_DIR}/{symbol}_{interval}_{kind}_h{horizon}.pkl"
    if not os.path.exists(path):
        raise FileNotFoundError(f"Model not found: {path}")
    return joblib.load(path)


def predict(symbol: str, interval: str, horizon: int):

    df = load_csv(symbol, interval)

    # === feature生成（trainと完全一致）
    df_feat = make_features(df)

    if len(df_feat) <= horizon:
        raise ValueError("Not enough data")

    current_price = float(df_feat["close"].iloc[-1])

    raw_time = df_feat["open_time"].iloc[-1]
    dt = pd.to_datetime(raw_time, utc=True)
    current_price_at = dt.strftime("%Y-%m-%d %H:%M")

    # 🔥 trainと同じ列抽出ロジック
    feature_cols = [
        col for col in df_feat.columns
        if col not in ["open_time"]
    ]

    X_all = df_feat[feature_cols]
    X = X_all.iloc[:-horizon]

    price_model = load_model(symbol, interval, "price", horizon)
    direction_model = load_model(symbol, interval, "direction", horizon)

    X_last = X.tail(1)

    predicted_price = float(price_model.predict(X_last)[0])

    direction_raw = int(direction_model.predict(X_last)[0])
    direction_internal = (
        "UP" if direction_raw == 1
        else "DOWN" if direction_raw == -1
        else "FLAT"
    )

    diff = predicted_price - current_price
    pct_change = diff / current_price * 100

    trend = (
        "UP" if diff > 0
        else "DOWN" if diff < 0
        else "FLAT"
    )

    diff_pct = abs(diff) / current_price
    confidence = max(10, min(95, int((1 - diff_pct) * 100)))

    return {
        "status": "ok",
        "symbol": symbol,
        "interval": interval,
        "horizon": horizon,
        "current_price": current_price,
        "predicted_price": predicted_price,
        "current_price_at": current_price_at,
        "diff": diff,
        "pct_change": round(pct_change, 2),
        "trend": trend,
        "direction_internal": direction_internal,
        "confidence": confidence,
        "generated_at": datetime.utcnow().isoformat(),
    }
