# agent.py
import os
import json
from typing import Dict, Any, List, Annotated, TypedDict
from dotenv import load_dotenv
from loguru import logger

from langchain_openai import ChatOpenAI
from langchain_core.tools import BaseTool, StructuredTool
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from pydantic import BaseModel, Field, ConfigDict
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
import httpx
import asyncio
from typing import Type

load_dotenv()

# -----------------------------------------------------------------------------
# MCP Client for SSE Transport
# -----------------------------------------------------------------------------
class MCPClient:
    """Client to connect to MCP server via SSE transport"""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url.rstrip('/')
        self.mcp_endpoint = f"{self.base_url}/mcp"
        self.tools_endpoint = f"{self.base_url}/v1/tools"
        self.call_endpoint = f"{self.base_url}/v1/tools/call"
        self.session_id = None
        
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools from MCP server"""
        async with httpx.AsyncClient() as client:
            response = await client.get(self.tools_endpoint)
            response.raise_for_status()
            data = response.json()
            return data.get("tools", [])
    
    async def call_tool(self, name: str, args: Dict[str, Any]) -> Any:
        """Call a tool on the MCP server"""
        async with httpx.AsyncClient() as client:
            payload = {"name": name, "args": args}
            response = await client.post(self.call_endpoint, json=payload)
            response.raise_for_status()
            result = response.json()
            if result.get("status") == "error":
                raise Exception(result.get("error", "Tool call failed"))
            return result.get("output", result)


# -----------------------------------------------------------------------------
# LangChain Tools from MCP (will be created per agent instance)
# -----------------------------------------------------------------------------

class MCPTool(BaseTool):
    """Custom async tool for MCP server calls"""
    mcp_client: Any
    tool_name: str
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    def _run(self, **kwargs) -> str:
        """Sync wrapper - should not be called directly"""
        raise NotImplementedError("This tool must be called asynchronously")
    
    async def _arun(self, **kwargs) -> str:
        """Async execution"""
        try:
            result = await self.mcp_client.call_tool(self.tool_name, kwargs)
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error: {str(e)}"

def create_mcp_tool_func(tool_name: str, description: str, input_schema: dict, client: MCPClient):
    """Create a custom async tool for a specific MCP tool"""
    
    # Build args schema from input_schema
    args_schema = None
    if input_schema and input_schema.get("properties"):
        from pydantic import create_model
        from typing import Optional
        
        properties = input_schema.get("properties", {})
        required = input_schema.get("required", [])
        
        field_definitions = {}
        for prop_name, prop_def in properties.items():
            prop_type = prop_def.get("type", "string")
            # Map JSON schema types to Python types
            if prop_type == "string":
                field_type = str
            elif prop_type == "integer":
                field_type = int
            elif prop_type == "number":
                field_type = float
            elif prop_type == "boolean":
                field_type = bool
            else:
                field_type = str
            
            # Make optional if not required
            if prop_name not in required:
                field_type = Optional[field_type]
            
            field_definitions[prop_name] = (field_type, Field(description=prop_def.get("description", "")))
        
        if field_definitions:
            ArgsModel = create_model(f"{tool_name}Args", **field_definitions)
            args_schema = ArgsModel
    
    # Create custom tool instance
    tool_instance = MCPTool(
        name=tool_name,
        description=description,
        mcp_client=client,
        tool_name=tool_name,
        args_schema=args_schema,
    )
    
    return tool_instance

async def create_mcp_tools(client: MCPClient) -> List:
    """Create LangChain tools from MCP server tools"""
    tools_info = await client.list_tools()
    langchain_tools = []
    
    for tool_info in tools_info:
        tool_name = tool_info["name"]
        tool_desc = tool_info.get("description", "")
        input_schema = tool_info.get("inputSchema", {})
        mcp_tool = create_mcp_tool_func(tool_name, tool_desc, input_schema, client)
        langchain_tools.append(mcp_tool)
    
    return langchain_tools


# -----------------------------------------------------------------------------
# Agent State
# -----------------------------------------------------------------------------
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


# -----------------------------------------------------------------------------
# LangGraph Agent
# -----------------------------------------------------------------------------
async def create_agent(mcp_client: MCPClient):
    """Create LangGraph agent with MCP tools"""
    
    # Initialize OpenAI
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # Get MCP tools and bind to LLM
    mcp_tools = await create_mcp_tools(mcp_client)
    llm_with_tools = llm.bind_tools(mcp_tools)
    
    # Create tool node
    tool_node = ToolNode(mcp_tools)
    
    # Define graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    async def agent_node(state: AgentState):
        response = await llm_with_tools.ainvoke(state["messages"])
        return {"messages": [response]}
    
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node)
    
    # Add edges
    workflow.set_entry_point("agent")
    workflow.add_conditional_edges(
        "agent",
        lambda state: _should_continue(state),
        {
            "continue": "tools",
            "end": END
        }
    )
    workflow.add_edge("tools", "agent")
    
    return workflow.compile()


def _should_continue(state: AgentState) -> str:
    """Determine if we should continue or end"""
    messages = state["messages"]
    last_message = messages[-1]
    
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "continue"
    return "end"


# -----------------------------------------------------------------------------
# Main Agent Interface
# -----------------------------------------------------------------------------
class SQLAgent:
    """Natural language to SQL agent using MCP tools"""
    
    def __init__(self):
        self.graph = None
        self.mcp_client = MCPClient()
    
    async def initialize(self):
        """Initialize the agent graph"""
        self.graph = await create_agent(self.mcp_client)
        logger.info("✅ SQL Agent initialized with MCP tools")
    
    async def query(self, user_input: str, db_key: str = None) -> dict:
        """
        Process natural language query and execute SQL
        
        Args:
            user_input: Natural language query
            db_key: Optional database key (if not provided, agent will need to infer)
        
        Returns:
            Dictionary with 'result' (response text) and 'sql_query' (SQL query executed)
        """
        if not self.graph:
            await self.initialize()
        
        # Build initial message with context
        system_context = """You are a SQL query expert. Your job is to:
1. Understand natural language questions about databases
2. Use available tools to explore database schema (list_tables, get_table_schema)
3. Generate appropriate SQL queries
4. Execute queries using run_sql_query tool
5. Return results in a clear, formatted way

Available tools:
- list_tables(db_key): Lists all tables in a database
- get_table_schema(db_key, table_name): Gets schema for a table
- run_sql_query(db_key, query): Executes a SQL query

Always start by exploring the database structure before generating queries.
"""
        
        messages = [
            HumanMessage(content=f"{system_context}\n\nUser question: {user_input}")
        ]
        
        # Add db_key context if provided
        if db_key:
            messages.append(AIMessage(content=f"Note: Use database key '{db_key}' for all operations."))
        
        # Run agent with recursion limit
        state = {"messages": messages}
        config = {"recursion_limit": 50}
        final_state = await self.graph.ainvoke(state, config)
        
        # Extract SQL queries from message history
        sql_queries = []
        for msg in final_state["messages"]:
            # Check AIMessage for tool_calls (where SQL query is specified)
            if isinstance(msg, AIMessage) and hasattr(msg, "tool_calls") and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    # Handle both dict and object formats
                    tool_name = None
                    tool_args = {}
                    
                    if isinstance(tool_call, dict):
                        tool_name = tool_call.get("name")
                        tool_args = tool_call.get("args", {})
                    else:
                        # Object format
                        tool_name = getattr(tool_call, "name", None)
                        tool_args = getattr(tool_call, "args", {})
                    
                    if tool_name == "run_sql_query" and "query" in tool_args:
                        sql_queries.append(tool_args["query"])
        
        # Extract final response
        last_message = final_state["messages"][-1]
        if isinstance(last_message, AIMessage):
            result_text = last_message.content
        elif isinstance(last_message, ToolMessage):
            result_text = last_message.content
        else:
            result_text = str(last_message)
        
        # Return both result and SQL queries
        return {
            "result": result_text,
            "sql_query": sql_queries[-1] if sql_queries else None
        }


# -----------------------------------------------------------------------------
# Standalone execution
# -----------------------------------------------------------------------------
async def main():
    """Test the agent"""
    agent = SQLAgent()
    
    # Example query
    query = "Show me the projects i currently have in the database that are yet to start or havn't started yet. or on_hold"
    response = await agent.query(query, db_key="PROJECT_DB_URL")
    print("\n" + "="*50)
    print("AGENT RESULT:")
    print("="*50)
    print(response.get("result", response))
    if response.get("sql_query"):
        print("\n" + "="*50)
        print("SQL QUERY:")
        print("="*50)
        print(response["sql_query"])


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

