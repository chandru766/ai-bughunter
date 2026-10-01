class AIAnalyzer:
    @staticmethod
    def analyze_response(test_response: dict, scope_decision: str) -> dict:
        # HARD SECURITY BOUNDARY
        if scope_decision != "IN_SCOPE":
            raise ValueError("Target is OUT_OF_SCOPE. AI analysis blocked.")
            
        # Example structured JSON response from LLM
        return {
            "title": "Example Potential Information Disclosure",
            "category": "Information Disclosure",
            "target": test_response.get("url", ""),
            "endpoint": test_response.get("path", ""),
            "observation": "Response size increased and contains stack trace patterns.",
            "root_cause": "Unhandled exception in input validation.",
            "potential_impact": "Exposure of internal server structure.",
            "confidence": "MEDIUM",
            "evidence_ids": [],
            "counter_evidence": ["Framework defaults often catch exceptions securely."],
            "validation_steps": ["Submit payload manually and observe output structure."],
            "status": "NEEDS_VALIDATION"
        }
        
    @staticmethod
    def analyze_false_positive(finding_details: dict) -> dict:
        return {
            "supporting_evidence": ["Status code changed from 403 to 200."],
            "counter_evidence": ["Length is exactly 0, could be a WAF drop."],
            "missing_evidence": ["Authentication state during test."],
            "validation_plan": "Re-run with valid session cookie."
        }
