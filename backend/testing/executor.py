import httpx
from sqlalchemy.orm import Session
from models.database import TestPlan, TestResult, TestStatus, TestLevel, AuthenticationMutation, AuthenticationContext
from testing.safety import SafetyPolicy
from scope.validator import ScopeValidator
from auth_bank.crypto import CryptoService
from auth_bank.redaction import SecretRedactor
from observability.logger import log_event
import time

class SafeExecutor:
    @staticmethod
    async def execute(db: Session, plan: TestPlan, validator: ScopeValidator):
        if SafetyPolicy.is_kill_switch_active(db):
            plan.status = TestStatus.BLOCKED
            db.commit()
            log_event("KILL_SWITCH_BLOCKED", level=30, plan_id=plan.id)
            raise ValueError("Execution Blocked: Kill Switch Active")
            
        decision = validator.evaluate(plan.url)
        if decision.value != "IN_SCOPE":
            plan.status = TestStatus.BLOCKED
            db.commit()
            log_event("SCOPE_BLOCKED", level=30, plan_id=plan.id, url=plan.url)
            raise ValueError(f"Execution Blocked: Target {plan.url} is OUT_OF_SCOPE")
            
        if not SafetyPolicy.rate_limit_check(db, plan.target_id):
            plan.status = TestStatus.BLOCKED
            db.commit()
            log_event("RATE_LIMIT_BLOCKED", level=30, plan_id=plan.id)
            raise ValueError("Execution Blocked: Rate Limit Exceeded")
            
        if plan.requires_human_approval and plan.status != TestStatus.APPROVED:
            log_event("APPROVAL_BLOCKED", level=30, plan_id=plan.id)
            raise ValueError("Execution Blocked: Human Approval Required")

        # Phase 9: Resolve Authentication Mutations safely
        headers = {"User-Agent": "AI-BugHunter-Authorized-Test"}
        mutation = db.query(AuthenticationMutation).filter(AuthenticationMutation.test_plan_id == plan.id).first()
        if mutation:
            tgt_ctx = db.query(AuthenticationContext).filter(AuthenticationContext.id == mutation.target_context_id).first()
            if tgt_ctx:
                secret = CryptoService.decrypt(tgt_ctx.encrypted_secret)
                if tgt_ctx.auth_type == "JWT":
                    headers["Authorization"] = f"Bearer {secret}"
                elif tgt_ctx.auth_type == "CUSTOM_HEADER":
                    headers["Authorization"] = secret

        try:
            start_time = time.time()
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.request(
                    method=plan.method,
                    url=plan.url,
                    headers=headers
                )
                
                duration_ms = int((time.time() - start_time) * 1000)
                
                # Redact the raw request before storing as evidence so JWTs never touch the database
                req_raw_safe = f"{plan.method} {plan.url} HTTP/1.1\n"
                if "Authorization" in headers:
                    req_raw_safe += f"Authorization: {SecretRedactor.redact(headers['Authorization'])}\n"
                
                resp_raw = f"HTTP/1.1 {res.status_code}\n{res.text}"
                
                result = TestResult(
                    test_plan_id=plan.id,
                    status=TestStatus.EXECUTED,
                    request_raw=req_raw_safe,
                    response_raw=resp_raw,
                    observations={"status": res.status_code}
                )
                plan.status = TestStatus.EXECUTED
                db.add(result)
                db.commit()
                
                log_event("TEST_EXECUTED", level=20, plan_id=plan.id, program_id=plan.program_id, target_id=plan.target_id, method=plan.method, http_status=res.status_code, duration_ms=duration_ms)
                
                return result
        except Exception as e:
            plan.status = TestStatus.FAILED
            db.commit()
            log_event("TEST_FAILED", level=40, plan_id=plan.id, error=str(e))
            raise ValueError(f"Execution Failed: {str(e)}")
