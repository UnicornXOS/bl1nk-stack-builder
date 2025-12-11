"""
Skill management endpoints for bl1nk-agent-builder
Provides REST API for skill registration and invocation
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Pydantic models
class SkillDefinition(BaseModel):
    """Skill definition model"""
    skill_id: str = Field(..., description="Unique skill identifier")
    name: str = Field(..., description="Human-readable skill name")
    description: Optional[str] = Field(None, description="Skill description")
    input_schema: Dict[str, Any] = Field(..., description="Input JSON schema")
    output_schema: Optional[Dict[str, Any]] = Field(None, description="Output JSON schema")
    auth: Optional[str] = Field(None, description="Authentication requirements")
    handler_url: str = Field(..., description="Skill handler endpoint")


class SkillInvokeRequest(BaseModel):
    """Request model for skill invocation"""
    skill_id: str = Field(..., description="Skill to invoke")
    inputs: Dict[str, Any] = Field(..., description="Skill inputs")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Execution context")
    request_id: str = Field(..., description="Request ID for idempotency")


class InvocationResponse(BaseModel):
    """Response model for skill invocation"""
    invocation_id: str = Field(..., description="Unique invocation ID")
    status: str = Field(..., description="Invocation status")
    result: Optional[Dict[str, Any]] = Field(None, description="Skill result")


router = APIRouter()

# In-memory skill registry (in production, this would be in database)
skills_registry = {}
invocations_db = {}

@router.post("/skills/register")
async def register_skill(skill: SkillDefinition):
    """Register a new skill (admin only)"""
    
    if skill.skill_id in skills_registry:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Skill {skill.skill_id} already exists"
        )
    
    skills_registry[skill.skill_id] = skill.dict()
    
    logger.info(f"Skill registered: {skill.skill_id}")
    
    return {"message": f"Skill {skill.skill_id} registered successfully"}


@router.get("/skills")
async def list_skills():
    """List all registered skills"""
    
    skills = []
    for skill_id, skill_data in skills_registry.items():
        skills.append({
            "skill_id": skill_id,
            "name": skill_data["name"],
            "description": skill_data.get("description"),
            "registered_at": skill_data.get("registered_at")
        })
    
    return {"skills": skills}


@router.get("/skills/{skill_id}")
async def get_skill(skill_id: str):
    """Get skill definition"""
    
    if skill_id not in skills_registry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill {skill_id} not found"
        )
    
    skill_data = skills_registry[skill_id]
    
    return {
        "skill_id": skill_id,
        "skill": skill_data
    }


@router.post("/skills/invoke", response_model=InvocationResponse)
async def invoke_skill(request: SkillInvokeRequest):
    """Invoke a skill"""
    
    if request.skill_id not in skills_registry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill {request.skill_id} not found"
        )
    
    # Generate invocation ID
    invocation_id = f"inv_{len(invocations_db) + 1}"
    
    # Store invocation record
    invocation_data = {
        "invocation_id": invocation_id,
        "skill_id": request.skill_id,
        "inputs": request.inputs,
        "context": request.context,
        "request_id": request.request_id,
        "status": "pending",
        "created_at": datetime.now().isoformat()
    }
    
    invocations_db[invocation_id] = invocation_data
    
    # Simulate skill execution
    # In production, this would call the actual skill handler
    try:
        # Mark as processing
        invocation_data["status"] = "processing"
        
        # Simulate execution result
        result = {
            "message": f"Skill {request.skill_id} executed successfully",
            "inputs_received": request.inputs,
            "execution_time": 1.5
        }
        
        invocation_data["status"] = "completed"
        invocation_data["result"] = result
        
        logger.info(f"Skill invocation completed: {invocation_id}")
        
    except Exception as e:
        invocation_data["status"] = "failed"
        invocation_data["error"] = str(e)
        
        logger.error(f"Skill invocation failed: {invocation_id} - {e}")
    
    return InvocationResponse(
        invocation_id=invocation_id,
        status=invocation_data["status"],
        result=invocation_data.get("result")
    )


@router.get("/skills/invocations/{invocation_id}")
async def get_invocation(invocation_id: str):
    """Get invocation status and result"""
    
    if invocation_id not in invocations_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invocation {invocation_id} not found"
        )
    
    invocation_data = invocations_db[invocation_id]
    
    return {
        "invocation_id": invocation_id,
        "skill_id": invocation_data["skill_id"],
        "status": invocation_data["status"],
        "created_at": invocation_data["created_at"],
        "result": invocation_data.get("result"),
        "error": invocation_data.get("error")
    }


@router.get("/skills/invocations")
async def list_invocations(
    skill_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """List skill invocations with optional filtering"""
    
    filtered_invocations = []
    
    for invocation_id, invocation_data in invocations_db.items():
        # Apply filters
        if skill_id and invocation_data["skill_id"] != skill_id:
            continue
        if status and invocation_data["status"] != status:
            continue
        
        filtered_invocations.append(invocation_data)
    
    # Apply pagination
    paginated_invocations = filtered_invocations[offset:offset + limit]
    
    return {
        "invocations": paginated_invocations,
        "total": len(filtered_invocations),
        "limit": limit,
        "offset": offset
    }


@router.delete("/skills/{skill_id}")
async def unregister_skill(skill_id: str):
    """Unregister a skill (admin only)"""
    
    if skill_id not in skills_registry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill {skill_id} not found"
        )
    
    del skills_registry[skill_id]
    
    logger.info(f"Skill unregistered: {skill_id}")
    
    return {"message": f"Skill {skill_id} unregistered successfully"}