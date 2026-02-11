import pandas as pd
import numpy as np

FEATURE_COLUMNS = [
    "return",
    "return_3",
    "return_6",
    "ma_5",
    "ma_20",
    "ema_20",
    "ema_50",
    "ema_diff",
    "rsi",
    "volatility",
    "volatility_20",
    "bb_width",
    "volume_ma",
    "volume_change"
]


def make_features(df):
    df = df.copy()

    # リターン
    df["return"] = df["close"].pct_change()
    df["return_3"] = df["close"].pct_change(3)
    df["return_6"] = df["close"].pct_change(6)

    # 移動平均
    df["ma_5"] = df["close"].rolling(5).mean()
    df["ma_20"] = df["close"].rolling(20).mean()

    # EMA
    df["ema_20"] = df["close"].ewm(span=20, adjust=False).mean()
    df["ema_50"] = df["close"].ewm(span=50, adjust=False).mean()
    df["ema_diff"] = df["ema_20"] - df["ema_50"]

    # RSI
    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    avg_loss = avg_loss.replace(0, np.nan)

    rs = avg_gain / avg_loss
    df["rsi"] = 100 - (100 / (1 + rs))

    # ボラティリティ
    df["volatility"] = df["return"].rolling(10).std()
    df["volatility_20"] = df["return"].rolling(20).std()

    # ボリンジャーバンド幅
    std20 = df["close"].rolling(20).std()
    upper = df["ma_20"] + 2 * std20
    lower = df["ma_20"] - 2 * std20
    df["bb_width"] = (upper - lower) / df["ma_20"]

    # 出来高
    df["volume_ma"] = df["volume"].rolling(10).mean()
    df["volume_change"] = df["volume"].pct_change()

    # 無限値対策
    df.replace([np.inf, -np.inf], np.nan, inplace=True)

    df = df.dropna()
    return df


def make_price_target(df, horizon=1):
    return df["close"].shift(-horizon)


# 🔥 二値分類（threshold緩和）
def make_direction_target(df, horizon=1, threshold=0.0015):
    future_return = df["close"].shift(-horizon) / df["close"] - 1
    return (future_return > threshold).astype(int)
