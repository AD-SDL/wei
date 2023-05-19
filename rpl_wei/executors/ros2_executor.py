"""Handling execution for steps in the RPL-SDL efforts"""
from rpl_wei.data_classes import Module, Step

wei_execution_node = None


def __init_rclpy():
    global wei_execution_node
    from wei_executor.weiExecutorNode import weiExecNode

    if not rclpy.utilities.ok():
        rclpy.init()
        print("Started RCLPY")
        wei_execution_node = weiExecNode()
    else:
        print("RCLPY OK ")

def __kill_node():
    global wei_execution_node
    print("killing node")
    wei_execution_node.destroy_node()
    rclpy.shutdown()

def wei_ros2_service_callback(step: Step, **kwargs):
    try:
        import rclpy
    except ImportError:
        print("No RCLPY found... Cannot use ROS2")

    __init_rclpy()

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

    action_response, action_msg, action_log = wei_execution_node.send_wei_command(
        msg["node"], msg["action_handle"], msg["action_vars"]
    )
    if action_msg:
        print(action_msg)

    __kill_node()
    return action_response, action_msg, action_log


def wei_ros2_camera_callback(step: Step, **kwargs):
    try:
        import rclpy
    except ImportError:
        print("No RCLPY found... Cannot use ROS2")

    __init_rclpy()
    module: Module = kwargs["step_module"]

    res = wei_execution_node.capture_image(
        node_name=module.config["ros_node"],
        image_name=step.args["file_name"],
        path=step.args["save_location"],
    )
    __kill_node()
    #TODO: process res
    return res 

