"""Tests WEI workflow functionality"""

from pathlib import Path

import pytest
from wei.types import WorkflowStatus
from wei.types.exceptions import WorkflowFailedException

from .test_base import TestWEI_Base


class TestWEI_Workflows(TestWEI_Base):
    """Tests WEI location management"""

    def test_workflow_run(self):
        """Test Running a simple workflow"""

        workflow_path = Path(__file__).parent / "workflows" / "test_workflow.yaml"

        run_info = self.experiment.start_run(
            workflow_file=workflow_path,
            payload={"wait_time": 5},
            blocking=True,
            simulate=False,
        )

        assert run_info.status == WorkflowStatus.COMPLETED
        assert self.experiment.get_datapoint_value(
            run_info.get_datapoint_id_by_label("test_label")
        )
        print(run_info.get_step_by_name("Measure foobar").result)
        assert self.experiment.get_datapoint_value(
            run_info.get_step_by_name("Measure foobar").result.data["test"]
        )
        with pytest.raises(KeyError):
            self.experiment.get_datapoint_value(
                run_info.get_datapoint_id_by_label("non_existent_label")
            )

    def test_workflow_failed(self):
        """Test Running a simple workflow"""

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
