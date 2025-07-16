"""
Model Context Protocol (MCP) Protocol Definitions

Defines the message structures and communication patterns for MCP.
"""

from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel, Field
from datetime import datetime
import uuid
from enum import Enum


class MCPMessageType(str, Enum):
    """MCP message types."""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"


class MCPMethod(str, Enum):
    """MCP method names."""
    # Initialization
    INITIALIZE = "initialize"
    INITIALIZED = "initialized"
    
    # Resource management
    LIST_RESOURCES = "resources/list"
    READ_RESOURCE = "resources/read"
    SUBSCRIBE_RESOURCE = "resources/subscribe"
    UNSUBSCRIBE_RESOURCE = "resources/unsubscribe"
    
    # Tool management
    LIST_TOOLS = "tools/list"
    CALL_TOOL = "tools/call"
    
    # Prompt management
    LIST_PROMPTS = "prompts/list"
    GET_PROMPT = "prompts/get"
    
    # Completion
    COMPLETE = "completion/complete"
    
    # Logging
    LOG = "notifications/log"
    PROGRESS = "notifications/progress"


class MCPCapabilities(BaseModel):
    """MCP capabilities description."""
    experimental: Dict[str, Any] = Field(default_factory=dict)
    roots: Optional[Dict[str, Any]] = Field(None, description="Root capabilities")
    sampling: Optional[Dict[str, Any]] = Field(None, description="Sampling capabilities")


class MCPClientInfo(BaseModel):
    """MCP client information."""
    name: str = Field(..., description="Client name")
    version: str = Field(..., description="Client version")


class MCPServerInfo(BaseModel):
    """MCP server information."""
    name: str = Field(..., description="Server name")
    version: str = Field(..., description="Server version")


class MCPResource(BaseModel):
    """MCP resource definition."""
    uri: str = Field(..., description="Resource URI")
    name: str = Field(..., description="Resource name")
    description: Optional[str] = Field(None, description="Resource description")
    mimeType: Optional[str] = Field(None, description="Resource MIME type")


class MCPTool(BaseModel):
    """MCP tool definition."""
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    inputSchema: Dict[str, Any] = Field(..., description="JSON schema for tool input")


class MCPPrompt(BaseModel):
    """MCP prompt definition."""
    name: str = Field(..., description="Prompt name")
    description: str = Field(..., description="Prompt description")
    arguments: Optional[List[Dict[str, Any]]] = Field(None, description="Prompt arguments")


class MCPMessage(BaseModel):
    """Base MCP message."""
    jsonrpc: str = Field("2.0", description="JSON-RPC version")
    id: Optional[Union[str, int]] = Field(None, description="Message ID")
    method: Optional[str] = Field(None, description="Method name")
    params: Optional[Dict[str, Any]] = Field(None, description="Method parameters")
    result: Optional[Any] = Field(None, description="Method result")
    error: Optional[Dict[str, Any]] = Field(None, description="Error details")
    
    @classmethod
    def create_request(cls, method: str, params: Optional[Dict[str, Any]] = None, id: Optional[str] = None) -> "MCPMessage":
        """Create a request message."""
        return cls(
            id=id or str(uuid.uuid4()),
            method=method,
            params=params or {}
        )
    
    @classmethod
    def create_response(cls, id: Union[str, int], result: Any = None, error: Optional[Dict[str, Any]] = None) -> "MCPMessage":
        """Create a response message."""
        return cls(
            id=id,
            result=result,
            error=error
        )
    
    @classmethod
    def create_notification(cls, method: str, params: Optional[Dict[str, Any]] = None) -> "MCPMessage":
        """Create a notification message."""
        return cls(
            method=method,
            params=params or {}
        )
    
    def is_request(self) -> bool:
        """Check if message is a request."""
        return self.method is not None and self.id is not None
    
    def is_response(self) -> bool:
        """Check if message is a response."""
        return self.id is not None and self.method is None
    
    def is_notification(self) -> bool:
        """Check if message is a notification."""
        return self.method is not None and self.id is None
    
    def is_error(self) -> bool:
        """Check if message is an error."""
        return self.error is not None


class MCPRequest(MCPMessage):
    """MCP request message."""
    method: str = Field(..., description="Method name")
    id: Union[str, int] = Field(..., description="Request ID")
    params: Dict[str, Any] = Field(default_factory=dict, description="Method parameters")


class MCPResponse(MCPMessage):
    """MCP response message."""
    id: Union[str, int] = Field(..., description="Request ID")
    
    def __init__(self, **data):
        super().__init__(**data)
        # Ensure we have either result or error, but not both
        if self.result is not None and self.error is not None:
            raise ValueError("Response cannot have both result and error")
        if self.result is None and self.error is None:
            raise ValueError("Response must have either result or error")


class MCPNotification(MCPMessage):
    """MCP notification message."""
    method: str = Field(..., description="Method name")
    params: Dict[str, Any] = Field(default_factory=dict, description="Method parameters")


class MCPError(BaseModel):
    """MCP error details."""
    code: int = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    data: Optional[Any] = Field(None, description="Additional error data")


class MCPInitializeParams(BaseModel):
    """Parameters for initialize request."""
    protocolVersion: str = Field("2024-11-05", description="MCP protocol version")
    capabilities: MCPCapabilities = Field(default_factory=MCPCapabilities)
    clientInfo: MCPClientInfo = Field(..., description="Client information")


class MCPInitializeResult(BaseModel):
    """Result for initialize request."""
    protocolVersion: str = Field("2024-11-05", description="MCP protocol version")
    capabilities: MCPCapabilities = Field(default_factory=MCPCapabilities)
    serverInfo: MCPServerInfo = Field(..., description="Server information")


class MCPListResourcesResult(BaseModel):
    """Result for list resources request."""
    resources: List[MCPResource] = Field(default_factory=list)


class MCPReadResourceParams(BaseModel):
    """Parameters for read resource request."""
    uri: str = Field(..., description="Resource URI")


class MCPReadResourceResult(BaseModel):
    """Result for read resource request."""
    contents: List[Dict[str, Any]] = Field(..., description="Resource contents")


class MCPListToolsResult(BaseModel):
    """Result for list tools request."""
    tools: List[MCPTool] = Field(default_factory=list)


class MCPCallToolParams(BaseModel):
    """Parameters for call tool request."""
    name: str = Field(..., description="Tool name")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Tool arguments")


class MCPCallToolResult(BaseModel):
    """Result for call tool request."""
    content: List[Dict[str, Any]] = Field(..., description="Tool result content")
    isError: bool = Field(False, description="Whether the result is an error")


class MCPListPromptsResult(BaseModel):
    """Result for list prompts request."""
    prompts: List[MCPPrompt] = Field(default_factory=list)


class MCPGetPromptParams(BaseModel):
    """Parameters for get prompt request."""
    name: str = Field(..., description="Prompt name")
    arguments: Optional[Dict[str, Any]] = Field(None, description="Prompt arguments")


class MCPGetPromptResult(BaseModel):
    """Result for get prompt request."""
    description: Optional[str] = Field(None, description="Prompt description")
    messages: List[Dict[str, Any]] = Field(..., description="Prompt messages")


class MCPProgressNotificationParams(BaseModel):
    """Parameters for progress notification."""
    progressToken: Union[str, int] = Field(..., description="Progress token")
    progress: float = Field(..., description="Progress value (0.0 to 1.0)")
    total: Optional[float] = Field(None, description="Total progress value")


class MCPLogNotificationParams(BaseModel):
    """Parameters for log notification."""
    level: str = Field(..., description="Log level")
    logger: Optional[str] = Field(None, description="Logger name")
    data: Any = Field(..., description="Log data")


# Error codes as defined in MCP specification
class MCPErrorCodes:
    """Standard MCP error codes."""
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    
    # MCP-specific error codes
    INVALID_RESOURCE_URI = -32001
    RESOURCE_NOT_FOUND = -32002
    RESOURCE_ACCESS_DENIED = -32003
    TOOL_NOT_FOUND = -32004
    TOOL_EXECUTION_ERROR = -32005