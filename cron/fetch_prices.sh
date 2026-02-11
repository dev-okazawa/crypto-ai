#!/bin/bash
set -euo pipefail

BASE="/Users/pismo/crypto-ai"
PY="/Users/pismo/miniforge3/envs/cryptoai311/bin/python"
LOG="$BASE/logs/fetch_$(date +%F).log"
OK="$BASE/ai/data/.last_fetch_ok"

echo "=== FETCH START $(date -u) ===" >> "$LOG"

$PY $BASE/ai/jobs/fetch_prices.py BTCUSDT 1h >> "$LOG" 2>&1

# 成功したら UTC 時刻を記録
date -u +"%Y-%m-%d %H:%M:%S" > "$OK"

echo "=== FETCH OK ===" >> "$LOG"
