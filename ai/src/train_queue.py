import json
import os
from datetime import datetime

QUEUE_PATH = "ai/queue/train_queue.json"
os.makedirs("ai/queue", exist_ok=True)


def _load():
    if not os.path.exists(QUEUE_PATH):
        return {"pending": [], "processing": []}
    with open(QUEUE_PATH, "r") as f:
        return json.load(f)


def _save(data):
    with open(QUEUE_PATH, "w") as f:
        json.dump(data, f, indent=2)


def enqueue(symbol: str, interval: str, horizon: int):
    data = _load()
    item = {
        "symbol": symbol,
        "interval": interval,
        "horizon": horizon,
        "requested_at": datetime.utcnow().isoformat()
    }

    if item in data["pending"] or item in data["processing"]:
        return False

    data["pending"].append(item)
    _save(data)
    return True


def pop_next():
    data = _load()
    if not data["pending"]:
        return None

    item = data["pending"].pop(0)
    data["processing"].append(item)
    _save(data)
    return item


def mark_done(item):
    data = _load()
    if item in data["processing"]:
        data["processing"].remove(item)
        _save(data)
