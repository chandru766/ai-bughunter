from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from models.database import (
    ResearchSession, ResearchSessionStatus, ResearchRecommendation, 
    ResearchNote, TestPlan, TestStatus, TestResult, Finding, Endpoint, 
    KnowledgeDocument, Program, AuditLog
)
from ai.advisor import ResearchAdvisor
from ai.providers.factory import ProviderFactory
from observability.logger import log_event, get_request_id

router = APIRouter(prefix="/research", tags=["Research"])

# We must import get_db lazily or pass it.
# Easiest is to import it from main
from main import get_db, log_audit

class SessionCreate(BaseModel):
    program_id: int
    name: str

class RecommendationGenerateRequest(BaseModel):
    endpoint: str

class TestPlanFromRec(BaseModel):
    category: str
    method: str

@router.post("/sessions")
def create_session(req: SessionCreate, db: Session = Depends(get_db)):
    session = ResearchSession(program_id=req.program_id, name=req.name)
    db.add(session)
    db.commit()
    db.refresh(session)
    log_audit(db, "SESSION_CREATED", f"Session:{session.id}", "SUCCESS")
    return {"id": session.id, "program_id": session.program_id, "name": session.name, "status": session.status}

@router.get("/sessions")
def get_sessions(program_id: Optional[int] = None, page: int = 1, limit: int = 50, db: Session = Depends(get_db)):
    query = db.query(ResearchSession)
    if program_id:
        query = query.filter(ResearchSession.program_id == program_id)
    results = query.order_by(ResearchSession.id.desc()).offset((page-1)*limit).limit(limit).all()
    return [{"id": s.id, "program_id": s.program_id, "name": s.name, "status": s.status} for s in results]

@router.get("/sessions/{session_id}")
def get_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(ResearchSession).filter(ResearchSession.id == session_id).first()
    if not session: raise HTTPException(404)
    return {"id": session.id, "program_id": session.program_id, "name": session.name, "status": session.status}

@router.post("/sessions/{session_id}/pause")
def pause_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(ResearchSession).filter(ResearchSession.id == session_id).first()
    if not session: raise HTTPException(404)
    session.status = ResearchSessionStatus.PAUSED
    db.commit()
    log_audit(db, "SESSION_PAUSED", f"Session:{session.id}", "SUCCESS")
    return {"status": "PAUSED"}

@router.post("/sessions/{session_id}/resume")
def resume_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(ResearchSession).filter(ResearchSession.id == session_id).first()
    if not session: raise HTTPException(404)
    session.status = ResearchSessionStatus.ACTIVE
    db.commit()
    log_audit(db, "SESSION_RESUMED", f"Session:{session.id}", "SUCCESS")
    return {"status": "ACTIVE"}

@router.post("/sessions/{session_id}/complete")
def complete_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(ResearchSession).filter(ResearchSession.id == session_id).first()
    if not session: raise HTTPException(404)
    session.status = ResearchSessionStatus.COMPLETED
    db.commit()
    log_audit(db, "SESSION_COMPLETED", f"Session:{session.id}", "SUCCESS")
    return {"status": "COMPLETED"}

@router.get("/sessions/{session_id}/coverage")
def get_session_coverage(session_id: int, db: Session = Depends(get_db)):
    from models.database import Target, Endpoint, AuthenticationContext, TestPlan, TestStatus, TestResult
    session = db.query(ResearchSession).filter(ResearchSession.id == session_id).first()
    if not session: raise HTTPException(404)
    
    # 1. Endpoints
    targets = db.query(Target).filter(Target.program_id == session.program_id).all()
    target_ids = [t.id for t in targets]
    endpoints = db.query(Endpoint).filter(Endpoint.target_id.in_(target_ids)).all() if target_ids else []
    
    # 2. Test Plans
    plans = db.query(TestPlan).filter(TestPlan.program_id == session.program_id).all()
    tested_urls = set([p.url for p in plans if p.status == TestStatus.EXECUTED])
    
    # 3. Auth Matrix
    auth_contexts = db.query(AuthenticationContext).filter(AuthenticationContext.program_id == session.program_id).all()
    auth_names = [ctx.name for ctx in auth_contexts] + ["Anonymous"]
    
    matrix = {}
    for ep in endpoints:
        ep_url = ep.path # Assume path is used as URL in tests for simplicity, or we match on suffix
        matrix[ep_url] = {name: "NOT TESTED" for name in auth_names}
        
        # Check tests for this endpoint
        ep_plans = [p for p in plans if p.url and ep.path in p.url]
        for p in ep_plans:
            # If a test executed, we mark it. A real system would track which auth context was used.
            # We approximate for now: if tested, mark Anonymous, if mutation exists mark others.
            if p.status == TestStatus.EXECUTED:
                matrix[ep_url]["Anonymous"] = "TESTED" 
    
    coverage_details = []
    for ep in endpoints:
        is_tested = any(ep.path in url for url in tested_urls)
        coverage_details.append({
            "id": ep.id,
            "path": ep.path,
            "method": ep.method,
            "status": "TESTED" if is_tested else "UNTESTED"
        })
        
    return {
        "session_id": session_id,
        "total_endpoints": len(endpoints),
        "tested_endpoints": len([e for e in coverage_details if e["status"] == "TESTED"]),
        "endpoints": coverage_details,
        "auth_matrix": matrix
    }

@router.post("/sessions/{session_id}/recommendations/generate")
def generate_recommendation(session_id: int, req: RecommendationGenerateRequest, db: Session = Depends(get_db)):
    session = db.query(ResearchSession).filter(ResearchSession.id == session_id).first()
    if not session: raise HTTPException(404)
    
    # Program policy context
    program = db.query(Program).filter(Program.id == session.program_id).first()
    docs = db.query(KnowledgeDocument).filter(KnowledgeDocument.program_id == session.program_id).all()
    policy = "\n".join([d.title for d in docs]) or "Standard authorization required."
    
    # Previous findings on this endpoint
    findings = db.query(Finding).filter(Finding.program_id == session.program_id).limit(10).all()
    findings_str = "\n".join([f"{f.title} ({f.category})" for f in findings])
    
    coverage = f"Endpoint {req.endpoint} has not been fully tested."
    
    advisor = ResearchAdvisor(ProviderFactory.get_provider())
    try:
        rec_data = advisor.generate_recommendation(req.endpoint, policy, findings_str, coverage)
    except Exception as e:
        raise HTTPException(500, detail=str(e))
        
    # Check for duplicates before saving? Not strictly required by prompt, but good.
    # The user says "Before creating a new test plan: check whether an equivalent test already exists."
    
    rec = ResearchRecommendation(
        session_id=session.id,
        endpoint=req.endpoint,
        possible_test_categories=rec_data.possible_test_categories,
        reasoning=rec_data.reasoning,
        missing_evidence=rec_data.missing_evidence,
        recommended_manual_validation=rec_data.recommended_manual_validation,
        confidence=rec_data.confidence
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    
    log_audit(db, "RECOMMENDATION_CREATED", f"Rec:{rec.id}", "SUCCESS")
    return rec

@router.get("/sessions/{session_id}/recommendations")
def get_recommendations(session_id: int, db: Session = Depends(get_db)):
    return db.query(ResearchRecommendation).filter(ResearchRecommendation.session_id == session_id).order_by(ResearchRecommendation.id.desc()).all()

@router.post("/recommendations/{rec_id}/create-test-plan")
def create_test_plan_from_rec(rec_id: int, req: TestPlanFromRec, db: Session = Depends(get_db)):
    rec = db.query(ResearchRecommendation).filter(ResearchRecommendation.id == rec_id).first()
    if not rec: raise HTTPException(404)
    
    session = db.query(ResearchSession).filter(ResearchSession.id == rec.session_id).first()
    
    if session.status == ResearchSessionStatus.PAUSED:
        raise HTTPException(403, "Cannot create test plan for paused session.")
        
    if req.category not in rec.possible_test_categories:
        raise HTTPException(400, "Category not recommended.")
        
    # Duplicate Test Detection
    existing = db.query(TestPlan).filter(
        TestPlan.program_id == session.program_id,
        TestPlan.url == rec.endpoint,
        TestPlan.method == req.method,
        TestPlan.test_category == req.category
    ).first()
    
    if existing:
        return {"status": "POSSIBLE_DUPLICATE", "existing_plan_id": existing.id, "message": "An equivalent test already exists. Do you want to proceed manually?"}
        
    plan = TestPlan(
        program_id=session.program_id,
        session_id=session.id,
        recommendation_id=rec.id,
        test_category=req.category,
        method=req.method,
        url=rec.endpoint,
        requires_human_approval=True
    )
    db.add(plan)
    rec.status = "ACCEPTED"
    db.commit()
    db.refresh(plan)
    
    log_audit(db, "TEST_PLAN_CREATED_FROM_RECOMMENDATION", f"Plan:{plan.id}", "SUCCESS")
    return {"status": "CREATED", "plan": plan}

@router.get("/sessions/{session_id}/timeline")
def get_session_timeline(session_id: int, db: Session = Depends(get_db)):
    # Simple timeline from audit logs and session items
    logs = db.query(AuditLog).filter(AuditLog.action.like("%SESSION%"), AuditLog.object == f"Session:{session_id}").all()
    recs = db.query(ResearchRecommendation).filter(ResearchRecommendation.session_id == session_id).all()
    plans = db.query(TestPlan).filter(TestPlan.session_id == session_id).all()
    
    timeline = []
    for l in logs: timeline.append({"time": l.timestamp, "event": l.action, "details": l.result})
    for r in recs: timeline.append({"time": r.created_at, "event": "RECOMMENDATION_CREATED", "details": r.endpoint})
    for p in plans: timeline.append({"time": p.created_at, "event": "TEST_PLAN_CREATED", "details": f"{p.method} {p.url} ({p.test_category})"})
    
@router.post("/findings/{finding_id}/deduplicate")
def check_finding_duplicate(finding_id: int, db: Session = Depends(get_db)):
    finding = db.query(Finding).filter(Finding.id == finding_id).first()
    if not finding: raise HTTPException(404, "Finding not found")
    
    # Deterministic check: Same program, same category, similar title (substring or word overlap)
    others = db.query(Finding).filter(
        Finding.program_id == finding.program_id,
        Finding.id != finding.id,
        Finding.category == finding.category
    ).all()
    
    duplicates = []
    finding_words = set(finding.title.lower().split())
    
    for other in others:
        other_words = set(other.title.lower().split())
        # Jaccard similarity > 0.5 or exact match
        intersection = len(finding_words.intersection(other_words))
        union = len(finding_words.union(other_words))
        if union > 0 and (intersection / union) > 0.5:
            duplicates.append({"id": other.id, "title": other.title, "status": "POSSIBLE_DUPLICATE"})
            
    return {"finding_id": finding.id, "potential_duplicates": duplicates}

@router.get("/endpoints/{endpoint_id}/coverage")
def get_endpoint_coverage(endpoint_id: int, db: Session = Depends(get_db)):
    endpoint = db.query(Endpoint).filter(Endpoint.id == endpoint_id).first()
    if not endpoint: raise HTTPException(404)
    # Simple coverage logic
    plans = db.query(TestPlan).filter(TestPlan.url.contains(endpoint.path)).all()
    return {
        "endpoint_id": endpoint.id,
        "path": endpoint.path,
        "tests_executed": len([p for p in plans if p.status == TestStatus.EXECUTED]),
        "tests_planned": len([p for p in plans if p.status == TestStatus.PLANNED])
    }

@router.post("/findings/{finding_id}/analyze-false-positive")
def analyze_false_positive(finding_id: int, db: Session = Depends(get_db)):
    from ai.advisor import FalsePositiveAnalyzer
    from models.database import Evidence
    
    finding = db.query(Finding).filter(Finding.id == finding_id).first()
    if not finding: raise HTTPException(404)
    
    # Simple evidence aggregation
    evidences = db.query(Evidence).filter(Evidence.finding_id == finding_id).all()
    evidence_str = f"Found {len(evidences)} evidence records." # In a real app we'd fetch actual test observations
    
    analyzer = FalsePositiveAnalyzer(ProviderFactory.get_provider())
    try:
        analysis = analyzer.analyze(finding.title, evidence_str)
        return analysis.model_dump()
    except Exception as e:
        raise HTTPException(500, detail=str(e))
