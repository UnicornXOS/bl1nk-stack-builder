"""
Configuration settings for bl1nk-agent-builder FastAPI Worker
Uses Pydantic Settings for environment variable management
"""

import os
from typing import List, Optional
from functools import lru_cache

from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # =============================================================================
    # APPLICATION SETTINGS
    # =============================================================================
    
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    reload: bool = Field(default=False, env="RELOAD")
    
    # Server settings
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    workers: int = Field(default=1, env="WORKERS")
    
    # SSL settings
    ssl_cert: Optional[str] = Field(default=None, env="SSL_CERT")
    ssl_key: Optional[str] = Field(default=None, env="SSL_KEY")
    ssl_ca_certs: Optional[str] = Field(default=None, env="SSL_CA_CERTS")
    ssl_cert_reqs: Optional[int] = Field(default=None, env="SSL_CERT_REQS")
    
    # Trusted hosts for security
    trusted_hosts: Optional[List[str]] = Field(default=None, env="TRUSTED_HOSTS")
    
    # =============================================================================
    # DATABASE SETTINGS
    # =============================================================================
    
    database_url: str = Field(
        ...,
        env="DATABASE_URL",
        description="PostgreSQL connection string"
    )
    
    # Connection pool settings
    db_pool_min: int = Field(default=5, env="DB_POOL_MIN")
    db_pool_max: int = Field(default=20, env="DB_POOL_MAX")
    db_pool_timeout: int = Field(default=30, env="DB_POOL_TIMEOUT")
    
    # =============================================================================
    # REDIS SETTINGS
    # =============================================================================
    
    redis_url: str = Field(
        ...,
        env="REDIS_URL",
        description="Redis connection URL"
    )
    
    # Queue settings
    task_queue_name: str = Field(default="bl1nk_tasks", env="TASK_QUEUE_NAME")
    max_workers: int = Field(default=10, env="MAX_WORKERS")
    
    # Cache settings
    cache_ttl: int = Field(default=3600, env="CACHE_TTL")
    embedding_cache_ttl: int = Field(default=86400, env="EMBEDDING_CACHE_TTL")
    
    # =============================================================================
    # LLM PROVIDERS
    # =============================================================================
    
    # OpenRouter
    openrouter_api_key: Optional[str] = Field(default=None, env="OPENROUTER_API_KEY")
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        env="OPENROUTER_BASE_URL"
    )
    
    # Cloudflare Gateway
    cloudflare_api_token: Optional[str] = Field(default=None, env="CLOUDFLARE_API_TOKEN")
    cloudflare_account_id: Optional[str] = Field(default=None, env="CLOUDFLARE_ACCOUNT_ID")
    
    # AWS Bedrock
    bedrock_region: str = Field(default="us-east-1", env="BEDROCK_REGION")
    bedrock_access_key_id: Optional[str] = Field(default=None, env="BEDROCK_ACCESS_KEY_ID")
    bedrock_secret_access_key: Optional[str] = Field(default=None, env="BEDROCK_SECRET_ACCESS_KEY")
    
    # =============================================================================
    # EMBEDDINGS
    # =============================================================================
    
    embedding_provider: str = Field(default="openrouter", env="EMBEDDING_PROVIDER")
    embedding_model: str = Field(default="gamma-300", env="EMBEDDING_MODEL")
    embedding_dimension: int = Field(default=768, env="EMBEDDING_DIMENSION")
    
    # =============================================================================
    # SECURITY
    # =============================================================================
    
    jwt_secret_key: str = Field(
        ...,
        env="JWT_SECRET_KEY",
        description="Secret key for JWT token signing"
    )
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(default=1440, env="JWT_EXPIRE_MINUTES")
    
    admin_api_key: Optional[str] = Field(default=None, env="ADMIN_API_KEY")
    
    encryption_key: Optional[str] = Field(default=None, env="ENCRYPTION_KEY")
    
    # =============================================================================
    # MONITORING AND LOGGING
    # =============================================================================
    
    # OpenTelemetry
    otel_exporter_otlp_endpoint: Optional[str] = Field(
        default=None,
        env="OTEL_EXPORTER_OTLP_ENDPOINT"
    )
    otel_service_name: str = Field(default="bl1nk-worker", env="OTEL_SERVICE_NAME")
    otel_service_version: str = Field(default="1.0.0", env="OTEL_SERVICE_VERSION")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    log_file: bool = Field(default=False, env="LOG_FILE")
    
    # =============================================================================
    # FEATURE FLAGS
    # =============================================================================
    
    enable_rag: bool = Field(default=True, env="ENABLE_RAG")
    enable_mcp: bool = Field(default=True, env="ENABLE_MCP")
    enable_skills: bool = Field(default=True, env="ENABLE_SKILLS")
    enable_multi_agent: bool = Field(default=False, env="ENABLE_MULTI_AGENT")
    
    # =============================================================================
    # RATE LIMITING
    # =============================================================================
    
    rate_limit_per_minute: int = Field(default=100, env="RATE_LIMIT_PER_MINUTE")
    rate_limit_per_hour: int = Field(default=1000, env="RATE_LIMIT_PER_HOUR")
    
    # =============================================================================
    # TASK PROCESSING
    # =============================================================================
    
    task_timeout: int = Field(default=300, env="TASK_TIMEOUT")
    task_retry_attempts: int = Field(default=3, env="TASK_RETRY_ATTEMPTS")
    task_retry_delay: int = Field(default=5, env="TASK_RETRY_DELAY")
    
    # SSE settings
    sse_heartbeat_interval: int = Field(default=30, env="SSE_HEARTBEAT_INTERVAL")
    sse_timeout: int = Field(default=3600, env="SSE_TIMEOUT")
    
    # =============================================================================
    # PROVIDER ROUTING
    # =============================================================================
    
    # Provider priorities (1=highest, 10=lowest)
    provider_priority_openrouter: int = Field(default=1, env="PROVIDER_PRIORITY_OPENROUTER")
    provider_priority_cloudflare: int = Field(default=2, env="PROVIDER_PRIORITY_CLOUDFLARE")
    provider_priority_bedrock: int = Field(default=3, env="PROVIDER_PRIORITY_BEDROCK")
    
    # Failover settings
    failover_enabled: bool = Field(default=True, env="FAILOVER_ENABLED")
    failover_max_attempts: int = Field(default=3, env="FAILOVER_MAX_ATTEMPTS")
    failover_backoff_base: float = Field(default=0.5, env="FAILOVER_BACKOFF_BASE")
    failover_backoff_factor: float = Field(default=2.0, env="FAILOVER_BACKOFF_FACTOR")
    
    # =============================================================================
    # VECTOR SEARCH
    # =============================================================================
    
    vector_index_type: str = Field(default="ivfflat", env="VECTOR_INDEX_TYPE")
    vector_index_lists: int = Field(default=100, env="VECTOR_INDEX_LISTS")
    vector_similarity_threshold: float = Field(default=0.8, env="VECTOR_SIMILARITY_THRESHOLD")
    
    # RAG settings
    rag_chunk_size: int = Field(default=1000, env="RAG_CHUNK_SIZE")
    rag_chunk_overlap: int = Field(default=200, env="RAG_CHUNK_OVERLAP")
    rag_top_k: int = Field(default=5, env="RAG_TOP_K")
    rag_rerank_enabled: bool = Field(default=True, env="RAG_RERANK_ENABLED")
    
    # =============================================================================
    # COST CONTROL
    # =============================================================================
    
    cost_limit_per_task: float = Field(default=0.50, env="COST_LIMIT_PER_TASK")
    cost_limit_per_user_daily: float = Field(default=10.00, env="COST_LIMIT_PER_USER_DAILY")
    cost_limit_per_user_monthly: float = Field(default=100.00, env="COST_LIMIT_PER_USER_MONTHLY")
    
    # =============================================================================
    # SKILLS & MCP
    # =============================================================================
    
    skills_registry_path: str = Field(default="/app/skills", env="SKILLS_REGISTRY_PATH")
    skills_auto_discovery: bool = Field(default=True, env="SKILLS_AUTO_DISCOVERY")
    skills_timeout: int = Field(default=60, env="SKILLS_TIMEOUT")
    
    mcp_tools_registry_path: str = Field(default="/app/mcp-tools", env="MCP_TOOLS_REGISTRY_PATH")
    mcp_tools_auto_discovery: bool = Field(default=True, env="MCP_TOOLS_AUTO_DISCOVERY")
    mcp_tools_timeout: int = Field(default=120, env="MCP_TOOLS_TIMEOUT")
    
    # =============================================================================
    # WEBHOOK SECURITY
    # =============================================================================
    
    webhook_signature_header_prefix: str = Field(
        default="X-Webhook",
        env="WEBHOOK_SIGNATURE_HEADER_PREFIX"
    )
    webhook_signature_algorithm: str = Field(default="SHA256", env="WEBHOOK_SIGNATURE_ALGORITHM")
    webhook_signature_tolerance: int = Field(default=300, env="WEBHOOK_SIGNATURE_TOLERANCE")
    
    # Webhook processing
    webhook_max_payload_size: int = Field(default=10485760, env="WEBHOOK_MAX_PAYLOAD_SIZE")
    webhook_processing_timeout: int = Field(default=30, env="WEBHOOK_PROCESSING_TIMEOUT")
    webhook_queue_size: int = Field(default=1000, env="WEBHOOK_QUEUE_SIZE")
    
    # =============================================================================
    # OBJECT STORAGE
    # =============================================================================
    
    # Cloudflare R2
    r2_account_id: Optional[str] = Field(default=None, env="R2_ACCOUNT_ID")
    r2_access_key: Optional[str] = Field(default=None, env="R2_ACCESS_KEY")
    r2_secret_key: Optional[str] = Field(default=None, env="R2_SECRET_KEY")
    r2_bucket_name: str = Field(default="bl1nk-artifacts", env="R2_BUCKET_NAME")
    r2_region: str = Field(default="wnam", env="R2_REGION")
    
    # AWS S3 (alternative)
    s3_bucket: Optional[str] = Field(default=None, env="S3_BUCKET")
    s3_region: str = Field(default="us-east-1", env="S3_REGION")
    s3_access_key: Optional[str] = Field(default=None, env="S3_ACCESS_KEY")
    s3_secret_key: Optional[str] = Field(default=None, env="S3_SECRET_KEY")
    
    # =============================================================================
    # VALIDATORS
    # =============================================================================
    
    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v.upper()
    
    @validator("environment")
    def validate_environment(cls, v):
        """Validate environment"""
        valid_envs = ["development", "staging", "production"]
        if v not in valid_envs:
            raise ValueError(f"Invalid environment: {v}. Must be one of {valid_envs}")
        return v
    
    @validator("embedding_dimension")
    def validate_embedding_dimension(cls, v):
        """Validate embedding dimension"""
        valid_dimensions = [768, 1024, 1536, 3072]
        if v not in valid_dimensions:
            raise ValueError(f"Invalid embedding dimension: {v}. Must be one of {valid_dimensions}")
        return v
    
    @validator("trusted_hosts", pre=True)
    def parse_trusted_hosts(cls, v):
        """Parse trusted hosts from string"""
        if isinstance(v, str):
            return [host.strip() for host in v.split(",") if host.strip()]
        return v
    
    @validator("workers")
    def validate_workers(cls, v):
        """Validate worker count"""
        if v < 1:
            raise ValueError("Workers must be at least 1")
        return v
    
    @validator("port")
    def validate_port(cls, v):
        """Validate port number"""
        if not (1 <= v <= 65535):
            raise ValueError("Port must be between 1 and 65535")
        return v
    
    # =============================================================================
    # COMPUTED PROPERTIES
    # =============================================================================
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment == "production"
    
    @property
    def is_staging(self) -> bool:
        """Check if running in staging environment"""
        return self.environment == "staging"
    
    @property
    def database_dsn(self) -> str:
        """Get database DSN"""
        return self.database_url
    
    @property
    def redis_connection_url(self) -> str:
        """Get Redis connection URL"""
        return self.redis_url
    
    @property
    def jwt_secret(self) -> str:
        """Get JWT secret key"""
        return self.jwt_secret_key
    
    @property
    def openrouter_enabled(self) -> bool:
        """Check if OpenRouter is configured"""
        return bool(self.openrouter_api_key)
    
    @property
    def cloudflare_enabled(self) -> bool:
        """Check if Cloudflare Gateway is configured"""
        return bool(self.cloudflare_api_token and self.cloudflare_account_id)
    
    @property
    def bedrock_enabled(self) -> bool:
        """Check if AWS Bedrock is configured"""
        return bool(self.bedrock_access_key_id and self.bedrock_secret_access_key)
    
    @property
    def object_storage_config(self) -> dict:
        """Get object storage configuration"""
        if self.r2_account_id:
            return {
                "type": "r2",
                "account_id": self.r2_account_id,
                "access_key": self.r2_access_key,
                "secret_key": self.r2_secret_key,
                "bucket": self.r2_bucket_name,
                "region": self.r2_region
            }
        elif self.s3_bucket:
            return {
                "type": "s3",
                "bucket": self.s3_bucket,
                "region": self.s3_region,
                "access_key": self.s3_access_key,
                "secret_key": self.s3_secret_key
            }
        else:
            return {"type": "none"}
    
    def get_provider_priority(self, provider: str) -> int:
        """Get provider priority (lower number = higher priority)"""
        priorities = {
            "openrouter": self.provider_priority_openrouter,
            "cloudflare": self.provider_priority_cloudflare,
            "bedrock": self.provider_priority_bedrock
        }
        return priorities.get(provider.lower(), 10)


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Global settings instance
settings = get_settings()