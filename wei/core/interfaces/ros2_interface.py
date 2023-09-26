"""Handling execution for steps in the RPL-SDL efforts"""
from typing import Tuple

from wei.core.data_classes import Interface, Module, Step, StepStatus

try:
    import rclpy
except ImportError:
    print("No RCLPY found... Cannot use ROS2")
    rclpy = None

try:
    from wei_executor.weiExecutorNode import weiExecNode

except ImportError as e:
    print(e)
    wei_execution_node = None


def __init_rclpy():
    """starts the execution node
    Parameters
       ----------
       None
       Returns
       -------
       None
    """
    global wei_execution_node

    if rclpy:  # use_rclpy:
        if not rclpy.utilities.ok():
            rclpy.init()
            print("Started RCLPY")
            wei_execution_node = weiExecNode("execNode")
        else:
            print("RCLPY OK ")
    return wei_execution_node


def __kill_node():
    """stops the execution node
    Parameters
       ----------
       None
       Returns
       -------
       None
    """

    global wei_execution_node
    print("killing node")
    wei_execution_node.destroy_node()
    rclpy.shutdown()


def wei_ros2_service_callback(step: Step, **kwargs):
    """Executes a single step from a workflow using a ROS messaging framework

    Parameters
    ----------
    step : Step
        A single step from a workflow definition

    Returns
    -------
    action_response: StepStatus
        A status of the step (in theory provides async support with IDLE, RUNNING, but for now is just SUCCEEDED/FAILED)
    action_msg: str
        the data or informtaion returned from running the step.
    action_log: str
        A record of the exeution of the step

    """
    __init_rclpy()

    module: Module = kwargs["step_module"]

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
    if rclpy:
        action_response, action_msg, action_log = wei_execution_node.send_wei_command(
            msg["node"], msg["action_handle"], msg["action_vars"]
        )

        if action_msg and kwargs.get("verbose", False):
            print(action_msg)

        __kill_node()
    return action_response, action_msg, action_log


def wei_ros2_camera_callback(step: Step, **kwargs):
    """Executes a single step from a workflow to take a picture using a ROS connected camera
    Parameters
    ----------
    step : Step
        A single step from a workflow definition

    Returns
    -------
    action_response: StepStatus
        A status of the step (in theory provides async support with IDLE, RUNNING, but for now is just SUCCEEDED/FAILED)
    action_msg: str
        The location where the image was saved
    action_log: str
        A record of the exeution of the step

    """
    try:
        import rclpy  # noqa
    except ImportError:
        print("No RCLPY found... Cannot use ROS2")

    __init_rclpy()
    module: Module = kwargs["step_module"]

    res = wei_execution_node.capture_image(  # noqa
        node_name=module.config["ros_node_address"],
        image_name=step.args["file_name"],
        path=step.args["save_location"],
    )
    __kill_node()
    # TODO: process res
    return (
        "StepStatus.SUCCEEDED",
        str({"img_path": step.args["save_location"] + "/" + step.args["file_name"]}),
        "action_log",
    )


class ROS2Interface(Interface):
    """Basic Interface for interacting with WEI modules using ROS2"""

    def __init__(self, name) -> None:
        """Initializes the ROS2 interface"""
        try:
            import rclpy as test
        except ImportError:
            print("No RCLPY found... Cannot use ROS2")
            test = None

        self.rclpy = test
        self.wei_execution_node = self.__init_rclpy(name)

    def __init_rclpy(self, name):
        if self.rclpy:  # use_rclpy:
            if not self.rclpy.utilities.ok():
                self.rclpy.init()
                print("Started RCLPY")
                wei_execution_node = weiExecNode(name)
            else:
                print("RCLPY OK ")
                wei_execution_node = weiExecNode(name)
        return wei_execution_node

    def __kill_node(self, wei_execution_node):
        # print("killing node")
        self.wei_execution_node.destroy_node()
        self.rclpy.shutdown()

    def send_action(self, step: Step, **kwargs) -> Tuple[StepStatus, str, str]:
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
        module: Module = kwargs["step_module"]
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
        if self.rclpy:
            (
                action_response,
                action_msg,
                action_log,
            ) = self.wei_execution_node.send_wei_command(
                msg["node"], msg["action_handle"], msg["action_vars"]
            )
            if action_msg and kwargs.get("verbose", False):
                print(action_msg)
            rclpy.spin_once(self.wei_execution_node)
        return action_response, action_msg, action_log

    def get_state(self, config) -> str:
        """Gets the state of the module and returns it."""
        state = self.wei_execution_node.get_state(config["ros_node_address"])
        rclpy.spin_once(self.wei_execution_node)
        print(state)
        return str(state)
