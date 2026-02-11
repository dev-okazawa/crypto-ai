#!/bin/bash
set -euo pipefail

BASE="/Users/pismo/crypto-ai"
PY="/Users/pismo/miniforge3/envs/cryptoai311/bin/python"
LOG="$BASE/logs/train_$(date +%F).log"
OK="$BASE/ai/data/.last_fetch_ok"

echo "=== TRAIN START $(date -u) ===" >> "$LOG"

# fetch 成功チェック
if [ ! -f "$OK" ]; then
  echo "NO FETCH OK FILE – ABORT" >> "$LOG"
  exit 1
fi

# データ鮮度（2時間以内）
LAST=$(cat "$OK")
AGE=$(( $(date -u +%s) - $(date -d "$LAST" +%s) ))

if [ "$AGE" -gt 7200 ]; then
  echo "FETCH TOO OLD ($AGE sec) – ABORT" >> "$LOG"
  exit 1
fi

$PY $BASE/ai/src/train_top_nightly.py >> "$LOG" 2>&1

echo "=== TRAIN OK ===" >> "$LOG"
