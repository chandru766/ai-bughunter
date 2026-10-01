# AI-BugHunter Release Notes

## Version v1.0.0 (Initial Portfolio Release)

This release finalizes the core AI-BugHunter orchestration platform, explicitly cementing the philosophy of "AI as an advisory assistant" and establishing rigid, human-in-the-loop security boundaries.

### Core Platform
- Built the foundation for program, target, and endpoint inventory tracking.
- Developed the core `TestPlan` scheduling mechanism allowing controlled test formulation before execution.

### Security Boundaries
- **Scope Enforcement**: Added `ScopeValidator` to enforce strict schema, domain, and path limitations for SSRF prevention.
- **Safety Levels**: Active payloads explicitly transition plans into `APPROVAL_REQUIRED`.
- **Kill Switch**: Global shutdown toggle that instantly drops `SafeExecutor` outbound requests.

### AI / RAG
- Integrated an intelligent Retrieval-Augmented Generation (RAG) backend utilizing a bundled knowledge base to analyze HTTP evidence.
- Defended the AI pipeline against untrusted target execution via strict XML-style delimiters (`<<<DATA>>>`).

### Authentication Bank
- Implemented `AuthBank` to encrypt sensitive API keys and JWTs using `Fernet` symmetric encryption.
- Enabled in-flight redaction, ensuring authorization tokens are stripped (`[REDACTED]`) before evidence is sent to the LLM.

### Human Validation
- Blocked AI from autonomously confirming vulnerabilities. All AI-flagged vulnerabilities strictly halt at `NEEDS_VALIDATION`.
- Built the human authorization workflow requiring explicit researcher validation.

### Reporting
- Integrated automated reporting logic returning clean, formatted Markdown reports composed solely of human-validated findings.

### Automated Demo
- Released a safe, `127.0.0.1`-bound Python script (`scripts/demo/run_demo.py`) wrapped in PowerShell that executes the entire end-to-end lifecycle.
- Included the Mock AI Lab for safe, local prompt-injection evaluations.

### Testing
- Fully refactored fixture architecture.
- **Test Result:** 43/43 PASS.
