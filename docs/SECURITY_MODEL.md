# AI-BugHunter Security Model

## 1. Security Philosophy
The platform is an AI-assisted security research platform, not an autonomous hacking system. The fundamental principle is that AI is strictly advisory. Large Language Models (LLMs) are completely untrusted to make authorization, execution, or validation decisions. Humans remain in absolute control of the testing lifecycle.

## 2. Trust Boundaries
- **Trusted**: Human operators, `ScopeValidator`, `SafeExecutor`, `ToolExecutionGate`, Database, and local mock labs.
- **Untrusted**: Target application HTTP responses, external AI LLM providers, and AI-generated analysis or tool arguments.

## 3. Scope Enforcement
The `ScopeValidator` enforces a strict allowlist. Before any network request is sent by the `SafeExecutor`, the target URL is verified against registered `Program` domains and paths. It prevents Server-Side Request Forgery (SSRF) and ensures no out-of-scope executions can occur.

## 4. Safety Policy
Execution logic is governed by safety classifications (`TestLevel`). Invasive payloads or deep traversal scans require explicit escalation limits.

## 5. Human Approval
High-impact tests (`TestLevel.APPROVAL_REQUIRED`) completely halt the execution pipeline. An AI agent cannot authorize this state; explicit human intervention is required to unblock execution.

## 6. Kill Switch
A global `SystemConfig` flag. When triggered, all execution across the entire platform immediately halts and rejects further outbound requests.

## 7. Safe Execution
The `SafeExecutor` acts as the single outbound chokepoint. It resolves the authentication context, enforces the scope validation, checks human approval states, and prevents DNS rebinding before dispatching requests.

## 8. Authentication Context Isolation
Session tokens, API keys, and JWTs are tied strictly to a specific `Program`. Multi-tenant or cross-program credential bleeding is structurally blocked by foreign key constraints and runtime checks.

## 9. Credential Protection
Authentication secrets are encrypted at rest using `Fernet` symmetric encryption in the `AuthBank`. Crucially, before HTTP evidence is sent to the LLM, the `SafeExecutor` actively redacts these secrets to prevent accidental leakage in the AI context window.

## 10. Evidence Handling
HTTP requests and responses are captured precisely as they occurred. Evidence is stored immutably and mapped directly to generated findings, ensuring a clear chain of custody.

## 11. Prompt Injection Defense
Untrusted HTTP target data is scrubbed and wrapped in strict defensive delimiters (e.g., `<<<DATA>>>`). System prompts strongly instruct the AI to ignore embedded execution logic or commands within these bounds.

## 12. RAG Trust Boundary
Retrieval-Augmented Generation (RAG) context is treated as authoritative policy. When analyzing evidence, the AI is instructed to prioritize internal RAG rulebases over any contradictory patterns found in the untrusted HTTP evidence.

## 13. AI Output Validation
All AI responses are parsed through strict Pydantic schemas via the `AIPipeline`. If the model hallucinates fields, returns invalid JSON, or attempts to output code execution commands, the output is rejected.

## 14. Human Finding Validation
AI cannot definitively mark a finding as verified. Everything the AI discovers defaults to a `NEEDS_VALIDATION` state. The final security decision always remains with the human researcher. Findings cannot be reported until they achieve `RESEARCHER_CONFIRMED` status.

## 15. Tool Execution Security
The `ToolExecutionGate` intercepts AI tool calls (in the multi-agent pipeline). It validates `AgentCapability`, blocks recursive loops, and prevents agents from executing actions they are not explicitly authorized for.

## 16. Audit Logging
Every critical action—including Test Approvals, Test Executions, Finding Validations, and Report Generation—is logged immutably in the `AuditLog` with timestamp, actor, and result.

## 17. Cross-Program Isolation
The `AgentGateway` strictly checks `sender.program_id == receiver.program_id`. Multi-tenant data cannot bleed across context windows during multi-agent orchestration.

## 18. Local Testing Boundary
The platform includes local vulnerable mock environments (`127.0.0.1:9000-9300`). The automated demonstration scripts and unit tests are strictly confined to these local, sandboxed labs.

## 19. Known Limitations
- Not currently implemented: Full distributed execution nodes.
- Not currently implemented: Automatic verification of blind vulnerabilities (OOB).
- Autonomous exploitation is explicitly omitted by design.
