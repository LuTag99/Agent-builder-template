# DevAgent Template

This template is a lightweight starting structure for AI-assisted development work. It gives a project a clear place to store stable context, define reusable agent roles, track run state, capture task briefs, and record outcomes without adding heavy process.

Its purpose is simple: reduce ambiguity. Instead of starting each new project from a blank folder or scattered notes, you get a small operating system for development work with a consistent flow:

`Request -> Plan -> Build -> Check -> Report`

Use this folder by copying it into a new project, then adjusting the few files that hold project-specific information. The agent role files are meant to stay mostly generic so they can be reused across many kinds of software work.

## Start here

Customize these files first:

- `PROJECT/zz - PROJECT_CONTEXT.md` for stable project facts, constraints, and quality expectations
- `TASKS/zz - TASK_BRIEF_TEMPLATE.md` to create the first real task brief for the work at hand
- `STATE/zz - run_state.json` to record the current working state of the project

After that, review `AGENTS.md` and the files in `AGENTS/` so the team understands how the workflow is intended to operate.

## Basic use

For a new task:

1. Capture the task briefly and clearly.
2. Decide whether the task needs a quick pass or a fuller workflow.
3. Plan only to the level the task needs.
4. Make the smallest sound change that solves the problem.
5. Check for obvious risks or regressions.
6. Write a short report that helps the next person continue.

Small tasks can move quickly. Larger or riskier tasks should use more of the system.

## Keep it lightweight

This template works best when it stays practical:

- Record stable facts once instead of repeating them in every task.
- Use short task briefs instead of long requirement documents.
- Prefer targeted checks over ceremonial process.
- Expand the workflow only when the task justifies it.

If a file stops helping decisions or execution, simplify it. The goal is better work and clearer handoffs, not bureaucracy.
