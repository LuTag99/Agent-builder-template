# Agent Delivery Workspace Template

This template is a lightweight operating system for agent-assisted software delivery. It is designed for a simple starting point: a user describes an idea, the intended result, and any important constraints, and the delivery system turns that brief into professional working structure.

The template separates:

- what the project is trying to do
- how agent roles should behave
- what quality bar the work should meet
- what tasks exist right now
- what happened in the latest run

## Core flow

`Brief -> Clarify -> Plan -> Architect -> Build -> Critic -> Regression -> Report -> Next Action`

## Start here

Review these files first:

- `PROJECT/zz - PROJECT_BRIEF.md`
- `SYSTEM/CONTEXT_CAPTURE_GUIDE.md`
- `SYSTEM/QUALITY_BAR.md`
- `SYSTEM/APPROVAL_GATES.md`
- `AGENTS.md`

Then move from backlog to active work only when the brief, architecture direction, and first delivery slice are clear enough.

## Keep it useful

- Keep the brief short and current.
- Keep plans proportional to the risk.
- Keep tasks small enough to review and test.
- Record decisions that materially affect delivery.
- Escalate approval-sensitive changes instead of hiding them in implementation.
