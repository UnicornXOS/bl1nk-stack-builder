"""
MCP (Model Context Protocol) tools endpoints for bl1nk-agent-builder
Provides REST API for MCP tool discovery and invocation
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Pydantic models
class ToolMetadata(BaseModel):
    """MCP tool metadata"""
    id: str = Field(..., description="Tool identifier")
    name: str = Field(..., description="Tool name")
    description: Optional[str] = Field(None, description="Tool description")
    input_schema: Dict[str, Any] = Field(..., description="Input JSON schema")


class ToolListResponse(BaseModel):
    """Response for tool list"""
    tools: List[ToolMetadata]


class ToolCallRequest(BaseModel):
    """Request model for tool invocation"""
    tool_id: str = Field(..., description="Tool to invoke")
    inputs: Dict[str, Any] = Field(..., description="Tool inputs")
    request_id: Optional[str] = Field(None, description="Request ID for idempotency")


class ToolCallResponse(BaseModel):
    """Response model for tool call"""
    result: Optional[Dict[str, Any]] = Field(None, description="Tool execution result")
    error: Optional[str] = Field(None, description="Error message if execution failed")


router = APIRouter()

# In-memory MCP tools registry (in production, this would be in database)
mcp_tools_registry = {}
tool_calls_db = {}

# Predefined MCP tools
DEFAULT_TOOLS = [
    {
        "id": "search",
        "name": "Web Search",
        "description": "Search the web for information",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "max_results": {"type": "integer", "default": 10}
            },
            "required": ["query"]
        }
    },
    {
        "id": "calculator",
        "name": "Calculator",
        "description": "Perform mathematical calculations",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "Mathematical expression"},
                "precision": {"type": "integer", "default": 2}
            },
            "required": ["expression"]
        }
    },
    {
        "id": "weather",
        "name": "Weather Lookup",
        "description": "Get weather information for a location",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "Location to get weather for"},
                "units": {"type": "string", "enum": ["celsius", "fahrenheit"], "default": "celsius"}
            },
            "required": ["location"]
        }
    }
]

# Initialize default tools
for tool in DEFAULT_TOOLS:
    mcp_tools_registry[tool["id"]] = tool

@router.get("/mcp/tools/list", response_model=ToolListResponse)
async def list_mcp_tools():
    """List all available MCP tools"""
    
    tools = []
    for tool_id, tool_data in mcp_tools_registry.items():
        tools.append(ToolMetadata(**tool_data))
    
    return ToolListResponse(tools=tools)


@router.get("/mcp/tools/{tool_id}")
async def get_mcp_tool(tool_id: str):
    """Get MCP tool definition"""
    
    if tool_id not in mcp_tools_registry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool {tool_id} not found"
        )
    
    tool_data = mcp_tools_registry[tool_id]
    
    return {
        "tool_id": tool_id,
        "tool": tool_data
    }


@router.post("/mcp/tools/call", response_model=ToolCallResponse)
async def call_mcp_tool(request: ToolCallRequest):
    """Invoke an MCP tool"""
    
    if request.tool_id not in mcp_tools_registry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool {request.tool_id} not found"
        )
    
    tool_data = mcp_tools_registry[request.tool_id]
    
    # Generate call ID
    call_id = f"call_{len(tool_calls_db) + 1}"
    
    # Store call record
    call_data = {
        "call_id": call_id,
        "tool_id": request.tool_id,
        "inputs": request.inputs,
        "request_id": request.request_id,
        "status": "pending",
        "created_at": datetime.now().isoformat()
    }
    
    tool_calls_db[call_id] = call_data
    
    # Simulate tool execution
    try:
        # Mark as processing
        call_data["status"] = "processing"
        
        # Execute tool based on type
        result = await execute_tool(request.tool_id, request.inputs)
        
        call_data["status"] = "completed"
        call_data["result"] = result
        
        logger.info(f"MCP tool call completed: {call_id}")
        
        return ToolCallResponse(result=result)
        
    except Exception as e:
        call_data["status"] = "failed"
        call_data["error"] = str(e)
        
        logger.error(f"MCP tool call failed: {call_id} - {e}")
        
        return ToolCallResponse(error=str(e))


async def execute_tool(tool_id: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Execute an MCP tool (simulated implementation)"""
    
    if tool_id == "search":
        # Simulate web search
        query = inputs.get("query", "")
        max_results = inputs.get("max_results", 10)
        
        return {
            "query": query,
            "results": [
                {
                    "title": f"Result {i+1} for '{query}'",
                    "url": f"https://example.com/result{i+1}",
                    "snippet": f"This is a simulated search result for '{query}'"
                }
                for i in range(min(max_results, 5))
            ],
            "total_results": max_results
        }
    
    elif tool_id == "calculator":
        # Simulate calculator
        expression = inputs.get("expression", "")
        precision = inputs.get("precision", 2)
        
        try:
            # Simple evaluation (in production, use a proper math parser)
            result = eval(expression)  # Note: eval is dangerous, use safe evaluation in production
            return {
                "expression": expression,
                "result": round(result, precision),
                "precision": precision
            }
        except Exception as e:
            raise ValueError(f"Invalid expression: {e}")
    
    elif tool_id == "weather":
        # Simulate weather lookup
        location = inputs.get("location", "")
        units = inputs.get("units", "celsius")
        
        # Simulate weather data
        temp_celsius = 22.5
        if units == "fahrenheit":
            temp = round(temp_celsius * 9/5 + 32, 1)
            temp_unit = "°F"
        else:
            temp = temp_celsius
            temp_unit = "°C"
        
        return {
            "location": location,
            "temperature": temp,
            "unit": temp_unit,
            "condition": "Partly Cloudy",
            "humidity": 65,
            "wind_speed": 10,
            "forecast": [
                {"day": "Today", "high": temp + 5, "low": temp - 3, "condition": "Sunny"},
                {"day": "Tomorrow", "high": temp + 2, "low": temp - 5, "condition": "Cloudy"}
            ]
        }
    
    else:
        raise ValueError(f"Unknown tool: {tool_id}")


@router.get("/mcp/tools/calls/{call_id}")
async def get_tool_call(call_id: str):
    """Get tool call status and result"""
    
    if call_id not in tool_calls_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool call {call_id} not found"
        )
    
    call_data = tool_calls_db[call_id]
    
    return {
        "call_id": call_id,
        "tool_id": call_data["tool_id"],
        "status": call_data["status"],
        "created_at": call_data["created_at"],
        "result": call_data.get("result"),
        "error": call_data.get("error")
    }


@router.get("/mcp/tools/calls")
async def list_tool_calls(
    tool_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """List tool calls with optional filtering"""
    
    filtered_calls = []
    
    for call_id, call_data in tool_calls_db.items():
        # Apply filters
        if tool_id and call_data["tool_id"] != tool_id:
            continue
        if status and call_data["status"] != status:
            continue
        
        filtered_calls.append(call_data)
    
    # Apply pagination
    paginated_calls = filtered_calls[offset:offset + limit]
    
    return {
        "calls": paginated_calls,
        "total": len(filtered_calls),
        "limit": limit,
        "offset": offset
    }


@router.post("/mcp/tools/register")
async def register_mcp_tool(tool: ToolMetadata):
    """Register a new MCP tool"""
    
    if tool.id in mcp_tools_registry:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tool {tool.id} already exists"
        )
    
    mcp_tools_registry[tool.id] = tool.dict()
    
    logger.info(f"MCP tool registered: {tool.id}")
    
    return {"message": f"Tool {tool.id} registered successfully"}


@router.delete("/mcp/tools/{tool_id}")
async def unregister_mcp_tool(tool_id: str):
    """Unregister an MCP tool"""
    
    if tool_id not in mcp_tools_registry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool {tool_id} not found"
        )
    
    del mcp_tools_registry[tool_id]
    
    logger.info(f"MCP tool unregistered: {tool_id}")
    
    return {"message": f"Tool {tool_id} unregistered successfully"}