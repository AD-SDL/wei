import json
import time
from typing import Optional, Union

import ulid
import yaml
from redis import Redis
from rq import Queue

from rpl_wei.core import DATA_DIR
from rpl_wei.core.loggers import WEI_Logger
from rpl_wei.core.workcell import Workcell
from rpl_wei.core.workflow import WorkflowRunner


redis_conn = Redis()
task_queue = Queue(connection=redis_conn, default_timeout=-1)

"""
# TODO figure out logging for tasks, and how to propogate them back to the client
# TODO error handling for tasks, how to propogate back to client, and retry for specific types of errors

1. create a workcell object from the workcell yaml file
3. run validation steps on modules and resources (not yet implemented)
4. run the workflow with the payload
5. cleanup? log results?
"""


def run_workflow_task(
    experiment_id,
    workflow_def,
    parsed_payload,
    workcell_def,
    job_id: Optional[Union[ulid.ULID, str]] = None,
    simulate: bool = False,
):
    """Placeholder"""
    job_id = ulid.from_str(job_id) if isinstance(job_id, str) else job_id
    workcell = Workcell(workcell_def)
    workflow_runner = WorkflowRunner(
        yaml.safe_load(workflow_def),
        experiment_id=experiment_id,
        run_id=job_id,
        simulate=simulate,
    )

    # Run validation
    workflow_runner.check_flowdef()
    workflow_runner.check_modules()
    log_dir = DATA_DIR / "runs" / experiment_id
    exp_log = WEI_Logger.get_logger("log_" + str(experiment_id), log_dir)

    # Run workflow
    # exp.events.wei_flow_run()
    exp_log.info(
        "WEI:WORKFLOW:RUN: "
        + str(workflow_runner.workflow.name)
        + ", RUN ID: "
        + str(job_id)
    )
    result_payload = workflow_runner.run_flow(
        workcell, payload=parsed_payload, simulate=simulate
    )
    if simulate:
        time.sleep(5)
    exp_log.info(
        "WEI:WORKFLOW:COMPLETE: "
        + str(workflow_runner.workflow.name)
        + ",  RUN ID: "
        + str(job_id)
    )
    print(f"Result payload:\t{json.dumps(result_payload)}")

    return result_payload


if __name__ == "__main__":
    from rq import Worker

    # Start the RQ worker
    worker = Worker(
        [task_queue], connection=task_queue.connection, name="workflow_runner"
    )
    worker.work()
