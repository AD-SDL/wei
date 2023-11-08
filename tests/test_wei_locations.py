import asyncio
import json

import yaml
from fastapi import UploadFile
from test_base import TestWEI_Base

from wei.core.data_classes import WorkcellData
from wei.core.scheduler import Scheduler
from wei.core.state_manager import StateManager
from wei.routers.runs import get_run_status, start_run
from wei.engine import Engine

class TestWEI_Locations(TestWEI_Base):
    def test_workflow_replace_locations(self):
        from pathlib import Path

        state_manager = StateManager()
        state_manager.set_workcell(WorkcellData.from_yaml("tests/test_workcell.yaml"))
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


    def test_workflow_running(self):
        from pathlib import Path

        state_manager = StateManager()
        print(state_manager.state_lock())
        engine = Engine()
        state_manager.set_workcell(WorkcellData.from_yaml("tests/test_workcell.yaml"))
        workflow_config_path = Path("tests/test_workflow.yaml")
        workflow_def = yaml.safe_load(workflow_config_path.read_text())
        arg_before_replace = workflow_def["flowdef"][1]["args"]
        print(workflow_def)
        
        with open("test.json", 'w') as f2:
            json.dump({"test": 5}, f2)
        with open(workflow_config_path, "rb") as f:
            with open("test.json", "rb") as f2:
                file = UploadFile(f)
                file2 = UploadFile(f2)
                v = asyncio.run(
                    start_run(
                        experiment_id="test",
                        workflow=file,
                        payload=file2,
                        simulate=True,
                    )
                )

                response = json.loads(v.body)
                self.assertListEqual(
                    response["wf"]["steps"][1]["args"]["source"], [0, 0, 0, 0, 0, 0]
                )
                self.assertListEqual(
                    response["wf"]["steps"][1]["args"]["target"], [0, 0, 0, 0, 0, 0]
                )
        scheduler = Scheduler()
        print(state_manager.state_lock())
        scheduler.run_iteration()
        with state_manager.state_lock():
            print("testing here")
        
        v = get_run_status(response["run_id"])
        scheduler.run_iteration()
        print(state_manager.get_workflow_run(response["run_id"]))
        print("first")
        v = get_run_status(response["run_id"])
        scheduler.run_iteration()
        v = get_run_status(response["run_id"])
        print(v)
        with state_manager.state_lock():
            print("second")
        scheduler.run_iteration()
        # while  state_manager.get_workflow_run(response["run_id"]).step_index == 0:
        #     pass
        scheduler.run_iteration()
        scheduler.run_iteration()
        scheduler.run_iteration()
        with state_manager.state_lock():
            print("testing here")
        print(state_manager.get_workflow_run(response["run_id"]))
        print(state_manager.state_lock())
        print(v)
        raise('e')