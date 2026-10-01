import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../backend')))
from main import app, get_db
from models.database import Base, Finding, FindingStatus, ValidationStatus

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_phase12.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    f1 = Finding(title="Test Finding 1", category="BOLA", status=FindingStatus.NEEDS_VALIDATION, validation_status=ValidationStatus.UNVALIDATED)
    f2 = Finding(title="Test Finding 2", category="IDOR", status=FindingStatus.NEEDS_VALIDATION, validation_status=ValidationStatus.UNVALIDATED)
    f3 = Finding(title="Already Validated", category="XSS", status=FindingStatus.VALIDATED, validation_status=ValidationStatus.RESEARCHER_CONFIRMED)
    db.add_all([f1, f2, f3])
    db.commit()
    db.close()

def test_get_findings():
    response = client.get("/findings")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3

def test_confirm_finding():
    response = client.post("/findings/1/validate", json={"decision": "CONFIRM", "reason": "Looks good"})
    assert response.status_code == 200
    assert response.json()["status"] == "VALIDATED"
    assert response.json()["validation_status"] == "RESEARCHER_CONFIRMED"

def test_reject_finding():
    response = client.post("/findings/2/validate", json={"decision": "REJECT", "reason": "False positive"})
    assert response.status_code == 200
    assert response.json()["status"] == "FALSE_POSITIVE"
    assert response.json()["validation_status"] == "RESEARCHER_REJECTED"

def test_invalid_decision():
    response = client.post("/findings/1/validate", json={"decision": "CONFIRM123", "reason": "bad"})
    assert response.status_code == 400

def test_empty_reason():
    response = client.post("/findings/1/validate", json={"decision": "CONFIRM", "reason": "   "})
    assert response.status_code == 400

def test_nonexistent_finding():
    response = client.post("/findings/999/validate", json={"decision": "CONFIRM", "reason": "exists?"})
    assert response.status_code == 404

def test_already_validated_finding():
    response = client.post("/findings/3/validate", json={"decision": "CONFIRM", "reason": "validate again"})
    assert response.status_code == 409
