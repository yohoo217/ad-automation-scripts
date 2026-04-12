#!/bin/bash
# Ad Workflow MCP Tool Installation Script

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "🚀 Installing Ad Workflow MCP Tools..."

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1-2)
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python 3.8 or higher required. Current version: $PYTHON_VERSION"
    exit 1
fi

echo "✅ Python version check passed: $PYTHON_VERSION"

# Install dependencies
echo "📦 Installing MCP dependencies..."
pip3 install -r "$SCRIPT_DIR/requirements.txt"

# Set executable permissions
chmod +x "$SCRIPT_DIR/mcp_server.py"

echo "✅ Ad Workflow MCP Tools installation complete!"
echo ""
echo "📋 Usage Instructions:"
echo "1. Restart Cursor to load the new MCP tools"
echo "2. Call 'get_workflow_requirements' tool in Cursor to view requirements"
echo "3. After preparing the three core pieces of information, call 'enforce_ad_workflow' tool"
echo "4. Enjoy improved development efficiency!"
echo ""
echo "🎯 Example:"
echo "Tool name: enforce_ad_workflow"
echo "Parameters: {"
echo "  \"ad_type\": \"treasure_box\","
echo "  \"json_fields\": {"
echo "    \"treasure_box_image\": {\"type\": \"string\", \"required\": true, \"description\": \"Treasure box image URL\"},"
echo "    \"reward_text\": {\"type\": \"string\", \"required\": true, \"description\": \"Reward text\"}"
echo "  },"
echo "  \"payload_format\": \"payload_game_widget\","
echo "  \"rich_media_params\": \"treasure_box\""
echo "}"
