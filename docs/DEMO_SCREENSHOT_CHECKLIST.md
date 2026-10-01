# Demo Screenshot Checklist

For a professional 2-3 minute portfolio demonstration, we need exactly 9 screenshots. Use this checklist to ensure all security concepts are visually represented correctly.

## 01-dashboard.png
- **What to capture**: The main dashboard (`/frontend/index.html`) showing overall stats (programs, findings, status).
- **What must be visible**: The overarching security view, indicating the platform is for controlled research.
- **Security concept**: Orchestration layer overview.
- **Privacy requirement**: Ensure no sensitive production metrics (if any) are displayed. Use dummy metrics.

## 02-program.png
- **What to capture**: The Program scope view.
- **What must be visible**: The target URL (`127.0.0.1` or `localhost`).
- **Security concept**: Scope Enforcement. Demonstrates the strict allowlist that prevents SSRF.
- **Privacy requirement**: No external client hostnames should be visible.

## 03-test-plan.png
- **What to capture**: The Test Plan creation or detail view showing a `HIGH_IMPACT` (Prompt Injection) payload.
- **What must be visible**: The payload, the target (`http://127.0.0.1:9100/api/chat`), and the `PLANNED` status.
- **Security concept**: Controlled execution planning. 
- **Privacy requirement**: No actual customer PII or real credentials in the test payload.

## 04-human-approval.png
- **What to capture**: The execution blocked state showing `APPROVAL_REQUIRED` or transitioning to `APPROVED`.
- **What must be visible**: The human interaction point (an "Approve" button or status badge).
- **Security concept**: Human Approval. AI cannot bypass this state.
- **Privacy requirement**: None.

## 05-execution.png
- **What to capture**: The SafeExecutor evidence log or terminal output showing the HTTP request/response.
- **What must be visible**: The exact HTTP payload sent and received.
- **Security concept**: Safe Execution & Evidence Handling.
- **Privacy requirement**: MUST show `[REDACTED]` for any `Authorization: Bearer` or API keys.

## 06-ai-analysis.png
- **What to capture**: The AI hypothesis JSON or formatted output.
- **What must be visible**: The RAG context matching (e.g., Citations like `[K1]`), confidence level, and structured schema.
- **Security concept**: AI Output Validation & Prompt Injection Defense.
- **Privacy requirement**: Ensure no raw sensitive HTTP evidence leaked into the plain-text analysis inadvertently without redaction.

## 07-needs-validation.png
- **What to capture**: The finding listed in the dashboard with a yellow/warning `NEEDS_VALIDATION` badge.
- **What must be visible**: The status badge explicitly proving the AI cannot confirm its own findings.
- **Security concept**: Human Decision Points.
- **Privacy requirement**: None.

## 08-researcher-validation.png
- **What to capture**: The interaction where a human researcher marks the finding as `RESEARCHER_CONFIRMED`.
- **What must be visible**: The confirmation reason ("Validated locally").
- **Security concept**: Human Finding Validation.
- **Privacy requirement**: None.

## 09-final-report.png
- **What to capture**: The generated Markdown or JSON report (`demo/output/ai-bughunter-demo-report.md`).
- **What must be visible**: The cleanly formatted security report ready for stakeholder review.
- **Security concept**: Automated Reporting of *only* human-validated findings.
- **Privacy requirement**: No actual credentials; use mocked data.
