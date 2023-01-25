"""Handling execution for steps in the RPL-SDL efforts"""
from typing import Callable, List, Optional

from rpl_wei.data_classes import Module, Step, StepStatus


try: 
    import rclpy
    from wei_executor.weiExecutorNode import weiExecNode

    rclpy.init()
    wei_execution_node = weiExecNode()
except ImportError as err: 
    print("No WEI executor found... Cannot use ROS")
    wei_execution_node = None


# Callbacks 
def wei_service_callback(step: Step, **kwargs):

    module: Module = kwargs["step_module"]

    msg = {
        "node": module.config["ros_node"],
        "action_handle": step.command,
        "action_vars": step.args,
    }

    if kwargs.get("verbose", False): 
        print("\n Callback message:")
        print(msg)
        print()

    wei_execution_node.send_wei_command(
        msg["node"], msg["action_handle"], msg["action_vars"]
    )

def wei_camera_callback(step: Step, **kwargs): 

    module: Module = kwargs["step_module"]

    wei_execution_node.capture_image(
        node_name = module.config["ros_node"],
        image_name = step.args['file_name'], 
        path = step.args['save_location'] 
    )

### Executor mapping

class Executor_Map: 
    function = {
        "wei_ros_node": wei_service_callback, 
        "wei_ros_camera": wei_camera_callback, 
    }


class StepExecutor:
    """Class to handle executing steps"""

    def __init__(self, run_logger) -> None:
        """Initialize the StepExecutor with necesary tools/data

        Parameters
        ----------
        run_logger : logging.Logger
            The run logger for this run
        """
        self.run_logger = run_logger

    def execute_step(
        self,
        step: Step,
        step_module: Module,
        callbacks: Optional[List[Callable]] = None,
    ) -> StepStatus:
        """Executes a single step from a workflow

        Parameters
        ----------
        step : Step
            A single step from a workflow definition

        Returns
        -------
        StepStatus
            A status of the step (in theory provides async support with IDLE, RUNNING, but for now is just SUCCEEDED/FAILED)
        """
        assert step_module.type in Executor_Map, f"Executor not found for {step_module.type}"
        
        self.run_logger.info(f"Started running step with name: {step.name}")
        self.run_logger.debug(step)

        #map the correct executor function to the step_module
        Executor_Map.function[step_module.type](step, step_module=step_module)

        # TODO: Allow for callbacks, disabled for now because we are switching to the in-package callbacks
        # if callbacks:
        #     for callback in callbacks:
        #         callback(step, step_module=step_module)

        self.run_logger.info(f"Finished running step with name: {step.name}")

        return StepStatus.SUCCEEDED
