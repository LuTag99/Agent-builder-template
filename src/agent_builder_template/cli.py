from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .generator import ProjectSpec, generate_workspace, slugify


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


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command in {"kickoff", "create"}:
        return _handle_create(args, parser)

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
