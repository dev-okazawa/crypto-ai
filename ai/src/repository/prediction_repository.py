from ai.src.repository.db import get_connection


def insert_prediction(
    symbol,
    timeframe,
    horizon,
    base_price,
    predicted_price,
    predict_time,
    confidence,
    model_version="v1"
):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO predictions (
            symbol,
            timeframe,
            horizon,
            predict_time,
            base_price,
            predicted_price,
            confidence,
            model_version
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        symbol,
        timeframe,
        horizon,
        predict_time,
        base_price,
        predicted_price,
        confidence,
        model_version
    ))

    conn.commit()
    cur.close()
    conn.close()
