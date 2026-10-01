import hashlib
import json
import uuid
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session
from models.database import (
    AIAgent, AgentCapability, AgentMessage, AgentTask,
    AgentTaskStatus, MessageStatus, MessageType
)
from observability.logger import log_event

class AgentGateway:
    def __init__(self, db: Session):
        self.db = db

    def compute_payload_hash(self, payload: dict) -> str:
        payload_str = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(payload_str.encode('utf-8')).hexdigest()

    def send_message(self, sender_id: int, receiver_id: int, msg_type: MessageType, resource_id: str, payload: dict) -> AgentMessage:
        sender = self.db.query(AIAgent).filter(AIAgent.id == sender_id).first()
        receiver = self.db.query(AIAgent).filter(AIAgent.id == receiver_id).first()
        
        if not sender or not receiver:
            raise HTTPException(status_code=404, detail="Agent not found.")
            
        # Program Isolation Boundary
        if sender.program_id != receiver.program_id:
            log_event("CROSS_PROGRAM_ACCESS_BLOCKED", level=40, sender_id=sender_id, receiver_id=receiver_id)
            raise HTTPException(status_code=403, detail="Cross-program communication is strictly blocked.")

        # Privilege Escalation / Spoofing Boundary
        # If payload contains instructions that look like capability grants, it's blocked.
        payload_str = json.dumps(payload).lower()
        if "give me" in payload_str and "privilege" in payload_str:
            log_event("PRIVILEGE_ESCALATION_BLOCKED", level=40, sender_id=sender_id, receiver_id=receiver_id)
            raise HTTPException(status_code=403, detail="Privilege escalation attempt detected and blocked.")

        msg_id = str(uuid.uuid4())
        payload_hash = self.compute_payload_hash(payload)
        
        msg = AgentMessage(
            message_id=msg_id,
            sender_agent_id=sender_id,
            receiver_agent_id=receiver_id,
            message_type=msg_type,
            resource_id=resource_id,
            payload=payload,
            payload_hash=payload_hash,
            status=MessageStatus.DELIVERED
        )
        self.db.add(msg)
        self.db.commit()
        self.db.refresh(msg)
        
        log_event("AGENT_MESSAGE_SENT", level=20, message_id=msg_id, sender_id=sender_id, receiver_id=receiver_id)
        return msg

    def receive_message(self, msg_id: str, expected_payload: dict):
        msg = self.db.query(AgentMessage).filter(AgentMessage.message_id == msg_id).first()
        if not msg:
            raise HTTPException(status_code=404, detail="Message not found.")
            
        # Evidence / Message Integrity Verification
        computed_hash = self.compute_payload_hash(expected_payload)
        if computed_hash != msg.payload_hash:
            log_event("EVIDENCE_INTEGRITY_FAILURE", level=40, message_id=msg_id)
            raise HTTPException(status_code=400, detail="Message/Evidence payload integrity verification failed.")
            
        return msg

    def create_task(self, session_id: str, assigner_id: int, assigned_id: int, task_type: str, resource_id: str, required_capability: str):
        assigner = self.db.query(AIAgent).filter(AIAgent.id == assigner_id).first()
        assigned = self.db.query(AIAgent).filter(AIAgent.id == assigned_id).first()
        
        # Capability validation
        cap = self.db.query(AgentCapability).filter(
            AgentCapability.agent_id == assigned_id,
            AgentCapability.capability_name == required_capability
        ).first()
        
        if not cap:
            log_event("CAPABILITY_CHECK_FAILED", level=30, agent_id=assigned_id, capability=required_capability)
            raise HTTPException(status_code=403, detail=f"Agent lacks required capability: {required_capability}")
            
        # Delegation loop protection (check history in DB or simple limit)
        existing_tasks = self.db.query(AgentTask).filter(
            AgentTask.session_id == session_id,
            AgentTask.assigned_agent_id == assigned_id
        ).count()
        if existing_tasks > 5: # Max depth / limits
            log_event("AGENT_DELEGATION_BLOCKED", level=40, agent_id=assigned_id)
            raise HTTPException(status_code=429, detail="Delegation depth or loop limit exceeded.")
            
        task = AgentTask(
            session_id=session_id,
            assigned_agent_id=assigned_id,
            task_type=task_type,
            resource_id=resource_id,
            status=AgentTaskStatus.QUEUED
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        log_event("AGENT_TASK_CREATED", level=20, task_id=task.id, assigned_id=assigned_id)
        return task
