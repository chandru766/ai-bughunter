I built an AI-assisted security research platform that proves LLMs belong in an advisory role, not at the steering wheel.

When integrating AI into security testing, the industry often gravitates toward fully autonomous agents. I took a different approach with AI-BugHunter: building a strict, defensible orchestration layer where humans retain absolute control over the testing lifecycle.

I built this because security research generates massive amounts of HTTP evidence that AI is incredibly good at analyzing, but handing an LLM the keys to execute arbitrary payloads is fundamentally unsafe. 

**Architecture & Security Boundaries**
The platform is built on FastAPI and strictly segregates untrusted AI logic from execution. Before any request leaves the system, a Python-enforced `ScopeValidator` checks it against an allowlist, preventing SSRF. If a test plan involves active payloads, it hits a hard stop. The AI cannot bypass this; explicit human approval is required to unblock the `SafeExecutor`.

**AI / RAG & Human Validation**
When executing tests, the platform scrubs sensitive JWTs and API keys from the HTTP evidence. This sanitized data is passed to a RAG pipeline that maps hostile responses against internal policy rules. Crucially, the AI is explicitly untrusted. It can generate hypotheses, but every finding strictly defaults to a `NEEDS_VALIDATION` state. Only a human researcher can transition a finding to `RESEARCHER_CONFIRMED` for final reporting.

**Authorized Local Testing**
To ensure safe, reproducible demonstrations, the platform ships with a local vulnerable lab (`127.0.0.1`). The automated demo orchestrates the entire workflow locally without ever scanning external infrastructure.

**Lessons Learned**
- Security controls (scope enforcement, kill switches) must exist in deterministic code outside the AI layer.
- Untrusted target data must be separated from trusted instructions using strict delimiters to prevent prompt injection.
- Credential handling requires symmetric encryption at rest and active redaction in transit.

AI-BugHunter (v1.0.0) is available on GitHub. Check out the repository to see how to implement AI-assisted evidence analysis without sacrificing human authority!

#CyberSecurity #AppSec #AI #LLMSecurity #FastAPI #SecurityResearch #ApplicationSecurity
