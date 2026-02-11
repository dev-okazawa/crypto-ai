import os
import joblib
import pandas as pd

from sklearn.ensemble import RandomForestRegressor

from ai.src.features import make_features, make_price_target

RAW_DIR = "ai/data/raw"
MODEL_DIR = "ai/models"

os.makedirs(MODEL_DIR, exist_ok=True)

FEATURE_COLS = [
    "return",
    "ma_5",
    "ma_20",
    "volatility",
    "volume_ma"
]


def train_price_model(symbol: str, interval: str, horizon: int = 1):
    path = f"{RAW_DIR}/{symbol}_{interval}.csv"
    if not os.path.exists(path):
        print(f"[SKIP] {path} not found")
        return

    df = pd.read_csv(path)

    # ① features
    df_feat = make_features(df)

    # ② target（同じ df_feat に追加）
    df_feat["target"] = make_price_target(df_feat, horizon=horizon)

    # ③ 欠損をまとめて削除
    df_feat = df_feat.dropna()

    X = df_feat[FEATURE_COLS]
    y = df_feat["target"]

    # =========================
    # 🔥 週足用に最小本数を分岐
    # =========================
    if interval == "1w":
        min_required = 80
    else:
        min_required = 200

    if len(X) < min_required:
        print(f"[SKIP] {symbol} {interval} h={horizon} (data too small: {len(X)})")
        return

    model = RandomForestRegressor(
        n_estimators=300,
        max_depth=6,
        random_state=42,
        n_jobs=-1
    )

    model.fit(X, y)

    model_path = f"{MODEL_DIR}/{symbol}_{interval}_price_h{horizon}.pkl"
    joblib.dump(model, model_path)

    print(f"[OK] saved {model_path}")
