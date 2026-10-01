# AI-BugHunter — Technical Case Study

## 1. Problem
The modern security-research workflow involves generating and analyzing vast quantities of HTTP evidence, diagnostic data, and vulnerability symptoms. While AI models present a massive opportunity to accelerate evidence analysis (e.g., parsing headers, evaluating payload reflections), integrating LLMs into security testing introduces severe risks. AI systems can hallucinate vulnerabilities, violate testing scopes, or inadvertently expose sensitive credentials. The core problem this project addresses is how to harness AI-assisted analysis while maintaining strict, non-negotiable security boundaries where human researchers retain absolute control over validation and execution.

## 2. Project Goals
- **Controlled testing**: Orchestrate HTTP requests strictly through an authorized choke point.
- **Scope enforcement**: Reject any target not explicitly allowlisted.
- **Safe execution**: Sanitize inputs and isolate environments.
- **Human approval**: Pause high-impact execution logic until a human verifies intent.
- **Evidence collection**: Log raw, immutable HTTP payloads for downstream analysis.
- **AI-assisted analysis**: Leverage LLMs to evaluate collected evidence for vulnerabilities.
- **RAG context**: Use authoritative internal policy documents to override AI hallucinations.
- **Human validation**: Enforce that humans explicitly confirm findings before reporting.
- **Reporting**: Auto-generate clean, readable security reports for validated findings.
- **Auditability**: Track every execution, approval, and validation step immutably.

## 3. Architecture
The AI-BugHunter architecture is built around a FastAPI Python backend utilizing SQLite for persistence. It strictly segregates the untrusted AI layer and target data from the trusted execution and human-decision components.

```text
Researcher
↓
Frontend
↓
Backend
↓
Scope
↓
Safety
↓
Approval
↓
Execution
↓
Evidence
↓
AI/RAG
↓
Finding
↓
Human Validation
↓
Report
```

## 4. Security Boundaries

### ScopeValidator
The `ScopeValidator` intercepts all outbound requests. It ensures the URL strictly matches the registered schema and domain allowlist, effectively neutralizing SSRF risks and ensuring no external scanning occurs.

### SafetyPolicy
Payloads are categorized by a `TestLevel`. Active, invasive payloads automatically escalate the state of the test.

### Human Approval
Tests tagged as `HIGH_IMPACT` (or `APPROVAL_REQUIRED`) block the execution pipeline. The AI cannot authorize itself to proceed. Only a human researcher can unblock the test.

### SafeExecutor
The single outbound module responsible for resolving authentication, parsing the scope, and dispatching the HTTP request.

### Kill Switch
A global backend flag. When toggled, the `SafeExecutor` immediately halts, rejecting any pending or new outbound requests.

### ToolExecutionGate
In multi-agent workflows, this gate explicitly blocks transitive privilege escalation. If an AI agent attempts to use a tool it isn't strictly authorized for, it is rejected.

### Authentication Bank
Stores all JWTs and API keys in encrypted `Fernet` structures. Before HTTP evidence is handed to the LLM, the AuthBank actively redacts (e.g., `[REDACTED]`) any occurrence of the secrets, protecting them from leakage.

### Audit Logging
Records non-repudiable timestamps of who authorized a test, what the AI hypothesized, and who validated the finding.

## 5. AI / RAG Architecture

```text
HTTP evidence
↓
Sanitization
↓
Knowledge retrieval
↓
RAG context
↓
AI analysis
↓
Structured output
↓
Semantic validation
↓
NEEDS_VALIDATION
```

Target data is treated as hostile, untrusted input. The platform employs prompt-injection defenses by wrapping the raw HTTP responses in strict delimiters (`<<<DATA>>>`) and commanding the LLM to ignore embedded logic. The AI output is heavily validated using Pydantic schemas. Most importantly, the AI *cannot independently validate the finding*; it strictly defaults to `NEEDS_VALIDATION`.

## 6. Agent Security
The project's agent and tool security model revolves around strict capability boundaries. Tools are bound by `AgentCapability` tags. An agent orchestrating a web request cannot spontaneously invoke database deletion commands unless explicitly granted. Loop-detection and budget restrictions prevent infinite, uncontrolled agent interactions.

## 7. Authentication Security
The Authentication Bank is the trusted authority for session data. It stores contexts tied strictly to specific programs. Secrets are stored symmetrically encrypted. During execution, it securely attaches tokens to requests and applies redaction to the returned evidence to ensure isolation.

## 8. Local Vulnerable Lab
The project utilizes a built-in vulnerable mock lab running on `127.0.0.1:9000-9300`. This lab is used exclusively for portfolio demonstration and unit testing. Local testing proves the end-to-end orchestration works cleanly without scanning unauthorized external systems.

## 9. End-to-End Demonstration
The included automated demo script correctly simulates the entire lifecycle:
1. Start application
2. Local program
3. Test plan
4. Human approval
5. Safe execution
6. Evidence
7. AI analysis
8. NEEDS_VALIDATION
9. Researcher validation
10. Report

Artifacts are reliably captured and safely redacted in `demo/output/`.

## 10. Testing
The project uses `pytest` for unit and integration testing.
Current status: **37 passed, 6 known fixture infrastructure collisions.**
The 6 failures are documented test-fixture issues resulting from SQLite/FastAPI async session teardown conflicts, not failures in the core application logic.

## 11. Security Testing
The test suite successfully asserts the core security boundaries:
- External target blocking (Scope Enforcement).
- Kill switch functionality.
- Human approval requirements.
- Credential redaction in evidence payloads.
- Structured AI output validation.
- Tool execution restrictions (preventing transitive escalation).
- Cross-program isolation (multi-tenant boundary logic).

## 12. Lessons Learned
- **Security controls must exist outside the AI layer.** Relying on an LLM to enforce scope is dangerous; the Python backend must handle it.
- **AI output requires structured validation.** Unchecked markdown from an LLM breaks pipelines.
- **Untrusted target data must be separated from trusted instructions.** Defending against prompt injection is critical when parsing HTTP responses.
- **Human validation remains important for security findings.** AI hallucination rates require an authoritative human checkpoint.
- **Scope enforcement should happen before execution.** SSRF defenses must be ironclad at the `SafeExecutor` layer.
- **Credential handling requires encryption and redaction.**
- **Automated demos must remain reproducible and bounded.**

## 13. Known Limitations
- No autonomous exploitation capabilities exist.
- No unrestricted external scanning (strictly blocked).
- No automatic bug-bounty submission workflows.
- AI does not independently validate findings.
- **Demo test-plan fixture currently uses SQLite** because no general test-plan creation API exists in the final backend implementation.
- Six known test-fixture infrastructure collisions related to async teardown.

## 14. Future Improvements
- Improve test fixture isolation to eliminate the six fixture collisions.
- Provide a controlled, general test-plan creation API (to remove the SQLite demo hack).
- Improve demo automation (e.g., UI automation integration).
- Expand RAG retrieval with broader knowledge bases.
- Improve AI analysis providers (e.g., custom local models).
- Improve observability metrics.

## 15. Conclusion
AI-BugHunter is an AI-assisted security research platform that combines controlled testing, strict security boundaries, immutable evidence collection, AI/RAG analysis, and definitive researcher validation. It demonstrates how to safely harness LLMs for security analysis without compromising authorization controls.
