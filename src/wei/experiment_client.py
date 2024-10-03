"""Contains the Experiment class that manages WEI flows and helps annotate the experiment run"""

import json
import time
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import requests

from wei.types import Workflow, WorkflowRun, WorkflowStatus
from wei.types.base_types import PathLike
from wei.types.datapoint_types import DataPoint
from wei.types.event_types import (
    CommentEvent,
    DecisionEvent,
    Event,
    ExperimentContinueEvent,
    ExperimentEndEvent,
    ExperimentStartEvent,
    GladierFlowEvent,
    GlobusComputeEvent,
    LocalComputeEvent,
    LoopStartEvent,
)
from wei.types.exceptions import WorkflowFailedException
from wei.types.experiment_types import Experiment, ExperimentDesign
from wei.utils import threaded_daemon


class ExperimentClient:
    """Methods for the running and logging of a WEI Experiment including running WEI workflows and logging"""

    def __init__(
        self,
        server_host: str,
        server_port: str,
        experiment_name: Optional[str] = None,
        experiment_id: Optional[str] = None,
        campaign_id: Optional[str] = None,
        description: Optional[str] = None,
        working_dir: Optional[PathLike] = None,
        email_addresses: List[str] = [],
        log_experiment_end_on_exit: bool = True,
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

        email_addresses: Optional[List[str]]
            List of email addresses to send notifications at the end of the experiment

        log_experiment_end_on_exit: bool
            Whether to log the end of the experiment when cleaning up the experiment
        """

        self.server_host = server_host
        self.server_port = server_port
        self.url = f"http://{self.server_host}:{self.server_port}"
        self.experiment_id = experiment_id
        self.email_addresses = email_addresses
        self.log_experiment_end_on_exit = log_experiment_end_on_exit

        if experiment_name is None:
            assert (
                experiment_id is not None
            ), "Experiment Name is required unless continuing an existing experiment"

        self.experiment_design = ExperimentDesign(
            experiment_name=experiment_name,
            campaign_id=campaign_id,
            description=description,
            email_addresses=email_addresses,
        )
        print(f"""
server_host: {self.server_host}
server_port: {self.server_port}
url: {self.url}
experiment_design: {self.experiment_design.model_dump_json(indent=2)}
              """)
        self.experiment_info = None

        if working_dir is None:
            self.working_dir = Path.cwd()
        else:
            self.working_dir = Path(working_dir)

        start_time = time.time()
        waiting = False
        while time.time() - start_time < 10:
            try:
                if experiment_id is None:
                    self._register_experiment()
                else:
                    self._continue_experiment(experiment_id)
                waiting = False
                break
            except requests.exceptions.ConnectionError:
                if not waiting:
                    waiting = True
                    print("Waiting to connect to server...")
                time.sleep(1)
        if waiting:
            raise Exception(
                "Timed out while attempting to connect with WEI server. Check that your server is running and the server_host and server_port are correct."
            )
        self.check_in()

    @threaded_daemon
    def check_in(self):
        """Checks in with the server to let it know the experiment is still running"""
        while True:
            time.sleep(10)
            try:
                response = requests.post(
                    f"http://{self.server_host}:{self.server_port}/experiments/{self.experiment_id}/check_in"
                )
                if not response.ok:
                    response.raise_for_status()
            except Exception:
                traceback.print_exc()
                pass

    def __del__(self):
        """Logs the end of the experiment when cleaning up the experiment, if log_experiment_end_on_exit is True"""
        if self.log_experiment_end_on_exit:
            self.log_experiment_end()

    def __enter__(self):
        """Creates the experiment application context"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Logs the end of the experiment when exiting the experiment application context, if log_experiment_end_on_exit is True"""
        pass

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
        self.experiment_info = Experiment.model_validate(response.json())
        print(f"Experiment ID: {self.experiment_info.experiment_id}")
        self.experiment_id = self.experiment_info.experiment_id

        self._log_event(ExperimentStartEvent(experiment=self.experiment_info))

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
        self.experiment_info = Experiment.model_validate(response.json())

        self._log_event(ExperimentContinueEvent(experiment=self.experiment_info))

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

    def _extract_files_from_workflow(
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
                                files[f"{step.id}_{file}"] = payload[
                                    str(path).split(".")[1]
                                ]
                            except KeyError:
                                files[f"{step.id}_{file}"] = payload[path]
                        except KeyError as e:
                            raise KeyError(
                                f"File '{file}' looks like a payload entry, but payload does not contain {path}"
                            ) from e
                    else:
                        files[f"{step.id}_{file}"] = path
                    if not Path(files[f"{step.id}_{file}"]).is_absolute():
                        files[f"{step.id}_{file}"] = (
                            self.working_dir / files[f"{step.id}_{file}"]
                        )
                    step.files[file] = Path(files[f"{step.id}_{file}"]).name
        return files

    def _log_event(
        self,
        event: Event,
    ) -> Event:
        """Logs an event to the WEI event log

        Parameters
        ----------
        event : Event
            The event to log

        Returns
        -------
        Event
            The event that was logged
        """
        event.experiment_id = self.experiment_info.experiment_id
        url = f"{self.url}/events/"
        response = requests.post(
            url,
            json=event.model_dump(mode="json"),
        )
        if response.ok:
            return Event.model_validate(response.json())
        else:
            response.raise_for_status()

    def start_run(
        self,
        workflow: Union[Workflow, PathLike],
        payload: Optional[Dict[str, Any]] = None,
        simulate: bool = False,
        blocking: bool = True,
        raise_on_failed: bool = True,
        raise_on_cancelled: bool = True,
    ) -> WorkflowRun:
        """Submits a workflow file to the server to be executed, and logs it in the overall event log.

        Parameters
        ----------
        workflow : str
           A workflow definition, or path to a workflow definition file

        payload: Optional[Dict[Any, Any]]
            The input to the workflow

        simulate: bool
            Whether or not to use real robots

        raise_on_failed: bool = True
            Whether to raise an exception if the workflow fails.

        Returns
        -------
        WorkflowRun
           Information about the run that was started
        """
        if payload is None:
            payload = {}
        if isinstance(workflow, str) or isinstance(workflow, Path):
            workflow = Path(workflow).expanduser().resolve()
            assert workflow.exists(), f"Workflow file {workflow} does not exist"
            workflow = Workflow.from_yaml(workflow)
        Workflow.model_validate(workflow)
        url = f"{self.url}/runs/start"
        files = self._extract_files_from_workflow(workflow, payload)
        response = requests.post(
            url,
            data={
                "workflow": workflow.model_dump_json(),
                "experiment_id": self.experiment_info.experiment_id,
                "payload": json.dumps(payload),
                "simulate": simulate,
            },
            files={
                ("files", (str(Path(path).name), open(path, "rb")))
                for _, path in files.items()
            },
        )
        if not response.ok:
            response.raise_for_status()
        response_json = response.json()
        if not blocking:
            run_info = self.query_run(response_json["run_id"])
            wf_run = WorkflowRun(**run_info)
        else:
            prior_status = None
            prior_index = None
            while True:
                run_info = self.query_run(response_json["run_id"])
                wf_run = WorkflowRun(**run_info)
                status = wf_run.status
                step_index = wf_run.step_index
                if prior_status != status or prior_index != step_index:
                    if step_index < len(wf_run.steps):
                        step_name = wf_run.steps[step_index].name
                    else:
                        step_name = "Workflow End"
                    print()
                    print(
                        f"{wf_run.name} [{step_index}]: {step_name} ({wf_run.status})",
                        end="",
                        flush=True,
                    )
                else:
                    print(".", end="", flush=True)
                time.sleep(1)
                if wf_run.status == WorkflowStatus.COMPLETED:
                    print()
                    break
                elif wf_run.status in [
                    WorkflowStatus.FAILED,
                    WorkflowStatus.CANCELLED,
                ]:
                    print()
                    print(json.dumps(wf_run.model_dump(mode="json"), indent=2))
                    break
                prior_status = status
                prior_index = step_index
        if wf_run.status == WorkflowStatus.FAILED and raise_on_failed:
            raise WorkflowFailedException(
                f"Workflow {wf_run.name} ({wf_run.run_id}) failed."
            )
        if wf_run.status == WorkflowStatus.CANCELLED and raise_on_cancelled:
            raise WorkflowFailedException(
                f"Workflow {wf_run.name} ({wf_run.run_id}) was cancelled."
            )
        return wf_run

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

    def list_wf_files(self, run_id: str) -> Any:
        """Returns a list of files from the WEI experiment run directory"""
        url = f"{self.url}/runs/{run_id}/files"

        response = requests.get(url)
        return response.json()["files"]

    def get_wf_result_file(
        self,
        run_id: str,
        filename: str,
        output_filepath: str,
    ) -> Any:
        """Returns a file from the WEI experiment result directory"""
        url = f"{self.url}/runs/{run_id}/file"

        response = requests.get(url, params={"filename": filename})

        Path(output_filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(output_filepath, "wb") as f:
            f.write(response.content)
        return output_filepath

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

    def create_datapoint(self, datapoint: DataPoint):
        """Creates a new datapoint attached to the experiment"""

        if datapoint.experiment_id is None:
            datapoint.experiment_id = self.experiment_info.experiment_id
        if datapoint.campaign_id is None:
            datapoint.campaign_id = self.experiment_info.campaign_id
        url = f"{self.url}/data/"
        if datapoint.type == "local_file":
            with open(datapoint.path, "rb") as f:
                response = requests.post(
                    url,
                    files={"file": (datapoint.path, f)},
                    data={"datapoint": datapoint.model_dump_json()},
                )
        else:
            response = requests.post(
                url, data={"datapoint": datapoint.model_dump_json()}
            )
        if response.ok:
            return response.json()
        else:
            response.raise_for_status()

    def get_datapoint_info(self, datapoint_id: str) -> DataPoint:
        """Returns the metadata for the datapoint for the given id

        Parameters
        ----------

        datapoint_id : str
            The id of the datapoint to get

        Returns
        -------

        response: DataPoint
           The metadata for the requested datapoint"""
        url = f"{self.url}/data/" + datapoint_id + "/info"
        response = requests.get(url)
        if response.ok:
            return DataPoint.model_validate(response.json())
        response.raise_for_status()

    def get_datapoint_value(self, datapoint_id: str) -> Dict[str, Any] | bytes:
        """Returns the value of the datapoint for the given id

        Parameters
        ----------

        datapoint_id : str
            The id of the datapoint to get

        Returns
        -------

        response: Dict[str, Any] | bytes
           Either a json object (for Value Datapoints) or bytes object (for File Datapoints) containing the value of the requested datapoint"""
        url = f"{self.url}/data/" + datapoint_id
        response = requests.get(url)
        if response.ok:
            try:
                return response.json()
            except Exception:
                return response.content
        response.raise_for_status()

    def save_datapoint_value(self, datapoint_id: str, output_filepath: str) -> None:
        """Saves the datapoint for the given id to the specified file

        Parameters
        ----------
        datapoint_id : str
            The id of the datapoint to save
        output_filepath : str
            The path to save the datapoint to

        Returns
        -------
        None"""
        url = f"{self.url}/data/" + datapoint_id
        response = requests.get(url)
        if response.ok:
            try:
                with open(output_filepath, "w") as f:
                    f.write(str(response.json()["value"]))

            except Exception:
                Path(output_filepath).parent.mkdir(parents=True, exist_ok=True)
                with open(output_filepath, "wb") as f:
                    f.write(response.content)
        response.raise_for_status()

    def get_experiment_datapoints(self) -> Dict[str, DataPoint]:
        """
        returns a dictionary of the datapoints for this experiment.
        """
        url = f"{self.url}/{self.experiment_id}/data"
        response = requests.get(url)
        if response.ok:
            return response.json()

    def log_experiment_end(self) -> Event:
        """Logs the end of the experiment in the experiment log

        Parameters
        ----------

        None

        Returns
        -------
        Event
            The event that was logged
        """
        return self._log_event(ExperimentEndEvent(experiment=self.experiment_info))

    def log_decision(self, decision_name: str, decision_value: bool) -> Event:
        """Logs a decision in the experiment log

        Parameters
        ----------
        decision_name : str
            The name of the decision

        decision_value : bool
            The value of the decision

        Returns
        -------
        Event
            The event that was logged
        """
        decision = DecisionEvent(
            decision_name=decision_name, decision_value=decision_value
        )
        return self._log_event(decision)

    def log_comment(self, comment: str) -> Event:
        """Logs a comment in the experiment log

        Parameters
        ----------
        comment : str
            The comment to log

        Returns
        -------
        Event
            The event that was logged
        """
        comment = CommentEvent(comment=comment)
        return self._log_event(comment)

    def log_local_compute(
        self,
        function_name: str,
        args: Optional[List[Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        result: Optional[Any] = None,
    ) -> Event:
        """Logs a local computation in the experiment log

        Parameters
        ----------
        function_name : str
            The name of the function called

        args : List[Any]
            The positional arguments passed to the function

        kwargs : Dict[str, Any]
            The keyword arguments passed to the function

        Returns
        -------
        Event
            The event that was logged
        """
        local_compute = LocalComputeEvent(
            function_name=function_name, args=args, kwargs=kwargs, result=result
        )
        return self._log_event(local_compute)

    def log_globus_compute(
        self,
        function_name: str,
        args: Optional[List[Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        result: Optional[Any] = None,
    ) -> Event:
        """Logs a Globus computation in the experiment log"""

        globus_compute = GlobusComputeEvent(
            function_name=function_name, args=args, kwargs=kwargs, result=result
        )
        return self._log_event(globus_compute)

    def log_gladier_flow(
        self,
        flow_name: str,
        flow_id: Any,
    ) -> Event:
        """Logs a Gladier flow in the experiment log"""

        gladier_flow = GladierFlowEvent(flow_name=flow_name, flow_id=flow_id)
        return self._log_event(gladier_flow)

    def log_loop_start(self, loop_name: str) -> Event:
        """Logs the start of a loop in the experiment log"""

        loop_start = LoopStartEvent(loop_name=loop_name)
        return self._log_event(loop_start)
