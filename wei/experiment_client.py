"""Contains the Experiment class that manages WEI flows and helps annotate the experiment run"""

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from warnings import warn

import requests

from wei.core.events import Events
from wei.types import Workflow, WorkflowStatus
from wei.types.base_types import PathLike
from wei.types.experiment_types import ExperimentDesign, ExperimentInfo


class ExperimentClient:
    """Methods for the running and logging of a WEI Experiment including running WEI workflows and logging"""

    def __init__(
        self,
        server_host: str,
        server_port: str,
        experiment_design: Optional[PathLike | ExperimentDesign] = None,
        experiment_id: Optional[str] = None,
        working_dir: Optional[PathLike] = None,
    ) -> None:
        """Initializes an Experiment, and creates its log files

        Parameters
        ----------
        server_host: str
            address for WEI server

        server_port: str
            port for WEI server

        experiment_name: str
            Human readable name for the experiment

        experiment_id: Optional[str]
            Programmatically generated experiment id, can be reused to continue an in-progress experiment

        working_dir: Optional[Union[str, Path]]
            The directory to resolve relative paths from. Defaults to the current working directory.

        """

        self.server_host = server_host
        self.server_port = server_port
        self.url = f"http://{self.server_host}:{self.server_port}"

        if isinstance(experiment_design, PathLike):
            self.experiment_design = ExperimentDesign.from_yaml(experiment_design)
        elif experiment_design:
            assert ExperimentDesign.model_validate(
                experiment_design
            ), "experiment_design is invalid"
            self.experiment_design = experiment_design
        else:
            assert (
                experiment_id is not None
            ), "ExperimentDesign is required unless continuing an existing experiment"

        if working_dir is None:
            self.working_dir = Path.cwd()
        else:
            self.working_dir = Path(working_dir)

        start_time = time.time()
        waiting = False
        while time.time() - start_time < 60:
            try:
                if experiment_id is None:
                    self._register_experiment()
                else:
                    self._continue_experiment(experiment_id)
                break
            except requests.exceptions.ConnectionError:
                if not waiting:
                    waiting = True
                    print("Waiting to connect to server...")
                time.sleep(1)

        self.events.start_experiment()

    def _register_experiment(self) -> None:
        """Registers a new experiment with the server

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
        response = requests.post(
            url,
            json=self.experiment_design.model_dump(mode="json"),
        )
        if not response.ok:
            response.raise_for_status()
        self.experiment_info = ExperimentInfo.model_validate(response.json())
        print(f"Experiment ID: {self.experiment_info.experiment_id}")

        self.events = Events(
            self.server_host,
            self.server_port,
            self.experiment_info.experiment_id,
        )

        self.events.start_experiment()

    def _continue_experiment(self, experiment_id) -> None:
        """Resumes an existing experiment with the server

        Parameters
        ----------
        experiment_id: str
            Programmatically generated experiment id, can be reused to continue an existing experiment

        Returns
        -------
        None
        """

        url = f"{self.url}/experiments/{experiment_id}"
        response = requests.get(url)
        if not response.ok:
            response.raise_for_status()
        self.experiment_info = ExperimentInfo.model_validate(response.json())

        self.events.continue_experiment()

    def validate_workflow(
        self,
        workflow_file: Path,
        payload: Optional[Dict[str, Any]] = None,
    ):
        """
        Submits a workflow file to the server to be validated
        """
        if payload is None:
            payload = {}
        assert workflow_file.exists(), f"{workflow_file} does not exist"
        url = f"{self.url}/runs/validate"

        with open(workflow_file, "r", encoding="utf-8") as workflow_file_handle:
            params = {
                "experiment_id": self.experiment_info.experiment_id,
                "payload": payload,
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
                },
            )
            if not response.ok:
                response.raise_for_status()
        return response

    def _get_files_from_workflow(
        self, workflow: Workflow, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Returns a dictionary of files from a workflow
        """
        files = {}
        for step in workflow.flowdef:
            if step.files:
                for file, path in step.files.items():
                    # * Try to get the file from the payload, if applicable
                    if str(path).startswith("payload."):
                        try:
                            try:
                                files[file] = payload[str(path).split(".")[1]]
                            except KeyError:
                                files[file] = payload[path]
                        except KeyError as e:
                            raise KeyError(
                                f"File '{file}' looks like a payload entry, but payload does not contain {path}"
                            ) from e
                    else:
                        files[file] = path
                    if not Path(files[file]).is_absolute():
                        files[file] = self.working_dir / files[file]
        return files

    def start_run(
        self,
        workflow_file: Path,
        payload: Optional[Dict[str, Any]] = None,
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
        workflow = Workflow.from_yaml(workflow_file)
        url = f"{self.url}/runs/start"
        files = self._get_files_from_workflow(workflow, payload)
        response = requests.post(
            url,
            data={
                "workflow": workflow.model_dump_json(),
                "experiment_id": self.experiment_info.experiment_id,
                "payload": json.dumps(payload),
                "simulate": simulate,
            },
            files={
                ("files", (str(file), open(path, "rb"))) for file, path in files.items()
            },
        )
        if not response.ok:
            response.raise_for_status()
        response_json = response.json()
        if blocking:
            prior_status = None
            prior_index = None
            while True:
                run_info = self.query_run(response_json["run_id"])
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
            run_info = self.query_run(response_json["run_id"])
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
        Path(output_filepath).parent.mkdir(parents=True, exist_ok=True)
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

        if response.ok:
            return response.json()
        else:
            response.raise_for_status()

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

        if response.ok:
            return response.json()
        else:
            response.raise_for_status()

    def register_exp(self) -> None:
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
