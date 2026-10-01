from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from models.database import AIAgent, AgentCapability, AgentMessage, AgentTask, AgentType, MessageType, AgentTaskStatus, MessageStatus
from main import get_db

router = APIRouter(prefix="/multi-agent", tags=["Multi-Agent"])

class CapabilityCreate(BaseModel):
    agent_id: int
    capability_name: str
    resource_type: str
    allowed_actions: str

@router.post("/capabilities")
def create_capability(req: CapabilityCreate, db: Session = Depends(get_db)):
    cap = AgentCapability(**req.dict())
    db.add(cap)
    db.commit()
    db.refresh(cap)
    return cap

@router.get("/capabilities/{agent_id}")
def get_capabilities(agent_id: int, db: Session = Depends(get_db)):
    return db.query(AgentCapability).filter(AgentCapability.agent_id == agent_id).all()

@router.get("/messages")
def get_messages(db: Session = Depends(get_db)):
    msgs = db.query(AgentMessage).order_by(AgentMessage.timestamp.desc()).limit(50).all()
    return [{"id": m.message_id, "sender_id": m.sender_agent_id, "receiver_id": m.receiver_agent_id, "type": m.message_type.value, "status": m.status.value, "timestamp": m.timestamp} for m in msgs]

@router.get("/tasks")
def get_tasks(db: Session = Depends(get_db)):
    tasks = db.query(AgentTask).order_by(AgentTask.created_at.desc()).limit(50).all()
    return [{"id": t.id, "agent_id": t.assigned_agent_id, "type": t.task_type, "status": t.status.value, "created_at": t.created_at} for t in tasks]
