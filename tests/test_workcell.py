import yaml
from pathlib import Path

from devtools import debug
from test_base import TestWEI_Base


class Test_Workcell_Base(TestWEI_Base):
    def test_workcell_property(self):
        from rpl_wei.core.workcell import Workcell

        workcell_config_path = Path("tests/test_workcell.yaml")
        workcell_def = yaml.safe_load(workcell_config_path.read_text())
        workcell = Workcell(workcell_def)

        debug(workcell.workcell)
        assert workcell is not None

    def test_payload(self):
        from rpl_wei.core.workflow import WorkflowRunner
        from rpl_wei.core.workcell import Workcell

        workcell_config_path = Path("tests/test_workcell.yaml")
        workcell_def = yaml.safe_load(workcell_config_path.read_text())
        workcell = Workcell(workcell_def)

        workflow_config_path = Path("tests/test_workflow.yaml")
        worfklow_def = yaml.safe_load(workflow_config_path.read_text())
        runner = WorkflowRunner(worfklow_def, "test_experiment")

        payload = {"thermocyle_time": 10, "thermocyle_temp": 175}

        run_info = runner.run_flow(workcell, payload=payload)

        assert run_info["payload"] == payload
