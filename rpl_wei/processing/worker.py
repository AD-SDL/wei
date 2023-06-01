import json
import time
from typing import Optional, Union

import yaml
from redis import Redis
from rq import Queue
import ulid

from rpl_wei.core.workcell import Workcell
from rpl_wei.core.workflow import WorkflowRunner

# TODO figure out logging for tasks, and how to propogate them back to the client
# TODO error handling for tasks, how to propogate back to client, and retry for specific types of errors

redis_conn = Redis()
task_queue = Queue(connection=redis_conn)

"""
Things to do in worker:

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
    job_id = ulid.from_str(job_id) if isinstance(job_id, str) else job_id
    workcell = Workcell(workcell_def)
    workflow_runner = WorkflowRunner(
        yaml.safe_load(workflow_def), experiment_id=experiment_id, run_id=job_id
    )

    # Run validation
    workflow_runner.check_flowdef()
    workflow_runner.check_modules()

    # Run workflow
    result_payload = workflow_runner.run_flow(
        workcell, payload=parsed_payload, simulate=simulate
    )
    if simulate:
        time.sleep(5)

    print(f"Result payload:\t{json.dumps(result_payload)}")

    return result_payload


if __name__ == "__main__":
    from rq import Worker

    # Start the RQ worker
    worker = Worker(
        [task_queue], connection=task_queue.connection, name="workflow_runner"
    )
    worker.work()
