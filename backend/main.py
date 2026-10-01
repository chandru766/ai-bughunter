import os
from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from models.database import engine, Base, SessionLocal, Program, ScopeRuleModel, Target, Endpoint, Finding, Evidence, Report, AuditLog, FindingStatus, ValidationStatus, BurpImport, KnowledgeDocument, AiAnalysisLog, TestPlan, TestResult, TestStatus, SystemConfig, AuthenticationContext, AuthenticationMutation
from scope.validator import ScopeValidator
from testing.planner import TestPlanner
from testing.executor import SafeExecutor
from analyzer.correlation import CorrelationEngine
from auth_bank.crypto import CryptoService
from auth_bank.schemas import AuthContextCreate, AuthContextResponse
from rag.knowledge import KnowledgeBaseMock, RAGContextBuilder
from ai.pipeline import AIPipeline
from ai.providers.factory import ProviderFactory
from observability.logger import log_event, get_request_id, set_request_id
import time
import uuid

class FindingValidationRequest(BaseModel):
    decision: str
    reason: str

class CorrelationRequest(BaseModel):
    program_id: Optional[int] = None

Base.metadata.create_all(bind=engine)
app = FastAPI(title="AI BugHunter API")

# Security Hardening: Environment-controlled CORS
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8080,http://127.0.0.1:8080").split(",")
if os.getenv("APP_ENV", "development").lower() == "production" and "*" in cors_origins:
    raise ValueError("Wildcard CORS is not permitted in production.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Security Headers and Observability Middleware
@app.middleware("http")
async def add_security_headers_and_log(request: Request, call_next):
    req_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    set_request_id(req_id)
    
    start_time = time.time()
    
    # Log Request
    log_event("HTTP_REQUEST", level=20, method=request.method, route=request.url.path, request_id=req_id)
    
    response = await call_next(request)
    
    duration_ms = int((time.time() - start_time) * 1000)
    
    # Log Response
    log_event("HTTP_RESPONSE", level=20, method=request.method, route=request.url.path, status=response.status_code, duration_ms=duration_ms, request_id=req_id)

    response.headers["X-Request-ID"] = req_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

@app.get("/health/live")
def health_live():
    return {"status": "alive"}

from sqlalchemy import text
@app.get("/health/ready")
def health_ready(db: Session = Depends(lambda: SessionLocal())):
    try:
        # Simple DB check
        db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception:
        raise HTTPException(status_code=503, detail="Database unavailable")
    finally:
        db.close()

knowledge_base = KnowledgeBaseMock()
ai_pipeline = AIPipeline(ProviderFactory.get_provider())

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

def log_audit(db, action, obj, result, request_id=None, severity="INFO"):
    if not request_id:
        request_id = get_request_id()
    log = AuditLog(action=action, object=obj, result=result, request_id=request_id, severity=severity)
    db.add(log)
    db.commit()
    
    log_event("AUDIT_LOG", level=20, action=action, object=obj, result=result, severity=severity, request_id=request_id)

# Existing Endpoints...
@app.get("/programs")
def get_programs(db: Session = Depends(get_db)): return db.query(Program).all()

@app.get("/audit-logs")
def get_audit_logs(page: int = 1, limit: int = 50, db: Session = Depends(get_db)): 
    offset = (page - 1) * limit
    return db.query(AuditLog).order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit).all()

import csv
import io
from fastapi.responses import PlainTextResponse
@app.get("/audit-logs/export")
def export_audit_logs(format: str = "json", db: Session = Depends(get_db)):
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).all()
    if format.lower() == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Timestamp", "Action", "Object", "Result", "Severity", "RequestID"])
        for log in logs:
            writer.writerow([log.id, log.timestamp.isoformat(), log.action, log.object, log.result, log.severity, log.request_id])
        return PlainTextResponse(output.getvalue(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=audit_logs.csv"})
    return logs

@app.get("/metrics")
def get_metrics(db: Session = Depends(get_db)):
    return {
        "tests_executed": db.query(TestResult).filter(TestResult.status == TestStatus.EXECUTED).count(),
        "tests_failed": db.query(TestResult).filter(TestResult.status == TestStatus.FAILED).count(),
        "tests_blocked": db.query(TestPlan).filter(TestPlan.status == TestStatus.BLOCKED).count(),
        "findings_created": db.query(Finding).count(),
        "findings_validated": db.query(Finding).filter(Finding.status == FindingStatus.VALIDATED).count(),
        "findings_false_positive": db.query(Finding).filter(Finding.status == FindingStatus.FALSE_POSITIVE).count(),
        "reports_generated": db.query(Report).count()
    }

@app.get("/system/status")
def get_system_status(db: Session = Depends(get_db)):
    config = db.query(SystemConfig).filter(SystemConfig.key == "KILL_SWITCH").first()
    provider_name = ProviderFactory.get_provider().__class__.__name__.replace("Provider", "").upper()
    return {
        "backend": "ONLINE",
        "database": "ONLINE",
        "ai_provider": provider_name,
        "rag": "READY",
        "kill_switch": config.value == "ACTIVE" if config else False,
        "local_fixture": "ONLINE"
    }

# --- AUTH BANK (PHASE 9) ---
@app.post("/auth-bank/contexts", response_model=AuthContextResponse)
def create_auth_context(ctx: AuthContextCreate, db: Session = Depends(get_db)):
    encrypted = CryptoService.encrypt(ctx.secret)
    db_ctx = AuthenticationContext(
        program_id=ctx.program_id,
        name=ctx.name,
        account_label=ctx.account_label,
        auth_type=ctx.auth_type,
        encrypted_secret=encrypted
    )
    db.add(db_ctx)
    db.commit()
    db.refresh(db_ctx)
    log_audit(db, "AUTH_CONTEXT_CREATED", ctx.name, "SUCCESS")
    
    return {
        "id": db_ctx.id,
        "name": db_ctx.name,
        "account_label": db_ctx.account_label,
        "auth_type": db_ctx.auth_type,
        "secret": "[REDACTED]",
        "enabled": db_ctx.enabled
    }

@app.get("/auth-bank/contexts", response_model=List[AuthContextResponse])
def get_auth_contexts(db: Session = Depends(get_db)):
    contexts = db.query(AuthenticationContext).all()
    return [{
        "id": c.id, "name": c.name, "account_label": c.account_label,
        "auth_type": c.auth_type, "secret": "[REDACTED]", "enabled": c.enabled
    } for c in contexts]

# --- TESTING ENGINE ---
@app.get("/testing/plans")
def get_test_plans(page: int = 1, limit: int = 50, db: Session = Depends(get_db)):
    offset = (page - 1) * limit
    return db.query(TestPlan).order_by(TestPlan.created_at.desc()).offset(offset).limit(limit).all()

@app.post("/testing/approve/{plan_id}")
def approve_test_plan(plan_id: int, db: Session = Depends(get_db)):
    plan = db.query(TestPlan).filter(TestPlan.id == plan_id).first()
    if not plan: raise HTTPException(404)
    plan.status = TestStatus.APPROVED
    db.commit()
    log_audit(db, "TEST_APPROVED", f"Plan:{plan_id}", "SUCCESS")
    return {"status": "APPROVED"}

@app.post("/testing/execute/{plan_id}")
async def execute_test(plan_id: int, db: Session = Depends(get_db)):
    plan = db.query(TestPlan).filter(TestPlan.id == plan_id).first()
    
    rules = db.query(ScopeRuleModel).filter(ScopeRuleModel.program_id == plan.program_id).all()
    validator = ScopeValidator()
    if not rules: validator.add_rule(plan.url, False) # Fallback for local testing scope MVP
    for rule in rules: validator.add_rule(rule.pattern, rule.is_exclusion)
        
    try:
        result = await SafeExecutor.execute(db, plan, validator)
        
        # Phase 10: RAG and AI Pipeline Integration
        retrieved_docs = knowledge_base.search(
            query=f"{result.request_raw}\n{result.response_raw}",
            program_id=plan.program_id
        )
        
        rag_context = RAGContextBuilder.build_prompt(
            request=result.request_raw,
            response=result.response_raw,
            retrieved_docs=retrieved_docs
        )
        
        ai_analysis = ai_pipeline.run_analysis(
            request_raw=result.request_raw,
            response_raw=result.response_raw,
            rag_context=rag_context
        )
        
        # Phase 12: Finding Creation & Evidence Association
        finding = Finding(
            program_id=plan.program_id,
            title=ai_analysis.title,
            category=ai_analysis.category,
            severity=ai_analysis.recommended_severity,
            status=FindingStatus.NEEDS_VALIDATION,
            validation_status=ValidationStatus.UNVALIDATED
        )
        db.add(finding)
        db.commit()
        db.refresh(finding)
        
        # Evidence limitation: Current schema only allows finding_id.
        # We associate a blank evidence record as a placeholder for the test result.
        evidence = Evidence(finding_id=finding.id)
        db.add(evidence)
        db.commit()
        
        log_audit(db, "TEST_EXECUTED", f"Plan:{plan_id}", "SUCCESS")
        log_audit(db, "FINDING_CREATED", f"Finding:{finding.id}", "SUCCESS")
        return {
            "status": "EXECUTED",
            "result_id": result.id,
            "finding_id": finding.id,
            "ai_analysis": ai_analysis.model_dump()
        }
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))

@app.post("/testing/bola")
async def plan_bola_test(program_id: int, url: str, source_id: int, target_id: int, db: Session = Depends(get_db)):
    src_ctx = db.query(AuthenticationContext).filter(AuthenticationContext.id == source_id).first()
    tgt_ctx = db.query(AuthenticationContext).filter(AuthenticationContext.id == target_id).first()
    if not src_ctx or not tgt_ctx:
        raise HTTPException(400, "Auth contexts not found")
        
    plan = TestPlanner.create_plan(program_id, None, url, "GET", "Authorization comparison")
    db.add(plan)
    db.commit()
    db.refresh(plan)
    
    mut = AuthenticationMutation(
        test_plan_id=plan.id,
        source_context_id=source_id,
        target_context_id=target_id,
        mutation_type="AUTH_CONTEXT_SWAP"
    )
    db.add(mut)
    db.commit()
    
    log_audit(db, "TEST_PLAN_CREATED", f"BOLA Test on {url}", "SUCCESS")
    return {"status": "PLANNED", "plan_id": plan.id}

@app.get("/testing/kill-switch/status")
def kill_switch_status(db: Session = Depends(get_db)):
    config = db.query(SystemConfig).filter(SystemConfig.key == "KILL_SWITCH").first()
    return {"active": config.value == "ACTIVE" if config else False}

@app.post("/testing/kill-switch")
def trigger_kill_switch(db: Session = Depends(get_db)):
    config = db.query(SystemConfig).filter(SystemConfig.key == "KILL_SWITCH").first()
    if not config:
        config = SystemConfig(key="KILL_SWITCH", value="ACTIVE")
        db.add(config)
    else:
        config.value = "ACTIVE" if config.value != "ACTIVE" else "INACTIVE"
    db.commit()
    return {"status": f"TESTING_{'HALTED' if config.value == 'ACTIVE' else 'RESUMED'}"}

# --- FINDING MANAGEMENT (PHASE 12) ---
@app.get("/findings")
def get_findings(page: int = 1, limit: int = 50, db: Session = Depends(get_db)):
    offset = (page - 1) * limit
    return db.query(Finding).order_by(Finding.id.desc()).offset(offset).limit(limit).all()

@app.get("/findings/{finding_id}")
def get_finding(finding_id: int, db: Session = Depends(get_db)):
    finding = db.query(Finding).filter(Finding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    return finding

@app.post("/findings/{finding_id}/validate")
def validate_finding(finding_id: int, req: FindingValidationRequest, db: Session = Depends(get_db)):
    finding = db.query(Finding).filter(Finding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
        
    if finding.status != FindingStatus.NEEDS_VALIDATION:
        raise HTTPException(status_code=409, detail="Finding is not awaiting validation")
        
    decision = req.decision.strip().upper()
    reason = req.reason.strip()
    
    if decision not in ["CONFIRM", "REJECT"]:
        raise HTTPException(status_code=400, detail="Invalid decision")
        
    if not reason:
        raise HTTPException(status_code=400, detail="Validation reason required")
        
    if decision == "CONFIRM":
        finding.status = FindingStatus.VALIDATED
        finding.validation_status = ValidationStatus.RESEARCHER_CONFIRMED
        log_audit(db, "FINDING_VALIDATED", f"Finding:{finding_id}", reason)
    else:
        finding.status = FindingStatus.FALSE_POSITIVE
        finding.validation_status = ValidationStatus.RESEARCHER_REJECTED
        log_audit(db, "FINDING_REJECTED", f"Finding:{finding_id}", reason)
        
    db.commit()
    db.refresh(finding)
    
    return {
        "finding_id": finding.id,
        "status": finding.status,
        "validation_status": finding.validation_status,
        "decision": decision
    }

@app.post("/findings/correlate")
def run_correlation(req: Optional[CorrelationRequest] = None, db: Session = Depends(get_db)):
    from analyzer.correlation import CorrelationEngine
    program_id = req.program_id if req else None
    log_audit(db, "CORRELATION_STARTED", f"Program:{program_id}", "STARTED")
    try:
        result = CorrelationEngine.correlate(db, program_id)
        log_audit(db, "CORRELATION_COMPLETED", f"Program:{program_id}", f"Analyzed:{result['findings_analyzed']}, Chains:{result['chains_created']}")
        return result
    except Exception as e:
        log_audit(db, "CORRELATION_FAILED", f"Program:{program_id}", str(e))
        raise HTTPException(status_code=500, detail="Correlation failed")

@app.get("/finding-chains")
def get_finding_chains(program_id: Optional[int] = None, page: int = 1, limit: int = 50, db: Session = Depends(get_db)):
    from models.database import FindingChain
    query = db.query(FindingChain)
    offset = (page - 1) * limit
    return query.order_by(FindingChain.id.desc()).offset(offset).limit(limit).all()

# --- REPORTS (PHASE 14) ---
@app.get("/reports")
def get_reports(page: int = 1, limit: int = 50, db: Session = Depends(get_db)):
    offset = (page - 1) * limit
    return db.query(Report).order_by(Report.id.desc()).offset(offset).limit(limit).all()

@app.get("/reports/{report_id}")
def get_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report: raise HTTPException(status_code=404, detail="Report not found")
    return report

@app.get("/reports/finding/{finding_id}")
def get_reports_by_finding(finding_id: int, db: Session = Depends(get_db)):
    return db.query(Report).filter(Report.finding_id == finding_id).order_by(Report.id.desc()).all()

@app.post("/reports/generate/{finding_id}")
def generate_report(finding_id: int, db: Session = Depends(get_db)):
    from reports.generator import ReportGenerator
    log_audit(db, "REPORT_GENERATION_STARTED", f"Finding:{finding_id}", "STARTED")
    try:
        result = ReportGenerator.generate_draft(db, finding_id)
        if result.get("status") == "ERROR":
            log_audit(db, "REPORT_GENERATION_FAILED", f"Finding:{finding_id}", result["reason"])
            raise HTTPException(status_code=409 if "VALIDATED" in result["reason"] else 404, detail=result["reason"])
        
        log_audit(db, "REPORT_GENERATED", f"Finding:{finding_id}", f"Report:{result['report_id']}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        log_audit(db, "REPORT_GENERATION_FAILED", f"Finding:{finding_id}", str(e))
        raise HTTPException(status_code=500, detail=str(e))

from api_phase19 import router as research_router
app.include_router(research_router)

from api_ai_security import router as ai_security_router
app.include_router(ai_security_router)

from api_agent_security import router as agent_security_router
app.include_router(agent_security_router)

from api_multi_agent import router as multi_agent_router
app.include_router(multi_agent_router)
