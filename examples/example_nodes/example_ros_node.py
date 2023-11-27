#! /usr/bin/env python3
"""Sealer Node"""


import json
from time import sleep

import rclpy  # import Rospy
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node  # import Rospy Node
from std_msgs.msg import String
from wei_services.srv import WeiActions, WeiDescription


class Example_Client(Node):

    """
    The init function is necessary for the sealerNode class to initialize all variables, parameters, and other functions.
    Inside the function the parameters exist, and calls to other functions and services are made so they can be executed in main.
    """

    def __init__(self, TEMP_NODE_NAME="exampleNode"):
        """Setup sealer node"""

        super().__init__(TEMP_NODE_NAME)
        self.node_name = self.get_name()

        self.state = "UNKNOWN"
        self.robot_status = ""
        self.action_flag = "READY"
        self.reset_request_count = 0
        self.connect_robot()
        self.description = {
            "name": self.node_name,
            "type": "",
            "actions": {"prepare_sealer": "%d %d"},
        }

        action_cb_group = ReentrantCallbackGroup()
        description_cb_group = ReentrantCallbackGroup()
        state_cb_group = ReentrantCallbackGroup()
        state_refresher_cb_group = ReentrantCallbackGroup()

        timer_period = 0.5  # seconds
        state_refresher_timer_period = 0.5  # seconds

        self.StateRefresherTimer = self.create_timer(
            state_refresher_timer_period,
            callback=self.robot_state_refresher_callback,
            callback_group=state_refresher_cb_group,
        )

        self.statePub = self.create_publisher(
            String, self.node_name + "/state", 10
        )  # Publisher for sealer state
        self.stateTimer = self.create_timer(
            timer_period, self.stateCallback, callback_group=state_cb_group
        )  # Callback that publishes to sealer state

        self.actionSrv = self.create_service(
            WeiActions,
            self.node_name + "/action_handler",
            self.actionCallback,
            callback_group=action_cb_group,
        )
        self.descriptionSrv = self.create_service(
            WeiDescription,
            self.node_name + "/description_handler",
            self.descriptionCallback,
            callback_group=description_cb_group,
        )

    def connect_robot(self):
        """Connect robot"""
        sleep(5)

    def robot_state_refresher_callback(self):
        """Get the State from the Robot"""
        sleep(0.1)
        # TODO: Get state from robot

    def stateCallback(self):
        """The state of the robot, can be ready, completed, busy, error"""
        self.state = "IDLE"
        msg = String(self.state)
        self.statePub.publish(msg)

    def descriptionCallback(self, request, response):
        """The descriptionCallback function is a service that can be called to showcase the available actions a robot
        can preform as well as deliver essential information required by the master node.

        Parameters:
        -----------
        request: str
            Request to the robot to deliver actions
        response: Tuple[str, List]
            The actions a robot can do, will be populated during execution

        Returns
        -------
        Tuple[str, List]
            The robot steps it can do
        """
        response.description_response = str(self.description)

        return response

    def actionCallback(self, request: str, response: str) -> None:
        """The actions the robot can perform, also performs them

        Parameters:
        -----------
        request: str
            Request to the robot to perform an action
        response: bool
            If action is performed

        Returns
        -------
        None
        """

        action_handle = (
            request.action_handle
        )  # Run commands if manager sends corresponding command
        vars = json.loads(request.vars)
        self.get_logger().info(str(vars))

        self.action_flag = "BUSY"

        if action_handle == "seal" or True:
            self.get_logger().info("Starting Action: " + request.action_handle.upper())
            sleep(5)
            response.action_response = -1
            response.action_msg = ""
            return response


def main(args=None):
    """Main function for the example ROS node"""
    rclpy.init(args=args)  # initialize Ros2 communication

    try:
        example_client = Example_Client()
        executor = MultiThreadedExecutor()
        executor.add_node(example_client)

        try:
            example_client.get_logger().info("Beginning client, shut down with CTRL-C")
            executor.spin()
        except KeyboardInterrupt:
            example_client.get_logger().info("Keyboard interrupt, shutting down.\n")
        finally:
            executor.shutdown()
            example_client.destroy_node()
    finally:
        rclpy.shutdown()


if __name__ == "__main__":
    main()
