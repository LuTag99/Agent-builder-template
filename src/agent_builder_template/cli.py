from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .generator import ProjectSpec, generate_workspace, slugify
from .workspace import (
    block_active_task,
    clarify_context,
    complete_active_task,
    continue_task,
    locate_workspace,
    plan_task,
    render_status,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agent-builder",
        description="Kick off an agent-operated delivery workspace from a short project brief.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    kickoff = subparsers.add_parser(
        "kickoff",
        help="Turn a short brief into an agent delivery workspace.",
    )
    _configure_kickoff_arguments(kickoff)

    create = subparsers.add_parser(
        "create",
        help="Backward-compatible alias for kickoff.",
    )
    _configure_kickoff_arguments(create)

    plan = subparsers.add_parser(
        "plan",
        help="Create a planned task in TASKS/BACKLOG.",
    )
    _configure_workspace_argument(plan)
    plan.add_argument("--title", help="Task title.")
    plan.add_argument("--request", help="Task request or desired change.")
    plan.add_argument("--why", default="", help="Why this task matters.")
    plan.add_argument("--constraints", default="", help="Task-specific constraints.")
    plan.add_argument("--priority", default="medium", help="Task priority.")
    plan.add_argument("--definition-of-done", default="", help="Definition of done.")
    plan.add_argument("--relevant-context", default="", help="Relevant files or context.")
    plan.add_argument("--risks", default="", help="Risks or cautions.")
    plan.add_argument("--notes", default="", help="Additional notes.")
    plan.add_argument("--activate", action="store_true", help="Create the task directly in TASKS/ACTIVE.")

    continue_cmd = subparsers.add_parser(
        "continue",
        help="Move the next task into TASKS/ACTIVE or show the current active task.",
    )
    _configure_workspace_argument(continue_cmd)
    continue_cmd.add_argument("--task", default=None, help="Specific task filename or partial match.")
    continue_cmd.add_argument(
        "--from",
        dest="source_stage",
        choices=["backlog", "blocked"],
        default="backlog",
        help="Source stage to continue from.",
    )

    block = subparsers.add_parser(
        "block",
        help="Move the current active task into TASKS/BLOCKED.",
    )
    _configure_workspace_argument(block)
    block.add_argument("--task", default=None, help="Specific active task to block.")
    block.add_argument("--reason", default="", help="Short blocking reason.")

    complete = subparsers.add_parser(
        "complete",
        help="Move the current active task into TASKS/DONE.",
    )
    _configure_workspace_argument(complete)
    complete.add_argument("--task", default=None, help="Specific active task to complete.")
    complete.add_argument("--note", default="", help="Short completion note for the next action.")

    status = subparsers.add_parser(
        "status",
        help="Show the current workspace state and task counts.",
    )
    _configure_workspace_argument(status)

    clarify = subparsers.add_parser(
        "clarify",
        help="Generate guided context gaps and questions for the current workspace.",
    )
    _configure_workspace_argument(clarify)

    return parser


def _configure_kickoff_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--project-name", help="Human-readable project name.")
    parser.add_argument("--idea", help="Short description of the core idea.")
    parser.add_argument(
        "--output",
        dest="desired_output",
        help="Describe the intended output or deliverable.",
    )
    parser.add_argument(
        "--destination",
        help="Target directory. Defaults to a slugified project name in the current directory.",
    )
    parser.add_argument(
        "--users",
        "--stakeholders",
        dest="stakeholders",
        default="",
        help="Primary users or stakeholders.",
    )
    parser.add_argument("--constraints", default="", help="Key constraints to respect.")
    parser.add_argument("--tech-stack", default="", help="Preferred stack or implementation direction.")
    parser.add_argument("--no-gos", default="", help="Things the project should explicitly avoid.")
    parser.add_argument(
        "--success-measures",
        default="",
        help="Concrete signals that would indicate project success.",
    )
    parser.add_argument("--status", default="kickoff_complete", help="Initial project status.")
    parser.add_argument("--priority", default="high", help="Initial task priority.")
    parser.add_argument("--quality-expectations", default="", help="Expected quality bar.")
    parser.add_argument("--notes", default="", help="Additional notes to include in the workspace.")
    parser.add_argument("--force", action="store_true", help="Allow writing into an existing non-empty destination.")


def _configure_workspace_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--workspace",
        default=".",
        help="Path to an existing generated workspace. Defaults to the current directory.",
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command in {"kickoff", "create"}:
        return _handle_create(args, parser)
    if args.command == "plan":
        return _handle_plan(args, parser)
    if args.command == "continue":
        return _handle_continue(args, parser)
    if args.command == "block":
        return _handle_block(args, parser)
    if args.command == "complete":
        return _handle_complete(args, parser)
    if args.command == "status":
        return _handle_status(args, parser)
    if args.command == "clarify":
        return _handle_clarify(args, parser)

    parser.error(f"Unsupported command: {args.command}")
    return 2


def _handle_create(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    project_name = _value_or_prompt(args.project_name, "Project name")
    idea = _value_or_prompt(args.idea, "Core idea")
    desired_output = _value_or_prompt(args.desired_output, "Intended output")

    destination = args.destination or slugify(project_name)
    spec = ProjectSpec(
        project_name=project_name,
        idea=idea,
        desired_output=desired_output,
        destination=Path(destination),
        stakeholders=args.stakeholders,
        constraints=args.constraints,
        tech_stack=args.tech_stack,
        no_gos=args.no_gos,
        current_status=args.status,
        priority=args.priority,
        quality_expectations=args.quality_expectations,
        success_measures=args.success_measures,
        notes=args.notes,
    )

    try:
        workspace_path = generate_workspace(spec, force=args.force)
    except FileExistsError as exc:
        parser.exit(status=2, message=f"{exc}\n")

    print(f"Created workspace: {workspace_path}")
    print("Next steps:")
    print("1. Review PROJECT/PROJECT_BRIEF.md and PROJECT/PROJECT_CONTEXT.md")
    print("2. Confirm PROJECT/ARCHITECTURE.md and PROJECT/DELIVERY_PLAN.md")
    print("3. Start with TASKS/BACKLOG/001-project-kickoff-and-foundation.md")
    return 0


def _handle_plan(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    workspace_root = _resolve_workspace(args.workspace, parser)
    title = _value_or_prompt(args.title, "Task title")
    request = _value_or_prompt(args.request, "Task request")

    try:
        task_path = plan_task(
            workspace_root,
            title=title,
            request=request,
            why=args.why,
            constraints=args.constraints,
            priority=args.priority,
            definition_of_done=args.definition_of_done,
            relevant_context=args.relevant_context,
            risks=args.risks,
            notes=args.notes,
            activate=args.activate,
        )
    except RuntimeError as exc:
        parser.exit(status=2, message=f"{exc}\n")

    print(f"Created task: {task_path.relative_to(workspace_root)}")
    if args.activate:
        print("Task is now active.")
    else:
        print("Task was added to the backlog.")
    return 0


def _handle_continue(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    workspace_root = _resolve_workspace(args.workspace, parser)

    try:
        task_path, moved = continue_task(
            workspace_root,
            task_ref=args.task,
            source_stage=args.source_stage,
        )
    except (RuntimeError, ValueError) as exc:
        parser.exit(status=2, message=f"{exc}\n")

    if moved:
        print(f"Moved to active: {task_path.relative_to(workspace_root)}")
    else:
        print(f"Active task unchanged: {task_path.relative_to(workspace_root)}")
    return 0


def _handle_block(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    workspace_root = _resolve_workspace(args.workspace, parser)

    try:
        task_path = block_active_task(
            workspace_root,
            task_ref=args.task,
            reason=args.reason,
        )
    except RuntimeError as exc:
        parser.exit(status=2, message=f"{exc}\n")

    print(f"Moved to blocked: {task_path.relative_to(workspace_root)}")
    return 0


def _handle_complete(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    workspace_root = _resolve_workspace(args.workspace, parser)

    try:
        task_path = complete_active_task(
            workspace_root,
            task_ref=args.task,
            note=args.note,
        )
    except RuntimeError as exc:
        parser.exit(status=2, message=f"{exc}\n")

    print(f"Moved to done: {task_path.relative_to(workspace_root)}")
    return 0


def _handle_status(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    workspace_root = _resolve_workspace(args.workspace, parser)
    print(render_status(workspace_root))
    return 0


def _handle_clarify(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    workspace_root = _resolve_workspace(args.workspace, parser)
    gap_path = clarify_context(workspace_root)
    print(f"Updated context gaps: {gap_path.relative_to(workspace_root)}")
    print("Review PROJECT/CONTEXT_GAPS.md and update the brief or context before the next major delivery step.")
    return 0


def _resolve_workspace(path: str, parser: argparse.ArgumentParser) -> Path:
    try:
        return locate_workspace(path)
    except FileNotFoundError as exc:
        parser.exit(status=2, message=f"{exc}\n")


def _value_or_prompt(value: str | None, label: str) -> str:
    if value:
        return value.strip()
    if not sys.stdin.isatty():
        raise SystemExit(f"Missing required value: {label}")
    prompt = f"{label}: "
    while True:
        entered = input(prompt).strip()
        if entered:
            return entered
        print(f"{label} is required.")
