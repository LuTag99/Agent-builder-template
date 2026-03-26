from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .generator import ProjectSpec, generate_workspace, slugify


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agent-builder",
        description="Generate an agent-ready project workspace from a short brief.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create", help="Create a project workspace.")
    create.add_argument("--project-name", help="Human-readable project name.")
    create.add_argument("--idea", help="Short description of the core idea.")
    create.add_argument(
        "--output",
        dest="desired_output",
        help="Describe the intended output or deliverable.",
    )
    create.add_argument(
        "--destination",
        help="Target directory. Defaults to a slugified project name in the current directory.",
    )
    create.add_argument("--stakeholders", default="", help="Primary users or stakeholders.")
    create.add_argument("--constraints", default="", help="Key constraints to respect.")
    create.add_argument("--tech-stack", default="", help="Preferred stack or implementation direction.")
    create.add_argument("--status", default="intake", help="Initial project status.")
    create.add_argument("--priority", default="high", help="Initial task priority.")
    create.add_argument("--quality-expectations", default="", help="Expected quality bar.")
    create.add_argument("--notes", default="", help="Additional notes to include in the workspace.")
    create.add_argument("--force", action="store_true", help="Allow writing into an existing non-empty destination.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "create":
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
        current_status=args.status,
        priority=args.priority,
        quality_expectations=args.quality_expectations,
        notes=args.notes,
    )

    try:
        workspace_path = generate_workspace(spec, force=args.force)
    except FileExistsError as exc:
        parser.exit(status=2, message=f"{exc}\n")

    print(f"Created workspace: {workspace_path}")
    print("Next steps:")
    print("1. Review PROJECT/PROJECT_CONTEXT.md")
    print("2. Start from TASKS/INITIAL_BUILD_TASK.md")
    print("3. Use AGENTS.md to choose a fast or full workflow")
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
