import json
import time

import yaml
from redis import Redis
from rq import Queue

# TODO: insert core logic to run workflows, should follow something like found in wei_workflow_base.py
# TODO figure out logging for tasks, and how to propogate them back to the client
# TODO error handling for tasks, how to propogate back to client, and retry for specific types of errors

redis_conn = Redis()
task_queue = Queue(connection=redis_conn)


def run_workflow_task(workflow_content, parsed_payload):
    workflow = yaml.safe_load(workflow_content)
    time.sleep(5)  # Simulate a blocking call where the workflow runs

    result = {
        "workflow": workflow,
        "payload": parsed_payload,
    }

    print(f"Workflow YAML:\n {workflow}\nPayload JSON:\n {json.dumps(parsed_payload)}")

    return result


if __name__ == "__main__":
    from rq import Worker

    # Start the RQ worker
    worker = Worker(
        [task_queue], connection=task_queue.connection, name="workflow_runner"
    )
    worker.work()
