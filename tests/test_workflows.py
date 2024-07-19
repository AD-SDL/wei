"""Tests WEI workflow functionality"""

import json

from test_base import TestWEI_Base

from wei.types import WorkflowStatus


class TestWEI_Workflows(TestWEI_Base):
    """Tests WEI location management"""

    def test_workflow_run(self):
        """Test Running a simple workflow"""
        from pathlib import Path

        workflow_path = Path(__file__).parent / "workflows" / "test_workflow.yaml"
        print(workflow_path)
        run_info = self.experiment.start_run(
            workflow_file=workflow_path,
            # payload={"wait_time": 5},
            # blocking=True,
            # simulate=False,
        )
        print(json.dumps(run_info, indent=2))

        assert run_info["status"] == WorkflowStatus.COMPLETED


if __name__ == "__main__":
    test = TestWEI_Workflows().test_workflow_run()
