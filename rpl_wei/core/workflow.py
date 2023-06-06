import logging
from typing import Any, Dict, List, Optional

import ulid
from devtools import debug

from rpl_wei.core import DATA_DIR
from rpl_wei.core.data_classes import Workflow as WorkflowData
from rpl_wei.core.executors.step_executor import StepExecutor
from rpl_wei.core.loggers import WEI_Logger
from rpl_wei.core.validators import ModuleValidator, StepValidator
from rpl_wei.core.workcell import Workcell


class WorkflowRunner:
    def __init__(
        self,
        workflow_def: Dict[str, Any],
        experiment_id: str,
        run_id: Optional[ulid.ULID] = None,
        log_level: int = logging.INFO,
        silent: bool = False,
    ) -> None:
        self.workflow = WorkflowData(**workflow_def)
        self.silent = silent
        # Setup validators
        self.module_validator = ModuleValidator()
        self.step_validator = StepValidator()

        # Setup executor
        self.executor = StepExecutor()

        # Setup runner
        if run_id:
            self.run_id = run_id
        else:
            self.run_id = ulid.new()
        self.log_dir = DATA_DIR / "runs" / experiment_id / str(self.run_id)
        # self.result_dir = self.log_dir / "results"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        # self.result_dir.mkdir(parents=True, exist_ok=True)
        self.logger = WEI_Logger.get_logger(
            "runLogger",
            log_dir=self.log_dir,
            log_level=log_level,
        )

    def check_modules(self):
        """Checks the modules required by the workflow"""
        for module in self.workflow.modules:
            self.module_validator.check_module(module=module)

    def check_flowdef(self):
        """Checks the actions provided by the workflow"""
        for step in self.workflow.flowdef:
            self.step_validator.check_step(step=step)

    def init_flow(
        self,
        workcell: Workcell,
        callbacks: Optional[List[Any]] = None,
        payload: Optional[Dict[str, Any]] = None,
        simulate: bool = False,
    ) -> Dict[str, Any]:
        """Executes the flowdef commmands"""
        # TODO: configure the exceptions in such a way that they get thrown here, will be client job to handle these for now

        # Start executing the steps
        steps = []
        for step in self.workflow.flowdef:
            # get module information from workcell file
            step_module = workcell.find_step_module(step.module)
            if not step_module:
                raise ValueError(
                    f"No module found for step module: {step.module}, in step: {step}"
                )

            # replace position names with actual positions
            if isinstance(step.args, dict) and len(step.args) > 0:
                for key, value in step.args.items():
                    if hasattr(value, "__contains__") and "positions" in value:
                        module_name = value.split(".")[0]
                        module = workcell.find_step_module(module_name)
                        if silent:
                            module.type = "silent_callback"
                        if not module:
                            raise ValueError(
                                f"Module positon not found for module '{module_name}' and identifier '{value}'"
                            )

                        location_varname = value.split(".")[-1]
                        assert (
                            location_varname in module.positions
                        ), f"Position {location_varname} not found"
                        location = module.positions[location_varname]

                        step.args[key] = location

            # Inject the payload
            if isinstance(payload, dict):
                if not isinstance(step.args, dict) or len(step.args) == 0:
                    continue
                # TODO check if you can see the attr of this class and match them with vars in the yaml
                (arg_keys, arg_values) = zip(*step.args.items())
                for key, value in payload.items():
                    # Covers naming issues when referring to namespace from yaml file
                    if "payload." not in key:
                        key = f"payload.{key}"
                    if key in arg_values:
                        idx = arg_values.index(key)
                        step_arg_key = arg_keys[idx]
                        step.args[step_arg_key] = value

                # TODO remove once there is a better result_dir injection method
                # WARNING WILL FAIL IF `local_run_results` IN ARGS MORE THAN ONCE
                if "local_run_results" in arg_values:
                    idx = arg_values.index("local_run_results")
                    step_arg_key = arg_keys[idx]
                    step.args[step_arg_key] = str(self.result_dir)

            # execute the step
            arg_dict = {
                "step": step,
                "step_module": step_module,
                "logger": self.logger,
                "callbacks": callbacks,
                "simulate": simulate,
            }
            steps.append(arg_dict)
        return steps

    def run_flow(
        self,
        workcell: Workcell,
        callbacks: Optional[List[Any]] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Executes the flowdef commmands"""
        # TODO: configure the exceptions in such a way that they get thrown here, will be client job to handle these for now

        # Start executing the steps
        steps = self.init_flow(workcell, callbacks, payload)
        for step in steps:
            self.executor.execute_step(**step)

        return {
            "run_dir": str(self.log_dir),
            "run_id": str(self.run_id),
            "payload": payload,
        }

    def print_flow(self):
        """Prints the workflow dataclass, for debugging"""
        debug(self.workflow)

    def print_workcell(self):
        """Print the workcell datacall, for debugging"""
        debug(self.workcell)
