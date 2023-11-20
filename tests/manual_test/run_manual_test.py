#!/usr/bin/env python3
"""Manually runs an integration test of WEI"""

from pathlib import Path

from wei import ExperimentClient


def main():
    """Manually runs an integration test of WEI"""
    # The path to the Workflow definition yaml file
    wf_path = Path("../manual_test/manual_test_workflow.yaml")
    # This defines the Experiment object that will communicate with the server for workflows
    exp = ExperimentClient("127.0.0.1", "8000", "Example Program")
    # This initilizes the connection to the server and the logs for this run of the program.
    exp.register_exp()
    # This runs the simulated_workflow a simulated workflow
    flow_info_1 = exp.start_run(wf_path.resolve(), simulate=False, blocking=False)
    # flow_info_2 = exp.start_run(wf_path.resolve(), simulate=False, blocking=False)
    # This checks the state of the flows in the queue
    flows = exp.await_runs([flow_info_1["run_id"]])
    # This will print out the queued job
    print(flows)
    # This will wait until the flow has run and then print out the final result of the flow
    # while flow_status["status"] != WorkflowStatus.COMPLETED:
    #     print(flow_status)
    #     time.sleep(1)
    #     flow_status = exp.query_run(flow_info["run_id"])
    # print(flow_status)


if __name__ == "__main__":
    main()
