# CodeProof

A Windows desktop developer engineering environment that helps developers who use AI to build software but may not fully understand, debug, test, or maintain the software they create.

## Architecture

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

## Core Principle

> The original user project is never directly modified by CodeProof.

## Repository Structure

```
codeproof/
├── AGENTS.md              # Project rules and context
├── README.md
├── .gitignore
├── .env.example
├── docs/
│   ├── ARCHITECTURE_V1.1.md
│   └── adrs/
├── desktop/               # Flutter Desktop (Friend 1)
├── backend/               # FastAPI Backend (Friend 3)
├── ai/                    # AI Engine (Project Lead)
├── workspace/             # Workspace Guardian (Project Lead)
├── sandbox/               # Docker Sandbox (Friend 3)
├── demo-project/          # Student Event Management (Friend 2)
├── tests/
└── scripts/
```

## Getting Started

1. Copy `.env.example` to `.env` and fill in API keys
2. Install dependencies for each component
3. Run tests to verify setup

## Development

See `AGENTS.md` for development rules and team roles.