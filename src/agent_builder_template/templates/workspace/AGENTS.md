# Agent System Overview

This template provides a simple, reusable operating model for development work supported by specialized agent roles. It is designed to help teams and individuals move from a request to a clear result with less confusion, better traceability, and more consistent handoffs.

The system is intentionally generic. The role files in `AGENTS/` describe how each agent should behave in broad terms. Project-specific rules, constraints, and technical context belong in `PROJECT/zz - PROJECT_CONTEXT.md`.

## Purpose

Use this template to organize work around a few practical questions:

- What is the task?
- What is the safest useful plan?
- What changed?
- What might have broken?
- What should happen next?

This structure supports development work. It does not replace judgment, local expertise, or direct communication when a situation is unclear.

## Agent Roles

Each role has a distinct purpose:

- `Planner` turns a request into a right-sized plan with clear success criteria.
- `Builder` makes the change with minimal, understandable implementation work.
- `Critic` reviews the reasoning, assumptions, and likely side effects.
- `Regression` checks whether the change introduced breakage elsewhere.
- `Report` summarizes the outcome in a concise, decision-useful format.
- `Artifact Steward` keeps runs, reports, and state organized across iterations.

Not every task needs every role. The system is meant to scale up or down based on task size and risk.

## How The Roles Work Together

The common pattern is straightforward:

- A request is captured in a task brief.
- The Planner decides what needs to happen and what success looks like.
- The Builder performs the work.
- The Critic challenges weak reasoning and likely blind spots.
- The Regression role checks for relevant breakage.
- The Report role records what happened and what remains open.
- The Artifact Steward keeps the supporting files and outputs orderly over time.

The value of this sequence is clarity. Each role has a narrow job, which makes it easier to spot missing thinking, incomplete implementation, or gaps in validation.

## Generic Behavior Vs Project Context

Keep the separation clean:

- `AGENTS/*.md` should define reusable behavior that can apply to many projects.
- `PROJECT/zz - PROJECT_CONTEXT.md` should contain project-specific facts such as goals, constraints, architecture, and quality expectations.

If a rule is likely to change from one project to another, it belongs in project context, not in the generic agent definitions.

## Operating Model

Choose the lightest path that fits the task.

### Fast Path

Use this for small, low-risk changes with clear scope.

Flow:

`Builder -> quick validation -> Report`

Example uses:

- minor bug fixes
- small content or configuration updates
- low-risk cleanup with obvious impact

### Full Path

Use this for medium or larger tasks, unclear work, or changes with broader impact.

Flow:

`Planner -> Builder -> Critic -> Regression -> Report`

Example uses:

- feature work
- refactoring
- multi-file bug fixes
- changes that affect shared behavior or interfaces

The `Artifact Steward` can support either path by keeping outputs and state consistent across runs.

## Practical Guidance

- Start with the smallest process that still protects quality.
- Escalate to the full path when uncertainty, impact, or risk increases.
- Keep role files generic and stable.
- Put project-specific guidance in project context.
- Keep reports short and useful.

The template is successful when it helps people work faster with clearer reasoning, not when it creates extra ceremony.
