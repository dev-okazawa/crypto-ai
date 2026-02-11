import os
from pathlib import Path
import joblib
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report

from ai.src.features import make_features, make_direction_target


# =====================
# Paths
# =====================

BASE_DIR = Path(__file__).resolve().parent.parent.parent
RAW_DIR = BASE_DIR / "ai" / "data" / "raw"
MODEL_DIR = BASE_DIR / "ai" / "models"

os.makedirs(MODEL_DIR, exist_ok=True)


# =====================
# Train One
# =====================

def train_direction_model(symbol: str, interval: str, horizon: int = 1):

    path = RAW_DIR / f"{symbol}_{interval}.csv"

    if not path.exists():
        print(f"[SKIP] {symbol} {interval} (CSV not found)")
        return

    df = pd.read_csv(path)

    # === features ===
    df_feat = make_features(df)

    # === target ===
    df_feat["target"] = make_direction_target(df_feat, horizon=horizon)

    df_feat = df_feat.dropna()

    # 最低本数チェック
    if len(df_feat) < 150:
        print(f"[SKIP] {symbol} {interval} (data too small: {len(df_feat)})")
        return

    feature_cols = [
        col for col in df_feat.columns
        if col not in ["target", "open_time"]
    ]

    X = df_feat[feature_cols]
    y = df_feat["target"]

    # クラスが1種類しかない場合は学習不可
    if len(y.unique()) < 2:
        print(f"[SKIP] {symbol} {interval} (only one class)")
        return

    model = RandomForestClassifier(
        n_estimators=300,
        max_depth=6,
        random_state=42,
        n_jobs=-1
    )

    model.fit(X, y)

    model_path = MODEL_DIR / f"{symbol}_{interval}_direction_h{horizon}.pkl"
    joblib.dump(model, model_path)

    print(f"[OK] saved {model_path.name}")


# =====================
# Train All
# =====================

def main():

    files = [f for f in os.listdir(RAW_DIR) if f.endswith(".csv")]

    print(f"Found {len(files)} CSV files\n")

    for file in files:
        try:
            name = file.replace(".csv", "")
            symbol, interval = name.rsplit("_", 1)
            train_direction_model(symbol, interval, horizon=1)

        except Exception as e:
            print(f"[ERROR] {file} -> {e}")

    print("\nDirection training completed.")


if __name__ == "__main__":
    main()
