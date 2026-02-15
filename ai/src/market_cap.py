# ai/src/market_cap.py

import json
from pathlib import Path

from ai.src.binance_symbols import load_binance_symbols

# =====================
# Paths
# =====================

PROJECT_ROOT = Path(__file__).resolve().parents[2]  # crypto-ai/
AI_DIR = PROJECT_ROOT / "ai"

DATA_DIR = AI_DIR / "data"
COINGECKO_CACHE = DATA_DIR / "coingecko_top.json"

# 学習済みモデルの実体
TRAINED_DIR = AI_DIR / "models"


# =========================
# Stablecoin definition
# =========================

STABLE_BASES = {
    "USDT", "USDC", "DAI", "BUSD", "TUSD",
    "USDP", "FDUSD", "USDE", "USD1",
    "PYUSD", "RLUSD", "USDD", "GUSD",
    "EURC", "EURS"
}


# =========================
# CoinGecko
# =========================

def load_coingecko_top(limit: int = 200) -> list[dict]:
    if not COINGECKO_CACHE.exists():
        raise FileNotFoundError("coingecko cache not found")

    data = json.loads(COINGECKO_CACHE.read_text())
    return data.get("items", [])[:limit]


# =========================
# Trained symbols（.pkl基準）
# =========================

def load_trained_symbols() -> set[str]:
    """
    学習済み通貨の定義：
    ai/models 配下に *_1h_price_h1.pkl が存在する通貨
    """
    trained = set()

    if not TRAINED_DIR.exists():
        return trained

    for p in TRAINED_DIR.glob("*_1h_price_h1.pkl"):
        # 例: AAVEUSDT_1h_price_h1.pkl → AAVEUSDT
        symbol = p.name.split("_")[0]
        trained.add(symbol)

    return trained


# =========================
# Train candidates
# =========================

def get_train_candidates(max_per_night: int) -> list[str]:
    """
    学習候補：
    - CoinGecko Top200
    - Binance USDT 上場
    - ステーブル除外
    - 未学習（1h price基準）
    """
    coins = load_coingecko_top(200)
    trained = load_trained_symbols()
    binance_symbols = load_binance_symbols()

    selected = []

    for c in coins:
        base = c["symbol"].upper()

        if base in STABLE_BASES:
            continue

        symbol = f"{base}USDT"

        if symbol not in binance_symbols:
            continue

        if symbol in trained:
            continue

        selected.append(symbol)

        if len(selected) >= max_per_night:
            break

    return selected


# =========================
# UI: Supported symbols
# =========================

def get_supported(interval: str = "1h"):
    """
    UI 用：
    - CoinGecko Top
    - Binance USDT 上場
    - ステーブル除外
    """
    try:
        coins = load_coingecko_top()
        binance = load_binance_symbols()
    except Exception as e:
        print("[ERROR] get_supported init failed:", e)
        return []

    result = []

    for c in coins:
        base = c["symbol"].upper()

        if base in STABLE_BASES:
            continue

        symbol = f"{base}USDT"

        if symbol not in binance:
            continue

        result.append({
            "rank": c.get("market_cap_rank"),
            "symbol": symbol,
            "name": c.get("name"),
            "market_cap": c.get("market_cap"),
            "image": c.get("image"),
        })

    return result


# =========================
# Market Overview compatibility
# =========================

def get_top100_with_status(interval: str = "1h"):
    """
    Market Overview 用。
    supported + 学習済み status を付与する。
    """
    supported = get_supported(interval)
    trained = load_trained_symbols()

    result = []

    for coin in supported:
        symbol = coin["symbol"]

        coin_copy = coin.copy()

        if symbol in trained:
            coin_copy["status"] = "trained"
        else:
            coin_copy["status"] = "untrained"

        result.append(coin_copy)

    return result