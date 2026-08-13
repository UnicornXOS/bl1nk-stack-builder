# Dependency Changes (Worker)

This document records dependency conflict fixes made under `apps/worker/requirements.in`, plus the required `aioredis` → `redis.asyncio` migration.

## Summary

- Removed invalid/duplicate requirement entries.
- Replaced deprecated `aioredis` usage with `redis.asyncio`.
- Fixed several pins that referenced non-existent/yanked PyPI versions.
- Resolved an actual dependency conflict between `fastapi==0.104.1` and `anyio==4.x`.

## `apps/worker/requirements.in` changes

### Removed

- `asyncio==3.4.3` (stdlib module; must not be listed as a dependency)
- Duplicate `httpx==0.25.2` entry (kept a single pinned entry)
- `pydantic==2.5.0` (redundant with `pydantic[email]==2.5.0`; kept the extra form)
- `aioredis==2.0.1` (deprecated)
- `swagger-ui==5.10.5` (no matching distribution on PyPI for that version; FastAPI already serves Swagger UI without this dependency)

### Updated (old → new)

- `sse-starlette==1.8.0` → `sse-starlette==1.8.2` (1.8.0 not available on PyPI)
- `litellm==1.13.4` → `litellm==1.13.2` (1.13.4 not available on PyPI)
- `cryptography==41.0.8` → `cryptography==41.0.7` (41.0.8 not available on PyPI)
- `anyio==4.1.0` → `anyio==3.7.1` (required by `fastapi==0.104.1` via `anyio<4.0.0`)
- `psycopg[binary]==3.1.12` → `psycopg[binary]==3.2.2` (ensures a compatible `psycopg-binary` build is available)

### Replaced

- `aioredis==2.0.1` + `redis==5.0.1` → `redis==5.0.1`
  - Note: `redis` (redis-py) includes asyncio support as `redis.asyncio`; there is no supported `redis[asyncio]` extra in `redis==5.0.1`.

## Code migration (`aioredis` → `redis.asyncio`)

File: `apps/worker/app/database/redis.py`

- Replaced:
  - `import aioredis` / `from aioredis import Redis`
- With:
  - `from redis import asyncio as aioredis`
  - `from redis.asyncio import Redis`
- Existing usage of `aioredis.from_url(...)` continues to work (now backed by `redis.asyncio.from_url`).

## Compatibility notes

- `fastapi==0.104.1` is compatible with `pydantic==2.5.0` (via `pydantic[email]==2.5.0`) and `pydantic-settings==2.1.0`.
- `fastapi==0.104.1` requires `anyio<4`, which is why `anyio` was pinned to `3.7.1`.

## Additional Changes (Latest Audit)

### Updated (old → new)
- `redis==5.0.1` → `redis[asyncio]==5.0.1` (explicitly include asyncio support for clarity, though redis-py includes it by default)

### Notes on Task Audit
- The following issues mentioned in the audit were not present in the current `requirements.in`:
  - `asyncio==3.4.3` (stdlib module) - not found
  - Duplicate `httpx==0.25.2` - only one instance present
  - Redundant `pydantic==2.5.0` vs `pydantic[email]==2.5.0` - already consolidated
  - `aioredis==2.0.1` - not present in requirements.in
- Code in `redis.py` was already migrated to use `redis.asyncio` instead of deprecated `aioredis`

## Verification performed

- Regenerated `apps/worker/requirements.txt` via `pip-compile` (backtracking resolver).
- Installed dependencies and ran `pip check` in a Python 3.11 virtual environment; result: `No broken requirements found.`

