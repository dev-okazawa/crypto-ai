# ai/src/binance_symbols.py

import json
from pathlib import Path

PATH = Path("ai/data/binance_symbols.json")


def load_binance_symbols() -> set[str]:
    if not PATH.exists():
        raise FileNotFoundError(
            "Binance symbols cache not found. "
            "Run ai/src/cache_binance_symbols.py first."
        )

    data = json.loads(PATH.read_text())
    return set(data.get("symbols", []))
