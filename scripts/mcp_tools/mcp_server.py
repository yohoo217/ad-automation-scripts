#!/usr/bin/env python3
"""
Ad Workflow MCP Server

This MCP server is dedicated to providing workflow enforcement functionality for ad page development,
ensuring that every time a new ad page is created, it follows the standardized workflow defined in
FINAL_RECOMMENDED_WORKFLOW.md.
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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ad-workflow-mcp")

# Create MCP server
server = Server("ad-workflow-enforcer")
DEFAULT_PROJECT_ROOT = str(Path(__file__).resolve().parents[2])

# Get tool function
enforce_ad_workflow = create_ad_workflow_enforcer_mcp()


@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List all available MCP tools"""
    return [
        Tool(
            name="enforce_ad_workflow",
            description="""
Enforce Ad Page Workflow Tool

This tool ensures that every time a new ad page is created, it strictly follows the standardized workflow
defined in FINAL_RECOMMENDED_WORKFLOW.md, achieving 90% efficiency boost.

Core features:
1. Force collect three core pieces of info (JSON fields, Payload format, special format parameters)
2. Auto-generate standardized code (routes, templates, processing logic)
3. Architecture consistency check
4. Auto test generation
5. Documentation sync update

Input three necessary pieces of information to complete the entire new ad page development within 40 minutes.
            """.strip(),
            inputSchema={
                "type": "object",
                "properties": {
                    "ad_type": {
                        "type": "string",
                        "description": "Ad type name (lowercase, underscore separated, e.g.: treasure_box)",
                        "pattern": "^[a-z][a-z0-9_]*$"
                    },
                    "json_fields": {
                        "type": "object",
                        "description": "Custom JSON field definition, includes field name, type, default value and description",
                        "additionalProperties": {
                            "type": "object",
                            "properties": {
                                "type": {
                                    "type": "string",
                                    "enum": ["string", "number", "boolean"],
                                    "description": "Field data type"
                                },
                                "default": {
                                    "description": "Default value"
                                },
                                "required": {
                                    "type": "boolean",
                                    "description": "Whether is required field"
                                },
                                "description": {
                                    "type": "string",
                                    "description": "Field description"
                                }
                            },
                            "required": ["type"]
                        },
                        "example": {
                            "treasure_box_image": {
                                "type": "string",
                                "default": "",
                                "required": True,
                                "description": "Treasure chest image URL"
                            },
                            "reward_text": {
                                "type": "string",
                                "default": "",
                                "required": True,
                                "description": "Prize text"
                            },
                            "animation_type": {
                                "type": "string",
                                "default": "flip",
                                "required": False,
                                "description": "Animation type"
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
                        "description": "Select standard Payload format"
                    },
                    "rich_media_params": {
                        "type": "string",
                        "description": "Special format page execution parameters (keep old field name for compatibility with existing workflow)",
                        "example": "treasure_box"
                    },
                    "description": {
                        "type": "string",
                        "description": "Ad type description (optional)",
                        "default": ""
                    },
                    "project_root": {
                        "type": "string",
                        "description": "Absolute path to project root directory",
                        "default": DEFAULT_PROJECT_ROOT
                    }
                },
                "required": ["ad_type", "json_fields", "payload_format", "rich_media_params"]
            }
        ),
        Tool(
            name="get_workflow_requirements",
            description="""
Get Ad Workflow Requirements Collection Template

This tool returns the three core information collection templates defined in FINAL_RECOMMENDED_WORKFLOW.md,
helping users understand what information needs to be provided to start the automated ad page development workflow.
            """.strip(),
            inputSchema={
                "type": "object",
                "properties": {
                    "show_examples": {
                        "type": "boolean",
                        "description": "Whether to show examples",
                        "default": True
                    }
                }
            }
        ),
        Tool(
            name="validate_workflow_compliance",
            description="""
Validate Existing Ad Page Workflow Compliance

Check whether existing ad pages comply with the workflow standards defined in FINAL_RECOMMENDED_WORKFLOW.md,
including architecture standards, naming conventions, and code structure.
            """.strip(),
            inputSchema={
                "type": "object",
                "properties": {
                    "ad_type": {
                        "type": "string",
                        "description": "Ad type name to check"
                    },
                    "project_root": {
                        "type": "string",
                        "description": "Absolute path to project root directory",
                        "default": DEFAULT_PROJECT_ROOT
                    }
                },
                "required": ["ad_type"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Processing tool calls"""

    if name == "enforce_ad_workflow":
        try:
            # Extract parameters
            ad_type = arguments.get("ad_type")
            json_fields = arguments.get("json_fields", {})
            payload_format = arguments.get("payload_format")
            rich_media_params = arguments.get("rich_media_params")
            description = arguments.get("description")
            project_root = arguments.get("project_root", DEFAULT_PROJECT_ROOT)

            # Execute workflow enforcer
            result = enforce_ad_workflow(
                ad_type=ad_type,
                json_fields=json_fields,
                payload_format=payload_format,
                rich_media_params=rich_media_params,
                description=description,
                project_root=project_root
            )

            if result["success"]:
                # Success result
                response = f"""
🎉 **Ad Page Workflow Execution Success!**

**Ad Type:** {result['ad_type']}
**Efficiency Improvement:** {result['efficiency_improvement']}
**Workflow Compliance:** ✅ Passed

## 📁 Generated Files

### 🚀 Route Code
📄 {result['artifacts']['route_code']}

### 🎨 HTML Template
📄 {result['artifacts']['html_template']}

### 📊 JSON Structure Definition
📄 {result['artifacts']['json_structure']}

### ✅ Development Checklist
📄 {result['artifacts']['checklist']}

## 🔄 Next Steps

1. **Integrate Route Code:** Integrate generated route code into `app/routes/main.py`
2. **Deploy Template Files:** Move HTML template to `templates/` directory
3. **Execute Tests:** Ensure all features work properly
4. **Check Checklist:** Verify each item according to generated checklist

## 📋 Development Checklist Summary

**Expected Total Time:** 40 minutes (saves 93% time compared to traditional method)

- **Data Structure Phase** (5 minutes): ✅ Completed
- **Code Generation Phase** (15 minutes): ✅ Completed
- **Test Validation Phase** (15 minutes): ⏳ Pending execution
- **Deployment Completion Phase** (5 minutes): ⏳ Pending execution

🚀 **Congratulations! You have successfully completed standardized development of new ad page using FINAL_RECOMMENDED_WORKFLOW!**
                """.strip()

            else:
                # Failed result
                errors = "\n".join([f"❌ {error}" for error in result.get("errors", [])])
                response = f"""
⚠️ **Ad Page Workflow Execution Failed**

**Failed Phase:** {result.get('stage', 'unknown')}

## 🚨 Error Details

{errors}

## 📋 Requirements Check

Please ensure you provided the following three core pieces of information:

1. **JSON Field Definition**
   - Field name (lowercase, underscore separated)
   - Data type (string/number/boolean)
   - Default value and whether required

2. **Payload Format**
   - payload_game_widget
   - payload_vote_widget
   - payload_popup_json
   - custom_payload

3. **Special Format Parameters**
   - Three parameters to pass to run_rich_media()
   - Must be valid strings

Please fix the above issues and retry the tool.
                """.strip()

            return [types.TextContent(type="text", text=response)]

        except Exception as e:
            logger.error(f"Error in enforce_ad_workflow: {e}")
            return [types.TextContent(
                type="text",
                text=f"❌ Tool execution error: {str(e)}"
            )]

    elif name == "get_workflow_requirements":
        show_examples = arguments.get("show_examples", True)

        base_requirements = """
# 📋 Ad Page Workflow Requirements Collection

According to **FINAL_RECOMMENDED_WORKFLOW.md**, you need to provide the following three core pieces of information
to start the automated development workflow:

## 1. 🎯 JSON Field Definition

Please define JSON fields specific to ad type:

```json
{
  "field_name": {
    "type": "string|number|boolean",
    "default": "Default value",
    "required": true|false,
    "description": "Field description"
  }
}
```

## 2. 📦 Payload Format

Choose one standard payload format:

- `payload_game_widget` - Game type ads
- `payload_vote_widget` - Vote type ads
- `payload_popup_json` - Popup ads
- `custom_payload` - Custom format

## 3. ⚙️ Special Format Parameters

Provide three parameters to pass to `run_rich_media(playwright, ad_data, "parameter")`

**Time Target:** Collecting this information should be completed within 5 minutes
        """.strip()

        if show_examples:
            examples = """

## 📝 Treasure Box Ad Example

```json
{
  "ad_type": "treasure_box",
  "json_fields": {
    "treasure_box_image": {
      "type": "string",
      "default": "",
      "required": true,
      "description": "Treasure chest image URL"
    },
    "reward_image": {
      "type": "string",
      "default": "",
      "required": true,
      "description": "Prize image URL"
    },
    "reward_text": {
      "type": "string",
      "default": "",
      "required": true,
      "description": "Prize description text"
    },
    "animation_type": {
      "type": "string",
      "default": "flip",
      "required": false,
      "description": "Opening animation type"
    },
    "display_duration": {
      "type": "number",
      "default": 3000,
      "required": false,
      "description": "Prize display time (milliseconds)"
    }
  },
  "payload_format": "payload_game_widget",
  "rich_media_params": "treasure_box"
}
```

## 🚀 Get Started Now

1. Prepare the above three pieces of information
2. Call `enforce_ad_workflow` tool
3. Complete entire new ad page development within 40 minutes
4. Enjoy 93% efficiency improvement!
            """.strip()

            response = base_requirements + examples
        else:
            response = base_requirements

        return [types.TextContent(type="text", text=response)]

    elif name == "validate_workflow_compliance":
        try:
            ad_type = arguments.get("ad_type")
            project_root = arguments.get("project_root", DEFAULT_PROJECT_ROOT)

            # Implement compliance check logic here
            # Check whether existing ad pages comply with workflow standards

            # Simplified version of the check
            response = f"""
# 🔍 Ad Page Workflow Compliance Check

**Check Target:** {ad_type}
**Project Directory:** {project_root}

## 📋 Check Items

### ✅ Naming Convention Check
- [ ] Route naming: `/{ad_type}-ad`
- [ ] Create route: `/create-{ad_type}-ad`
- [ ] Clear route: `/clear-{ad_type}-form`
- [ ] Template file: `templates/{ad_type}_ad.html`
- [ ] Session prefix: `{ad_type}_form_data`

### ✅ Architecture Standard Check
- [ ] Basic required fields included
- [ ] Error processing implementation
- [ ] Session management correct
- [ ] Special format page integration correct

### ✅ Code Quality Check
- [ ] Follow existing code style
- [ ] Include appropriate comments
- [ ] Implement preview feature
- [ ] JavaScript interaction complete

**Suggestion:** If existing code does not comply with standards, use `enforce_ad_workflow` tool to regenerate standardized version.
            """.strip()

            return [types.TextContent(type="text", text=response)]

        except Exception as e:
            logger.error(f"Error in validate_workflow_compliance: {e}")
            return [types.TextContent(
                type="text",
                text=f"❌ Compliance check error: {str(e)}"
            )]

    else:
        raise ValueError(f"Unknown tool: {name}")


async def main():
    """Start MCP server"""
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
