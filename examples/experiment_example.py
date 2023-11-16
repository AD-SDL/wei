#!/usr/bin/env python3

import json
from pathlib import Path

from wei import ExperimentClient

SIMULATE = True


def main() -> None:
    # The path to the Workflow definition yaml file
    wf_path = Path(__file__).parent / "example_yaml/example_workflow.yaml"
    # This defines the Experiment object that will communicate with the WEI server
    exp = ExperimentClient("127.0.0.1", "8000", "Example_Program")
    # This initializes the connection to the server and the logs for this run of the program.
    exp.register_exp()
    # This runs the workflow
    flow_info = exp.start_run(wf_path.resolve(), simulate=SIMULATE, blocking=True)
    print(json.dumps(flow_info, indent=2))
    # If the workflow run isn't simulated, the below line can be used to fetch the result and save it in our local directory
    if not SIMULATE:
        exp.get_file(
            flow_info["hist"]["Take Picture"]["action_msg"], "experiment_output.jpg"
        )


if __name__ == "__main__":
    main()
