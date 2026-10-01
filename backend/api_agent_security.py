from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from models.database import AIAgent, AgentTool, ToolPermission, AgentStatus, ToolRiskLevel, PermissionState, Program, AIApplication
from main import get_db

router = APIRouter(prefix="/agent-security", tags=["Agent Security"])

class AgentCreate(BaseModel):
    application_id: int
    program_id: int
    name: str
    description: str

class ToolCreate(BaseModel):
    agent_id: int
    name: str
    description: str
    risk_level: str
    requires_approval: bool = False
    schema_def: Optional[dict] = None

class PermissionCreate(BaseModel):
    agent_id: int
    tool_id: int
    user_identity: str
    state: str

@router.post("/agents")
def create_agent(req: AgentCreate, db: Session = Depends(get_db)):
    agent = AIAgent(
        application_id=req.application_id,
        program_id=req.program_id,
        name=req.name,
        description=req.description,
        status=AgentStatus.ACTIVE
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return {"id": agent.id, "name": agent.name, "status": agent.status.value}

@router.get("/agents")
def get_agents(db: Session = Depends(get_db)):
    query = db.query(AIAgent)
    return [{"id": a.id, "name": a.name, "status": a.status.value, "program_id": a.program_id} for a in query.all()]

@router.post("/tools")
def create_tool(req: ToolCreate, db: Session = Depends(get_db)):
    tool = AgentTool(
        agent_id=req.agent_id,
        name=req.name,
        description=req.description,
        risk_level=ToolRiskLevel(req.risk_level),
        requires_approval=req.requires_approval,
        schema_def=req.schema_def
    )
    db.add(tool)
    db.commit()
    db.refresh(tool)
    return {"id": tool.id, "name": tool.name, "risk_level": tool.risk_level.value}

@router.get("/tools")
def get_tools(agent_id: int, db: Session = Depends(get_db)):
    tools = db.query(AgentTool).filter(AgentTool.agent_id == agent_id).all()
    return [{"id": t.id, "name": t.name, "risk_level": t.risk_level.value} for t in tools]

@router.post("/permissions")
def set_permission(req: PermissionCreate, db: Session = Depends(get_db)):
    perm = db.query(ToolPermission).filter(
        ToolPermission.agent_id == req.agent_id,
        ToolPermission.tool_id == req.tool_id,
        ToolPermission.user_identity == req.user_identity
    ).first()
    
    if perm:
        perm.state = PermissionState(req.state)
    else:
        perm = ToolPermission(
            agent_id=req.agent_id,
            tool_id=req.tool_id,
            user_identity=req.user_identity,
            state=PermissionState(req.state)
        )
        db.add(perm)
    
    db.commit()
    db.refresh(perm)
    return {"id": perm.id, "state": perm.state.value}

@router.get("/permissions")
def get_permissions(agent_id: int, db: Session = Depends(get_db)):
    perms = db.query(ToolPermission).filter(ToolPermission.agent_id == agent_id).all()
    return [{"id": p.id, "tool_id": p.tool_id, "user_identity": p.user_identity, "state": p.state.value} for p in perms]
