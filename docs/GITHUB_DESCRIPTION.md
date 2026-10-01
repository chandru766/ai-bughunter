### Short Description
An AI-assisted security research platform focusing on strict execution boundaries, immutable evidence collection, and human-in-the-loop vulnerability validation.

### Long Description
AI-BugHunter is an AI-assisted security research platform built to orchestrate controlled vulnerability testing. Instead of acting as an unpredictable autonomous hacking system, the platform utilizes strict Python-enforced security boundaries—such as scope validators, global kill switches, and explicit human approval gates—to maintain absolute control over the testing lifecycle.

The system uses a Retrieval-Augmented Generation (RAG) pipeline to analyze captured HTTP evidence, actively defending against prompt injections while sanitizing sensitive credentials from the context window. All AI-generated hypotheses strictly default to a `NEEDS_VALIDATION` state, ensuring that humans always retain the final authority over vulnerability confirmation and reporting.

### Key Features
- Strict Scope Enforcement (SSRF prevention)
- Human Approval Gates for high-impact payloads
- Credential Encryption & Context Redaction
- Immutable HTTP Evidence Collection
- RAG-assisted Evidence Analysis
- Prompt-Injection Defense Mechanisms
- Multi-Agent Tool Execution Gating
- Local Vulnerable Lab environments for safe testing

### Technology Stack
- Python 3.10+
- FastAPI
- SQLite
- Pydantic
- SQLAlchemy
- Vanilla HTML/JS Frontend

### Security Architecture
The platform enforces a hard boundary between the trusted orchestration components (ScopeValidator, SafeExecutor, AuthBank) and untrusted external inputs (Target HTTP Responses, LLM Output). The LLM is confined purely to an advisory role, stripped of any authority to execute payloads or independently validate findings.

### Demo
The repository ships with an automated local demonstration script (`.\scripts\demo\run_demo.ps1`). This workflow simulates the entire lifecycle—planning, human approval, execution, AI analysis, human validation, and reporting—exclusively against a bundled local mock lab (`127.0.0.1:9100`), ensuring zero external risk.

### Repository Topics
`ai-security`, `cybersecurity`, `security-research`, `llm-security`, `rag`, `fastapi`, `python`, `application-security`
