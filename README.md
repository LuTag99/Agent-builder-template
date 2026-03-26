# Agent Builder Template

`agent-builder-template` is a CLI for kicking off an agent-operated delivery workspace from a short project brief.

You provide:

- the project name
- the core idea
- the intended output
- optional users, constraints, preferred stack, and no-go areas

The tool creates the working system a senior delivery team would need:

- a filled `PROJECT_BRIEF.md`
- derived project context, architecture, and delivery plan
- an initial backlog task
- run state and next-action tracking
- agent role definitions
- system-level quality and approval guidance

## Why this exists

AI-assisted project work usually stalls before delivery quality becomes the problem. The first failure is simpler: the idea exists, but the operating system around the work does not. This tool closes that gap.

It turns a short brief into a structured workspace that supports planning, architecture, implementation, review, regression checking, reporting, and handoff.

## Install

```bash
pip install -e .
```

## Usage

Interactive:

```bash
agent-builder kickoff
```

Non-interactive:

```bash
agent-builder kickoff ^
  --project-name "Agentic Landing Page Builder" ^
  --idea "Create a reusable system that scaffolds project delivery from a short business brief." ^
  --output "A working project workspace and initial delivery system that agents can continue from." ^
  --users "Small product teams and solo founders" ^
  --tech-stack "Python CLI" ^
  --constraints "Keep the first version simple and dependency-light." ^
  --no-gos "Do not add provider-specific coupling in the core design."
```

PowerShell directly from the repo:

```powershell
$env:PYTHONPATH = "src"
python -m agent_builder_template kickoff
```

`create` remains available as a compatibility alias, but `kickoff` is the primary command.

## What gets generated

The generated workspace includes:

- `PROJECT/PROJECT_BRIEF.md`
- `PROJECT/PROJECT_CONTEXT.md`
- `PROJECT/ARCHITECTURE.md`
- `PROJECT/DELIVERY_PLAN.md`
- `PROJECT/DECISIONS.md`
- `TASKS/BACKLOG/001-project-kickoff-and-foundation.md`
- `STATE/run_state.json`
- `STATE/NEXT_ACTION.md`
- `AGENTS/` plus system guidance in `SYSTEM/`

## Delivery model

The generated workspace is built around this flow:

`Brief -> Clarify -> Plan -> Architect -> Build -> Critic -> Regression -> Report -> Next Action`

The user should mainly refine the brief and approve meaningful decisions. The agents should handle the structured delivery work.

## Current scope

This version focuses on kickoff and workspace generation. It does not yet execute external LLM provider calls automatically. It prepares the project so an agent workflow can start with clear structure, quality expectations, and delivery state.
