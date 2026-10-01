import json
from pydantic import BaseModel, ValidationError, Field
from typing import List, Optional
from sqlalchemy.orm import Session
from models.database import Finding, FindingChain
from ai.providers.factory import ProviderFactory

class RelationshipData(BaseModel):
    from_finding: int = Field(alias="from")
    to_finding: int = Field(alias="to")
    relationship: str
    confidence: str
    
    class Config:
        populate_by_name = True

class CorrelationAnalysis(BaseModel):
    relationships: List[RelationshipData]
    combined_impact: str
    missing_evidence: List[str]
    validation_steps: List[str]
    potential_duplicate: bool = False
    duplicate_finding_ids: List[int] = []

class CorrelationEngine:
    @staticmethod
    def correlate(db: Session, program_id: Optional[int] = None):
        query = db.query(Finding).filter(Finding.status.in_(["NEEDS_VALIDATION", "UNVALIDATED"]))
        if program_id is not None:
            query = query.filter(Finding.program_id == program_id)
            
        unvalidated = query.all()
        if len(unvalidated) < 2:
            return {
                "status": "CORRELATED",
                "program_id": program_id,
                "chains_created": 0,
                "findings_analyzed": len(unvalidated),
                "chains": []
            }
            
        # Group by program_id to enforce program isolation
        from collections import defaultdict
        program_findings = defaultdict(list)
        for f in unvalidated:
            program_findings[f.program_id].append(f)
            
        provider = ProviderFactory.get_provider()
        chains_created = 0
        chains_info = []
        
        for pid, findings in program_findings.items():
            if len(findings) < 2:
                continue
                
            findings_json = []
            for f in findings:
                findings_json.append({"id": f.id, "title": f.title, "category": f.category, "severity": f.severity})
                
            prompt = f"""
SYSTEM:
Analyze the following authorized security findings to detect potential kill-chains or relationships.
Do not claim exploitability. Output strictly valid JSON.

FINDINGS:
{json.dumps(findings_json, indent=2)}

TASK:
1. Determine relationships (e.g. Auth bypass -> IDOR).
2. Check for potential duplicates based on title and category.
3. Output JSON matching:
{{
    "relationships": [
        {{ "from": 1, "to": 2, "relationship": "AUTHORIZATION_TO_BOLA", "confidence": "MEDIUM" }}
    ],
    "combined_impact": "Impact explanation",
    "missing_evidence": [],
    "validation_steps": [],
    "potential_duplicate": false,
    "duplicate_finding_ids": []
}}
"""
            raw_output = provider.analyze(prompt)
            try:
                parsed = json.loads(raw_output)
                analysis = CorrelationAnalysis(**parsed)
                
                if analysis.relationships:
                    finding_ids = list(set([r.from_finding for r in analysis.relationships] + [r.to_finding for r in analysis.relationships]))
                    relationships_dict = [r.model_dump(by_alias=True) for r in analysis.relationships]
                    
                    chain = FindingChain(
                        findings=finding_ids,
                        relationships=relationships_dict,
                        combined_impact=analysis.combined_impact,
                        validation_status="UNVALIDATED"
                    )
                    db.add(chain)
                    db.commit()
                    db.refresh(chain)
                    
                    chains_created += 1
                    chains_info.append({
                        "chain_id": chain.id,
                        "findings": finding_ids,
                        "validation_status": "UNVALIDATED",
                        "relationships": relationships_dict,
                        "potential_duplicate": analysis.potential_duplicate
                    })
                    
            except (json.JSONDecodeError, ValidationError) as e:
                pass # Skip failed analyses
                
        return {
            "status": "CORRELATED",
            "program_id": program_id,
            "chains_created": chains_created,
            "findings_analyzed": len(unvalidated),
            "chains": chains_info
        }
