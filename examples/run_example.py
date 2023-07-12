#!/usr/bin/env python3

from pathlib import Path
from rpl_wei import Experiment


def main():
    # The path to the Workflow definition yaml file
    wf_path = Path("../tests/test_workflow.yaml")
    # This defines the Experiment object that will communicate with the server for workflows
    exp = Experiment("127.0.0.1", "8000", "Example Program")
    # This initilizes the connection to the server and the logs for this run of the program.
    exp.register_exp()
    # This runs the simulated_workflow a simulated workflow
    flow_info = exp.run_job(wf_path.resolve(), simulate=True)
    print(flow_info)
    # This checks the state of the experiment in the queue
    flow_status = exp.query_job(flow_info["job_id"])
    # This will print out the queued job
    print(flow_status)
    # This will wait until the flow has run and then print out the final result of the flow
    while flow_status["status"] != "finished":
        flow_status = exp.query_job(flow_info["job_id"])
    print(flow_status)


if __name__ == "__main__":
    main()
