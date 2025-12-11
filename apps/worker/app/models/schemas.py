"""
Models and schemas for bl1nk-agent-builder
Pydantic models for API requests and responses
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum


# Enums
class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(str, Enum):
    CHAT = "chat"
    EMBEDDING = "embedding"
    RERANK = "rerank"
    SKILL_INVOCATION = "skill_invocation"
    MCP_TOOL_CALL = "mcp_tool_call"


class TaskPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


# Base models
class BaseResponse(BaseModel):
    """Base response model"""
    success: bool = True
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = False
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


# Task models
class TaskBase(BaseModel):
    """Base task model"""
    task_type: TaskType
    input_data: Dict[str, Any]
    priority: TaskPriority = TaskPriority.NORMAL
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TaskCreateRequest(TaskBase):
    """Task creation request"""
    pass


class TaskResponse(BaseModel):
    """Task response model"""
    task_id: int
    status: TaskStatus
    task_type: Optional[TaskType] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    progress: Optional[int] = Field(default=0, ge=0, le=100)


class TaskListResponse(BaseModel):
    """Task list response"""
    tasks: List[TaskResponse]
    total: int
    limit: int
    offset: int


# Webhook models
class WebhookPayload(BaseModel):
    """Base webhook payload"""
    source: str
    external_id: str
    user_id: str
    conversation_id: Optional[str] = None
    message: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WebhookAckResponse(BaseModel):
    """Webhook acknowledgment response"""
    status: str = "accepted"
    task_id: Optional[int] = None
    message: Optional[str] = None


# User models
class UserBase(BaseModel):
    """Base user model"""
    email: str
    display_name: Optional[str] = None
    tier: str = "free"


class UserCreateRequest(UserBase):
    """User creation request"""
    pass


class UserResponse(BaseModel):
    """User response model"""
    user_id: str
    email: str
    display_name: Optional[str] = None
    tier: str
    created_at: datetime
    updated_at: Optional[datetime] = None


# Provider models
class ProviderRequest(BaseModel):
    """Provider request model"""
    provider: str
    model: str
    prompt: str
    parameters: Dict[str, Any] = Field(default_factory=dict)


class ProviderResponse(BaseModel):
    """Provider response model"""
    response: str
    model: str
    tokens_used: Optional[Dict[str, int]] = None
    cost: Optional[float] = None
    provider: str
    response_time_ms: Optional[float] = None


# Embedding models
class EmbeddingRequest(BaseModel):
    """Embedding request model"""
    text: str
    model: str = "gamma-300"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EmbeddingResponse(BaseModel):
    """Embedding response model"""
    embedding: List[float]
    model: str
    dimension: int
    tokens_used: Optional[int] = None
    cost: Optional[float] = None


# Skill models
class SkillDefinition(BaseModel):
    """Skill definition model"""
    skill_id: str
    name: str
    description: Optional[str] = None
    input_schema: Dict[str, Any]
    output_schema: Optional[Dict[str, Any]] = None
    auth: Optional[str] = None
    handler_url: str


class SkillInvokeRequest(BaseModel):
    """Skill invocation request"""
    skill_id: str
    inputs: Dict[str, Any]
    context: Dict[str, Any] = Field(default_factory=dict)
    request_id: Optional[str] = None


class SkillInvokeResponse(BaseModel):
    """Skill invocation response"""
    invocation_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# MCP models
class MCPToolMetadata(BaseModel):
    """MCP tool metadata"""
    id: str
    name: str
    description: Optional[str] = None
    input_schema: Dict[str, Any]


class MCPToolCallRequest(BaseModel):
    """MCP tool call request"""
    tool_id: str
    inputs: Dict[str, Any]
    request_id: Optional[str] = None


class MCPToolCallResponse(BaseModel):
    """MCP tool call response"""
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# Health models
class HealthStatus(BaseModel):
    """Health status model"""
    status: str
    service: str
    version: str
    timestamp: datetime


class DetailedHealthResponse(BaseModel):
    """Detailed health response"""
    overall_status: str
    api: HealthStatus
    database: Dict[str, Any]
    redis: Dict[str, Any]
    system: Dict[str, Any]
    providers: Dict[str, str]


# Analytics models
class AnalyticsData(BaseModel):
    """Analytics data model"""
    date: str
    metric: str
    value: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class UserAnalytics(BaseModel):
    """User analytics model"""
    user_id: str
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    total_cost: float
    last_activity: Optional[datetime] = None


# Admin models
class AdminStats(BaseModel):
    """Admin statistics model"""
    total_users: int
    total_tasks: int
    active_tasks: int
    total_cost: float
    uptime_hours: float
    memory_usage_mb: float
    cpu_usage_percent: float


class SystemConfig(BaseModel):
    """System configuration model"""
    key: str
    value: Any
    description: Optional[str] = None
    updated_at: Optional[datetime] = None


# Notification models
class NotificationRequest(BaseModel):
    """Notification request model"""
    user_id: str
    title: str
    message: str
    type: str = "info"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class NotificationResponse(BaseModel):
    """Notification response model"""
    notification_id: str
    status: str
    delivered_at: Optional[datetime] = None


# Audit models
class AuditLog(BaseModel):
    """Audit log model"""
    log_id: str
    user_id: Optional[str] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


# Rate limiting models
class RateLimitInfo(BaseModel):
    """Rate limit information model"""
    limit: int
    remaining: int
    reset_time: datetime
    scope: str


class RateLimitExceededResponse(BaseModel):
    """Rate limit exceeded response"""
    success: bool = False
    error: str = "Rate limit exceeded"
    rate_limit_info: RateLimitInfo