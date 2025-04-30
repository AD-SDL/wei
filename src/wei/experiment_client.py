"""Contains the Experiment class that manages WEI flows and helps annotate the experiment run"""

import json
import time
import traceback
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import requests
from pydantic_extra_types.ulid import ULID
from rich import print
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from wei import __version__
from wei.core.workflow import insert_parameter_values
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
from wei.types.experiment_types import (
    Campaign,
    CampaignDesign,
    Experiment,
    ExperimentDesign,
)
from wei.utils import threaded_daemon


class ExperimentClient:
    """Methods for the running and logging of a WEI Experiment including running WEI workflows"""

    connected = False
    timeout = 10
    experiment_started = False

    """
    *****************
    Lifecycle Methods
    *****************
    """

    def __init__(
        self,
        server_host: str = "localhost",
        server_port: str = "8000",
        experiment: Optional[Union[ExperimentDesign, Experiment, str]] = None,
        campaign: Optional[Union[CampaignDesign, Campaign, str]] = None,
        working_dir: Optional[PathLike] = None,
        log_experiment_end_on_exit: bool = True,
        timeout=10,
    ) -> None:
        """Initializes an Experiment, and creates its log files

        Parameters
        ----------
        server_host: str
            address for WEI server

        server_port: str
            port for WEI server

        experiment: Optional[Union[ExperimentDesign, Experiment, str]]
            A new experiment design, or an existing experiment or experiment_id to continue

        campaign: Optional[Union[CampaignDesign, Campaign, str]]
            A new campaign design, or an existing campaign or campaign_id to associate with the experiment

        working_dir: Optional[Union[str, Path]]
            The directory to resolve relative paths from. Defaults to the current working directory.

        log_experiment_end_on_exit: bool
            Whether to log the end of the experiment when cleaning up the experiment
        """
        console = Console()

        self.server_host = server_host
        self.server_port = server_port
        self.url = f"http://{self.server_host}:{self.server_port}"
        self.log_experiment_end_on_exit = log_experiment_end_on_exit
        self.timeout = timeout
        self.experiment = experiment
        self.campaign = campaign
        self.working_dir = Path(working_dir) if working_dir else Path.cwd()

        if experiment:
            self.start_or_continue_experiment(experiment, campaign)

        with console.capture() as capture:
            console.print("url:", self.url)
            console.print("timeout:", self.timeout)
            console.print("working_dir:", self.working_dir)
            console.print(
                "log_experiment_end_on_exit:", self.log_experiment_end_on_exit
            )
            console.print("experiment:", self.experiment)
            console.print("campaign:", self.campaign)
        panel = Panel(
            Text.from_ansi(capture.get()), title="Experiment Client Configuration"
        )
        console.print(panel)

        if self.experiment:
            print(
                f'To continue this experiment, use [bold]experiment="{self.experiment.experiment_id}"[/bold] in the ExperimentClient constructor'
            )
        if self.campaign:
            print(
                f'To continue this campaign, use [bold]campaign="{self.campaign.campaign_id}"[/bold] in the ExperimentClient constructor'
            )

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

    def _connect_to_server(self):
        """Ensures the server is reachable, and waits for it to be available"""
        if not self.connected:
            start_time = time.time()
            while time.time() - start_time < self.timeout and not self.connected:
                try:
                    requests.get(f"{self.url}/up")
                    self.connected = True
                    break
                except requests.exceptions.ConnectionError:
                    if not self.connected:
                        print("Waiting to connect to server...")
                    time.sleep(1)
            if not self.connected:
                raise TimeoutError(
                    "Timed out while attempting to connect with WEI server. Check that your server is running and the server_host and server_port are correct."
                )
        server_version = requests.get(f"{self.url}/version").json()["version"]
        if server_version != __version__:
            warnings.warn(
                message=f"WEI Server version {server_version} does not match client's WEI library version {__version__}!",
                category=UserWarning,
                stacklevel=1,
            )

    def start_or_continue_experiment(
        self,
        experiment: Union[ExperimentDesign, Experiment, str],
        campaign: Optional[Union[CampaignDesign, Campaign, str]] = None,
    ):
        """Creates a new experiment, or continues an existing experiment

        Parameters
        ----------
        experiment: Union[ExperimentDesign, Experiment, str]
            A new experiment design, or an existing experiment or experiment_id to continue

        campaign: Optional[Union[CampaignDesign, Campaign, str]]
            A new campaign design, or an existing campaign or campaign_id to associate with the experiment

        Returns
        -------
        None
        """
        self._connect_to_server()

        if isinstance(campaign, ULID) or isinstance(campaign, str):
            self.campaign = self._get_campaign(campaign)
        elif isinstance(campaign, Campaign):
            self.campaign = self._get_campaign(campaign.campaign_id)
        elif isinstance(campaign, CampaignDesign):
            self._register_campaign(campaign)
        elif campaign is not None:
            raise ValueError(
                "Campaign must be of type Campaign, CampaignDesign, or a ULID campaign_id"
            )

        if isinstance(experiment, ULID) or isinstance(experiment, str):
            self._continue_experiment(experiment)
        elif isinstance(experiment, Experiment):
            self._continue_experiment(experiment.experiment_id)
        elif isinstance(experiment, ExperimentDesign):
            if self.campaign:
                experiment.campaign_id = self.campaign.campaign_id
            self._register_experiment(experiment)
        elif experiment is not None:
            raise ValueError(
                "Experiment must be of type Experiment, ExperimentDesign, or a ULID experiment_id"
            )

        if self.experiment.campaign_id:
            self.campaign = self._get_campaign(self.experiment.campaign_id)

        self.experiment_started = True
        self.check_in()

    def _register_experiment(self, experiment_design: ExperimentDesign) -> None:
        """Registers a new experiment with the server

        Parameters
        ----------
        experiment_design: ExperimentDesign
            The design of the new experiment to register

        Returns
        -------
        None
        """
        self._connect_to_server()

        url = f"{self.url}/experiments/"
        response = requests.post(
            url,
            json=experiment_design.model_dump(mode="json"),
        )
        if not response.ok:
            response.raise_for_status()
        self.experiment = Experiment.model_validate(response.json())

        self.log_event(ExperimentStartEvent(experiment=self.experiment))

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
        self._connect_to_server()

        url = f"{self.url}/experiments/{str(experiment_id)}"
        response = requests.get(url)
        if not response.ok:
            response.raise_for_status()
        self.experiment = Experiment.model_validate(response.json())

        self.log_event(ExperimentContinueEvent(experiment=self.experiment))

    def _register_campaign(self, campaign_design: CampaignDesign) -> None:
        """Registers a new campaign with the server

        Parameters
        ----------
        campaign_design: CampaignDesign
            The design of a new Campaign

        Returns
        -------
        None
        """
        self._connect_to_server()

        url = f"{self.url}/campaigns/"
        response = requests.post(
            url,
            json=campaign_design.model_dump(mode="json"),
        )
        if not response.ok:
            response.raise_for_status()
        self.campaign = Campaign.model_validate(response.json())

    def _get_campaign(self, campaign_id: str) -> Campaign:
        """Returns the campaign details for the given campaign id

        Parameters
        ----------
        campaign_id: str
            Programmatically generated campaign id

        Returns
        -------
        Campaign
            The campaign details
        """
        self._connect_to_server()

        url = f"{self.url}/campaigns/{campaign_id}"
        response = requests.get(url)
        if not response.ok:
            response.raise_for_status()
        return Campaign.model_validate(response.json())

    @threaded_daemon
    def check_in(self):
        """Checks in with the server to let it know the experiment is still running"""
        self._connect_to_server()
        while True:
            try:
                response = requests.post(
                    f"http://{self.server_host}:{self.server_port}/experiments/{self.experiment.experiment_id}/check_in"
                )
                if not response.ok:
                    response.raise_for_status()
            except Exception:
                traceback.print_exc()
                pass
            time.sleep(10)

    def _check_experiment(self):
        """Checks that the experiment has been created"""
        if self.experiment_started is None:
            if self.experiment is None:
                raise ValueError(
                    "Experiment has not been set. Please assign a valid experiment before performing this action."
                )
            else:
                self.start_or_continue_experiment(self.experiment, self.campaign)

    """
    ****************
    Workflow Methods
    ****************
    """

    def start_run(
        self,
        workflow: Union[Workflow, PathLike],
        payload: Optional[Dict[str, Any]] = None,
        parameters: Optional[Dict[str, Any]] = {},
        simulate: bool = False,
        blocking: bool = True,
        validate_only: bool = False,
        raise_on_failed: bool = True,
        raise_on_cancelled: bool = True,
    ) -> WorkflowRun:
        """Submits a workflow file to the server to be executed, and logs it in the overall event log.

        Parameters
        ----------
        workflow : str
           A workflow definition, or path to a workflow definition file

        payload: Optional[Dict[str, Any]]
            Arguments to the workflow

        simulate: bool = False
            Whether or not to run the workflow purely simulated

        blocking: bool = True
            Whether to wait for the workflow to complete before returning

        validate_only: bool = False
            Whether to only validate the workflow without actually running it

        raise_on_failed: bool = True
            Whether to raise an exception if the workflow fails.

        raise_on_cancelled: bool = True
            Whether to raise an exception if the workflow is cancelled.

        Returns
        -------
        WorkflowRun
           Information about the run that was started
        """
        self._connect_to_server()
        self._check_experiment()
        if payload is not None:
            warnings.warn(
                message="Payload is deprecated, use parameters and $ insertion syntax instead",
                category=UserWarning,
                stacklevel=1,
            )
        else:
            payload = {}
        if isinstance(workflow, str) or isinstance(workflow, Path):
            workflow = Path(workflow).expanduser().resolve()
            assert workflow.exists(), f"Workflow file {workflow} does not exist"
            workflow = Workflow.from_yaml(workflow)
        Workflow.model_validate(workflow)
        insert_parameter_values(workflow, parameters)
        url = f"{self.url}/runs/start"
        files = self._extract_files_from_workflow(workflow, payload)
        response = requests.post(
            url,
            data={
                "workflow": workflow.model_dump_json(),
                "experiment_id": self.experiment.experiment_id,
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
            wf_run = self.query_run(response_json["run_id"])
        else:
            prior_status = None
            prior_index = None
            while True:
                wf_run = self.query_run(response_json["run_id"])
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
                if wf_run.status in [
                    WorkflowStatus.COMPLETED,
                    WorkflowStatus.FAILED,
                    WorkflowStatus.CANCELLED,
                ]:
                    print("EXP_CLIENT: break, ", wf_run.status)
                    break
                prior_status = status
                prior_index = step_index
        if wf_run.status == WorkflowStatus.FAILED and raise_on_failed:
            raise WorkflowFailedException(
                f"Workflow {wf_run.name} ({wf_run.run_id}) failed on step {wf_run.step_index}: '{wf_run.steps[wf_run.step_index].name}'."
            )
        if wf_run.status == WorkflowStatus.CANCELLED and raise_on_cancelled:
            raise WorkflowFailedException(
                f"Workflow {wf_run.name} ({wf_run.run_id}) was cancelled on step {wf_run.step_index}: '{wf_run.steps[wf_run.step_index].name}."
            )
        print()
        print(wf_run)
        return wf_run

    def validate_workflow(
        self,
        workflow: Union[Workflow, PathLike],
        payload: Optional[Dict[str, Any]] = None,
    ):
        """
        Submits a workflow file to the server to be validated

        Parameters
        ----------
        workflow : Union[Workflow, PathLike]
           A workflow definition, or path to a workflow definition file

        payload: Optional[Dict[str, Any]]
            Arguments to the workflow
        """
        self._connect_to_server()
        self._check_experiment()
        return self.start_run(
            workflow=workflow,
            payload=payload,
            validate_only=True,
        )

    def await_runs(self, run_ids: List[Union[str, ULID]]) -> Dict[str, WorkflowRun]:
        """
        Waits for all provided runs to complete, then returns a dictionary of their results
        """
        self._connect_to_server()
        self._check_experiment()
        results: Dict[str, WorkflowRun] = {}
        while len(results.keys()) < len(run_ids):
            for id in run_ids:
                if id not in results:
                    wf_run = self.query_run(id)
                    if not wf_run.status.is_active:
                        results[id] = wf_run
            time.sleep(1)
        return results

    def query_run(self, run_id: Union[str, ULID]) -> WorkflowRun:
        """Checks on a workflow run using the id given

        Parameters
        ----------

        run_id : str
           The id returned by the run_job function for this run

        Returns
        -------

        response: Dict
           The JSON portion of the response from the server"""

        url = f"{self.url}/runs/{run_id}"
        response = requests.get(url)

        if response.ok:
            return WorkflowRun(**response.json())
        else:
            response.raise_for_status()

    get_run = query_run

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

    """
    *****************
    Datapoint Methods
    *****************
    """

    def create_datapoint(self, datapoint: DataPoint):
        """Creates a new datapoint attached to the experiment"""

        if datapoint.experiment_id is None:
            datapoint.experiment_id = self.experiment.experiment_id
        if datapoint.campaign_id is None:
            datapoint.campaign_id = self.experiment.campaign_id
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
        url = f"{self.url}/{self.experiment.experiment_id}/data"
        response = requests.get(url)
        if response.ok:
            return response.json()

    """
    Event Logging Methods
    """

    def log_event(
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
        event.experiment_id = self.experiment.experiment_id
        url = f"{self.url}/events/"
        response = requests.post(
            url,
            json=event.model_dump(mode="json"),
        )
        if response.ok:
            return Event.model_validate(response.json())
        else:
            response.raise_for_status()

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
        return self.log_event(ExperimentEndEvent(experiment=self.experiment))

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
        return self.log_event(decision)

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
        return self.log_event(comment)

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
        return self.log_event(local_compute)

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
        return self.log_event(globus_compute)

    def log_gladier_flow(
        self,
        flow_name: str,
        flow_id: Any,
    ) -> Event:
        """Logs a Gladier flow in the experiment log"""

        gladier_flow = GladierFlowEvent(flow_name=flow_name, flow_id=flow_id)
        return self.log_event(gladier_flow)

    def log_loop_start(self, loop_name: str) -> Event:
        """Logs the start of a loop in the experiment log"""

        loop_start = LoopStartEvent(loop_name=loop_name)
        return self.log_event(loop_start)

    """
    ***************
    Private Methods
    ***************
    """

    def get_workcell_state(self) -> dict:
        """
        Fetches the current state of the workcell from the server.

        Returns
        -------
        dict
            A dictionary containing the current state of the workcell

        Raises
        ------
        requests.exceptions.RequestException
            If there's an error communicating with the server
        """
        self._connect_to_server()

        state_url = f"{self.url}/wc/state"
        state_response = requests.get(state_url)
        state_response.raise_for_status()

        return state_response.json()

    """
    Deprecated Methods
    """

    def list_wf_files(self, run_id: str) -> Any:
        """Returns a list of files from the WEI experiment run directory"""
        warnings.warn(
            "The method list_wf_files is deprecated. Please use the new datapoints functionality instead.",
            DeprecationWarning,
            stacklevel=1,
        )
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
        warnings.warn(
            "The method get_wf_result_file is deprecated. Please use save_datapoint_value instead.",
            DeprecationWarning,
            stacklevel=1,
        )
        url = f"{self.url}/runs/{run_id}/file"

        response = requests.get(url, params={"filename": filename})

        Path(output_filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(output_filepath, "wb") as f:
            f.write(response.content)
        return output_filepath

    def wait_for_workflow(
        self, workflow: Union[WorkflowRun, str, ULID], polling_interval: float = 1.0
    ) -> WorkflowRun:
        """
        Waits for a workflow to reach a terminal state (COMPLETED, FAILED, or CANCELLED).

        Parameters
        ----------
        workflow : Union[WorkflowRun, str, ULID]
            The workflow run object, run_id, or ULID to wait for.
        polling_interval : float, optional
            The time in seconds to wait between status checks. Defaults to 1.0 second.

        Returns
        -------
        WorkflowRun
            The final state of the workflow run.

        Raises
        ------
        ValueError
            If the provided workflow is invalid.
        """
        self._connect_to_server()
        self._check_experiment()

        if isinstance(workflow, WorkflowRun):
            run_id = workflow.run_id
        elif isinstance(workflow, (str, ULID)):
            run_id = str(workflow)
        else:
            raise ValueError(
                "Invalid workflow type. Expected WorkflowRun, str, or ULID."
            )

        while True:
            wf_run = self.query_run(run_id)
            if wf_run.status in [
                WorkflowStatus.COMPLETED,
                WorkflowStatus.FAILED,
                WorkflowStatus.CANCELLED,
            ]:
                return wf_run
            time.sleep(polling_interval)
