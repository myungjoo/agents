"""
LLM Request and Response Models

Defines the standardized data structures for LLM interactions
across different providers with validation and serialization.
"""

from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class LLMMessage(BaseModel):
    """A single message in an LLM conversation."""
    role: str = Field(..., description="Message role: system, user, or assistant")
    content: str = Field(..., description="Message content")
    name: Optional[str] = Field(None, description="Optional name for the message sender")
    function_call: Optional[Dict[str, Any]] = Field(None, description="Function call data")


class LLMRequest(BaseModel):
    """Standardized request structure for LLM providers."""
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    messages: List[LLMMessage] = Field(..., description="Conversation messages")
    model: Optional[str] = Field(None, description="Specific model to use")
    max_tokens: Optional[int] = Field(4096, description="Maximum tokens to generate")
    temperature: Optional[float] = Field(0.7, description="Sampling temperature")
    top_p: Optional[float] = Field(None, description="Nucleus sampling parameter")
    stream: bool = Field(False, description="Whether to stream the response")
    functions: Optional[List[Dict[str, Any]]] = Field(None, description="Available functions")
    function_call: Optional[Union[str, Dict[str, str]]] = Field(None, description="Function call mode")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        extra = "allow"


class LLMUsage(BaseModel):
    """Token usage statistics for an LLM response."""
    prompt_tokens: int = Field(0, description="Tokens used in the prompt")
    completion_tokens: int = Field(0, description="Tokens used in the completion")
    total_tokens: int = Field(0, description="Total tokens used")
    estimated_cost: Optional[float] = Field(None, description="Estimated cost in USD")


class LLMResponse(BaseModel):
    """Standardized response structure from LLM providers."""
    request_id: str = Field(..., description="ID of the original request")
    content: str = Field("", description="Generated text content")
    finish_reason: Optional[str] = Field(None, description="Reason for completion")
    function_call: Optional[Dict[str, Any]] = Field(None, description="Function call result")
    usage: Optional[LLMUsage] = Field(None, description="Token usage statistics")
    model: Optional[str] = Field(None, description="Model used for generation")
    provider: str = Field(..., description="Provider name")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    latency_ms: Optional[float] = Field(None, description="Response latency in milliseconds")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    error: Optional[str] = Field(None, description="Error message if request failed")
    
    class Config:
        extra = "allow"


class LLMStreamChunk(BaseModel):
    """A single chunk in a streaming LLM response."""
    request_id: str = Field(..., description="ID of the original request")
    content: str = Field("", description="Incremental content")
    finish_reason: Optional[str] = Field(None, description="Reason for completion")
    is_final: bool = Field(False, description="Whether this is the final chunk")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")