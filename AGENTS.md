# CodeProof — AGENTS.md

## What is CodeProof

CodeProof is a Windows desktop developer engineering environment that helps developers who use AI to build software but may not fully understand, debug, test, or maintain the software they create.

## Current Architecture

```
Flutter Desktop
    ↓
Workspace Guardian
    ↓
FastAPI Backend
    ↓
AI Engine
    ↓
Patch Lab
    ↓
Docker Sandbox
    ↓
Test Runner
    ↓
Release Readiness
```

## Team Roles

- **Project Lead**: AI + System Architect + Integration Lead (owns AI Engine, Workspace Guardian)
- **Friend 1**: Flutter Desktop Lead
- **Friend 2**: UI/Product Developer
- **Friend 3**: Backend + Sandbox Lead (owns Backend-side Guardian integration)

## Core Security Principle

> The original user project is never directly modified by CodeProof.

The AI can inspect and analyze project information, but all mutations happen only on temporary copies.

## AI Permissions

- READ: Project structure, source code, configuration files, dependencies
- READ: Git history (via Guardian-controlled access)
- WRITE: Temporary sandbox copies only
- NEVER: Direct filesystem writes to user's original project
- NEVER: Arbitrary command execution on host

## Sandbox Rules

1. All code execution happens in Docker containers
2. Containers are ephemeral and destroyed after each run
3. No network access unless explicitly granted
4. Resource limits enforced (CPU, memory, disk, time)
5. Snapshots are read-only views of the project

## Architecture Protection Rules

1. **NEVER silently change architecture**
2. Before making a cross-component architectural change, inspect dependencies and report:
   - CURRENT: Current state
   - REQUEST: Proposed change
   - WHY: Justification
   - AFFECTED COMPONENTS: List of impacted components
   - REQUIRED CHANGES: Specific changes needed
   - RISKS: Potential issues
   - RECOMMENDATION: Approve/reject with reasoning
3. Do not proceed with architectural change unless explicitly approved
4. Do not change API contracts owned by another team member

## Development Rules

1. **One task at a time** — Complete one task fully before starting another
2. **Cross-component impact reporting** — Any change affecting multiple components requires impact report
3. **Required implementation reports** — Each task must end with a report containing:
   - TASK: What was requested
   - IMPLEMENTED: What was built
   - FILES CREATED/CHANGED: List
   - ARCHITECTURE IMPACT: None or exact impact
   - API IMPACT: None or exact impact
   - DATA MODEL IMPACT: None or exact impact
   - SECURITY IMPACT: Explanation
   - TESTS: Tests run and results
   - KNOWN ISSUES: Anything unresolved
   - NEXT DEPENDENCY: What teammates need to know
4. **Do not continue into additional implementation** after task is complete

## Code Standards

- Use typed models (Pydantic/dataclasses)
- Provider abstraction pattern for external services
- Environment variables for secrets (never hardcode)
- Structured logging
- Comprehensive tests for security-critical components

## File Ownership

- `ai/` — Project Lead
- `workspace/` — Project Lead
- `backend/` — Friend 3 (Backend + Sandbox Lead)
- `desktop/` — Friend 1 (Flutter Desktop Lead)
- `sandbox/` — Friend 3
- `demo-project/` — Friend 2 (UI/Product Developer)