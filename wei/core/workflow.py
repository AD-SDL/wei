"""The module that initializes and runs the step by step WEI workflow"""
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import requests
import ulid
from devtools import debug

from wei.core.data_classes import Workflow, WorkcellData, WorkflowRun, PathLike
from wei.core.loggers import WEI_Logger
from wei.core.step_executor import StepExecutor
from wei.core.validators import ModuleValidator, StepValidator
from wei.core.workcell import find_step_module


class WorkflowRunner:
    """Initializes and runs the step by step WEI workflow"""

    def __init__(
        self,
        workflow_def: Union[Dict[str, Any], Workflow],
        workcell: Union[Dict[str, Any], WorkcellData],
        experiment_path: str,
        payload,
        run_id: Optional[str] = None,
        log_level: int = logging.INFO,
        simulate: bool = False,
        workflow_name: str = "",
    ) -> None:
        """Manages the execution of a workflow

        Parameters
        ----------
        workflow_def : [Dict[str, Any], Workflow]
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

        if type(workflow_def) is dict:
            workflow = Workflow(**workflow_def)
        elif type(workflow_def) is Workflow:
            workflow = workflow_def
        simulate = simulate
        # Setup validators
        module_validator = ModuleValidator()
        step_validator = StepValidator()
        path = Path(experiment_path)
        experiment_id = path.name.split("_id_")[-1]
        if type(workcell) is dict:
            workcell = WorkcellData(**workcell)
        elif type(workcell) is WorkcellData:
            workcell = workcell
        

        # Setup executor
        executor = StepExecutor()

        # Setup runner
        if run_id:
            run_id = run_id
        else:
            run_id = ulid.new()
        log_dir = (
            Path(experiment_path)
            / "wei_runs"
            / (workflow_name + "_" + str(run_id))
        )
        result_dir = log_dir / "results"
        log_dir.mkdir(parents=True, exist_ok=True)
        result_dir.mkdir(parents=True, exist_ok=True)
        logger = WEI_Logger.get_logger(
            "runLogger",
            log_dir=log_dir,
            log_level=log_level,
        )
        steps = init_flow(
            workcell, None, payload=payload, simulate=simulate
        )
        hist = {}

 
def create_run(
    workflow: Workflow,
    workcell: WorkcellData,
    payload: Optional[Dict[str, Any]] = None,
    experiment_path: Optional[PathLike] = None,
    simulate: bool = False,
) -> List[Dict[str, Any]]:
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
    for module in workflow.modules:
        if not (find_step_module(workcell, module.name)):
            raise ValueError(
                f"Module {module} not in Workcell {workflow.modules}"
            )
    wf_run = WorkflowRun(label= workflow.name, payload=payload, steps = workflow.steps, )
    for step in workflow.flowdef:
        # get module information from workcell file
        step_module = find_step_module(workcell, step.module)
        if not step_module:
            raise ValueError(
                f"No module found for step module: {step.module}, in step: {step}"
            )
        valid = False
        for module in workflow.modules:
            if step.module == module.name:
                valid = True
        if not (valid):
            raise ValueError(f"Module {step.module} not in flow modules")
        # replace position names with actual positions
        if (
            isinstance(step.args, dict)
            and len(step.args) > 0
            and workcell.locations
        ):
            if step.module in workcell.locations.keys():
                for key, value in step.args.items():
                    # if hasattr(value, "__contains__") and "positions" in value:
                    if str(value) in workcell.locations[step.module].keys():
                        step.locations[key] = value

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


        # execute the step

        
        steps.append(step)
    return steps

    