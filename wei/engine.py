"""
Engine Class and associated helpers and data
"""

import time
import traceback

from wei.config import Config
from wei.core.module import update_active_modules
from wei.core.scheduler import Scheduler, SequentialScheduler
from wei.core.state_manager import StateManager
from wei.helpers import initialize_state, parse_args


class Engine:
    """
    Handles scheduling workflows and executing steps on the workcell.
    Pops incoming workflows off a redis-based queue and executes them.
    """

    def __init__(self) -> None:
        """Initialize the scheduler."""
        self.state_manager = StateManager()
        self.state_manager.clear_state(reset_locations=Config.reset_locations)
        if Config.sequential_scheduler:
            self.scheduler = SequentialScheduler()
        else:
            self.scheduler = Scheduler()
        with self.state_manager.state_lock():
            initialize_state()
        time.sleep(Config.cold_start_delay)
        print("Engine initialized, waiting for workflows...")

    def spin(self) -> None:
        """
        Continuously loop, updating module states every Config.update_interval seconds.
        If the state of the workcell has changed, update the active modules and run the scheduler.
        """
        update_active_modules()
        tick = time.time()
        while True:
            try:
                if (
                    time.time() - tick > Config.update_interval
                    or self.state_manager.has_state_changed()
                ):
                    update_active_modules()
                    self.scheduler.run_iteration()
                    update_active_modules()
                    tick = time.time()
            except Exception:
                traceback.print_exc()
                print(
                    f"Error in engine loop, waiting {Config.update_interval} seconds before trying again."
                )
                time.sleep(Config.update_interval)


if __name__ == "__main__":
    parse_args()
    engine = Engine()
    engine.spin()
