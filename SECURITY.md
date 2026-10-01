# SECURITY POLICY: AI-BugHunter

## Authorized Use Only
AI-BugHunter is an authorized security research platform. It is strictly designed to operate against targets you explicitly own or have explicit authorization to test (e.g., bug bounty programs in scope).

## Core Security Boundaries
- **Scope Enforcement**: No HTTP request related to security testing is permitted to leave the backend unless the target matches an explicitly defined scope rule.
- **Kill Switch**: A fail-safe toggle that blocks all execution across the platform when ACTIVE.
- **Human Approval**: The system will NOT execute any active testing plans unless explicitly approved by a human operator.
- **Authentication Handling**: The Auth Bank encrypts all credentials at rest. API responses strictly return `[REDACTED]`. Decryption only occurs at the moment of HTTP request dispatch.

## AI Limitations & Hard Security Boundary
The AI integration is purely advisory.
- The AI **cannot** execute HTTP requests.
- The AI **cannot** automatically mark a vulnerability as `VALIDATED`. All findings default to `NEEDS_VALIDATION`.
- The AI **cannot** bypass the Kill Switch or Scope Validator.
- Untrusted data (HTTP responses, RAG contexts) are explicitly wrapped in prompt-injection defense boundaries before being fed to the LLM.

## Report Workflow
Security reports cannot be generated for findings with a status of `NEEDS_VALIDATION` or `FALSE_POSITIVE`. The system strictly redacts secrets before report generation.

## Vulnerability Disclosure
This platform is intended to help researchers find and report vulnerabilities responsibly. Do not use this tool for unauthorized access, denial of service, or destructive testing.
