import jsonschema
from fastapi import HTTPException
from models.database import AIAgent, AgentTool, ToolPermission, PermissionState, AgentStatus
from observability.logger import log_event
import time

class ToolExecutionGate:
    def __init__(self, db):
        self.db = db
        # Action budget: store calls per agent in memory (for local test lab simulation)
        self.agent_call_history = {}
        self.MAX_CALLS_PER_AGENT = 5

    def check_loop(self, agent_id: int, tool_name: str) -> bool:
        if agent_id not in self.agent_call_history:
            self.agent_call_history[agent_id] = []
        
        history = self.agent_call_history[agent_id]
        
        # Action budget limit
        if len(history) >= self.MAX_CALLS_PER_AGENT:
            log_event("AGENT_BLOCKED", level=40, agent_id=agent_id, reason="Action budget exceeded")
            return True
            
        # Loop detection (e.g. same tool called 3 times sequentially)
        if len(history) >= 3 and all(h == tool_name for h in history[-3:]):
            log_event("AGENT_LOOP_DETECTED", level=40, agent_id=agent_id, tool_name=tool_name)
            return True
            
        history.append(tool_name)
        return False

    def validate_execution(self, agent_id: int, tool_name: str, arguments: dict, user_identity: str, is_kill_switch_active: bool = False):
        if is_kill_switch_active:
            log_event("TOOL_BLOCKED", level=40, agent_id=agent_id, tool_name=tool_name, reason="KILL_SWITCH_ACTIVE")
            raise HTTPException(403, "Kill switch is active.")
            
        agent = self.db.query(AIAgent).filter(AIAgent.id == agent_id).first()
        if not agent or agent.status != AgentStatus.ACTIVE:
            log_event("TOOL_BLOCKED", level=40, agent_id=agent_id, tool_name=tool_name, reason="AGENT_INACTIVE")
            raise HTTPException(403, "Agent is not active.")
            
        tool = self.db.query(AgentTool).filter(AgentTool.agent_id == agent_id, AgentTool.name == tool_name).first()
        if not tool or not tool.enabled:
            log_event("TOOL_BLOCKED", level=40, agent_id=agent_id, tool_name=tool_name, reason="TOOL_NOT_FOUND_OR_DISABLED")
            raise HTTPException(403, f"Tool {tool_name} not found or disabled.")
            
        # Check permissions
        permission = self.db.query(ToolPermission).filter(
            ToolPermission.agent_id == agent_id,
            ToolPermission.tool_id == tool.id,
            ToolPermission.user_identity == user_identity
        ).first()
        
        if not permission or permission.state == PermissionState.BLOCKED:
            log_event("TOOL_BLOCKED", level=40, agent_id=agent_id, tool_name=tool_name, reason="UNAUTHORIZED_FOR_USER")
            raise HTTPException(403, "Unauthorized to use this tool.")
            
        if permission.state == PermissionState.APPROVAL_REQUIRED or tool.requires_approval:
            # Simulated approval requirement check
            log_event("APPROVAL_REQUESTED", level=30, agent_id=agent_id, tool_name=tool_name)
            raise HTTPException(403, "Tool execution requires human approval.")
            
        # Validate schema
        if tool.schema_def:
            try:
                jsonschema.validate(instance=arguments, schema=tool.schema_def)
            except jsonschema.exceptions.ValidationError as e:
                log_event("TOOL_BLOCKED", level=40, agent_id=agent_id, tool_name=tool_name, reason="SCHEMA_VALIDATION_FAILED")
                raise ValueError(f"Invalid arguments: {e.message}")
        
        # Check loops and budget
        if self.check_loop(agent_id, tool_name):
            raise HTTPException(429, "Action budget exceeded or loop detected.")
            
        log_event("TOOL_ALLOWED", level=20, agent_id=agent_id, tool_name=tool_name)
        return True

    def sanitize_result(self, result: dict) -> dict:
        """Sanitizes tool output before returning to LLM"""
        sanitized = {}
        for k, v in result.items():
            if "secret" in k.lower() or "password" in k.lower() or "token" in k.lower():
                sanitized[k] = "[REDACTED]"
            elif isinstance(v, str) and len(v) > 1000:
                sanitized[k] = v[:1000] + "... [TRUNCATED]"
            else:
                sanitized[k] = v
        return sanitized
