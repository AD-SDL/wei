from pathlib import Path
import yaml

from test_base import TestWEI_Base
from wei.core.data_classes import WorkcellData


class TestValidators(TestWEI_Base):
    def test_validators(self):
        from wei.core.validators import ModuleValidator
        from wei.core.workflow import WorkflowRunner

        module_validator = ModuleValidator()

        workflow_config_path = Path("tests/test_workflow.yaml")
        workflow_def = yaml.safe_load(workflow_config_path.read_text())
        runner = WorkflowRunner(
            workflow_def=workflow_def,
            workcell=WorkcellData.from_yaml("tests/test_workcell.yaml"),
            payload={},
            experiment_path="test_experiment",
            run_id=0,
            simulate=True,
            workflow_name="Test Workflow",
        )

        for module in runner.workflow.modules:
            valid, msg = module_validator.check_module(module)
            assert valid
