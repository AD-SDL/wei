"""standardizes communications with different damons"""

from wei.core.interfaces.rest_interface import RestInterface
from wei.core.interfaces.ros2_interface import ROS2Interface
from wei.core.interfaces.simulate_interface import SimulateInterface
from wei.core.interfaces.tcp_interface import TcpInterface
from wei.core.interfaces.zmq_interface import ZmqInterface


class Interface:
    """Standardizes communications with different daemons"""

    def send_action():
        """sends an action"""
        pass

    def get_about():
        """gets about information"""
        pass

    def get_state():
        """gets the robot state"""
        pass

    def get_resources():
        """gets the robot resources"""
        pass


class Interface_Map:
    """Mapping of YAML names to functions from interfaces"""

    function = {
        "wei_ros_node": ROS2Interface,
        "wei_tcp_node": TcpInterface,
        "wei_rest_node": RestInterface,
        "wei_zmq_node": ZmqInterface,
        "simulate_callback": SimulateInterface,
    }
