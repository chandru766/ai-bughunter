# Phase 19: Security Intelligence & Research Orchestration

## Overview
The Research Orchestration layer coordinates security research workflows without violating the platform's non-negotiable safety boundaries. It provides AI-assisted recommendations and deterministic tracking while ensuring all execution and validation remain firmly under human control.

## Key Components

### 1. Research Sessions
A `ResearchSession` encapsulates an active security workflow against a specific `Program`. It allows researchers to:
- Group recommendations and test coverage.
- Pause/resume testing (preventing new automated tasks when paused).
- Track progress via a unified timeline.

### 2. Coverage Tracking & Authentication Matrix
Coverage tracking deterministically calculates which endpoints have been tested against which authentication contexts. 
- The **Authentication Matrix** identifies testing gaps (e.g., Endpoint X was tested as Account A, but not as Account B or Anonymous).
- It does not calculate arbitrary "risk scores" but simply surfaces factual testing coverage.

### 3. AI Research Advisor
The `ResearchAdvisor` uses large language models to analyze endpoints, previous findings, and program policies.
- It recommends specific security categories (e.g., `BOLA`, `IDOR`).
- It generates structured JSON (via strict Pydantic schemas).
- **Safety Boundary**: The AI is strictly prohibited from generating executable commands or executing tests automatically.

### 4. Deterministic Deduplication
The platform detects potential duplicate test plans and duplicate findings using deterministic similarity logic (e.g., Jaccard similarity on finding titles and categories).
- It highlights potential overlaps (`POSSIBLE_DUPLICATE`) but requires the researcher to manually confirm or dismiss them.

### 5. False Positive Assistance
The `FalsePositiveAnalyzer` examines evidence and a finding to provide hypotheses on whether a finding is a false positive.
- Provides supporting observations, counter-observations, and missing evidence.
- It does NOT automatically change the state of any finding. The researcher must explicitly `CONFIRM` or `REJECT`.

### 6. Timeline and Auditing
Every operation within a Research Session is recorded in the `AuditLog` table.
- Timeline APIs aggregate logs and recommendations to give a chronological view of the session.

## Safety Guarantees Verified
- The AI cannot execute tests. (Only TestPlans are created, requiring human approval).
- Program isolation is maintained by filtering queries to specific `program_id`.
- Duplicate findings are never automatically merged.
- Context windows passed to the AI do not include credentials or unredacted secrets.
