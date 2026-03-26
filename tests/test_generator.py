from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from agent_builder_template.generator import ProjectSpec, generate_workspace


class GeneratorTests(unittest.TestCase):
    def test_generate_workspace_creates_filled_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            destination = Path(temp_dir) / "sample-workspace"
            spec = ProjectSpec(
                project_name="Sample Project",
                idea="Create a small tool that scaffolds agent-ready workspaces.",
                desired_output="A generated project workspace with context, task, and state files.",
                destination=destination,
                tech_stack="Python CLI",
                constraints="Keep the first version dependency-light.",
            )

            generate_workspace(spec)

            self.assertTrue((destination / "README.md").exists())
            self.assertTrue((destination / "PROJECT" / "PROJECT_CONTEXT.md").exists())
            self.assertTrue((destination / "TASKS" / "INITIAL_BUILD_TASK.md").exists())
            self.assertTrue((destination / "STATE" / "run_state.json").exists())
            self.assertFalse((destination / "PROJECT" / "zz - PROJECT_CONTEXT.md").exists())

            readme = (destination / "README.md").read_text(encoding="utf-8")
            self.assertIn("Sample Project", readme)

            state = json.loads((destination / "STATE" / "run_state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["project_name"], "Sample Project")
            self.assertEqual(state["current_status"], "intake")


if __name__ == "__main__":
    unittest.main()
