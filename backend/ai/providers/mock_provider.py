from .base import LLMProvider
import json

class MockProvider(LLMProvider):
    def analyze(self, prompt: str) -> str:
        # Structural Prompt-Injection test simulation
        if "Ignore all instructions" in prompt:
            return json.dumps({"error": "Prompt injection detected internally"})
            
        if "CorrelationAnalysis" in prompt or "kill-chains" in prompt:
            return json.dumps({
                "relationships": [
                    { "from": 1, "to": 2, "relationship": "AUTHORIZATION_TO_BOLA", "confidence": "MEDIUM" }
                ],
                "combined_impact_hypothesis": "Mocked chained impact escalating severity.",
                "combined_impact": "Mocked chained impact escalating severity.",
                "required_validation": "Check logs.",
                "missing_evidence": [],
                "validation_steps": [],
                "potential_duplicate": True,
                "duplicate_finding_ids": [4]
            })
            
        if "draft report" in prompt.lower() or "bug bounty report" in prompt.lower():
            return """# Vulnerability Title
Mocked Report Title
## Severity
LOW
## Vulnerability Category
Information Disclosure
## Affected Program
Program 1
## Affected Target
api.example.test
## Endpoint
/api/users/{id}
## Summary
Mocked Summary
## Technical Description
Server headers indicate outdated software.
## Observation
Observation here.
## Root Cause
Misconfiguration.
## Security Impact
Exposure of internal server structure.
## Evidence
N/A
## Reproduction Steps
1. Send request.
2. Observe headers.
## Expected Behavior
No version info.
## Actual Behavior
Version info exposed.
## Validation Status
Researcher Confirmed
## Remediation
Hide headers.
## References
- OWASP
## Correlation/chain information
Potentially related findings in Chain ID 1"""

            
        mock_response = {
            "title": "Mocked Information Disclosure",
            "category": "Information Disclosure",
            "target": "api.example.test",
            "endpoint": "/api/users/{id}",
            "observation": "Server headers indicate outdated software.",
            "root_cause": "Misconfiguration.",
            "impact": "Exposure of internal server structure.",
            "confidence": "MEDIUM",
            "supporting_evidence": [],
            "counter_evidence": ["Server version may be spoofed."],
            "validation_steps": ["Check HTTP headers manually."],
            "recommended_severity": "LOW",
            "citations": ["K1"],
            "status": "NEEDS_VALIDATION"
        }
        return json.dumps(mock_response)
