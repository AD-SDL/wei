"""Tests WEI workflow functionality"""

from pathlib import Path

import pytest

from wei.core.workflow import insert_parameter_values
from wei.types import WorkflowStatus
from wei.types.exceptions import WorkflowFailedException
from wei.types.workflow_types import Workflow

from .test_base import TestWEI_Base


class TestWEI_Workflows(TestWEI_Base):
    """Tests WEI workflow functionality"""

    def test_workflow_payload(self):
        """test parameter insertion works properly"""
        wf = Workflow.from_yaml(
            Path(__file__).parent / "workflows" / "test_workflow.yaml"
        )
        insert_parameter_values(
            wf, {"delay": 5, "pos": "transfer.pos", "aim": "target"}
        )
        assert wf.flowdef[0].args["target"] == "transfer.pos"
        assert wf.flowdef[5].name == "Wait for 5 seconds"
        assert wf.flowdef[5].args["seconds"] == 5
        wf = Workflow.from_yaml(
            Path(__file__).parent / "workflows" / "test_workflow.yaml"
        )
        insert_parameter_values(wf, {"pos": "transfer.pos", "aim": "target"})
        assert wf.flowdef[5].name == "Wait for 1.5 seconds"
        assert wf.flowdef[5].args["seconds"] == 1.5
        wf = Workflow.from_yaml(
            Path(__file__).parent / "workflows" / "test_workflow_payload.yaml"
        )
        insert_parameter_values(wf, {"test": "test.pos", "test2": "target"})
        assert wf.flowdef[0].name == "Get plate wotest.posrd test.pos.nottest"
        assert wf.flowdef[2].args == {
            "foo": {"thing": {"test": "test.pos"}},
            "bar": "test",
        }
        wf = Workflow.from_yaml(
            Path(__file__).parent / "workflows" / "test_workflow_payload.yaml"
        )
        with pytest.raises(ValueError):
            insert_parameter_values(wf, {"test": "test.pos"})

    def test_workflow_run(self):
        """Test Running a simple workflow"""

        workflow_path = Path(__file__).parent / "workflows" / "test_workflow.yaml"

        run_info = self.experiment_client.start_run(
            workflow=workflow_path,
            parameters={"delay": 1, "pos": "transfer.pos", "aim": "target"},
            blocking=True,
            simulate=False,
        )

        assert run_info.status == WorkflowStatus.COMPLETED
        assert self.experiment_client.get_datapoint_value(
            run_info.get_datapoint_id_by_label("test_label")
        )
        print(run_info.get_step_by_name("Measure foobar").result)
        assert self.experiment_client.get_datapoint_value(
            run_info.get_step_by_name("Measure foobar").result.data["test"]
        )
        with pytest.raises(KeyError):
            self.experiment_client.get_datapoint_value(
                run_info.get_datapoint_id_by_label("non_existent_label")
            )

    def test_workflow_failed(self):
        """Test Running a simple workflow"""

        workflow_path = (
            Path(__file__).parent / "workflows" / "test_workflow_failure.yaml"
        )

        with pytest.raises(WorkflowFailedException):
            run_info = self.experiment_client.start_run(
                workflow=workflow_path,
                blocking=True,
                simulate=False,
                raise_on_failed=True,
            )

        run_info = self.experiment_client.start_run(
            workflow=workflow_path,
            blocking=True,
            simulate=False,
            raise_on_failed=False,
        )

        assert run_info.status == WorkflowStatus.FAILED
