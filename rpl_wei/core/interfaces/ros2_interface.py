"""Handling execution for steps in the RPL-SDL efforts"""
from rpl_wei.core.data_classes import Module, Step

try:
    import rclpy
except ImportError:
    print("No RCLPY found... Cannot use ROS2")
    rclpy = None

try:
    from wei_executor.weiExecutorNode import weiExecNode
except ImportError:
    wei_execution_node = None


def __init_rclpy():
    """stops the execution node
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
            wei_execution_node = weiExecNode()
        else:
            print("RCLPY OK ")


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
    # assert use_rclpy, "No RCLPY found... Cannot send messages using ROS2"
    __init_rclpy()

    module: Module = kwargs["step_module"]

    msg = {
        "node": module.config["ros_node"],
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
    """Placeholder"""
    try:
        import rclpy  # noqa
    except ImportError:
        print("No RCLPY found... Cannot use ROS2")

    __init_rclpy()
    module: Module = kwargs["step_module"]

    res = wei_execution_node.capture_image(  # noqa
        node_name=module.config["ros_node"],
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
