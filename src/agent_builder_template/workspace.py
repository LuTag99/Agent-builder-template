from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re

from .generator import slugify


TASK_STAGES = ("BACKLOG", "ACTIVE", "BLOCKED", "DONE")
PLACEHOLDER_PATTERNS = (
    "to be defined",
    "not specified",
    "open for decision",
    "to be decided",
    "unknown",
    "pending decision",
    "still need",
)


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
    open_issues = refreshed.get("open_issues") or []
    clarification_needed = any("critical context gaps" in issue.lower() for issue in open_issues)

    if active:
        refreshed["current_phase"] = "execution"
        refreshed["current_status"] = "in_progress"
    elif blocked:
        refreshed["current_phase"] = "blocked"
        refreshed["current_status"] = "blocked"
    elif clarification_needed:
        refreshed["current_phase"] = "planning"
        refreshed["current_status"] = "context_clarification_needed"
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

    open_issues = state.get("open_issues") or []
    if open_issues:
        lines.append(f"Open issues: {len(open_issues)}")

    pending_approvals = state.get("approval_gates_pending") or []
    if pending_approvals:
        lines.append(f"Approval gates pending: {len(pending_approvals)}")

    return "\n".join(lines)


def clarify_context(workspace_root: Path) -> Path:
    brief_text = (workspace_root / "PROJECT" / "PROJECT_BRIEF.md").read_text(encoding="utf-8")
    context_text = (workspace_root / "PROJECT" / "PROJECT_CONTEXT.md").read_text(encoding="utf-8")
    architecture_text = (workspace_root / "PROJECT" / "ARCHITECTURE.md").read_text(encoding="utf-8")

    brief_sections = _parse_sections(brief_text)
    context_sections = _parse_sections(context_text)
    architecture_sections = _parse_sections(architecture_text)

    known = [
        ("Project name", _first_meaningful_line(brief_sections.get("Project Name", ""))),
        ("Core idea", _first_meaningful_line(brief_sections.get("Core Idea", ""))),
        ("Intended output", _first_meaningful_line(brief_sections.get("Intended Output", ""))),
    ]

    critical_gaps: list[dict[str, str]] = []
    helpful_gaps: list[dict[str, str]] = []

    _collect_gap(
        critical_gaps,
        title="Users and approvers are still unclear",
        current_signal=_section_excerpt(
            brief_sections.get("Intended Users Or Stakeholders", "")
            + "\n"
            + context_sections.get("Intended Users Or Stakeholders", "")
        ),
        question="Who uses this first, who signs off on architecture or scope decisions, and who is affected by mistakes?",
        why="Without clear users and approvers, prioritization and approval gates stay weak.",
    )
    _collect_gap(
        critical_gaps,
        title="Constraints are not specific enough yet",
        current_signal=_section_excerpt(brief_sections.get("Constraints", "")),
        question="What constraints are real and non-negotiable across time, budget, policy, operations, or delivery?",
        why="Weak constraints lead to plans that look clean but are not actually executable.",
    )
    _collect_gap(
        critical_gaps,
        title="Success measures need to be sharper",
        current_signal=_section_excerpt(brief_sections.get("Success Measures", "")),
        question="What concrete signals would tell you the project is successful enough for the next checkpoint?",
        why="Without success measures, the team can ship activity instead of outcome.",
    )
    _collect_gap(
        critical_gaps,
        title="Stack direction is still open",
        current_signal=_section_excerpt(
            brief_sections.get("Preferred Stack Or Direction", "")
            + "\n"
            + context_sections.get("Tech Stack", "")
        ),
        question="Is there a preferred stack, language, framework, runtime, or hosting direction that should constrain early decisions?",
        why="The first implementation slice gets more expensive if the stack direction changes late.",
    )
    _collect_gap(
        helpful_gaps,
        title="Architecture boundaries are still generic",
        current_signal=_section_excerpt(
            architecture_sections.get("Open Decisions", "")
            + "\n"
            + context_sections.get("Architecture Notes", "")
        ),
        question="What are the first major components, boundaries, or integration points that matter for delivery?",
        why="Clear boundaries reduce rework and make task slicing cleaner.",
    )
    _collect_gap(
        helpful_gaps,
        title="Known risks can be made more concrete",
        current_signal=_section_excerpt(context_sections.get("Known Risks", "")),
        question="Which technical, delivery, or dependency risks are genuinely likely in the next slice of work?",
        why="Sharper risks improve planning and validation depth.",
    )
    _collect_gap(
        helpful_gaps,
        title="Out-of-scope boundaries may need sharpening",
        current_signal=_section_excerpt(context_sections.get("Out Of Scope", "")),
        question="What tempting work should be explicitly excluded from the first delivery window?",
        why="Strong out-of-scope boundaries protect focus.",
    )

    gap_path = workspace_root / "PROJECT" / "CONTEXT_GAPS.md"
    gap_path.write_text(
        _build_context_gaps_report(
            known=known,
            critical_gaps=critical_gaps,
            helpful_gaps=helpful_gaps,
        ),
        encoding="utf-8",
    )

    state = sync_state(workspace_root)
    state["last_run_id"] = _run_id("clarify")
    state["open_issues"] = (
        [f"{len(critical_gaps)} critical context gaps remain."] if critical_gaps else []
    )
    if critical_gaps and not state.get("active_task"):
        state["current_status"] = "context_clarification_needed"
        state["current_phase"] = "planning"
        _write_next_action(
            workspace_root,
            step="Review `PROJECT/CONTEXT_GAPS.md` and answer the highest-priority context questions before deep implementation work.",
            owner="User, supported by Intake and Planner.",
            why="The workspace now has a focused list of context gaps that should be reduced before the next major delivery step.",
        )
    elif not critical_gaps and not state.get("active_task"):
        _write_next_action(
            workspace_root,
            step="Context is sufficient for the next planning step. Move the next backlog task into active work when ready.",
            owner="Planner.",
            why="No critical context gaps were detected in the current brief and context files.",
        )

    write_state(workspace_root, state)
    return gap_path


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


def _parse_sections(text: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current: str | None = None

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if line.startswith("## "):
            current = line[3:].strip()
            sections[current] = []
            continue
        if current is not None:
            sections[current].append(line)

    return {heading: "\n".join(lines).strip() for heading, lines in sections.items()}


def _first_meaningful_line(text: str) -> str:
    for raw_line in text.splitlines():
        line = raw_line.strip().lstrip("-").strip()
        if line:
            return _shorten(line, 140)
    return "Not captured yet."


def _section_excerpt(text: str) -> str:
    cleaned = " ".join(line.strip() for line in text.splitlines() if line.strip())
    return _shorten(cleaned or "No current signal captured.", 200)


def _collect_gap(
    bucket: list[dict[str, str]],
    *,
    title: str,
    current_signal: str,
    question: str,
    why: str,
) -> None:
    if _contains_gap_signal(current_signal):
        bucket.append(
            {
                "title": title,
                "current_signal": current_signal,
                "question": question,
                "why": why,
            }
        )


def _contains_gap_signal(text: str) -> bool:
    normalized = text.lower()
    return not normalized.strip() or any(pattern in normalized for pattern in PLACEHOLDER_PATTERNS)


def _build_context_gaps_report(
    *,
    known: list[tuple[str, str]],
    critical_gaps: list[dict[str, str]],
    helpful_gaps: list[dict[str, str]],
) -> str:
    lines = [
        "# Context Gaps",
        "",
        "This file helps the agent fill context without inventing unnecessary detail. It highlights what already looks clear, what still blocks confident planning, and what can be clarified later.",
        "",
        "## What Already Looks Clear",
        "",
    ]

    for label, value in known:
        lines.append(f"- {label}: {value}")

    lines.extend(["", "## Critical Gaps To Resolve", ""])
    if critical_gaps:
        for gap in critical_gaps:
            lines.extend(
                [
                    f"### {gap['title']}",
                    "",
                    f"- Current signal: {gap['current_signal']}",
                    f"- Why it matters: {gap['why']}",
                    f"- Question to answer: {gap['question']}",
                    "",
                ]
            )
    else:
        lines.extend(["No critical context gaps were detected from the current brief and context files.", ""])

    lines.extend(["## Helpful Clarifications", ""])
    if helpful_gaps:
        for gap in helpful_gaps:
            lines.extend(
                [
                    f"### {gap['title']}",
                    "",
                    f"- Current signal: {gap['current_signal']}",
                    f"- Why it matters: {gap['why']}",
                    f"- Question to answer: {gap['question']}",
                    "",
                ]
            )
    else:
        lines.extend(["No additional clarification candidates were detected right now.", ""])

    lines.extend(
        [
            "## Safe Short-Term Rule",
            "",
            "Fill context to the level needed for the next delivery slice. Record facts, mark assumptions clearly, and escalate approval-sensitive decisions instead of guessing.",
            "",
            "## Recommended Next Step",
            "",
            "Answer the critical questions first, update `PROJECT/PROJECT_BRIEF.md` and `PROJECT/PROJECT_CONTEXT.md`, then run `agent-builder clarify` again if the context is still shifting.",
        ]
    )
    return "\n".join(lines) + "\n"


def _shorten(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."
