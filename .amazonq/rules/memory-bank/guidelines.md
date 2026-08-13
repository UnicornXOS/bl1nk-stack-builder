# bl1nk-agent-builder Development Guidelines

## Code Quality Standards

### Python Code Style
- **PEP 8 Compliance**: All Python code follows PEP 8 standards
- **Type Hints**: Comprehensive type hints on all functions and methods
- **Docstrings**: Module-level docstrings with triple quotes describing purpose
- **Line Length**: Maximum 100 characters (enforced by Black formatter)
- **Imports**: Organized with standard library first, then third-party, then local
- **Naming Conventions**:
  - Classes: PascalCase (e.g., `TaskOrchestrator`, `RetryConfig`)
  - Functions/Methods: snake_case (e.g., `execute_query`, `get_task_status`)
  - Constants: UPPER_SNAKE_CASE (e.g., `RETRY_CONFIGS`, `MAX_ATTEMPTS`)
  - Private members: Leading underscore (e.g., `_db_pool`, `_process_task`)

### TypeScript Code Style
- **ESLint**: Enforced via eslint configuration
- **Prettier**: Automatic code formatting
- **Type Safety**: Strict TypeScript with no implicit any
- **Naming**: camelCase for variables/functions, PascalCase for types/interfaces

### Documentation Standards
- **Module Docstrings**: Every module starts with a docstring explaining its purpose
- **Function Docstrings**: Include Args, Returns, and Raises sections
- **Inline Comments**: Minimal; code should be self-documenting
- **Example**: 
  ```python
  """
  Task Orchestrator for bl1nk-agent-builder
  Coordinates task execution across multiple providers and manages the task lifecycle
  """
  
  async def submit_task(
      self,
      task_type: TaskType,
      input_data: Dict[str, Any],
      user_id: str,
      priority: TaskPriority = TaskPriority.NORMAL,
      metadata: Dict[str, Any] = None
  ) -> int:
      """Submit a new task for processing
      
      Args:
          task_type: Type of task to execute
          input_data: Input data for the task
          user_id: User submitting the task
          priority: Task priority level
          metadata: Additional metadata
      
      Returns:
          Task ID for tracking
      """
  ```

## Structural Conventions

### Async/Await Patterns
- **Async Functions**: All I/O operations use async/await
- **Context Managers**: Use `@asynccontextmanager` for resource management
- **Error Handling**: Try/except blocks with proper logging
- **Example**:
  ```python
  @asynccontextmanager
  async def get_db() -> AsyncGenerator[Connection, None]:
      """Get database connection from pool"""
      if not _db_pool:
          raise RuntimeError("Database connection pool not initialized")
      
      async with _db_pool.acquire() as connection:
          try:
              yield connection
          except Exception as e:
              logger.error(f"Database operation failed: {e}")
              raise
  ```

### Enum Usage
- **Status Enums**: Use Enum classes for status values (not strings)
- **Example**:
  ```python
  class TaskStatus(Enum):
      """Task execution status"""
      PENDING = "pending"
      PROCESSING = "processing"
      COMPLETED = "completed"
      FAILED = "failed"
      CANCELLED = "cancelled"
  ```

### Configuration Management
- **Settings Class**: Centralized configuration via Pydantic settings
- **Environment Variables**: All config from `.env` files
- **Type Validation**: Pydantic validates all settings on load

### Logging Standards
- **Logger Setup**: `logger = logging.getLogger(__name__)` in each module
- **Log Levels**:
  - `DEBUG`: Detailed execution flow (retry attempts, function calls)
  - `INFO`: Important events (startup, task submission, completion)
  - `WARNING`: Recoverable issues (retry failures, non-critical errors)
  - `ERROR`: Failures requiring attention (task failures, exceptions)
- **Structured Logging**: Use `extra` dict for contextual data
- **Example**:
  ```python
  logger.info(
      f"Task submitted successfully - ID: {task_id}",
      extra={
          "event": "task_submitted",
          "task_id": task_id,
          "task_type": task_type.value,
          "user_id": user_id,
          "priority": priority.value
      }
  )
  ```

## Semantic Patterns

### Retry Logic Pattern
- **Configuration-Based**: Retry behavior defined via `RetryConfig` class
- **Strategies**: FIXED, LINEAR, EXPONENTIAL backoff strategies
- **Jitter**: Random jitter added to prevent thundering herd
- **Exception Handling**: Distinguish retryable vs non-retryable exceptions
- **Callbacks**: Optional `on_retry` callbacks for custom logic
- **Example**:
  ```python
  config = RetryConfig(
      max_attempts=3,
      base_delay=1.0,
      max_delay=60.0,
      strategy=RetryStrategy.EXPONENTIAL,
      jitter=True,
      retryable_exceptions=[ConnectionError, TimeoutError],
      non_retryable_exceptions=[ValueError]
  )
  
  result = await retry_async(func, *args, config=config, **kwargs)
  if not result.success:
      raise result.exception
  ```

### Task Orchestration Pattern
- **Status Tracking**: Tasks tracked in both database and Redis cache
- **Lifecycle Management**: PENDING → PROCESSING → COMPLETED/FAILED/CANCELLED
- **Worker Tasks**: Each task gets an asyncio.Task for execution
- **Cleanup**: Completed tasks cleaned up from active tracking
- **Example**:
  ```python
  # Submit task
  task_id = await orchestrator.submit_task(
      task_type=TaskType.CHAT,
      input_data={"message": "Hello"},
      user_id="user-123"
  )
  
  # Check status
  status = await orchestrator.get_task_status(task_id)
  
  # Cancel if needed
  await orchestrator.cancel_task(task_id)
  ```

### Database Connection Pattern
- **Connection Pooling**: asyncpg pool with min/max size configuration
- **Context Manager**: Always use `async with get_db()` for connections
- **Query Helpers**: Specialized functions for fetch_one, fetch_many, execute
- **Health Checks**: Periodic health checks verify pgvector and table status
- **Example**:
  ```python
  async with get_db() as conn:
      row = await conn.fetchrow("SELECT * FROM tasks WHERE id = $1", task_id)
      return dict(row) if row else None
  ```

### FastAPI Application Pattern
- **Lifespan Management**: Use `@asynccontextmanager` for startup/shutdown
- **Service Initialization**: Services created during startup, stored in `app.state`
- **Middleware Stack**: CORS, auth, tracing middleware in specific order
- **Error Handlers**: Global exception handlers for HTTP and general exceptions
- **Route Organization**: Routes grouped by feature in separate modules
- **Example**:
  ```python
  @asynccontextmanager
  async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
      # Startup
      await init_db()
      await init_redis()
      app.state.task_orchestrator = TaskOrchestrator(...)
      
      yield
      
      # Shutdown
      await close_redis()
      await close_db()
  ```

### Middleware Pattern
- **Authentication**: JWT token validation in auth middleware
- **CORS**: Configurable CORS policy based on environment
- **Tracing**: OpenTelemetry instrumentation for distributed tracing
- **Rate Limiting**: slowapi for per-endpoint rate limiting

### Error Handling Pattern
- **Custom Exceptions**: Domain-specific exception classes
- **HTTP Exceptions**: Use FastAPI HTTPException for API errors
- **Logging**: Always log exceptions with context
- **Response Format**: Consistent error response structure with trace_id
- **Example**:
  ```python
  @app.exception_handler(Exception)
  async def general_exception_handler(request: Request, exc: Exception):
      logger.error(f"Uncaught exception: {exc}", exc_info=True)
      return JSONResponse(
          status_code=500,
          content={
              "error": "InternalServerError",
              "message": "An unexpected error occurred",
              "trace_id": getattr(request.state, "trace_id", "unknown")
          }
      )
  ```

## Common Code Idioms

### Result Objects
- **RetryResult**: Encapsulates success/failure with result or exception
- **Attributes**: success, result, exception, attempts, total_delay
- **Usage**: Check `result.success` before accessing `result.result`

### Enum-Based State Management
- **TaskStatus**: Enum for task states (PENDING, PROCESSING, COMPLETED, FAILED, CANCELLED)
- **TaskType**: Enum for task types (CHAT, EMBEDDING, RERANK, SKILL_INVOCATION, MCP_TOOL_CALL)
- **TaskPriority**: Enum for priority levels (LOW, NORMAL, HIGH, URGENT)

### Async Context Managers
- **Database Connections**: `async with get_db() as conn:`
- **Tracing**: `async with AsyncTraceContext("operation_name", **context):`
- **Resource Cleanup**: Guaranteed cleanup via context manager

### Predefined Configurations
- **RETRY_CONFIGS**: Dictionary of common retry configurations
  - `database`: 5 attempts, exponential backoff
  - `api_call`: 3 attempts, exponential backoff
  - `quick_retry`: 2 attempts, fixed backoff
  - `long_retry`: 10 attempts, exponential backoff

### Structured Logging with Extra Context
- **Event Tracking**: `"event"` key identifies the event type
- **Contextual Data**: All relevant IDs and values included
- **Consistency**: Same event types logged consistently across codebase

## Popular Annotations

### Pydantic Decorators
- `@validator`: Field-level validation
- `@root_validator`: Model-level validation
- `Field(...)`: Field configuration with defaults and descriptions

### FastAPI Decorators
- `@app.get()`, `@app.post()`: Route definition
- `@limiter.limit()`: Rate limiting per endpoint
- `@app.exception_handler()`: Custom exception handling

### Async Decorators
- `@asynccontextmanager`: Async context manager
- `@wraps`: Preserve function metadata in decorators
- `@retry_async_decorator`: Automatic retry for async functions

## Testing Patterns

### Test Organization
- Unit tests for individual functions
- Integration tests for API endpoints
- Load tests for performance validation
- Coverage target: 80%+

### Test Fixtures
- Database fixtures with transaction rollback
- Mock external services (LLM providers, Redis)
- Async test support via pytest-asyncio

### Assertion Patterns
- Clear assertion messages
- Test one thing per test
- Use descriptive test names

## Performance Considerations

### Database Optimization
- Connection pooling with appropriate min/max sizes
- Indexes on frequently queried columns
- Batch operations where possible
- pgvector indexes for similarity search

### Caching Strategy
- Redis for session management
- Task status cached in Redis
- TTL-based expiration for temporary data

### Async Concurrency
- Use `asyncio.gather()` for parallel operations
- Limit concurrent connections via pool size
- Proper timeout configuration

## Security Best Practices

### Authentication
- JWT tokens with expiration
- Secure token storage (httponly cookies)
- Token refresh mechanisms

### Input Validation
- Pydantic models for request validation
- Type checking on all inputs
- SQL injection prevention via parameterized queries

### Secrets Management
- Environment variables for sensitive data
- No hardcoded credentials
- Validation of required secrets on startup

### Rate Limiting
- Per-user rate limits
- Per-endpoint rate limits
- Graceful degradation under load

## Deployment Patterns

### Configuration Management
- Environment-specific settings
- Feature flags for gradual rollout
- Health check endpoints

### Graceful Shutdown
- Signal handlers for SIGINT/SIGTERM
- Task cleanup on shutdown
- Connection pool closure

### Monitoring
- OpenTelemetry instrumentation
- Prometheus metrics export
- Structured logging for analysis
