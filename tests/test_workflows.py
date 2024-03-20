"""Tests WEI workflow functionality"""

from wei.core.data_classes import WorkflowStatus

from .test_base import TestWEI_Base


class TestWEI_Workflows(TestWEI_Base):
    """Tests WEI location management"""

    def test_workflow_run(self):
        """Test Running a simple workflow"""
        from pathlib import Path

        workflow_path = Path(__file__).parent / "workflows" / "test_workflow.yaml"

        run_info = self.experiment.start_run(
            workflow_file=workflow_path,
            payload={"wait_time": 5},
            blocking=True,
            simulate=False,
        )

        assert run_info["status"] == WorkflowStatus.COMPLETED
