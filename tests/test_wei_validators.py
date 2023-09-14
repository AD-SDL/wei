from pathlib import Path
import yaml

from test_base import TestWEI_Base


class TestValidators(TestWEI_Base):
    def test_validators(self):
        from wei.core.validators import ModuleValidator
        from wei.core.workflow import WorkflowRunner

        module_validator = ModuleValidator()

        workflow_config_path = Path("tests/test_workflow.yaml")
        worfklow_def = yaml.safe_load(workflow_config_path.read_text())
        runner = WorkflowRunner(worfklow_def, "test_experiment")

        for module in runner.workflow.modules:
            valid, msg = module_validator.check_module(module)
            assert valid
