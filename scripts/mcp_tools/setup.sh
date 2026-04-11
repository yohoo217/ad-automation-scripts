#!/bin/bash
# 廣告 Workflow MCP 工具安裝腳本

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "🚀 安裝廣告 Workflow MCP 工具..."

# 檢查 Python 版本
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1-2)
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ 需要 Python 3.8 或更高版本，當前版本：$PYTHON_VERSION"
    exit 1
fi

echo "✅ Python 版本檢查通過：$PYTHON_VERSION"

# 安裝依賴
echo "📦 安裝 MCP 依賴..."
pip3 install -r "$SCRIPT_DIR/requirements.txt"

# 設定執行權限
chmod +x "$SCRIPT_DIR/mcp_server.py"

echo "✅ 廣告 Workflow MCP 工具安裝完成！"
echo ""
echo "📋 使用說明："
echo "1. 重啟 Cursor 以載入新的 MCP 工具"
echo "2. 在 Cursor 中調用 'get_workflow_requirements' 工具查看需求"
echo "3. 準備好三項核心資訊後調用 'enforce_ad_workflow' 工具"
echo "4. 享受 93% 的開發效率提升！"
echo ""
echo "🎯 範例："
echo "工具名稱: enforce_ad_workflow"
echo "參數: {"
echo "  \"ad_type\": \"treasure_box\","
echo "  \"json_fields\": {"
echo "    \"treasure_box_image\": {\"type\": \"string\", \"required\": true, \"description\": \"寶箱圖片 URL\"},"
echo "    \"reward_text\": {\"type\": \"string\", \"required\": true, \"description\": \"獎品文字\"}"
echo "  },"
echo "  \"payload_format\": \"payload_game_widget\","
echo "  \"rich_media_params\": \"treasure_box\""
echo "}"
