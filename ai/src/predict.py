import os
import joblib
import pandas as pd
from datetime import datetime
import traceback

from ai.src.features import make_features
from ai.src.repository.prediction_repository import insert_prediction


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "ai", "data", "raw")
MODEL_DIR = os.path.join(BASE_DIR, "ai", "models")


# ==========================
# Loaders
# ==========================

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


# ==========================
# Predict
# ==========================

def predict(symbol: str, interval: str, horizon: int):

    # --------------------------
    # CSVロード
    # --------------------------
    df = load_csv(symbol, interval)
    df_feat = make_features(df)

    if len(df_feat) <= horizon:
        raise ValueError("Not enough data")

    current_price = float(df_feat["close"].iloc[-1])

    # --------------------------
    # open_time → ms変換
    # --------------------------
    raw_time = df_feat["open_time"].iloc[-1]

    if isinstance(raw_time, (int, float)):
        predict_time = int(raw_time)
    else:
        predict_time = int(pd.Timestamp(raw_time).timestamp() * 1000)

    dt = pd.to_datetime(predict_time, unit="ms", utc=True)
    current_price_at = dt.strftime("%Y-%m-%d %H:%M")

    # --------------------------
    # 特徴量抽出
    # --------------------------
    feature_cols = [col for col in df_feat.columns if col != "open_time"]

    X_all = df_feat[feature_cols]

    # horizon分未来を除外
    X = X_all.iloc[:-horizon]

    if X.empty:
        raise ValueError("Feature set empty after horizon slice")

    X_last = X.tail(1)

    # --------------------------
    # モデルロード
    # --------------------------
    price_model = load_model(symbol, interval, "price", horizon)
    direction_model = load_model(symbol, interval, "direction", horizon)

    # 🔥 学習時カラム順に合わせる（超重要）
    if hasattr(price_model, "feature_names_in_"):
        X_last = X_last[price_model.feature_names_in_]

    # --------------------------
    # 価格予測
    # --------------------------
    predicted_price = float(price_model.predict(X_last)[0])

    if current_price == 0:
        diff = 0.0
        pct_change = 0.0
    else:
        diff = predicted_price - current_price
        pct_change = (diff / current_price) * 100

    # --------------------------
    # 確率ベースConfidence
    # --------------------------
    try:
        proba = direction_model.predict_proba(X_last)[0]
        classes = direction_model.classes_
        class_prob = dict(zip(classes, proba))

        prob_up = class_prob.get(1, 0.0)
        prob_down = class_prob.get(-1, 0.0)

        if prob_up >= prob_down:
            direction_internal = "UP"
            confidence = round(prob_up * 100, 2)
        else:
            direction_internal = "DOWN"
            confidence = round(prob_down * 100, 2)

    except Exception:
        direction_internal = "FLAT"
        confidence = 50.0

    trend = direction_internal

    # --------------------------
    # DB保存（失敗しても止めない）
    # --------------------------
    try:
        insert_prediction(
            symbol=symbol,
            timeframe=interval,
            horizon=horizon,
            base_price=current_price,
            predicted_price=predicted_price,
            predict_time=predict_time,
            confidence=confidence,
            model_version="v2_prob"
        )
    except Exception:
        print(f"[WARN] DB insert failed: {symbol}")
        print(traceback.format_exc())

    # --------------------------
    # Return
    # --------------------------
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