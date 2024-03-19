"""Handling execution for steps in the RPL-SDL efforts"""

from typing import Any, Dict, Tuple

from wei.config import Config
from wei.core.data_classes import Interface, Module, Step

try:
    import rclpy  # type: ignore
    from wei_executor.weiExecutorNode import weiExecNode  # type: ignore
except ImportError:
    print("ROS Environment not found... Cannot use ROS2Interface")


class ROS2Interface(Interface):
    """Basic Interface for interacting with WEI modules using ROS2"""

    @staticmethod
    def __init_rclpy(name: str) -> Any:
        if not rclpy:
            raise ImportError("ROS2 environment not found")
        if not rclpy.utilities.ok():
            rclpy.init()
            print("Started RCLPY")
            wei_execution_node = weiExecNode(name)
        else:
            print("RCLPY OK ")
            wei_execution_node = weiExecNode(name)
        return wei_execution_node

    @staticmethod
    def config_validator(config: Dict[str, Any]) -> bool:
        """Validates the configuration for the interface

        Parameters
        ----------
        config : Dict
            The configuration for the module

        Returns
        -------
        bool
            Whether the configuration is valid or not
        """
        for key in ["ros_node_address"]:
            if key not in config:
                return False
        return True

    @staticmethod
    def send_action(step: Step, module: Module, **kwargs: Any) -> Tuple[str, str, str]:
        """Executes a single step from a workflow using a ZMQ messaging framework with the ZMQ library

        Parameters
        ----------
        step : Step
            A single step from a workflow definition

        Returns
        -------
        action_response: StepStatus
            A status of the step (in theory provides async support with IDLE, RUNNING, but for now is just SUCCEEDED/FAILED)
        action_msg: str
            the data or information returned from running the step.
        action_log: str
            A record of the execution of the step

        """
        wei_execution_node = ROS2Interface.__init_rclpy(
            Config.workcell_name + "_exec_node"
        )
        msg = {
            "node": module.config["ros_node_address"],
            "action_handle": step.action,
            "action_vars": step.args,
        }

        if kwargs.get("verbose", False):
            print("\n Callback message:")
            print(msg)
            print()
        action_response = ""
        action_msg = ""
        action_log = ""
        (
            action_response,
            action_msg,
            action_log,
        ) = wei_execution_node.send_wei_command(
            msg["node"], msg["action_handle"], msg["action_vars"]
        )
        if action_msg and kwargs.get("verbose", False):
            print(action_msg)
        rclpy.spin_once(wei_execution_node)
        wei_execution_node.destroy_node()
        rclpy.shutdown()
        return action_response, action_msg, action_log

    @staticmethod
    def get_state(module: Module, **kwargs: Any) -> str:
        """Gets the state of the module and returns it."""
        wei_execution_node = ROS2Interface.__init_rclpy(
            Config.workcell_name + "_wei_exec_node"
        )
        state = wei_execution_node.get_state(module.config["ros_node_address"])
        rclpy.spin_once(wei_execution_node)
        wei_execution_node.destroy_node()
        rclpy.shutdown()
        return str(state)
