import os
import joblib
import pandas as pd
from datetime import datetime

from ai.src.features import make_features

DATA_DIR = "ai/data/raw"
MODEL_DIR = "ai/models"

FEATURE_COLS = [
    "return",
    "ma_5",
    "ma_20",
    "volatility",
    "volume_ma"
]


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
    # =====================
    # Load CSV & features
    # =====================
    df = load_csv(symbol, interval)
    df_feat = make_features(df)

    if len(df_feat) <= horizon:
        raise ValueError("Not enough data")

    # ★ CSV 最終行 = モデル基準価格
    current_price = float(df_feat["close"].iloc[-1])

    # ★ CSV 最終行の時刻（UTC / 分まで）
    raw_time = df_feat["open_time"].iloc[-1]

    if isinstance(raw_time, str):
        dt = pd.to_datetime(raw_time, utc=True)
    else:
        dt = raw_time

    current_price_at = dt.strftime("%Y-%m-%d %H:%M")

    X = df_feat[FEATURE_COLS].iloc[:-horizon]

    # =====================
    # Load models
    # =====================
    price_model = load_model(symbol, interval, "price", horizon)
    direction_model = load_model(symbol, interval, "direction", horizon)

    # =====================
    # Predict
    # =====================
    predicted_price = float(price_model.predict(X.tail(1))[0])

    direction_raw = int(direction_model.predict(X.tail(1))[0])
    direction_internal = (
        "UP" if direction_raw == 1
        else "DOWN" if direction_raw == -1
        else "FLAT"
    )

    # =====================
    # 差分（UIの唯一の真実）
    # =====================
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

        # ★ UIが信じる価格
        "current_price": current_price,
        "predicted_price": predicted_price,

        # ★ 表示用（UTC / 分まで）
        "current_price_at": current_price_at,

        "diff": diff,
        "pct_change": round(pct_change, 2),
        "trend": trend,

        # 内部参考
        "direction_internal": direction_internal,

        "confidence": confidence,

        # 推論実行時刻（UIには使わない）
        "generated_at": datetime.utcnow().isoformat(),
    }
