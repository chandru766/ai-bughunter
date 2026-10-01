# Project Structure

This document outlines the core layout of the AI-BugHunter repository.

```text
C:.
+---backend                 # Core FastAPI Application
|   |   main.py             # Entrypoint and REST Routers
|   |   requirements.txt    # Production dependencies
|   |   local_ai_lab.py     # Local Mock Lab (Port 9100)
|   |
|   +---ai                  # LLM Orchestration
|   |   +---providers       # OpenAI / Anthropic / Mock Interfaces
|   |   advisor.py          # AI Research Advisor
|   |   analyzer.py         # Secondary Correlation
|   |   pipeline.py         # AI Pipeline & Prompt Injection Defense
|   |   security.py         # Semantic Validation Checks
|   |
|   +---analyzer            # Finding correlation logic
|   +---auth_bank           # Secrets management & Redaction
|   +---evidence            # Immutable HTTP Logging
|   +---models              # SQLAlchemy DB Schemas
|   +---observability       # Audit Logging
|   +---rag                 # Knowledge Retrieval Base
|   +---reports             # Markdown/JSON Generator
|   +---scope               # URL Boundary Allowlist (SSRF Defense)
|   \---testing             # SafeExecutor, Planners, SafetyPolicy
|
+---demo                    # Automated Demo Output & Logs
|   +---logs                # Immutable demo ledger
|   \---output              # Redacted execution artifacts
|
+---docs                    # Portfolio & Technical Documentation
|   +---architecture        # Structural diagrams
|   SECURITY_MODEL.md       # Trust boundaries 
|   CASE_STUDY.md           # Technical case study
|
+---frontend                # Vanilla HTML/JS Dashboard
|
+---scripts                 # CI/CD and Utilities
|   +---demo                # PowerShell/Python Demo Wrappers
|   +---release             # Audit & Release Pipeline
|
\---tests                   # PyTest Suite
    +---integration         # Multi-phase module integration
    \---unit                # Isolated phase-by-phase testing
```
