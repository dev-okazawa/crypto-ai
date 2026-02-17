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

    # 1. 未評価データの実際の価格(Actual Price)を特定して埋める
    cur.execute("SELECT * FROM predictions WHERE evaluated = FALSE")
    rows = cur.fetchall()
    print(f"[EVALUATE] Found {len(rows)} unevaluated rows.")

    for row in rows:
        symbol = row["symbol"]
        timeframe = row["timeframe"]
        horizon = row["horizon"]
        predict_time = row["predict_time"]

        df = load_csv(symbol, timeframe)
        if df is None: continue

        df["open_time"] = pd.to_datetime(df["open_time"], utc=True)
        df["open_time"] = df["open_time"].apply(lambda x: int(x.timestamp() * 1000))
        df = df.sort_values("open_time").reset_index(drop=True)

        interval_ms = INTERVAL_MS.get(timeframe)
        if interval_ms is None: continue

        # 未来のターゲット時刻を計算
        target_time = predict_time + horizon * interval_ms
        # 事実：完全一致しない場合に備え、ターゲット時刻以降の直近の足を取得
        target_row = df[df["open_time"] >= target_time].head(1)

        if len(target_row) == 0:
            continue

        actual_price = float(target_row.iloc[0]["close"])

        cur.execute("""
            UPDATE predictions
            SET actual_price = %s, evaluated = TRUE
            WHERE id = %s
        """, (actual_price, row["id"]))
        print(f"Filled actual_price for {symbol} id={row['id']}")

    conn.commit()

    # 2. 的中率(Accuracy)の計算とランキングテーブルの更新
    print("[EVALUATE] Calculating accuracy metrics...")
    cur.execute("SELECT DISTINCT symbol FROM predictions WHERE evaluated = TRUE")
    active_symbols = cur.fetchall()

    for s in active_symbols:
        symbol = s['symbol']
        
        # 過去直近100件の評価済みデータを取得
        cur.execute("""
            SELECT current_price, predicted_price, actual_price 
            FROM predictions 
            WHERE symbol = %s AND evaluated = TRUE 
            ORDER BY predict_time DESC LIMIT 100
        """, (symbol,))
        
        history = cur.fetchall()
        if not history: continue

        hits = 0
        total = len(history)
        
        for record in history:
            # 予測：上がると言ったか？ / 実績：上がったか？
            pred_up = record['predicted_price'] > record['current_price']
            actual_up = record['actual_price'] > record['current_price']
            
            if pred_up == actual_up:
                hits += 1

        accuracy = round((hits / total) * 100, 2)

        # 的中率ランキングテーブルを更新
        cur.execute("""
            INSERT INTO accuracy_ranking (symbol, accuracy, count)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE accuracy = %s, count = %s
        """, (symbol, accuracy, total, accuracy, total))
        
        print(f"Updated Accuracy: {symbol} = {accuracy}% ({hits}/{total})")

    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    evaluate_predictions()