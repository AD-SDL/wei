"""standardizes communications with different damons"""


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
