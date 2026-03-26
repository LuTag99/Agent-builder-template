from __future__ import annotations

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


if __name__ == "__main__":
    unittest.main()
