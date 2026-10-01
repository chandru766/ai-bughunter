import json
import hashlib
from datetime import datetime
from sqlalchemy.orm import Session
from models.database import Finding, FindingStatus, ValidationStatus, Report, TestResult, FindingChain, Evidence
from ai.providers.factory import ProviderFactory
from auth_bank.redaction import SecretRedactor

class ReportGenerator:
    @staticmethod
    def _sanitize_evidence(evidence_str: str) -> str:
        if not evidence_str:
            return "Not available in the current evidence."
        
        lines = evidence_str.split('\n')
        safe_lines = []
        suspicious = ["jwt", "cookie", "api-key", "password", "authorization", "secret", "token"]
        for line in lines:
            if any(k in line.lower() for k in suspicious):
                parts = line.split(":", 1)
                if len(parts) == 2:
                    safe_lines.append(f"{parts[0]}: {SecretRedactor.redact(parts[1].strip())}")
                else:
                    safe_lines.append(SecretRedactor.redact(line))
            else:
                safe_lines.append(line)
        return '\n'.join(safe_lines)

    @staticmethod
    def generate_draft(db: Session, finding_id: int):
        finding = db.query(Finding).filter(Finding.id == finding_id).first()
        if not finding:
            return {"status": "ERROR", "reason": "Finding not found"}
            
        if finding.status != FindingStatus.VALIDATED or finding.validation_status != ValidationStatus.RESEARCHER_CONFIRMED:
            return {"status": "ERROR", "reason": "Finding must be VALIDATED and RESEARCHER_CONFIRMED to generate a report"}
            
        # Retrieve Evidence
        evidence_record = db.query(Evidence).filter(Evidence.finding_id == finding.id).first()
        # Find related TestResult (Mock: We find latest executed test plan)
        test_result = db.query(TestResult).order_by(TestResult.id.desc()).first()
        
        evidence_str = ""
        if test_result:
            evidence_str += f"Request:\n{test_result.request_raw}\n\nResponse:\n{test_result.response_raw}"
            
        safe_evidence = ReportGenerator._sanitize_evidence(evidence_str)
        
        # Retrieve Correlation
        chain_info = "Not available in the current evidence."
        chain = db.query(FindingChain).filter(FindingChain.findings.contains(finding.id)).first()
        if chain:
            chain_info = f"Potentially related findings in Chain ID {chain.id}: {chain.combined_impact}"
            
        provider = ProviderFactory.get_provider()
        
        prompt = f"""
SYSTEM:
You are an expert Application Security Engineer writing a professional bug bounty report.
The researcher has manually VALIDATED this finding. Treat the AI output as draft text only. Do not invent CVSS scores or missing data.

FINDING SUMMARY:
Title: {finding.title}
Category: {finding.category}
Severity: {finding.severity}
Status: {finding.validation_status.value}

EVIDENCE:
{safe_evidence}

CORRELATION:
{chain_info}

TASK:
Write a comprehensive draft report in strictly Markdown format using exactly this structure:
# Vulnerability Title
## Severity
## Vulnerability Category
## Affected Program
## Affected Target
## Endpoint
## Summary
## Technical Description
## Observation
## Root Cause
## Security Impact
## Evidence
## Reproduction Steps
## Expected Behavior
## Actual Behavior
## Validation Status
## Remediation
## References
## Correlation/chain information
"""
        draft_markdown = provider.analyze(prompt)
        report_hash = hashlib.sha256(draft_markdown.encode('utf-8')).hexdigest()
        
        json_content = {
            "title": finding.title,
            "severity": finding.severity,
            "category": finding.category,
            "target": "Not available in the current evidence.",
            "endpoint": "Not available in the current evidence.",
            "summary": "Not available in the current evidence.",
            "description": "Not available in the current evidence.",
            "impact": "Not available in the current evidence.",
            "root_cause": "Not available in the current evidence.",
            "evidence": [safe_evidence],
            "reproduction_steps": ["Not available in the current evidence."],
            "expected_behavior": "Not available in the current evidence.",
            "actual_behavior": "Not available in the current evidence.",
            "remediation": "Not available in the current evidence.",
            "validation_status": finding.validation_status.value
        }
        
        report_record = Report(
            finding_id=finding.id,
            markdown_content=draft_markdown,
            json_content=json_content,
            report_hash=report_hash
        )
        db.add(report_record)
        db.commit()
        db.refresh(report_record)
        
        return {
            "status": "DRAFT_GENERATED",
            "report_id": report_record.id,
            "finding_id": finding.id,
            "timestamp": report_record.created_at.isoformat(),
            "report_hash": report_hash,
            "markdown": draft_markdown,
            "json": json_content
        }
