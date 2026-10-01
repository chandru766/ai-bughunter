import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../backend')))
from main import app, get_db
from models.database import Base, Finding, FindingStatus, ValidationStatus, Report, TestResult, Evidence, FindingChain, AuditLog

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_phase14.db"
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
    
    f_val = Finding(id=1, program_id=1, title="Validated DB leak", category="Information Disclosure", status=FindingStatus.VALIDATED, validation_status=ValidationStatus.RESEARCHER_CONFIRMED)
    f_needs = Finding(id=2, program_id=1, title="Needs validation", category="IDOR", status=FindingStatus.NEEDS_VALIDATION, validation_status=ValidationStatus.UNVALIDATED)
    f_false = Finding(id=3, program_id=1, title="False positive", category="BOLA", status=FindingStatus.FALSE_POSITIVE, validation_status=ValidationStatus.RESEARCHER_REJECTED)
    
    db.add_all([f_val, f_needs, f_false])
    db.commit()
    
    # Add Evidence & TestResult with secrets
    ev = Evidence(finding_id=1)
    tr = TestResult(
        test_plan_id=1,
        status="EXECUTED",
        request_raw="GET /api/users HTTP/1.1\nAuthorization: Bearer REAL_SECRET_JWT_HERE",
        response_raw="HTTP/1.1 200 OK\nUser data leak"
    )
    db.add_all([ev, tr])
    db.commit()
    
    # Add FindingChain
    fc = FindingChain(id=1, findings=[1, 2], combined_impact="Chained impact of info disclosure and IDOR.", relationships=[])
    db.add(fc)
    db.commit()
    
    db.close()

def test_validated_generates_report():
    response = client.post("/reports/generate/1")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "DRAFT_GENERATED"
    assert "report_id" in data
    assert "markdown" in data
    assert "json" in data
    assert "report_hash" in data
    
    # 6. Markdown contains expected sections
    md = data["markdown"]
    assert "## Severity" in md
    assert "## Affected Program" in md
    
    # 7. Secrets are redacted
    # REAL_SECRET_JWT_HERE should be redacted to REAL_...[REDACTED] or [REDACTED]
    evidence_str = data["json"]["evidence"][0]
    assert "REAL_SECRET_JWT_HERE" not in evidence_str
    assert "[REDACTED]" in evidence_str or "REAL_...[REDACTED]" in evidence_str
    
    # 8. Missing fields are not fabricated
    assert "Not available in the current evidence." in data["json"]["target"]
    
    # 11. Correlation information included
    assert "Potentially related findings in Chain ID 1" in md or "Chained impact" in md

def test_needs_validation_fails():
    response = client.post("/reports/generate/2")
    assert response.status_code == 409
    assert "must be VALIDATED" in response.json()["detail"]

def test_false_positive_fails():
    response = client.post("/reports/generate/3")
    assert response.status_code == 409

def test_nonexistent_finding():
    response = client.post("/reports/generate/999")
    assert response.status_code == 404

def test_status_not_changed():
    client.post("/reports/generate/1")
    db = TestingSessionLocal()
    f1 = db.query(Finding).filter(Finding.id == 1).first()
    assert f1.status == FindingStatus.VALIDATED  # Did not auto-change to REPORTED
    
    # 5. Report record is created
    report = db.query(Report).filter(Report.finding_id == 1).first()
    assert report is not None
    assert report.report_hash is not None
    
    # 12. Audit log is created
    logs = db.query(AuditLog).filter(AuditLog.action.like("REPORT_GENERAT%")).all()
    assert len(logs) > 0
    
    db.close()
