import pandas as pd
import os
from ai.src.repository.db import get_connection


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "ai", "data", "raw")

INTERVAL_MS = {
    "1h": 60 * 60 * 1000,
    "1d": 24 * 60 * 60 * 1000,
    "1w": 7 * 24 * 60 * 60 * 1000,
}


def load_csv(symbol, timeframe):
    path = f"{DATA_DIR}/{symbol}_{timeframe}.csv"
    if not os.path.exists(path):
        return None
    return pd.read_csv(path)


def evaluate_predictions():

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    # 未評価データ取得
    cur.execute("""
        SELECT * FROM predictions
        WHERE evaluated = FALSE
    """)

    rows = cur.fetchall()

    for row in rows:

        symbol = row["symbol"]
        timeframe = row["timeframe"]
        horizon = row["horizon"]
        predict_time = row["predict_time"]  # これはミリ秒

        df = load_csv(symbol, timeframe)
        if df is None:
            continue

        # 🔥 open_time を確実にミリ秒へ変換
        df["open_time"] = pd.to_datetime(df["open_time"], utc=True)
        df["open_time"] = df["open_time"].apply(
            lambda x: int(x.timestamp() * 1000)
        )

        df = df.sort_values("open_time").reset_index(drop=True)

        interval_ms = INTERVAL_MS.get(timeframe)
        if interval_ms is None:
            continue

        # 🔥 正しい未来足の時間を計算
        target_time = predict_time + horizon * interval_ms

        target_row = df[df["open_time"] == target_time]

        # 未来足がまだ存在しない場合はスキップ
        if len(target_row) == 0:
            continue

        actual_price = float(target_row.iloc[0]["close"])

        # DB更新
        cur.execute("""
            UPDATE predictions
            SET actual_price = %s,
                evaluated = TRUE
            WHERE id = %s
        """, (actual_price, row["id"]))

        print(f"Evaluated id={row['id']}")

    conn.commit()
    cur.close()
    conn.close()


if __name__ == "__main__":
    evaluate_predictions()
