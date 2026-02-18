import os
from pathlib import Path
import joblib
import pandas as pd

from sklearn.ensemble import RandomForestRegressor
from ai.src.features import make_features, make_price_target


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

def train_price_model(symbol: str, interval: str, horizon: int = 1):

    path = RAW_DIR / f"{symbol}_{interval}.csv"

    if not path.exists():
        print(f"[SKIP] {symbol} {interval} (CSV not found)")
        return

    df = pd.read_csv(path)

    df_feat = make_features(df)
    df_feat["target"] = make_price_target(df_feat, horizon=horizon)
    df_feat = df_feat.dropna()

    # --- 修正箇所: 時間軸(interval)に応じて最低必要行数を可変にする ---
    # 週足(1w)はデータ密度が低いため、20行（約5ヶ月分）あれば学習を許可する。
    # 日足(1d)・時間足(1h)は、精度担保のため従来の150行を維持。
    min_data_rows = 20 if interval == "1w" else 150

    if len(df_feat) < min_data_rows:
        print(f"[SKIP] {symbol} {interval} (data too small: {len(df_feat)} < {min_data_rows})")
        return
    # -------------------------------------------------------------

    feature_cols = [
        col for col in df_feat.columns
        if col not in ["target", "open_time"]
    ]

    X = df_feat[feature_cols]
    y = df_feat["target"]

    model = RandomForestRegressor(
        n_estimators=300,
        max_depth=6,
        random_state=42,
        n_jobs=-1
    )

    model.fit(X, y)

    model_path = MODEL_DIR / f"{symbol}_{interval}_price_h{horizon}.pkl"
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
            # ファイル名が symbol_interval.csv であることを想定
            if "_" not in name: continue
            
            symbol, interval = name.rsplit("_", 1)
            train_price_model(symbol, interval, horizon=1)

        except Exception as e:
            print(f"[ERROR] {file} -> {e}")

    print("\nPrice training completed.")


if __name__ == "__main__":
    main()