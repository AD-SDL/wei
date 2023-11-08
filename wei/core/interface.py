"""standardizes communications with different types of module interfaces"""

from typing import Dict, Type, Union

from wei.core.interfaces.rest_interface import RestInterface
from wei.core.interfaces.ros2_interface import ROS2Interface
from wei.core.interfaces.simulate_interface import SimulateInterface
from wei.core.interfaces.tcp_interface import TcpInterface
from wei.core.interfaces.zmq_interface import ZmqInterface

InterfaceTypes = Union[
    Type[RestInterface],
    Type[ROS2Interface],
    Type[SimulateInterface],
    Type[TcpInterface],
    Type[ZmqInterface],
]


class InterfaceMap:
    """Mapping of YAML names to functions from interfaces"""

    interfaces: Dict[str, InterfaceTypes] = {
        "wei_ros_node": ROS2Interface,
        "wei_tcp_node": TcpInterface,
        "wei_rest_node": RestInterface,
        "wei_zmq_node": ZmqInterface,
        "simulate_callback": SimulateInterface,
    }
