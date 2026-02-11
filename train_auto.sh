#!/bin/bash

# conda 初期化（cron 用）
source /Users/pismo/miniforge3/etc/profile.d/conda.sh

# 正しい環境を有効化
conda activate cryptoai311

# プロジェクトへ移動
cd /Users/pismo/crypto-ai || exit 1

# ログディレクトリ
mkdir -p logs

# 学習実行
python -m ai.src.train_all_auto >> logs/train.log 2>&1
