import pandas as pd

FEATURE_COLUMNS = [
    "return",
    "ma_5",
    "ma_20",
    "volatility",
    "volume_ma"
]

def make_features(df):
    df = df.copy()

    df["return"] = df["close"].pct_change()
    df["ma_5"] = df["close"].rolling(5).mean()
    df["ma_20"] = df["close"].rolling(20).mean()
    df["volatility"] = df["return"].rolling(10).std()
    df["volume_ma"] = df["volume"].rolling(10).mean()

    df = df.dropna()
    return df

def make_price_target(df, horizon=1):
    return df["close"].shift(-horizon)

def make_direction_target(df, horizon=1, threshold=0.002):
    future_return = df["close"].shift(-horizon) / df["close"] - 1
    return future_return.apply(
        lambda x: 1 if x > threshold else (-1 if x < -threshold else 0)
    )
