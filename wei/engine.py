"""
Engine Class and associated helpers and data
"""

import time

from wei.config import config, load_engine_config, parse_args
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
            config.workcell_file, config.redis_host, config.redis_port
        )
        self.state_manager.clear_state(reset_locations=config.reset_locations)
        self.update_interval = config.update_interval
        self.scheduler = Scheduler(
            state_manager=self.state_manager,
        )
        with self.state_manager.state_lock():
            self.state_manager.set_workcell(WorkcellData.from_yaml(config.workcell))
            initialize_workcell_modules()
            initialize_workcell_locations()

    def spin(self):
        """Run the scheduler, popping incoming workflows queued by the server and executing them."""
        print("Starting Process")
        while True:
            with self.state_manager.state_lock():  # * Lock the state for the duration of the update loop
                update_active_modules()
                self.scheduler.run_iteration()
            time.sleep(self.update_interval)


if __name__ == "__main__":
    print("testing")
    args = parse_args()
    load_engine_config(args)
    engine = Engine()
    engine.spin()
