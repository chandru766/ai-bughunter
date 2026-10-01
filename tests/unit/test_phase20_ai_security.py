import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../backend')))
from main import app, get_db
from models.database import Base, Program, AIApplication, AITestCase, AITestCategory, TestStatus
from ai.advisor import AISecurityAnalyzer

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_phase20.db"
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
    
    prog = Program(id=1, name="AI Lab Program")
    app_ai = AIApplication(id=1, program_id=1, name="Lab", base_url="http://127.0.0.1:9100")
    
    db.add_all([prog, app_ai])
    db.commit()
    db.close()

def test_ai_application_creation():
    res = client.post("/ai-security/applications", json={"program_id": 1, "name": "Test App", "base_url": "http://127.0.0.1", "description": ""})
    assert res.status_code == 200
    assert res.json()["name"] == "Test App"

def test_ai_testcase_planning():
    tc_res = client.post("/ai-security/testcases", json={
        "application_id": 1,
        "category": "PROMPT_INJECTION",
        "test_name": "Test PI",
        "description": "PI test"
    })
    assert tc_res.status_code == 200
    case_id = tc_res.json()["id"]
    
    plan_res = client.post(f"/ai-security/testcases/{case_id}/plan")
    assert plan_res.status_code == 200
    assert plan_res.json()["status"] == "PLANNED"
    plan_id = plan_res.json()["plan_id"]
    
    # Verify the test plan requires approval and exists
    db = TestingSessionLocal()
    from models.database import TestPlan
    plan = db.query(TestPlan).filter(TestPlan.id == plan_id).first()
    assert plan is not None
    assert plan.requires_human_approval is True
    assert plan.test_category == "PROMPT_INJECTION"
    db.close()

def test_ai_security_analyzer_semantic_validation():
    # Test strict validation by directly invoking analyzer with mock
    class MockProvider:
        def analyze(self, p):
            return '{"title": "Vuln", "category": "PROMPT_INJECTION", "observation": "Obs", "impact": "Imp", "confidence": "HIGH", "supporting_evidence": [], "counter_evidence": [], "missing_evidence": [], "validation_steps": [], "recommended_severity": "MEDIUM", "status": "VALIDATED"}'
    
    adv = AISecurityAnalyzer(MockProvider())
    # Should reject because status is VALIDATED
    with pytest.raises(ValueError, match="Semantic Validation Failed"):
        adv.analyze("Req", "Res", "PROMPT_INJECTION", "Policy")

def test_ai_security_analyzer_success():
    class MockProvider:
        def analyze(self, p):
            return '{"title": "Vuln", "category": "PROMPT_INJECTION", "observation": "Obs", "impact": "Imp", "confidence": "HIGH", "supporting_evidence": [], "counter_evidence": [], "missing_evidence": [], "validation_steps": [], "recommended_severity": "MEDIUM", "status": "NEEDS_VALIDATION"}'
    
    adv = AISecurityAnalyzer(MockProvider())
    res = adv.analyze("Req", "Res", "PROMPT_INJECTION", "Policy")
    assert res.status == "NEEDS_VALIDATION"
    assert res.category == "PROMPT_INJECTION"
