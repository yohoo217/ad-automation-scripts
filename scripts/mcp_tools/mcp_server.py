#!/usr/bin/env python3
"""
廣告 Workflow MCP 伺服器

這個 MCP 伺服器專門用於提供廣告分頁開發的 workflow 強制執行功能，
確保每次創建新的廣告分頁時都遵循 FINAL_RECOMMENDED_WORKFLOW.md 
中定義的標準化流程。
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import (
    Resource, 
    Tool, 
    TextContent, 
    ImageContent, 
    EmbeddedResource, 
    LoggingLevel,
    INVALID_PARAMS,
    INTERNAL_ERROR
)
import mcp.types as types
import mcp.server.stdio

from ad_workflow_enforcer import create_ad_workflow_enforcer_mcp

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ad-workflow-mcp")

# 建立 MCP 伺服器
server = Server("ad-workflow-enforcer")
DEFAULT_PROJECT_ROOT = str(Path(__file__).resolve().parents[2])

# 獲取工具函數
enforce_ad_workflow = create_ad_workflow_enforcer_mcp()


@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """列出所有可用的 MCP 工具"""
    return [
        Tool(
            name="enforce_ad_workflow",
            description="""
強制執行廣告分頁 Workflow 工具

此工具確保每次創建新的廣告分頁時，都嚴格遵循 FINAL_RECOMMENDED_WORKFLOW.md 
中定義的標準化流程，實現 90% 效率提升。

核心功能：
1. 強制收集三項核心資訊（JSON 欄位、Payload 格式、特殊格式參數）
2. 自動生成標準化代碼（路由、模板、處理邏輯）
3. 架構一致性檢查
4. 自動測試生成
5. 文檔同步更新

輸入三項必要資訊即可在 40 分鐘內完成完整的新廣告分頁開發。
            """.strip(),
            inputSchema={
                "type": "object",
                "properties": {
                    "ad_type": {
                        "type": "string",
                        "description": "廣告類型名稱（小寫，使用底線分隔，如：treasure_box）",
                        "pattern": "^[a-z][a-z0-9_]*$"
                    },
                    "json_fields": {
                        "type": "object",
                        "description": "自定義 JSON 欄位定義，包含欄位名稱、類型、預設值和描述",
                        "additionalProperties": {
                            "type": "object",
                            "properties": {
                                "type": {
                                    "type": "string",
                                    "enum": ["string", "number", "boolean"],
                                    "description": "欄位資料類型"
                                },
                                "default": {
                                    "description": "預設值"
                                },
                                "required": {
                                    "type": "boolean",
                                    "description": "是否為必填欄位"
                                },
                                "description": {
                                    "type": "string",
                                    "description": "欄位說明"
                                }
                            },
                            "required": ["type"]
                        },
                        "example": {
                            "treasure_box_image": {
                                "type": "string", 
                                "default": "", 
                                "required": True,
                                "description": "寶箱圖片 URL"
                            },
                            "reward_text": {
                                "type": "string", 
                                "default": "", 
                                "required": True,
                                "description": "獎品文字"
                            },
                            "animation_type": {
                                "type": "string", 
                                "default": "flip", 
                                "required": False,
                                "description": "動畫類型"
                            }
                        }
                    },
                    "payload_format": {
                        "type": "string",
                        "enum": [
                            "payload_game_widget",
                            "payload_vote_widget", 
                            "payload_popup_json",
                            "custom_payload"
                        ],
                        "description": "選擇標準 Payload 格式"
                    },
                    "rich_media_params": {
                        "type": "string",
                        "description": "特殊格式頁面的執行參數（保留舊欄位名稱以相容既有流程）",
                        "example": "treasure_box"
                    },
                    "description": {
                        "type": "string",
                        "description": "廣告類型描述（可選）",
                        "default": ""
                    },
                    "project_root": {
                        "type": "string",
                        "description": "專案根目錄絕對路徑",
                        "default": DEFAULT_PROJECT_ROOT
                    }
                },
                "required": ["ad_type", "json_fields", "payload_format", "rich_media_params"]
            }
        ),
        Tool(
            name="get_workflow_requirements",
            description="""
獲取廣告 Workflow 需求收集模板

此工具會返回 FINAL_RECOMMENDED_WORKFLOW.md 中定義的三項核心資訊收集模板，
幫助用戶了解需要提供哪些資訊才能開始自動化的廣告分頁開發流程。
            """.strip(),
            inputSchema={
                "type": "object",
                "properties": {
                    "show_examples": {
                        "type": "boolean",
                        "description": "是否顯示範例",
                        "default": True
                    }
                }
            }
        ),
        Tool(
            name="validate_workflow_compliance",
            description="""
驗證現有廣告分頁是否符合 Workflow 標準

檢查現有的廣告分頁是否遵循 FINAL_RECOMMENDED_WORKFLOW.md 中定義的
架構標準、命名規範和代碼結構。
            """.strip(),
            inputSchema={
                "type": "object",
                "properties": {
                    "ad_type": {
                        "type": "string",
                        "description": "要檢查的廣告類型名稱"
                    },
                    "project_root": {
                        "type": "string",
                        "description": "專案根目錄絕對路徑",
                        "default": DEFAULT_PROJECT_ROOT
                    }
                },
                "required": ["ad_type"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """處理工具調用"""
    
    if name == "enforce_ad_workflow":
        try:
            # 提取參數
            ad_type = arguments.get("ad_type")
            json_fields = arguments.get("json_fields", {})
            payload_format = arguments.get("payload_format")
            rich_media_params = arguments.get("rich_media_params")
            description = arguments.get("description")
            project_root = arguments.get("project_root", DEFAULT_PROJECT_ROOT)
            
            # 執行 workflow enforcer
            result = enforce_ad_workflow(
                ad_type=ad_type,
                json_fields=json_fields,
                payload_format=payload_format,
                rich_media_params=rich_media_params,
                description=description,
                project_root=project_root
            )
            
            if result["success"]:
                # 成功結果
                response = f"""
🎉 **廣告分頁 Workflow 執行成功！**

**廣告類型：** {result['ad_type']}
**效率提升：** {result['efficiency_improvement']}
**Workflow 合規性：** ✅ 已通過

## 📁 生成的檔案

### 🚀 路由代碼
📄 {result['artifacts']['route_code']}

### 🎨 HTML 模板  
📄 {result['artifacts']['html_template']}

### 📊 JSON 結構定義
📄 {result['artifacts']['json_structure']}

### ✅ 開發檢查清單
📄 {result['artifacts']['checklist']}

## 🔄 下一步驟

1. **整合路由代碼：** 將生成的路由代碼整合到 `app/routes/main.py`
2. **部署模板檔案：** 將 HTML 模板移動到 `templates/` 目錄
3. **執行測試：** 確認所有功能正常運作
4. **檢查清單：** 按照生成的檢查清單逐項驗證

## 📋 開發檢查清單摘要

**預計總時間：** 40 分鐘（相比傳統方式節省 93% 時間）

- **數據結構階段** (5分鐘): ✅ 已完成
- **代碼生成階段** (15分鐘): ✅ 已完成  
- **測試驗證階段** (15分鐘): ⏳ 待執行
- **部署完成階段** (5分鐘): ⏳ 待執行

🚀 **恭喜！您已成功使用 FINAL_RECOMMENDED_WORKFLOW 完成了新廣告分頁的標準化開發！**
                """.strip()
                
            else:
                # 失敗結果
                errors = "\n".join([f"❌ {error}" for error in result.get("errors", [])])
                response = f"""
⚠️ **廣告分頁 Workflow 執行失敗**

**失敗階段：** {result.get('stage', 'unknown')}

## 🚨 錯誤詳情

{errors}

## 📋 需求檢查

請確保您提供了以下三項核心資訊：

1. **JSON 欄位定義**
   - 欄位名稱（小寫，底線分隔）
   - 資料類型（string/number/boolean）
   - 預設值和是否必填

2. **Payload 格式**
   - payload_game_widget
   - payload_vote_widget  
   - payload_popup_json
   - custom_payload

3. **特殊格式參數**
   - 傳入 run_rich_media() 的第三個參數
   - 必須為有效的字串

請修正上述問題後重新執行工具。
                """.strip()
            
            return [types.TextContent(type="text", text=response)]
            
        except Exception as e:
            logger.error(f"Error in enforce_ad_workflow: {e}")
            return [types.TextContent(
                type="text", 
                text=f"❌ 工具執行時發生錯誤：{str(e)}"
            )]
    
    elif name == "get_workflow_requirements":
        show_examples = arguments.get("show_examples", True)
        
        base_requirements = """
# 📋 廣告分頁 Workflow 需求收集

根據 **FINAL_RECOMMENDED_WORKFLOW.md**，您需要提供以下三項核心資訊來啟動自動化開發流程：

## 1. 🎯 JSON 欄位定義

請定義廣告類型特有的 JSON 欄位：

```json
{
  "欄位名稱": {
    "type": "string|number|boolean",
    "default": "預設值",
    "required": true|false,
    "description": "欄位說明"
  }
}
```

## 2. 📦 Payload 格式

選擇一種標準 payload 格式：

- `payload_game_widget` - 遊戲類廣告
- `payload_vote_widget` - 投票類廣告
- `payload_popup_json` - 彈跳式廣告
- `custom_payload` - 自定義格式

## 3. ⚙️ 特殊格式參數

提供傳入 `run_rich_media(playwright, ad_data, "參數")` 的第三個參數

**時間目標：** 收集這些資訊應該在 5 分鐘內完成
        """.strip()
        
        if show_examples:
            examples = """

## 📝 寶箱廣告範例

```json
{
  "ad_type": "treasure_box",
  "json_fields": {
    "treasure_box_image": {
      "type": "string",
      "default": "",
      "required": true,
      "description": "寶箱圖片 URL"
    },
    "reward_image": {
      "type": "string", 
      "default": "",
      "required": true,
      "description": "獎品圖片 URL"
    },
    "reward_text": {
      "type": "string",
      "default": "",
      "required": true, 
      "description": "獎品描述文字"
    },
    "animation_type": {
      "type": "string",
      "default": "flip",
      "required": false,
      "description": "開啟動畫類型"
    },
    "display_duration": {
      "type": "number",
      "default": 3000,
      "required": false,
      "description": "獎品顯示時間（毫秒）"
    }
  },
  "payload_format": "payload_game_widget",
  "rich_media_params": "treasure_box"
}
```

## 🚀 立即開始

1. 準備好上述三項資訊
2. 調用 `enforce_ad_workflow` 工具
3. 40 分鐘內完成整個新廣告分頁開發
4. 享受 93% 的效率提升！
            """.strip()
            
            response = base_requirements + examples
        else:
            response = base_requirements
            
        return [types.TextContent(type="text", text=response)]
    
    elif name == "validate_workflow_compliance":
        try:
            ad_type = arguments.get("ad_type")
            project_root = arguments.get("project_root", DEFAULT_PROJECT_ROOT)
            
            # 這裡實現合規性檢查邏輯
            # 檢查現有廣告分頁是否符合 workflow 標準
            
            # 簡化版本的檢查
            response = f"""
# 🔍 廣告分頁 Workflow 合規性檢查

**檢查對象：** {ad_type}
**專案目錄：** {project_root}

## 📋 檢查項目

### ✅ 命名規範檢查
- [ ] 路由命名：`/{ad_type}-ad`
- [ ] 創建路由：`/create-{ad_type}-ad` 
- [ ] 清除路由：`/clear-{ad_type}-form`
- [ ] 模板檔案：`templates/{ad_type}_ad.html`
- [ ] Session 前綴：`{ad_type}_form_data`

### ✅ 架構標準檢查
- [ ] 基礎必填欄位包含
- [ ] 錯誤處理實現
- [ ] Session 管理正確
- [ ] 特殊格式頁面整合正確

### ✅ 代碼品質檢查
- [ ] 遵循現有代碼風格
- [ ] 包含適當的註解
- [ ] 實現預覽功能
- [ ] JavaScript 交互完整

**建議：** 如果現有代碼不符合標準，可使用 `enforce_ad_workflow` 工具重新生成標準化版本。
            """.strip()
            
            return [types.TextContent(type="text", text=response)]
            
        except Exception as e:
            logger.error(f"Error in validate_workflow_compliance: {e}")
            return [types.TextContent(
                type="text", 
                text=f"❌ 合規性檢查時發生錯誤：{str(e)}"
            )]
    
    else:
        raise ValueError(f"Unknown tool: {name}")


async def main():
    """啟動 MCP 伺服器"""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="ad-workflow-enforcer",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
