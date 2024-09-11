"""
Engine Class and associated helpers and data
"""

import time
import traceback

import requests

from wei.config import Config
from wei.core.events import send_event
from wei.core.experiment import parse_experiments_from_disk
from wei.core.module import update_active_modules
from wei.core.scheduler import Scheduler
from wei.core.state_manager import state_manager
from wei.core.storage import initialize_storage
from wei.core.workflow import cancel_active_workflow_runs
from wei.types.event_types import WorkcellStartEvent
from wei.utils import initialize_state, parse_args, threaded_daemon


class Engine:
    """
    Handles scheduling workflows and executing steps on the workcell.
    Pops incoming workflows off a redis-based queue and executes them.
    """

    def __init__(self) -> None:
        """Initialize the scheduler."""

        initialize_storage()
        parse_experiments_from_disk()
        state_manager.clear_state(
            reset_locations=Config.reset_locations,
            clear_workflow_runs=Config.clear_workflow_runs,
        )
        cancel_active_workflow_runs()
        self.scheduler = Scheduler(sequential=Config.sequential_scheduler)
        with state_manager.wc_state_lock():
            initialize_state()
        time.sleep(Config.cold_start_delay)

        print("Engine initialized, waiting for workflows...")
        send_event(WorkcellStartEvent(workcell=state_manager.get_workcell()))

    def wait_for_server(self):
        """Checks that the server is up before starting the engine."""
        start_wait = time.time()
        server_alive = False
        while time.time() - start_wait < 60:
            try:
                response = requests.get(
                    f"http://{Config.server_host}:{Config.server_port}/up"
                )
                if response.ok:
                    server_alive = True
                    break
                else:
                    response.raise_for_status()
            except Exception:
                time.sleep(1)
        if not server_alive:
            raise Exception("Server did not respond after 60 seconds")

    def spin(self) -> None:
        """
        Continuously loop, updating module states every Config.update_interval seconds.
        If the state of the workcell has changed, update the active modules and run the scheduler.
        """
        update_active_modules()
        tick = time.time()
        heartbeat = time.time()
        while True and not state_manager.shutdown:
            try:
                if time.time() - heartbeat > 2:
                    heartbeat = time.time()
                    print(f"Heartbeat: {time.time()}")
                if (
                    time.time() - tick > Config.update_interval
                    or state_manager.has_state_changed()
                ):
                    update_active_modules()
                    if not state_manager.paused:
                        self.scheduler.run_iteration()
                        update_active_modules()
                    tick = time.time()
            except Exception:
                traceback.print_exc()
                print(
                    f"Error in engine loop, waiting {Config.update_interval} seconds before trying again."
                )
                time.sleep(Config.update_interval)

    @threaded_daemon
    def start_engine_thread(self):
        """Spins the engine in its own thread"""
        self.spin()


if __name__ == "__main__":
    parse_args()
    engine = Engine()
    engine.spin()
