import os
import pandas as pd

RAW_DIR = "ai/data/raw"


def generate_weekly(symbol: str):
    daily_path = f"{RAW_DIR}/{symbol}_1d.csv"
    weekly_path = f"{RAW_DIR}/{symbol}_1w.csv"

    if not os.path.exists(daily_path):
        print(f"[SKIP] {symbol} 1d not found")
        return

    df = pd.read_csv(daily_path)

    if len(df) < 7:
        print(f"[SKIP] {symbol} 1d too small")
        return

    # open_time を datetime に変換（UTC）
    df["open_time"] = pd.to_datetime(df["open_time"], utc=True)

    # 週単位にリサンプリング（週は月曜開始）
    df = df.set_index("open_time")

    weekly = pd.DataFrame()
    weekly["open"] = df["open"].resample("W-MON").first()
    weekly["high"] = df["high"].resample("W-MON").max()
    weekly["low"] = df["low"].resample("W-MON").min()
    weekly["close"] = df["close"].resample("W-MON").last()
    weekly["volume"] = df["volume"].resample("W-MON").sum()

    weekly = weekly.dropna().reset_index()

    if len(weekly) < 10:
        print(f"[SKIP] {symbol} weekly result too small")
        return

    weekly.to_csv(weekly_path, index=False)

    print(f"[OK] generated {weekly_path} ({len(weekly)} rows)")


def main():
    files = [f for f in os.listdir(RAW_DIR) if f.endswith("_1d.csv")]

    print(f"Found {len(files)} daily CSV files\n")

    for file in files:
        symbol = file.replace("_1d.csv", "")
        try:
            generate_weekly(symbol)
        except Exception as e:
            print(f"[ERROR] {symbol}: {e}")

    print("\nWeekly generation completed.")


if __name__ == "__main__":
    main()
