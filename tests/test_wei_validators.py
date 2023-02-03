from pathlib import Path

from test_base import TestWEI_Base


class TestValidators(TestWEI_Base):
    def test_validators(self):
        from rpl_wei.validators import ModuleValidator
        from rpl_wei.wei_workcell_base import WEI

        module_validator = ModuleValidator()

        workflow_config_path = Path("tests/test_pcr_workflow.yaml")
        wei = WEI(wf_config=workflow_config_path)

        # get run id (TODO: this is clunky...)
        run_id = list(wei.get_workflows().keys())[0]
        wf_dict = wei.get_workflow(run_id)
        wf = wf_dict.get("workflow")
        for module in wf.workcell.modules:
            valid, msg = module_validator.check_module(module)
            assert valid
