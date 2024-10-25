"""Automated testing for the admin API"""

import time
from pathlib import Path

import requests

from wei.types.module_types import ModuleStatus
from wei.types.workflow_types import WorkflowStatus

from .test_base import TestWEI_Base

# Constants
SERVER_URL = "http://test_wei_server:8000"
ADMIN_URL = f"{SERVER_URL}/admin"
WORKFLOW = Path(__file__).parent / "workflows" / "test_admin_workflow.yaml"
POLL_INTERVAL = 0.5  # seconds
TIMEOUT = 10  # seconds


class TestWEI_AdminCommands(TestWEI_Base):
    """Tests WEI admin command functionality"""

    def get_module_statuses(self):
        """Get the status of all modules in the workcell"""
        return {
            module["name"]: module["state"]["status"]
            for module in self.experiment_client.get_workcell_state()[
                "modules"
            ].values()
        }

    def wait_for_condition(self, condition_func, timeout=TIMEOUT):
        """Wait for a condition to be true, with a timeout"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if condition_func():
                return True
            time.sleep(POLL_INTERVAL)
        return False

    def test_pause_resume(self):
        """Test pausing and resuming the workcell"""
        # Start a workflow
        run_info = self.experiment_client.start_run(
            workflow=WORKFLOW,
            payload={"wait_time": 30},
            blocking=False,
        )

        # Wait for the workflow to start
        assert self.wait_for_condition(
            lambda: self.experiment_client.get_run(run_info.run_id).status
            == WorkflowStatus.RUNNING
        )

        # Pause the workcell
        response = requests.post(f"{ADMIN_URL}/pause")
        assert response.status_code == 200

        # Check if all modules are paused
        assert self.wait_for_condition(
            lambda: all(
                status[ModuleStatus.PAUSED]
                for module, status in self.get_module_statuses().items()
                if module != "utilities"
            )
        )

        # Resume the workcell
        response = requests.post(f"{ADMIN_URL}/resume")
        assert response.status_code == 200

        # Check if all modules are running or ready
        assert self.wait_for_condition(
            lambda: all(
                status[ModuleStatus.RUNNING] or status[ModuleStatus.READY]
                for status in self.get_module_statuses().values()
            )
        )

        # Check that the workflow is resumed
        assert self.wait_for_condition(
            lambda: self.experiment_client.get_run(run_info.run_id).status
            in [WorkflowStatus.COMPLETED, WorkflowStatus.RUNNING]
        )

    def test_cancel(self):
        """Test cancelling a workflow"""
        # Start a workflow
        run_info = self.experiment_client.start_run(
            workflow=WORKFLOW,
            payload={"wait_time": 30},
            blocking=False,
        )

        # Wait for the workflow to start
        assert self.wait_for_condition(
            lambda: self.experiment_client.get_run(run_info.run_id).status
            == WorkflowStatus.RUNNING
        )

        # Cancel the workcell
        response = requests.post(f"{ADMIN_URL}/cancel")
        assert response.status_code == 200

        # Check if the workflow is cancelled
        assert self.wait_for_condition(
            lambda: self.experiment_client.get_run(run_info.run_id).status
            == WorkflowStatus.CANCELLED
        )

        # Check if all modules are cancelled
        assert self.wait_for_condition(
            lambda: all(
                status[ModuleStatus.CANCELLED]
                for module, status in self.get_module_statuses().items()
                if module != "utilities"
            )
        )

        # Send a reset admin command
        response = requests.post(f"{ADMIN_URL}/reset")
        assert response.status_code == 200

        # Check if all modules are ready
        assert self.wait_for_condition(
            lambda: all(
                status[ModuleStatus.READY]
                for status in self.get_module_statuses().values()
            )
        )
        assert self.wait_for_condition(
            lambda: not any(
                status[ModuleStatus.CANCELLED]
                for status in self.get_module_statuses().values()
            )
        )

    def test_reset(self):
        """Test resetting the workcell"""
        # Reset the workcell
        response = requests.post(f"{ADMIN_URL}/reset")
        assert response.status_code == 200

        # Check if all modules are ready
        assert self.wait_for_condition(
            lambda: all(
                status[ModuleStatus.READY]
                for status in self.get_module_statuses().values()
            )
        )

    def test_lock_unlock(self):
        """Test locking and unlocking the workcell"""
        # Lock the workcell
        response = requests.post(f"{ADMIN_URL}/lock")
        assert response.status_code == 200

        # Check if all modules are locked
        assert self.wait_for_condition(
            lambda: all(
                status[ModuleStatus.LOCKED]
                for module, status in self.get_module_statuses().items()
                if module != "utilities"
            )
        )

        # Try to start a workflow (should fail)
        run_info = self.experiment_client.start_run(
            workflow=WORKFLOW,
            payload={"wait_time": 5},
            blocking=False,
        )

        # Make sure the scheduler has time to process
        assert self.wait_for_condition(
            lambda: self.experiment_client.get_run(run_info.run_id).status
            == WorkflowStatus.QUEUED
        )

        # Unlock the workcell
        response = requests.post(f"{ADMIN_URL}/unlock")
        assert response.status_code == 200

        # Check if all modules are unlocked
        assert self.wait_for_condition(
            lambda: not any(
                status[ModuleStatus.LOCKED]
                for status in self.get_module_statuses().values()
            )
        )

        # Check if the workflow starts after unlock
        assert self.wait_for_condition(
            lambda: self.experiment_client.get_run(run_info.run_id).status
            in [
                WorkflowStatus.COMPLETED,
                WorkflowStatus.RUNNING,
                WorkflowStatus.IN_PROGRESS,
            ]
        )

    def test_safety_stop(self):
        """Test that the safety stop functionality works"""
        # Start a workflow
        run_info = self.experiment_client.start_run(
            workflow=WORKFLOW,
            payload={"wait_time": 30},
            blocking=False,
        )

        # Wait for the workflow to start
        assert self.wait_for_condition(
            lambda: self.experiment_client.get_run(run_info.run_id).status
            == WorkflowStatus.RUNNING
        )

        # Trigger safety stop
        response = requests.post(f"{ADMIN_URL}/safety_stop")
        assert response.status_code == 200

        # Check if all modules are in error state or paused
        assert self.wait_for_condition(
            lambda: all(
                status[ModuleStatus.ERROR]
                or status[ModuleStatus.PAUSED]
                or status[ModuleStatus.LOCKED]
                for module, status in self.get_module_statuses().items()
                if module != "utilities"
            )
        )

        # Check if the workflow is cancelled
        assert self.wait_for_condition(
            lambda: self.experiment_client.get_run(run_info.run_id).status
            in [WorkflowStatus.CANCELLED, WorkflowStatus.FAILED]
        )

        # Reset the workcell to recover from safety stop
        requests.post(f"{ADMIN_URL}/reset")

        # Check if all modules are ready
        assert self.wait_for_condition(
            lambda: all(
                status[ModuleStatus.READY]
                for status in self.get_module_statuses().values()
            )
        )
