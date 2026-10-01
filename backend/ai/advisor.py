import json
from pydantic import BaseModel, ValidationError, field_validator
from typing import List
from observability.logger import log_event
import time

class RecommendationOutput(BaseModel):
    endpoint: str
    observations: List[str]
    possible_test_categories: List[str]
    reasoning: List[str]
    missing_evidence: List[str]
    recommended_manual_validation: List[str]
    confidence: str

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: str) -> str:
        v = v.upper()
        if v not in ["LOW", "MEDIUM", "HIGH"]:
            raise ValueError("Invalid confidence level")
        return v
        
    @field_validator("possible_test_categories")
    @classmethod
    def validate_categories(cls, v: List[str]) -> List[str]:
        valid_cats = ["AUTHENTICATION", "AUTHORIZATION", "BOLA", "IDOR", "INPUT_VALIDATION", 
                      "SQL_INJECTION", "XSS", "CSRF", "SSRF", "FILE_UPLOAD", "PATH_TRAVERSAL", 
                      "SECURITY_MISCONFIGURATION", "API_SECURITY"]
        for cat in v:
            if cat.upper() not in valid_cats:
                raise ValueError(f"Invalid category: {cat}")
        return [c.upper() for c in v]

class ResearchAdvisor:
    def __init__(self, provider):
        self.provider = provider
        
    def build_prompt(self, endpoint: str, program_policy: str, findings: str, coverage: str) -> str:
        return f"""
SYSTEM:
You are an authorized security research advisor.
Your role is to analyze the provided endpoint context and suggest possible test categories.
You must NOT output commands like EXECUTE_NOW, nor arbitrary URLs, shell commands, or automatic approval instructions.
Your output must be strictly valid JSON matching this schema:
{{
    "endpoint": "{endpoint}",
    "observations": ["obs1", "obs2"],
    "possible_test_categories": ["BOLA", "AUTHORIZATION"],
    "reasoning": ["reason1", "reason2"],
    "missing_evidence": ["missing1"],
    "recommended_manual_validation": ["step1"],
    "confidence": "LOW|MEDIUM|HIGH"
}}

PROGRAM POLICY:
{program_policy}

ENDPOINT:
{endpoint}

COVERAGE SO FAR:
{coverage}

FINDINGS:
{findings}

TASK: Provide JSON output as requested.
"""

    def generate_recommendation(self, endpoint: str, program_policy: str, findings: str, coverage: str) -> RecommendationOutput:
        prompt = self.build_prompt(endpoint, program_policy, findings, coverage)
        
        provider_name = self.provider.__class__.__name__
        log_event("AI_ADVISOR_STARTED", provider=provider_name, endpoint=endpoint)
        start_time = time.time()
        
        retries = 2
        for _ in range(retries):
            raw_output = self.provider.analyze(prompt)
            try:
                # Basic sanity checks to reject injection attempts posing as output
                if "EXECUTE_NOW" in raw_output or "http://" in raw_output.replace(endpoint, "") or "https://" in raw_output.replace(endpoint, ""):
                     raise ValueError("Malicious output detected")
                
                parsed = json.loads(raw_output)
                rec = RecommendationOutput(**parsed)
                
                duration_ms = int((time.time() - start_time) * 1000)
                log_event("AI_ADVISOR_COMPLETED", provider=provider_name, endpoint=endpoint, duration_ms=duration_ms)
                return rec
            except (json.JSONDecodeError, ValidationError, ValueError) as e:
                prompt += f"\n\nERROR IN PREVIOUS OUTPUT: {str(e)}\nReturn ONLY valid JSON matching the schema."
                
        duration_ms = int((time.time() - start_time) * 1000)
        log_event("AI_ADVISOR_FAILED", level=40, provider=provider_name, endpoint=endpoint, duration_ms=duration_ms)
        raise ValueError("AI_ADVISOR_FAILED: Max retries exceeded.")

class FalsePositiveOutput(BaseModel):
    supporting_observations: List[str]
    counter_observations: List[str]
    missing_evidence: List[str]
    manual_validation_steps: List[str]

class FalsePositiveAnalyzer:
    def __init__(self, provider):
        self.provider = provider
        
    def build_prompt(self, finding_title: str, evidence: str) -> str:
        return f"""
SYSTEM:
Analyze the finding and evidence to determine if it might be a false positive.
Provide supporting observations, counter observations, missing evidence, and manual validation steps.
Do not change finding status. You are an advisor.
Return strictly valid JSON matching this schema:
{{
    "supporting_observations": ["..."],
    "counter_observations": ["..."],
    "missing_evidence": ["..."],
    "manual_validation_steps": ["..."]
}}

FINDING: {finding_title}
EVIDENCE: {evidence}
"""

    def analyze(self, finding_title: str, evidence: str) -> FalsePositiveOutput:
        prompt = self.build_prompt(finding_title, evidence)
        raw_output = self.provider.analyze(prompt)
        try:
            parsed = json.loads(raw_output)
            return FalsePositiveOutput(**parsed)
        except Exception as e:
            raise ValueError(f"Failed to parse false-positive analysis: {e}")

class AISecurityOutput(BaseModel):
    title: str
    category: str
    observation: str
    impact: str
    confidence: str
    supporting_evidence: List[str]
    counter_evidence: List[str]
    missing_evidence: List[str]
    validation_steps: List[str]
    recommended_severity: str
    status: str

class AISecurityAnalyzer:
    def __init__(self, provider):
        self.provider = provider

    def build_prompt(self, request_raw: str, response_raw: str, test_category: str, policy: str) -> str:
        return f"""
SYSTEM:
You are an AI Security Analyzer. Analyze the interaction to determine if a vulnerability exists according to the test category.
Return strictly valid JSON matching this schema:
{{
    "title": "...",
    "category": "{test_category}",
    "observation": "...",
    "impact": "...",
    "confidence": "MEDIUM",
    "supporting_evidence": [],
    "counter_evidence": [],
    "missing_evidence": [],
    "validation_steps": [],
    "recommended_severity": "MEDIUM",
    "status": "NEEDS_VALIDATION"
}}

POLICY: {policy}
TEST CATEGORY: {test_category}
REQUEST: {request_raw}
RESPONSE: {response_raw}
"""

    def analyze(self, request_raw: str, response_raw: str, test_category: str, policy: str = "") -> AISecurityOutput:
        prompt = self.build_prompt(request_raw, response_raw, test_category, policy)
        raw_output = self.provider.analyze(prompt)
        try:
            parsed = json.loads(raw_output)
            # Semantic validation: AI must not override the researcher or claim automatic verification
            status = parsed.get("status")
            if status in ["VALIDATED", "RESEARCHER_CONFIRMED", "FALSE_POSITIVE", "RESEARCHER_REJECTED"]:
                raise ValueError(f"Semantic Validation Failed: AI cannot output status '{status}'")
            return AISecurityOutput(**parsed)
        except Exception as e:
            raise ValueError(f"Failed to parse AI security analysis: {e}")
