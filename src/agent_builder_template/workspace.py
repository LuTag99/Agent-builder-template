from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re

from .generator import slugify


TASK_STAGES = ("BACKLOG", "ACTIVE", "BLOCKED", "DONE")


def locate_workspace(path: str | Path | None = None) -> Path:
    start = Path(path).expanduser().resolve() if path else Path.cwd().resolve()
    if start.is_file():
        start = start.parent

    for current in (start, *start.parents):
        if (
            (current / "STATE" / "run_state.json").exists()
            and (current / "PROJECT" / "PROJECT_BRIEF.md").exists()
            and (current / "TASKS").exists()
        ):
            return current

    raise FileNotFoundError(
        "Could not find a workspace root. Run this command inside a generated workspace "
        "or pass --workspace."
    )


def read_state(workspace_root: Path) -> dict:
    return json.loads((workspace_root / "STATE" / "run_state.json").read_text(encoding="utf-8"))


def write_state(workspace_root: Path, state: dict) -> None:
    state["last_updated"] = _timestamp()
    (workspace_root / "STATE" / "run_state.json").write_text(
        json.dumps(state, indent=2) + "\n",
        encoding="utf-8",
    )


def list_tasks(workspace_root: Path, stage: str) -> list[Path]:
    stage_path = workspace_root / "TASKS" / stage.upper()
    if not stage_path.exists():
        return []
    return sorted(
        path
        for path in stage_path.iterdir()
        if path.is_file() and path.suffix == ".md" and not path.name.startswith("TEMPLATE -")
    )


def sync_state(workspace_root: Path) -> dict:
    state = read_state(workspace_root)
    refreshed = refresh_state(state, workspace_root)
    write_state(workspace_root, refreshed)
    return refreshed


def refresh_state(state: dict, workspace_root: Path) -> dict:
    refreshed = dict(state)
    backlog = list_tasks(workspace_root, "BACKLOG")
    active = list_tasks(workspace_root, "ACTIVE")
    blocked = list_tasks(workspace_root, "BLOCKED")
    done = list_tasks(workspace_root, "DONE")

    refreshed["backlog_count"] = len(backlog)
    refreshed["blocked_count"] = len(blocked)
    refreshed["completed_count"] = len(done)
    refreshed["active_task"] = active[0].name if active else None

    if active:
        refreshed["current_phase"] = "execution"
        refreshed["current_status"] = "in_progress"
    elif blocked:
        refreshed["current_phase"] = "blocked"
        refreshed["current_status"] = "blocked"
    elif backlog:
        refreshed["current_phase"] = "planning"
        refreshed["current_status"] = "ready_for_next_task"
    else:
        refreshed["current_phase"] = "planning"
        refreshed["current_status"] = "awaiting_planning"

    return refreshed


def plan_task(
    workspace_root: Path,
    *,
    title: str,
    request: str,
    why: str = "",
    constraints: str = "",
    priority: str = "medium",
    definition_of_done: str = "",
    relevant_context: str = "",
    risks: str = "",
    notes: str = "",
    activate: bool = False,
) -> Path:
    state = sync_state(workspace_root)
    active_tasks = list_tasks(workspace_root, "ACTIVE")
    if activate and active_tasks:
        raise RuntimeError(
            f"There is already an active task: {active_tasks[0].name}. Complete or block it before activating another task."
        )

    filename = f"{_next_task_number(workspace_root):03d}-{slugify(title)[:64]}.md"
    stage = "ACTIVE" if activate else "BACKLOG"
    path = workspace_root / "TASKS" / stage / filename
    path.write_text(
        _build_task_content(
            title=title,
            request=request,
            why=why,
            constraints=constraints,
            priority=priority,
            definition_of_done=definition_of_done,
            relevant_context=relevant_context,
            risks=risks,
            notes=notes,
        ),
        encoding="utf-8",
    )

    state["last_run_id"] = _run_id("plan")
    if activate:
        state["current_phase"] = "execution"
        state["current_status"] = "in_progress"
        state["active_task"] = filename
        _write_next_action(
            workspace_root,
            step=f"Execute `{filename}` in `TASKS/ACTIVE`.",
            owner="Builder, with Planner support as needed.",
            why="A new task was created and activated immediately.",
        )
    else:
        _write_next_action(
            workspace_root,
            step=f"Review `{filename}` in `TASKS/BACKLOG` and decide when it should move into active work.",
            owner="Planner.",
            why="A new planned task has been added to the backlog.",
        )

    refreshed = refresh_state(state, workspace_root)
    write_state(workspace_root, refreshed)
    return path


def continue_task(
    workspace_root: Path,
    *,
    task_ref: str | None = None,
    source_stage: str = "BACKLOG",
) -> tuple[Path, bool]:
    state = sync_state(workspace_root)
    active = list_tasks(workspace_root, "ACTIVE")
    if active:
        return active[0], False

    source = source_stage.upper()
    if source not in {"BACKLOG", "BLOCKED"}:
        raise ValueError(f"Unsupported source stage: {source_stage}")

    task = _select_task(workspace_root, source, task_ref)
    moved = _move_task(task, workspace_root / "TASKS" / "ACTIVE" / task.name)

    state["last_run_id"] = _run_id("continue")
    state["current_phase"] = "execution"
    state["current_status"] = "in_progress"
    state["active_task"] = moved.name
    _write_next_action(
        workspace_root,
        step=f"Work on `{moved.name}` in `TASKS/ACTIVE`.",
        owner="Builder.",
        why="This is the next task in active execution.",
    )

    refreshed = refresh_state(state, workspace_root)
    write_state(workspace_root, refreshed)
    return moved, True


def block_active_task(
    workspace_root: Path,
    *,
    task_ref: str | None = None,
    reason: str = "",
) -> Path:
    state = sync_state(workspace_root)
    task = _get_active_task(workspace_root, task_ref)
    moved = _move_task(task, workspace_root / "TASKS" / "BLOCKED" / task.name)

    state["last_run_id"] = _run_id("block")
    state["current_phase"] = "blocked"
    state["current_status"] = "blocked"
    state["active_task"] = None
    reason_text = reason or "No blocking reason was recorded."
    _write_next_action(
        workspace_root,
        step=f"Resolve the blocker on `{moved.name}` before returning it to active work.",
        owner="Planner and user approval where needed.",
        why=reason_text,
    )

    refreshed = refresh_state(state, workspace_root)
    write_state(workspace_root, refreshed)
    return moved


def complete_active_task(
    workspace_root: Path,
    *,
    task_ref: str | None = None,
    note: str = "",
) -> Path:
    state = sync_state(workspace_root)
    task = _get_active_task(workspace_root, task_ref)
    moved = _move_task(task, workspace_root / "TASKS" / "DONE" / task.name)

    state["last_run_id"] = _run_id("complete")
    state["active_task"] = None
    refreshed = refresh_state(state, workspace_root)

    backlog = list_tasks(workspace_root, "BACKLOG")
    if backlog:
        _write_next_action(
            workspace_root,
            step=f"Move `{backlog[0].name}` from `TASKS/BACKLOG` into active work when ready.",
            owner="Planner.",
            why=note or "The previous active task was completed and the backlog is ready for the next slice.",
        )
    else:
        _write_next_action(
            workspace_root,
            step="Create or plan the next delivery slice.",
            owner="Planner.",
            why=note or "The previous active task was completed and there are no remaining backlog tasks.",
        )

    write_state(workspace_root, refreshed)
    return moved


def render_status(workspace_root: Path) -> str:
    state = sync_state(workspace_root)
    backlog = list_tasks(workspace_root, "BACKLOG")
    active = list_tasks(workspace_root, "ACTIVE")
    blocked = list_tasks(workspace_root, "BLOCKED")

    lines = [
        f"Workspace: {workspace_root}",
        f"Project: {state.get('project_name', 'Unknown')}",
        f"Status: {state.get('current_status', 'unknown')}",
        f"Phase: {state.get('current_phase', 'unknown')}",
        f"Active task: {state.get('active_task') or 'none'}",
        (
            "Tasks: "
            f"backlog={state.get('backlog_count', 0)} "
            f"active={len(active)} "
            f"blocked={state.get('blocked_count', 0)} "
            f"done={state.get('completed_count', 0)}"
        ),
    ]

    if backlog:
        lines.append(f"Next backlog task: {backlog[0].name}")
    if blocked:
        lines.append(f"Blocked task: {blocked[0].name}")

    next_action = _read_next_action(workspace_root)
    if next_action:
        lines.append(f"Next action: {next_action}")

    pending_approvals = state.get("approval_gates_pending") or []
    if pending_approvals:
        lines.append(f"Approval gates pending: {len(pending_approvals)}")

    return "\n".join(lines)


def _get_active_task(workspace_root: Path, task_ref: str | None) -> Path:
    active = list_tasks(workspace_root, "ACTIVE")
    if not active:
        raise RuntimeError("There is no active task to move.")
    if task_ref is None:
        return active[0]
    return _match_task(active, task_ref)


def _select_task(workspace_root: Path, stage: str, task_ref: str | None) -> Path:
    tasks = list_tasks(workspace_root, stage)
    if not tasks:
        raise RuntimeError(f"There are no tasks in TASKS/{stage}.")
    if task_ref is None:
        return tasks[0]
    return _match_task(tasks, task_ref)


def _match_task(tasks: list[Path], task_ref: str) -> Path:
    ref = task_ref.strip().lower()
    matches = [
        task
        for task in tasks
        if ref == task.name.lower() or ref == task.stem.lower() or ref in task.name.lower()
    ]
    if not matches:
        raise RuntimeError(f"Could not find a task matching '{task_ref}'.")
    if len(matches) > 1:
        names = ", ".join(task.name for task in matches)
        raise RuntimeError(f"Task reference '{task_ref}' is ambiguous: {names}")
    return matches[0]


def _move_task(source: Path, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    source.replace(destination)
    return destination


def _next_task_number(workspace_root: Path) -> int:
    highest = 0
    for stage in TASK_STAGES:
        for task in list_tasks(workspace_root, stage):
            match = re.match(r"^(\d+)-", task.name)
            if match:
                highest = max(highest, int(match.group(1)))
    return highest + 1


def _build_task_content(
    *,
    title: str,
    request: str,
    why: str,
    constraints: str,
    priority: str,
    definition_of_done: str,
    relevant_context: str,
    risks: str,
    notes: str,
) -> str:
    return f"""# {title}

## Request

{request}

## Why This Matters

{why or "Clarify why this task matters before execution begins."}

## Constraints

{constraints or "No additional constraints were captured for this task."}

## Priority

{priority}

## Definition Of Done

{definition_of_done or "Define the observable conditions that make this task complete."}

## Relevant Files Or Context

{relevant_context or "Add the most relevant files, decisions, or context here."}

## Risks Or Cautions

{risks or "Record likely side effects, blockers, or approval-sensitive areas here."}

## Notes

{notes or "No additional notes."}
"""


def _write_next_action(workspace_root: Path, *, step: str, owner: str, why: str) -> None:
    content = f"""# Next Action

## Recommended Next Step

{step}

## Owner

{owner}

## Why This Is Next

{why}
"""
    (workspace_root / "STATE" / "NEXT_ACTION.md").write_text(content, encoding="utf-8")


def _read_next_action(workspace_root: Path) -> str:
    path = workspace_root / "STATE" / "NEXT_ACTION.md"
    if not path.exists():
        return ""

    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
    filtered = [line for line in lines if line and not line.startswith("#")]
    return filtered[0] if filtered else ""


def _run_id(prefix: str) -> str:
    return f"{prefix}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"


def _timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
