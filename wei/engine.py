"""
Engine Class and associated helpers and data
"""

import time

from wei.config import Config
from wei.core.data_classes import WorkcellData
from wei.core.location import initialize_workcell_locations
from wei.core.module import initialize_workcell_modules, update_active_modules
from wei.core.scheduler import Scheduler
from wei.core.state_manager import StateManager


class Engine:
    """
    Handles scheduling workflows and executing steps on the workcell.
    Pops incoming workflows off a redis-based queue (a LIST) and executes them.
    """

    def __init__(self):
        """Initialize the scheduler."""
        self.state_manager = StateManager(
            Config.workcell_file, Config.redis_host, Config.redis_port
        )
        self.state_manager.clear_state(reset_locations=Config.reset_locations)
        self.scheduler = Scheduler()
        with self.state_manager.state_lock():
            self.state_manager.set_workcell(
                WorkcellData.from_yaml(Config.workcell_file)
            )
            initialize_workcell_modules()
            initialize_workcell_locations()

    def spin(self):
        """Run the scheduler, popping incoming workflows queued by the server and executing them."""
        print("Starting Process")
        last_check = time.time()
        while True:
            if time.time() - last_check > Config.update_interval:
                update_active_modules()
            if self.state_manager.has_state_changed():
                self.scheduler.run_iteration()
                update_active_modules()
            time.sleep(Config.update_interval)


if __name__ == "__main__":
    engine = Engine()
    engine.spin()
