#!/usr/bin/env python3

import json
from pathlib import Path
import cv2
from wei import ExperimentClient


def main():
    # The path to the Workflow definition yaml file
    wf_path = Path("./example_workflow.yaml")
    # This defines the Experiment object that will communicate with the server for workflows
    exp = ExperimentClient("127.0.0.1", "8000", "Example_Program")
    # This initializes the connection to the server and the logs for this run of the program.
    exp.register_exp()
    # This runs the simulated_workflow a simulated workflow
    flow_info = exp.start_run(wf_path.resolve(), simulate=False, blocking=True)
    print(json.dumps(flow_info, indent=2))
    exp.get_file(flow_info["hist"]["Take Picture"]["action_msg"], "test2.jpg")
   

if __name__ == "__main__":
    main()
