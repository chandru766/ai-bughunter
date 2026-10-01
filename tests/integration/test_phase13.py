import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../backend')))
from main import app, get_db
from models.database import Base, Finding, FindingStatus, ValidationStatus, FindingChain

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_phase13.db"
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
    
    # Program 1 Findings
    f1 = Finding(program_id=1, title="Test Auth Bypass", category="Authentication", status=FindingStatus.NEEDS_VALIDATION, validation_status=ValidationStatus.UNVALIDATED)
    f2 = Finding(program_id=1, title="Test IDOR", category="IDOR", status=FindingStatus.NEEDS_VALIDATION, validation_status=ValidationStatus.UNVALIDATED)
    f_val = Finding(program_id=1, title="Validated DB leak", category="Information Disclosure", status=FindingStatus.VALIDATED, validation_status=ValidationStatus.RESEARCHER_CONFIRMED)
    f_dup = Finding(program_id=1, title="Test IDOR duplicate", category="IDOR", status=FindingStatus.NEEDS_VALIDATION, validation_status=ValidationStatus.UNVALIDATED)
    
    # Program 2 Findings
    f3 = Finding(program_id=2, title="Other Auth bypass", category="Authentication", status=FindingStatus.NEEDS_VALIDATION, validation_status=ValidationStatus.UNVALIDATED)
    f4 = Finding(program_id=2, title="Other IDOR", category="IDOR", status=FindingStatus.NEEDS_VALIDATION, validation_status=ValidationStatus.UNVALIDATED)
    
    db.add_all([f1, f2, f_val, f_dup, f3, f4])
    db.commit()
    db.close()

def test_related_findings_chain():
    # 1. Two related findings create a potential chain
    response = client.post("/findings/correlate", json={"program_id": 1})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "CORRELATED"
    assert data["chains_created"] == 1
    
    # 8. FindingChain remains UNVALIDATED
    chain = data["chains"][0]
    assert chain["validation_status"] == "UNVALIDATED"
    
    # 9. Potential duplicates are reported but not automatically marked DUPLICATE
    assert "potential_duplicate" in chain

def test_different_programs():
    # 2. Findings from different programs do not correlate (unless specified, they are grouped. Let's run all programs)
    response = client.post("/findings/correlate")
    assert response.status_code == 200
    data = response.json()
    # Mock Provider will create 1 chain per program group (Program 1 and Program 2)
    assert data["chains_created"] == 2

def test_empty_findings():
    # 3. Empty finding set returns safely.
    response = client.post("/findings/correlate", json={"program_id": 999})
    assert response.status_code == 200
    data = response.json()
    assert data["chains_created"] == 0
    assert data["findings_analyzed"] == 0

def test_correlation_does_not_modify_status():
    # 5. Correlation does not modify original Finding status.
    # 6. NEEDS_VALIDATION remains NEEDS_VALIDATION.
    # 7. VALIDATED remains VALIDATED.
    client.post("/findings/correlate", json={"program_id": 1})
    db = TestingSessionLocal()
    f1 = db.query(Finding).filter(Finding.id == 1).first()
    assert f1.status == FindingStatus.NEEDS_VALIDATION
    f_val = db.query(Finding).filter(Finding.id == 3).first()
    assert f_val.status == FindingStatus.VALIDATED
    db.close()

def test_invalid_program_id():
    # 10. Invalid program ID returns appropriate response (empty findings safe return)
    response = client.post("/findings/correlate", json={"program_id": -1})
    assert response.status_code == 200
    assert response.json()["chains_created"] == 0
