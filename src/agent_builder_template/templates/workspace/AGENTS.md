# Agent System Overview

This workspace is designed to behave like a disciplined delivery team. The user provides direction through the project brief. The agents turn that direction into a plan, architecture, implementation slices, checks, and reports.

The role files in `AGENTS/` should stay generic. Project-specific facts belong in `PROJECT/`. Delivery standards and approval rules belong in `SYSTEM/`.

## Purpose

Use this system when the goal is not just to store notes, but to run work with structure:

- clarify the brief
- define the delivery path
- make implementation decisions explicit
- control risk and scope
- keep the next action obvious

This system supports judgment. It does not replace it.

## Agent Roles

- `Intake` converts a rough idea into a usable delivery brief.
- `Planner` turns the brief into right-sized tasks and success criteria.
- `Architect` defines the initial solution shape and identifies approval-sensitive decisions.
- `Builder` executes the agreed slice with minimal, reviewable changes.
- `Critic` tests the quality of the reasoning and flags overreach, weak assumptions, or side effects.
- `Regression` checks relevant surrounding behavior after changes.
- `Report` summarizes outcome, risk, and next steps.
- `Artifact Steward` keeps tasks, runs, reports, and state consistent across iterations.

## How The Roles Work Together

Common sequence:

`Intake -> Planner -> Architect -> Builder -> Critic -> Regression -> Report -> Artifact Steward`

Not every task needs every role at full depth. Small, isolated changes may compress the flow. Higher-risk work should use the full sequence.

## Project Context Vs Generic Behavior

Keep the split clean:

- `AGENTS/*.md` defines reusable role behavior.
- `PROJECT/PROJECT_BRIEF.md` captures the project in user terms.
- `PROJECT/PROJECT_CONTEXT.md`, `PROJECT/ARCHITECTURE.md`, `PROJECT/DELIVERY_PLAN.md`, and `PROJECT/DECISIONS.md` capture project-specific working context.
- `SYSTEM/*.md` defines the quality bar and approval logic for the operating model.

If something changes from project to project, it should not be baked into the generic role files.

## Operating Paths

### Fast Path

Use this for small, low-risk changes with stable context.

`Builder -> focused validation -> Report -> Artifact Steward`

### Full Path

Use this for new projects, medium or larger tasks, architecture work, or anything with unclear requirements.

`Intake -> Planner -> Architect -> Builder -> Critic -> Regression -> Report -> Artifact Steward`

## Practical Guidance

- Start from the brief, not from implementation guesses.
- Keep tasks small enough to review and validate.
- Escalate approval-sensitive changes instead of burying them in delivery work.
- Keep state and next action current after each meaningful run.
- Use the smallest process that still protects quality.
