import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../backend')))
from main import app, get_db
from models.database import Base, Program, AIApplication, AIAgent, AgentTool, ToolPermission, ToolRiskLevel, PermissionState, AgentStatus
from ai.tool_gate import ToolExecutionGate
from fastapi import HTTPException

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_phase21.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try: yield db
    finally: db.close()

@pytest.fixture(autouse=True)
def apply_db_override():
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()
client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    prog = Program(id=1, name="Agent Program")
    app_ai = AIApplication(id=1, program_id=1, name="Lab", base_url="http://127.0.0.1:9200")
    agent = AIAgent(id=1, application_id=1, program_id=1, name="Test Agent", description="...")
    tool = AgentTool(id=1, agent_id=1, name="get_user", risk_level=ToolRiskLevel.READ_ONLY, enabled=True, schema_def={"type": "object", "properties": {"user_id": {"type": "string"}}, "required": ["user_id"]})
    perm = ToolPermission(id=1, agent_id=1, tool_id=1, user_identity="user_a", state=PermissionState.ALLOWED)
    
    db.add_all([prog, app_ai, agent, tool, perm])
    db.commit()
    db.close()

def test_tool_execution_gate_success():
    db = TestingSessionLocal()
    gate = ToolExecutionGate(db)
    
    # Should succeed because user_a has ALLOWED permission
    res = gate.validate_execution(1, "get_user", {"user_id": "user_a"}, "user_a")
    assert res is True
    db.close()

def test_tool_execution_gate_authorization_block():
    db = TestingSessionLocal()
    gate = ToolExecutionGate(db)
    
    # Should fail because user_b does not have a ToolPermission (defaults to BLOCKED if missing/blocked)
    with pytest.raises(HTTPException) as exc:
        gate.validate_execution(1, "get_user", {"user_id": "user_b"}, "user_b")
    assert exc.value.status_code == 403
    assert "Unauthorized" in exc.value.detail
    db.close()

def test_tool_execution_gate_schema_validation():
    db = TestingSessionLocal()
    gate = ToolExecutionGate(db)
    
    # Should fail due to missing required 'user_id' parameter
    with pytest.raises(ValueError, match="Invalid arguments"):
        gate.validate_execution(1, "get_user", {"wrong_arg": 123}, "user_a")
    db.close()

def test_tool_execution_gate_kill_switch():
    db = TestingSessionLocal()
    gate = ToolExecutionGate(db)
    
    with pytest.raises(HTTPException) as exc:
        gate.validate_execution(1, "get_user", {"user_id": "user_a"}, "user_a", is_kill_switch_active=True)
    assert exc.value.status_code == 403
    assert "Kill switch is active" in exc.value.detail
    db.close()

def test_tool_execution_gate_loop_detection():
    db = TestingSessionLocal()
    gate = ToolExecutionGate(db)
    
    # 3 sequential calls should be fine, 4th should raise 429
    gate.validate_execution(1, "get_user", {"user_id": "user_a"}, "user_a")
    gate.validate_execution(1, "get_user", {"user_id": "user_a"}, "user_a")
    gate.validate_execution(1, "get_user", {"user_id": "user_a"}, "user_a")
    
    with pytest.raises(HTTPException) as exc:
        gate.validate_execution(1, "get_user", {"user_id": "user_a"}, "user_a")
    assert exc.value.status_code == 429
    db.close()

def test_tool_result_sanitization():
    db = TestingSessionLocal()
    gate = ToolExecutionGate(db)
    
    result = {
        "status": "success",
        "aws_secret_key": "real_secret_here",
        "data": "A" * 1500
    }
    
    sanitized = gate.sanitize_result(result)
    assert sanitized["aws_secret_key"] == "[REDACTED]"
    assert "TRUNCATED" in sanitized["data"]
    db.close()
