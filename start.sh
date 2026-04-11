#!/bin/bash

echo "🚀 啟動廣告自動化系統..."
echo "📁 專案已重構為模組化架構"
echo "🔗 應用將在 http://127.0.0.1:5002 啟動"
echo ""

# 檢查 Python 環境
if ! command -v python &> /dev/null; then
    echo "❌ 錯誤: 找不到 Python"
    exit 1
fi

# 檢查必要的套件
python -c "import flask, playwright, pymongo" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  警告: 某些必要套件可能未安裝"
    echo "請執行: pip install -r requirements.txt"
    echo ""
fi

# 啟動應用
echo "✅ 啟動應用..."
python run.py 