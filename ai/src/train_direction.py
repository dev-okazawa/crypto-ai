from sklearn.ensemble import RandomForestClassifier
from sklearn.calibration import CalibratedClassifierCV
import joblib
import os
import pandas as pd
import numpy as np

from ai.src.features import make_features


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "ai", "data", "raw")
MODEL_DIR = os.path.join(BASE_DIR, "ai", "models")


def load_csv(symbol, interval):
    path = f"{DATA_DIR}/{symbol}_{interval}.csv"
    if not os.path.exists(path):
        return None
    return pd.read_csv(path)


def train_direction_model(symbol: str, interval: str, horizon: int):

    df = load_csv(symbol, interval)
    if df is None:
        print(f"[SKIP] {symbol} {interval} (no csv)")
        return

    df_feat = make_features(df)

    if len(df_feat) <= horizon + 50:
        print(f"[SKIP] {symbol} {interval} (data too small: {len(df_feat)})")
        return

    # ==========================
    # ターゲット作成
    # ==========================
    df_feat["future_price"] = df_feat["close"].shift(-horizon)

    df_feat["direction"] = 0
    df_feat.loc[
        df_feat["future_price"] > df_feat["close"], "direction"
    ] = 1
    df_feat.loc[
        df_feat["future_price"] < df_feat["close"], "direction"
    ] = -1

    df_feat = df_feat.dropna()

    feature_cols = [
        col for col in df_feat.columns
        if col not in ["open_time", "future_price", "direction"]
    ]

    X = df_feat[feature_cols]
    y = df_feat["direction"]

    # ==========================
    # クラス分布チェック
    # ==========================
    class_counts = y.value_counts()
    min_class_samples = class_counts.min()

    if len(class_counts) < 2:
        print(f"[SKIP] {symbol} {interval} (only one class)")
        return

    if min_class_samples < 2:
        print(f"[SKIP] {symbol} {interval} (too few samples per class)")
        return

    # cvはクラス最小数以下にする
    cv_folds = min(3, min_class_samples)

    # ==========================
    # モデル
    # ==========================
    base_model = RandomForestClassifier(
        n_estimators=300,
        max_depth=8,
        random_state=42,
        n_jobs=-1
    )

    calibrated_model = CalibratedClassifierCV(
        estimator=base_model,
        method="sigmoid",
        cv=cv_folds
    )

    calibrated_model.fit(X, y)

    # ==========================
    # 保存
    # ==========================
    os.makedirs(MODEL_DIR, exist_ok=True)

    model_path = f"{MODEL_DIR}/{symbol}_{interval}_direction_h{horizon}.pkl"

    joblib.dump(calibrated_model, model_path)

    print(f"[OK] Direction calibrated: {symbol} {interval} h{horizon} (cv={cv_folds})")
