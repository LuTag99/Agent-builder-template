# Agent Builder Template

`agent-builder-template` is a small CLI that turns a short project brief into an agent-ready project workspace.

You describe:

- the project name
- the core idea
- the intended output
- optional constraints, stakeholders, and stack preferences

The tool then creates a working folder with:

- a filled `PROJECT_CONTEXT.md`
- an initial build task brief
- a starter `run_state.json`
- generic agent role definitions for planning, building, review, regression checks, reporting, and artifact handling

## Why this exists

Starting an AI-assisted project usually breaks down in the same place: the idea is clear in your head, but the working structure around it is missing. This tool gives you a clean starting point without forcing a heavy process.

The result is not a finished application. It is a prepared project workspace that agents can use to plan, build, check, and report work in a consistent way.

## Install

```bash
pip install -e .
```

## Usage

Interactive:

```bash
agent-builder create
```

Non-interactive:

```bash
agent-builder create ^
  --project-name "Agentic Landing Page Builder" ^
  --idea "Create a reusable system that scaffolds landing page projects from a short brief." ^
  --output "A project workspace with context, tasks, state tracking, and agent role definitions." ^
  --tech-stack "Python CLI" ^
  --constraints "Keep the first version simple and dependency-light."
```

PowerShell with the module directly from the repo:

```powershell
$env:PYTHONPATH = "src"
python -m agent_builder_template create
```

## What gets generated

The generated workspace includes:

- `README.md` with project-specific orientation
- `AGENTS.md` and `AGENTS/` with generic role behavior
- `PROJECT/PROJECT_CONTEXT.md`
- `TASKS/INITIAL_BUILD_TASK.md`
- `STATE/run_state.json`
- `RUNS/` and `REPORTS/` for working outputs

## Typical flow

1. Run `agent-builder create`.
2. Review the generated project context.
3. Start from `TASKS/INITIAL_BUILD_TASK.md`.
4. Let your agents work through `Plan -> Build -> Check -> Report`.
5. Keep `STATE/run_state.json` current as the project evolves.

## Scope of version 1

This first version focuses on project intake and workspace generation. It does not call an LLM provider directly or run agent steps automatically. It prepares the workspace so an agent-based workflow can start cleanly.
