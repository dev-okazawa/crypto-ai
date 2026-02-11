import os
import joblib
import pandas as pd

from sklearn.ensemble import GradientBoostingClassifier

from ai.src.features import make_features, make_direction_target

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


def train_direction_model(symbol: str, interval: str, horizon: int = 1):
    path = f"{RAW_DIR}/{symbol}_{interval}.csv"
    if not os.path.exists(path):
        print(f"[SKIP] {path} not found")
        return

    df = pd.read_csv(path)

    df_feat = make_features(df)
    df_feat["target"] = make_direction_target(df_feat, horizon=horizon)

    df_feat = df_feat.dropna()

    X = df_feat[FEATURE_COLS]
    y = df_feat["target"]

    # =========================
    # 🔥 最小データ数を足種で分岐
    # =========================
    if interval == "1w":
        min_required = 80
    else:
        min_required = 200

    if len(X) < min_required:
        print(f"[SKIP] {symbol} {interval} h={horizon} (data too small: {len(X)})")
        return

    # =========================
    # 🔥 クラス数チェック（超重要）
    # =========================
    if len(set(y)) < 2:
        print(f"[SKIP] {symbol} {interval} h={horizon} (only one class)")
        return

    model = GradientBoostingClassifier(
        n_estimators=200,
        learning_rate=0.05,
        max_depth=3,
        random_state=42
    )

    model.fit(X, y)

    model_path = f"{MODEL_DIR}/{symbol}_{interval}_direction_h{horizon}.pkl"
    joblib.dump(model, model_path)

    print(f"[OK] saved {model_path}")
