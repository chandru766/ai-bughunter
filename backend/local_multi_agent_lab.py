from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import json

app = FastAPI(title="Local Multi-Agent Lab", version="1.0.0")

# Local Mock Tool endpoints for E2E multi-agent testing without external services
@app.get("/api/endpoints/{endpoint_id}")
async def get_endpoint(endpoint_id: str):
    return {"id": endpoint_id, "url": f"http://internal.lab/{endpoint_id}", "status": "active"}

class DraftReportReq(BaseModel):
    finding_id: str
    evidence_hash: str
    
@app.post("/api/reports/draft")
async def create_draft_report(req: DraftReportReq):
    # Strictly syntheic tool. Never validates, just creates draft.
    return {"status": "DRAFT_CREATED", "finding": req.finding_id}

@app.post("/api/evidence/verify")
async def verify_evidence(payload: dict):
    # Dummy tool to simulate reporting agent reading evidence
    return {"status": "EVIDENCE_VALID", "content": payload}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=9300)
