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
    Pops incoming workflows off a redis-based queue and executes them.
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
        """
        Continuously loop, updating module states every Config.update_interval seconds.
        If the state of the workcell has changed, update the active modules and run the scheduler.
        """
        print("Starting Process")
        last_check = time.time()
        while True:
            if time.time() - last_check > Config.update_interval:
                update_active_modules()
                last_check = time.time()
            if self.state_manager.has_state_changed():
                update_active_modules()
                self.scheduler.run_iteration()
                last_check = time.time()


if __name__ == "__main__":
    engine = Engine()
    engine.spin()
