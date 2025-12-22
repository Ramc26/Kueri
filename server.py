# server.py

import os
import json
import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel
from typing import Dict, Any, List

# Import tool registration
from register_tools import register_db_tools


# -----------------------------------------------------------------------------
# Load environment
# -----------------------------------------------------------------------------
def load_environment():
    """Load environment variables from .env file"""
    load_dotenv(override=True)
    logger.info("✅ Environment variables loaded from .env")


# # -----------------------------------------------------------------------------
# # Tool configuration
# # -----------------------------------------------------------------------------
# def setup_tool_configuration():
#     """Setup which tools are allowed via ENV filters"""
#     try:
#         ENABLED_TOOLS = {n.lower() for n in json.loads(os.getenv("ENABLED_TOOLS", "[]"))}
#     except (json.JSONDecodeError, TypeError):
#         ENABLED_TOOLS = set()

#     disabled_env = os.getenv("DISABLED_TOOLS", "").strip()
#     DISABLED_TOOLS = {n.strip().lower() for n in disabled_env.split(",") if n.strip()}

#     def tool_allowed(tool_name: str) -> bool:
#         low = tool_name.lower()
#         if low in DISABLED_TOOLS:
#             return False
#         if ENABLED_TOOLS and low not in ENABLED_TOOLS:
#             return False
#         return True

#     return tool_allowed


# -----------------------------------------------------------------------------
# FastAPI + MCP Setup
# -----------------------------------------------------------------------------
mcp = FastMCP("DBTools")
app = FastAPI(title="DBView MCP Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)

# Mount MCP SSE transport (for MCP Dev Inspector)
app.mount("/mcp", mcp.sse_app())


# -----------------------------------------------------------------------------
# HTTP Tool Invocation Layer
# -----------------------------------------------------------------------------
class ToolCallRequest(BaseModel):
    name: str
    args: Dict[str, Any] | None = None


def _serialize_tool_result(result: Any) -> Any:
    """Convert MCP results into JSON-serializable data"""
    try:
        if isinstance(result, list):
            out = []
            for item in result:
                if hasattr(item, "text"):
                    out.append(getattr(item, "text"))
                elif isinstance(item, (str, int, float, bool, type(None), dict, list)):
                    out.append(item)
                else:
                    out.append(str(item))
            return out
        if isinstance(result, (str, int, float, bool, type(None), dict, list)):
            return result
        return str(result)
    except Exception as e:
        logger.error("Serialization failed: {}", e)
        return str(result)


@app.get("/v1/tools")
async def list_tools():
    """List all registered MCP tools with full schemas"""
    tools = await mcp.list_tools()
    tool_list = []
    for t in tools:
        tool_dict = {
            "name": t.name,
            "description": t.description,
            "inputSchema": t.inputSchema if hasattr(t, 'inputSchema') else {}
        }
        tool_list.append(tool_dict)
    return {"tools": tool_list}


@app.post("/v1/tools/call")
async def call_tool(req: ToolCallRequest):
    """Call a registered MCP tool"""
    try:
        result = await mcp.call_tool(req.name, req.args or {})
        return {
            "status": "success",
            "name": req.name,
            "args": req.args,
            "output": _serialize_tool_result(result),
        }
    except Exception as e:
        logger.error("Tool call failed for {}: {}", req.name, e)
        return {"status": "error", "error": str(e)}


# -----------------------------------------------------------------------------
# Initialization
# -----------------------------------------------------------------------------
def initialize_server():
    load_environment()
    # tool_allowed_func = setup_tool_configuration()

    # Register DB tools
    register_db_tools(mcp)

    logger.info("🚀 MCP DB Server initialized successfully!")


initialize_server()


# -----------------------------------------------------------------------------
# Run server (for local dev / MCP Inspector)
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    logger.info("🌍 Starting DB MCP server at http://0.0.0.0:8001")
    uvicorn.run(app, host="0.0.0.0", port=8001)
