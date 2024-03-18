"""Tests WEI location management"""

import asyncio
import json

import pytest
import yaml
from fastapi import UploadFile

from wei.core.data_classes import Workcell
from wei.core.state_manager import StateManager

# from wei.engine import Engine
from wei.routers.workflow_runs import start_run

from .test_base import TestWEI_Base


class TestWEI_Locations(TestWEI_Base):
    """Tests WEI location management"""

    @pytest.mark.skip(reason="Not working")
    def test_workflow_replace_locations(self):
        """Test to see if wei properly replaces location values"""
        from pathlib import Path

        state_manager = StateManager()
        state_manager.set_workcell(
            Workcell.from_yaml("workcell_defs/test_workcell.yaml")
        )
        workflow_config_path = Path("tests/test_workflow.yaml")
        workflow_def = yaml.safe_load(workflow_config_path.read_text())
        arg_before_replace = workflow_def["flowdef"][1]["args"]
        self.assertEqual(arg_before_replace["source"], "webcam.pos")
        self.assertEqual(arg_before_replace["target"], "webcam.pos")
        with open("test.json", "w") as f2:
            json.dump({}, f2)
        with open(workflow_config_path, "rb") as f:
            with open("test.json", "rb") as f2:
                file = UploadFile(f)
                file2 = UploadFile(f2)
                v = asyncio.run(
                    start_run(experiment_id="test", workflow=file, payload=file2)
                )

                response = json.loads(v.body)
                print(response)
                self.assertListEqual(
                    response["wf"]["steps"][1]["args"]["source"], [0, 0, 0, 0, 0, 0]
                )
                self.assertListEqual(
                    response["wf"]["steps"][1]["args"]["target"], [0, 0, 0, 0, 0, 0]
                )

    # @pytest.mark.skip(reason="Not working")
