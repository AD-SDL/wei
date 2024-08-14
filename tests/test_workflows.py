"""Tests WEI workflow functionality"""

import pytest
from wei.types import WorkflowStatus
from wei.types.exceptions import WorkflowFailedException

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

        assert run_info.status == WorkflowStatus.COMPLETED

    def test_workflow_failed(self):
        """Test Running a simple workflow"""
        from pathlib import Path

        workflow_path = (
            Path(__file__).parent / "workflows" / "test_workflow_failure.yaml"
        )

        with pytest.raises(WorkflowFailedException):
            run_info = self.experiment.start_run(
                workflow_file=workflow_path,
                payload={"wait_time": 5, "fail": True},
                blocking=True,
                simulate=False,
                raise_on_failed=True,
            )

        run_info = self.experiment.start_run(
            workflow_file=workflow_path,
            payload={"wait_time": 5, "fail": True},
            blocking=True,
            simulate=False,
            raise_on_failed=False,
        )

        assert run_info.status == WorkflowStatus.FAILED
