from ai.src.repository.db import get_connection

conn = get_connection()
cur = conn.cursor(dictionary=True)

try:
    # 1. テーブルがなければ作成する
    print("Checking/Creating accuracy_ranking table...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS accuracy_ranking (
            symbol VARCHAR(20) PRIMARY KEY,
            accuracy DOUBLE NOT NULL,
            count INT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    """)

    # 2. 評価済みデータから的中率を集計
    print("Calculating accuracy from evaluated records...")
    cur.execute("""
        SELECT symbol, base_price, predicted_price, actual_price 
        FROM predictions 
        WHERE evaluated = 1
    """)
    rows = cur.fetchall()

    if not rows:
        print("No evaluated records found in 'predictions' table.")
    else:
        stats = {}
        for r in rows:
            s = r['symbol']
            if s not in stats: stats[s] = {'hits': 0, 'total': 0}
            
            # 判定ロジック
            pred_up = r['predicted_price'] > r['base_price']
            actual_up = r['actual_price'] > r['base_price']
            
            stats[s]['total'] += 1
            if pred_up == actual_up:
                stats[s]['hits'] += 1

        # 3. 結果を反映
        for symbol, data in stats.items():
            accuracy = round((data['hits'] / data['total']) * 100, 2)
            cur.execute("""
                INSERT INTO accuracy_ranking (symbol, accuracy, count)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE accuracy = %s, count = %s
            """, (symbol, accuracy, data['total'], accuracy, data['total']))
            print(f"DONE: {symbol.ljust(10)} | Accuracy: {str(accuracy).rjust(6)}% | Samples: {data['total']}")

        conn.commit()
        print("\nSUCCESS: Table created and accuracy metrics updated.")

except Exception as e:
    print(f"Error: {e}")
finally:
    cur.close()
    conn.close()
