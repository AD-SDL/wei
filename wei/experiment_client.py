"""Contains the Experiment class that manages WEI flows and helps annotate the experiment run"""
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from warnings import warn

import requests

from wei.core.data_classes import WorkflowStatus
from wei.core.events import Events


class ExperimentClient:
    """Methods for the running and logging of a WEI Experiment including running WEI workflows and logging"""

    def __init__(
        self,
        server_addr: str,
        server_port: str,
        experiment_name: Optional[str] = None,
        experiment_id: Optional[str] = None,
    ) -> None:
        """Initializes an Experiment, and creates its log files

        Parameters
        ----------
        server_addr: str
            address for WEI server

        server_port: str
            port for WEI server

        experiment_name: str
            Human chosen name for experiment

        experiment_id: Optional[str]
            Programmatically generated experiment id, can be reused if needed

        """

        self.server_addr = server_addr
        self.server_port = server_port
        self.url = f"http://{self.server_addr}:{self.server_port}"

        start_time = time.time()
        while time.time() - start_time < 60:
            try:
                self.register_experiment(experiment_id, experiment_name)
                break
            except requests.exceptions.ConnectionError:
                time.sleep(1)

        self.loops: list[str] = []

        self.events = Events(
            self.server_addr,
            self.server_port,
            self.experiment_id,
        )

        self.events.start_experiment()

    def _return_response(self, response: requests.Response) -> Dict[Any, Any]:
        if response.status_code != 200:
            return {"http_error": response.status_code}

        return dict(response.json())

    def register_experiment(self, experiment_id, experiment_name) -> None:
        """Gets an existing experiment from the server,
           or creates a new one if it doesn't exist

        Parameters
        ----------
        experiment_id: str
            Programmatically generated experiment id, can be reused to continue an existing experiment

        experiment_name: str
            Human chosen name for experiment

        Returns
        -------
        None
        """

        url = f"{self.url}/experiments/"
        response = requests.get(
            url,
            params={
                "experiment_id": experiment_id,
                "experiment_name": experiment_name,
            },
        )
        self.experiment_id = response.json()["experiment_id"]
        self.experiment_path = response.json()["experiment_path"]
        self.experiment_name = response.json()["experiment_name"]

    def start_run(
        self,
        workflow_file: Path,
        payload: Optional[Dict[Any, Any]] = None,
        simulate: bool = False,
        blocking: bool = True,
    ) -> Dict[Any, Any]:
        """Submits a workflow file to the server to be executed, and logs it in the overall event log.

        Parameters
        ----------
        workflow_file : str
           The path to the workflow file to be executed

        payload: Optional[Dict[Any, Any]]
            The input to the workflow

        simulate: bool
            Whether or not to use real robots

        Returns
        -------
        Dict
           The JSON portion of the response from the server, including the ID of the job as job_id
        """
        if payload is None:
            payload = {}
        assert workflow_file.exists(), f"{workflow_file} does not exist"
        url = f"{self.url}/runs/start"

        payload_path = Path("~/.wei/temp/payload.txt")
        payload_path.expanduser().parent.mkdir(parents=True, exist_ok=True)
        with open(payload_path.expanduser(), "w+") as payload_file_handle:
            json.dump(payload, payload_file_handle)

        with open(workflow_file, "r", encoding="utf-8") as workflow_file_handle:
            with open(payload_path.expanduser(), "rb") as payload_file_handle:
                params = {
                    "experiment_id": self.experiment_id,
                    "simulate": simulate,
                }
                response = requests.post(
                    url,
                    params=params,  # type: ignore
                    json=payload,
                    files={
                        "workflow": (
                            str(workflow_file),
                            workflow_file_handle,
                            "application/x-yaml",
                        ),
                        "payload": (
                            str("payload_file.txt"),
                            payload_file_handle,
                            "text",
                        ),
                    },
                )
        response_dict = self._return_response(response)
        if blocking:
            prior_status = None
            prior_index = None
            while True:
                run_info = self.query_run(response_dict["run_id"])
                status = run_info["status"]
                step_index = run_info["step_index"]
                if prior_status != status or prior_index != step_index:
                    if step_index < len(run_info["steps"]):
                        step_name = run_info["steps"][step_index]["name"]
                    else:
                        step_name = "Workflow End"
                    print()
                    print(
                        f"{run_info['name']} [{step_index}]: {step_name} ({run_info['status']})",
                        end="",
                        flush=True,
                    )
                else:
                    print(".", end="", flush=True)
                time.sleep(1)
                if run_info["status"] == WorkflowStatus.COMPLETED:
                    print()
                    break
                elif run_info["status"] == WorkflowStatus.FAILED:
                    print()
                    print(json.dumps(response.json(), indent=2))
                    break
                prior_status = status
                prior_index = step_index
            return run_info
        else:
            run_info = self.query_run(response_dict["run_id"])
            return run_info

    def await_runs(self, run_list: List[str]) -> Dict[Any, Any]:
        """
        Waits for all provided runs to complete, then returns results
        """
        results: Dict[str, Any] = {}
        while len(results.keys()) < len(run_list):
            for id in run_list:
                if id not in results:
                    run_status = self.query_run(id)
                    if (
                        run_status["status"] == "completed"
                        or run_status["status"] == "failure"
                    ):
                        results[id] = run_status
            time.sleep(1)
        return results

    def get_file(self, input_filepath: str, output_filepath: str) -> None:
        """Returns a file from the WEI experiment directory"""
        url = f"{self.url}/experiments/{self.experiment_id}/file"

        response = requests.get(url, params={"filepath": input_filepath})
        with open(output_filepath, "wb") as f:
            f.write(response.content)

    def query_run(self, run_id: str) -> Dict[Any, Any]:
        """Checks on a workflow run using the id given

        Parameters
        ----------

        job_id : str
           The id returned by the run_job function for this run

        Returns
        -------

        response: Dict
           The JSON portion of the response from the server"""

        url = f"{self.url}/runs/{run_id}/state"
        response = requests.get(url)

        return self._return_response(response)

    def get_run_log(self, run_id: str) -> Dict[Any, Any]:
        """Returns the log for this experiment as a string

        Parameters
        ----------

        None

        Returns
        -------

        response: Dict
           The JSON portion of the response from the server with the experiment log"""

        url = f"{self.url}/runs/" + run_id + "/log"
        response = requests.get(url)

        return self._return_response(response)

    def query_queue(self) -> Dict[Any, Any]:
        """Returns the queue info for this experiment as a string

        Parameters
        ----------

        None

        Returns
        -------

        response: Dict
           The JSON portion of the response from the server with the queue info"""
        url = f"{self.url}/queue/info"
        response = requests.get(url)

        if response.status_code != 200:
            return {"http_error": response.status_code}

        return self._return_response(response)

    def register_exp(self) -> Dict[Any, Any]:
        """Deprecated method for registering an experiment with the server

        Parameters
        ----------
        None

        Returns
        -------

        response: Dict
        The JSON portion of the response from the server"""
        warn(
            """
                This method is deprecated.
                Experiment registration is now handled when initializing the ExperimentClient.
                You can safely remove any calls to this function.
                """,
            DeprecationWarning,
            stacklevel=2,
        )
        return {"exp_dir": self.experiment_path}
