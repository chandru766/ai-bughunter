# OBSERVABILITY AND SECURITY OPERATIONS: AI-BugHunter

## Observability Architecture
AI-BugHunter utilizes structured JSON logging in conjunction with database-backed audit events and metrics. This ensures all actions are traceable while preventing secret exposure in observability streams.

## Log Format
Application logs are written in a structured JSON format to stdout.
```json
{
    "timestamp": "2026-09-30T17:31:00Z",
    "level": "INFO",
    "event": "HTTP_REQUEST",
    "message": "",
    "request_id": "uuid-here",
    "method": "POST",
    "route": "/testing/execute/12"
}
```

## Request IDs
A unique `X-Request-ID` is assigned to every incoming HTTP request. This correlation ID propagates throughout the execution lifecycle. It is attached to:
- Standard HTTP telemetry
- Testing telemetry
- Database AuditLogs
- AI telemetry
- Security event blocks

## Core Security Events
The following security event categories are explicitly tracked:
- `KILL_SWITCH_BLOCKED`: The system kill switch was active.
- `SCOPE_BLOCKED`: A target was out of scope.
- `APPROVAL_BLOCKED`: Required human approval was missing.
- `RATE_LIMIT_BLOCKED`: Safety rate limits were exceeded.
- `PROMPT_INJECTION_BLOCKED`: Suspicious AI instructions were detected and stripped.
- `AI_ANALYSIS_STARTED` / `COMPLETED` / `FAILED`: Lifecycle of the LLM pipeline.
- `FINDING_VALIDATED` / `REJECTED`: Audit trail of human decisions.

## Secret Redaction
- Observability output MUST NOT log full HTTP response bodies.
- `Authorization` headers are redacted in raw request payloads before being saved as Evidence.
- The `AUTH_BANK_ENCRYPTION_KEY` is completely isolated from the logging pipeline.

## System Health & Metrics
- `/health/live`: Checks if the FastAPI backend is running.
- `/health/ready`: Checks if the Database is reachable.
- `/system/status`: Reports status of Kill Switch, AI Provider, and RAG context.
- `/metrics`: Reports summary counts of executed tests, blocked tests, findings generated, and reports.

## Export & Retention
Audit Logs can be retrieved in bulk (paginated) via the API or exported via `/audit-logs/export?format=csv`.
By default, audit logs are retained indefinitely. Operational logs stored in stdout/files should be rotated by the deployment orchestrator (e.g., Docker or logrotate).

## Dashboard Integration
The Frontend Dashboard queries paginated API endpoints (`/testing/plans`, `/findings`, `/audit-logs`) to provide real-time visibility. Always review `OBSERVABILITY.md` prior to adding new log streams to ensure you don't inadvertently log secrets.
