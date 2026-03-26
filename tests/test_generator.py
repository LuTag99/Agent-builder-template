from __future__ import annotations

from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest

from agent_builder_template.cli import main
from agent_builder_template.generator import ProjectSpec, generate_workspace


class GeneratorTests(unittest.TestCase):
    def test_generate_workspace_creates_filled_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            destination = Path(temp_dir) / "sample-workspace"
            spec = ProjectSpec(
                project_name="Sample Project",
                idea="Create a small tool that scaffolds agent-ready workspaces.",
                desired_output="A generated project workspace with brief, context, architecture, plan, tasks, and state files.",
                destination=destination,
                tech_stack="Python CLI",
                constraints="Keep the first version dependency-light.",
            )

            generate_workspace(spec)

            self.assertTrue((destination / "README.md").exists())
            self.assertTrue((destination / "PROJECT" / "PROJECT_BRIEF.md").exists())
            self.assertTrue((destination / "PROJECT" / "PROJECT_CONTEXT.md").exists())
            self.assertTrue((destination / "PROJECT" / "ARCHITECTURE.md").exists())
            self.assertTrue((destination / "PROJECT" / "DELIVERY_PLAN.md").exists())
            self.assertTrue((destination / "PROJECT" / "DECISIONS.md").exists())
            self.assertTrue((destination / "TASKS" / "BACKLOG" / "001-project-kickoff-and-foundation.md").exists())
            self.assertTrue((destination / "STATE" / "run_state.json").exists())
            self.assertTrue((destination / "STATE" / "NEXT_ACTION.md").exists())
            self.assertFalse((destination / "PROJECT" / "zz - PROJECT_BRIEF.md").exists())

            readme = (destination / "README.md").read_text(encoding="utf-8")
            self.assertIn("Sample Project", readme)
            self.assertIn("TASKS/BACKLOG/001-project-kickoff-and-foundation.md", readme)

            state = json.loads((destination / "STATE" / "run_state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["project_name"], "Sample Project")
            self.assertEqual(state["current_status"], "kickoff_complete")
            self.assertEqual(state["backlog_count"], 1)

    def test_cli_kickoff_creates_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            destination = Path(temp_dir) / "cli-workspace"
            exit_code = main(
                [
                    "kickoff",
                    "--project-name",
                    "CLI Project",
                    "--idea",
                    "Turn a short brief into an agent delivery workspace.",
                    "--output",
                    "A structured project OS for agent-assisted execution.",
                    "--destination",
                    str(destination),
                ]
            )

            self.assertEqual(exit_code, 0)
            self.assertTrue((destination / "PROJECT" / "PROJECT_BRIEF.md").exists())
            self.assertTrue((destination / "TASKS" / "BACKLOG" / "001-project-kickoff-and-foundation.md").exists())

    def test_task_flow_commands_move_tasks_between_stages(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            destination = Path(temp_dir) / "flow-workspace"
            exit_code = main(
                [
                    "kickoff",
                    "--project-name",
                    "Flow Project",
                    "--idea",
                    "Manage an agent delivery flow from brief to task execution.",
                    "--output",
                    "A workspace with controllable task stages.",
                    "--destination",
                    str(destination),
                ]
            )
            self.assertEqual(exit_code, 0)

            exit_code = main(
                [
                    "plan",
                    "--workspace",
                    str(destination),
                    "--title",
                    "Define execution slice",
                    "--request",
                    "Create the next implementable slice for the project.",
                    "--priority",
                    "high",
                ]
            )
            self.assertEqual(exit_code, 0)
            self.assertTrue((destination / "TASKS" / "BACKLOG" / "002-define-execution-slice.md").exists())

            exit_code = main(["continue", "--workspace", str(destination)])
            self.assertEqual(exit_code, 0)
            self.assertTrue((destination / "TASKS" / "ACTIVE" / "001-project-kickoff-and-foundation.md").exists())

            exit_code = main(
                [
                    "block",
                    "--workspace",
                    str(destination),
                    "--reason",
                    "Waiting for approval.",
                ]
            )
            self.assertEqual(exit_code, 0)
            self.assertTrue((destination / "TASKS" / "BLOCKED" / "001-project-kickoff-and-foundation.md").exists())

            exit_code = main(
                [
                    "continue",
                    "--workspace",
                    str(destination),
                    "--from",
                    "blocked",
                ]
            )
            self.assertEqual(exit_code, 0)
            self.assertTrue((destination / "TASKS" / "ACTIVE" / "001-project-kickoff-and-foundation.md").exists())

            exit_code = main(
                [
                    "complete",
                    "--workspace",
                    str(destination),
                    "--note",
                    "Ready for the next task.",
                ]
            )
            self.assertEqual(exit_code, 0)
            self.assertTrue((destination / "TASKS" / "DONE" / "001-project-kickoff-and-foundation.md").exists())

            state = json.loads((destination / "STATE" / "run_state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["completed_count"], 1)
            self.assertEqual(state["backlog_count"], 1)
            self.assertEqual(state["active_task"], None)

            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = main(["status", "--workspace", str(destination)])
            self.assertEqual(exit_code, 0)
            output = buffer.getvalue()
            self.assertIn("Project: Flow Project", output)
            self.assertIn("Tasks: backlog=1 active=0 blocked=0 done=1", output)

    def test_clarify_creates_context_gaps_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            destination = Path(temp_dir) / "clarify-workspace"
            exit_code = main(
                [
                    "kickoff",
                    "--project-name",
                    "Clarify Project",
                    "--idea",
                    "Create a workspace that can surface missing context.",
                    "--output",
                    "A project OS with guided context clarification.",
                    "--destination",
                    str(destination),
                ]
            )
            self.assertEqual(exit_code, 0)

            exit_code = main(["clarify", "--workspace", str(destination)])
            self.assertEqual(exit_code, 0)

            gap_file = destination / "PROJECT" / "CONTEXT_GAPS.md"
            self.assertTrue(gap_file.exists())
            content = gap_file.read_text(encoding="utf-8")
            self.assertIn("## Critical Gaps To Resolve", content)
            self.assertIn("Users and approvers are still unclear", content)

            state = json.loads((destination / "STATE" / "run_state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["current_status"], "context_clarification_needed")
            self.assertTrue(state["open_issues"])


if __name__ == "__main__":
    unittest.main()
