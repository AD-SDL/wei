"""The module that initilizes and runs the step by step WEI workflow"""
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import ulid
from devtools import debug

from rpl_wei.core.data_classes import Workflow as WorkflowData
from rpl_wei.core.loggers import WEI_Logger
from rpl_wei.core.step_executor import StepExecutor
from rpl_wei.core.validators import ModuleValidator, StepValidator
from rpl_wei.core.workcell import Workcell


class WorkflowRunner:
    """Initilizes and runs the step by step WEI workflow"""

    def __init__(
        self,
        workflow_def: Dict[str, Any],
        experiment_path: str,
        run_id: Optional[ulid.ULID] = None,
        log_level: int = logging.INFO,
        simulate: bool = False,
        workflow_name: str = "",
    ) -> None:
        """Manages the execution of a workflow

        Parameters
        ----------
        workflow_def : Dict[str, Any]
           The list of workflow steps to complete

        experiment_path: str
            Path for logging the experiment

        run_id: str
            id for the specific workflow

        log_level: int
            Level for logging the workflow

        simulate: bool
            Whether or not to use real robots

        workflow_name: str
            Human-created name of the workflow
        """

        self.workflow = WorkflowData(**workflow_def)
        self.simulate = simulate
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
        self.log_dir = (
            Path(experiment_path)
            / "wei_runs"
            / (workflow_name + "_" + str(self.run_id))
        )
        self.result_dir = self.log_dir / "results"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.result_dir.mkdir(parents=True, exist_ok=True)
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
        """Pulls the workcell and builds a list of dictionary steps to be executed

        Parameters
        ----------
        workcell : Workcell
           The Workcell data file loaded in from the workcell yaml file

        payload: Dict
            The input to the workflow

        simulate: bool
            Whether or not to use real robots

        Returns
        -------
        steps: List[Dict]
           a list of steps and the metadata relevant to execute them
        """
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
            if (
                isinstance(step.args, dict)
                and len(step.args) > 0
                and workcell.locations
            ):
                if step.module in workcell.locations.keys():
                    for key, value in step.args.items():
                        # if hasattr(value, "__contains__") and "positions" in value:
                        if value in workcell.locations[step.module].keys():
                            step.args[key] = workcell.locations[step.module][value]

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
        callbacks: Optional[Dict[str, Any]] = None,
        payload: Optional[Dict[str, Any]] = None,
        simulate: bool = False,
    ) -> Dict[str, Any]:
        """Runs through the steps of the workflow and sends the necessary

         Parameters
         ----------
         workcell : Workcell
            The Workcell data file loaded in from the workcell yaml file

         payload: bool
             The input to the workflow

         simulate: bool
             Whether or not to use real robots

         Returns
         -------
        response: Dict
            The result of running the workflow, including the log directory, the run_id the payload and the hist, which is the list of steps and their individual results
        """
        # TODO: configure the exceptions in such a way that they get thrown here, will be client job to handle these for now

        # TODO: configure the exceptions in such a way that they get thrown here, will be client job to handle these for now
        # Start executing the steps
        hist = {}
        steps = self.init_flow(workcell, callbacks, payload=payload, simulate=simulate)
        for step in steps:
            action_response, action_msg, action_log = self.executor.execute_step(**step)
            hist[step["step"].name] = {
                "action_response": str(action_response),
                "action_msg": str(action_msg),
                "action_log": str(action_log),
            }
        return {
            "run_dir": str(self.log_dir),
            "run_id": str(self.run_id),
            "payload": payload,
            "hist": hist,
        }

    def print_flow(self):
        """Prints the workflow dataclass, for debugging"""
        debug(self.workflow)

    def print_workcell(self):
        """Print the workcell datacall, for debugging"""
        debug(self.workcell)
