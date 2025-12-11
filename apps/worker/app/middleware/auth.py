"""
Authentication middleware for bl1nk-agent-builder
Handles JWT authentication and admin key validation
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import BaseModel

from app.config.settings import settings

logger = logging.getLogger(__name__)

# Security schemes
security = HTTPBearer()


class User(BaseModel):
    """User model for authentication"""
    user_id: str
    email: Optional[str] = None
    display_name: Optional[str] = None
    tier: str = "free"
    is_admin: bool = False
    scopes: list[str] = []


class TokenData(BaseModel):
    """Token data model"""
    user_id: str
    email: Optional[str] = None
    scopes: list[str] = []
    exp: int


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    
    return encoded_jwt


def verify_token(token: str) -> TokenData:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        
        user_id: str = payload.get("sub")
        email: Optional[str] = payload.get("email")
        scopes: list = payload.get("scopes", [])
        exp: int = payload.get("exp")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return TokenData(
            user_id=user_id,
            email=email,
            scopes=scopes,
            exp=exp
        )
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current authenticated user"""
    token_data = verify_token(credentials.credentials)
    
    # In a real implementation, you would fetch user from database
    # For now, create a basic user object
    user = User(
        user_id=token_data.user_id,
        email=token_data.email,
        scopes=token_data.scopes,
        is_admin="admin" in token_data.scopes
    )
    
    return user


async def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current admin user (requires admin scope)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


def verify_admin_key(request: Request) -> bool:
    """Verify admin API key from headers"""
    admin_key = request.headers.get("X-Admin-Key")
    
    if not admin_key:
        return False
    
    # In production, this should be hashed and compared
    return admin_key == settings.admin_api_key


class AuthenticationMiddleware:
    """Middleware for authentication handling"""
    
    def __init__(self):
        self.whitelist_paths = {
            "/health",
            "/health/",
            "/metrics",
            "/metrics/",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/webhook",
            "/webhook/",
            "/favicon.ico",
        }
    
    async def __call__(self, request: Request, call_next):
        # Skip authentication for whitelisted paths
        if request.url.path in self.whitelist_paths or request.url.path.startswith("/webhook/"):
            return await call_next(request)
        
        # Skip if it's a health check
        if request.method == "GET" and request.url.path.startswith("/health"):
            return await call_next(request)
        
        # Check for admin key (alternative to JWT)
        if verify_admin_key(request):
            # Add admin marker to request state
            request.state.is_admin = True
            request.state.user = User(
                user_id="admin",
                email="admin@bl1nk.site",
                is_admin=True,
                scopes=["admin"]
            )
            return await call_next(request)
        
        # Check for Bearer token
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        try:
            token = auth_header.split(" ")[1]
            token_data = verify_token(token)
            
            # Create user object
            user = User(
                user_id=token_data.user_id,
                email=token_data.email,
                scopes=token_data.scopes,
                is_admin="admin" in token_data.scopes
            )
            
            # Add user to request state
            request.state.user = user
            request.state.is_admin = user.is_admin
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed"
            )
        
        return await call_next(request)


class AdminRequiredMiddleware:
    """Middleware to require admin access"""
    
    def __init__(self):
        self.admin_only_paths = {
            "/admin",
            "/admin/",
            "/admin/",
        }
    
    async def __call__(self, request: Request, call_next):
        # Check if this is an admin-only path
        if request.url.path.startswith("/admin") and not request.url.path.startswith("/admin/health"):
            # Check if user is admin
            if not getattr(request.state, "is_admin", False):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin access required"
                )
        
        return await call_next(request)


def setup_auth(app: FastAPI) -> None:
    """Setup authentication middleware"""
    
    # Add authentication middleware
    app.add_middleware(AuthenticationMiddleware)
    
    # Add admin required middleware (only if needed)
    # app.add_middleware(AdminRequiredMiddleware)
    
    logger.info("Authentication middleware configured")


# Utility functions for token generation (for testing)
def create_test_token(user_id: str, scopes: list[str] = None) -> str:
    """Create a test JWT token"""
    if scopes is None:
        scopes = ["user"]
    
    data = {
        "sub": user_id,
        "scopes": scopes,
        "email": f"{user_id}@example.com",
    }
    
    return create_access_token(data)


def create_admin_token() -> str:
    """Create an admin token"""
    return create_test_token("admin", ["admin", "user"])


def create_user_token(user_id: str) -> str:
    """Create a regular user token"""
    return create_test_token(user_id, ["user"])