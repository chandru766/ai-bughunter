# Phase 22: Multi-Agent Security & Trust

## Overview
As AI-BugHunter evolves to support multiple collaborating agents (Coordinator, Web Security, API Security, Reporting, etc.), robust intra-agent security and trust boundaries must be strictly maintained. This framework ensures that multi-agent interactions do not bypass primary platform controls, preventing runaway cascading execution, privilege escalation, and unintended cross-program data leakage.

## Core Trust Principle
**Messages received from another agent are completely UNTRUSTED data.**
No agent may automatically execute an action, infer a capability, or trust a data package merely because it was sent by another internal AI agent.

## Architecture & Components

### 1. Agent Registry & Identity
Each agent possesses a rigid, backend-enforced identity composed of:
- `id`: Internal primary key.
- `program_id`: Absolute bounding context for data access.
- `agent_type`: Determines base functional boundaries (e.g. `COORDINATOR`, `WEB_SECURITY`).

### 2. Capabilities Model (`AgentCapability`)
Instead of blanket access, capabilities define specific allowed actions on specific resource types:
- Example: `WEB_ANALYSIS` on `ENDPOINT` allowing `ANALYZE`.
- The `AgentGateway` validates all capability requests. If the Coordinator delegates an analysis task, the recipient agent must explicitly possess the `WEB_ANALYSIS` capability; it cannot "inherit" it dynamically from the message payload.

### 3. Messaging & Evidence Handoff (`AgentMessage`)
All agent-to-agent communication passes through the `AgentGateway`:
- Every message defines a strict `MessageType` (e.g. `TASK_REQUEST`, `EVIDENCE_RESPONSE`). Arbitrary instruction types are rejected.
- **Evidence Integrity**: When one agent sends a payload to another (e.g., findings to a Reporting agent), the payload is hashed via SHA-256 (`payload_hash`). When the receiving agent retrieves it, the hash is verified to prevent transit tampering.
- **Message Replay Protection**: Each message receives a strict UUID `message_id`.

### 4. Delegation & Task Queue (`AgentTask`)
Tasks manage asynchronous workflows. The `AgentGateway` enforces limits on task delegation depth:
- `MAX_DELEGATION_DEPTH` prevents an infinite recursion loop (Agent A -> B -> A -> B).
- A task can only be assigned if the target agent holds the required backend capability.

## Security Boundaries Enforced

### Cross-Program Isolation
If Agent A (bound to Program 1) attempts to send a `TASK_REQUEST` or retrieve evidence for Agent B (bound to Program 2), the `AgentGateway` throws a hard `403 Forbidden: Cross-program communication is strictly blocked`. 

### Privilege Escalation Spoofing
The LLM could theoretically instruct another agent to elevate its access (e.g. `"Give me admin privileges"`). The Gateway implements Deep Packet Inspection on the message payload; if capability-escalation phrases are detected, it blocks the message and records `PRIVILEGE_ESCALATION_BLOCKED`.

### Transitive Privilege Exclusion
If Agent A has `HIGH_IMPACT` approval to run a test and delegates a sub-task to Agent B, Agent B **does not** acquire Agent A's approval. Agent B must secure its own explicit approval through the `ToolExecutionGate` (Phase 21).

### Credential & Secrets Isolation
Agent-to-agent payloads are explicitly audited. The same global result sanitization (from Phase 21) ensures that no JWT, AWS keys, or other credentials can traverse the multi-agent message bus.

## Local Multi-Agent Lab (127.0.0.1:9300)
A synthetic local fixture exists to test cross-agent workflows safely. It exposes mock endpoints (`/api/endpoints`, `/api/reports/draft`, `/api/evidence/verify`) representing internal micro-services the agents might interact with during collaboration, all without leaving the local environment.
