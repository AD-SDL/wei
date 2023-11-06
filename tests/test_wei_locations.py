import yaml
from test_base import TestWEI_Base
from wei.config import Config
from argparse import Namespace
from wei.core.data_classes import WorkcellData
from wei.routers.runs import start_run
from fastapi import UploadFile
import asyncio
import json
from wei.core.state_manager import StateManager



class TestWEI_Locations(TestWEI_Base):
    def  test_workflow_replace_locations(self):
        from pathlib import Path
        
        #from wei.core.workflow import WorkflowRunner
        state_manager = StateManager()
        state_manager.set_workcell(WorkcellData.from_yaml("./test_workcell.yaml"))
        workflow_config_path = Path("test_workflow.yaml")
        workflow_def = yaml.safe_load(workflow_config_path.read_text())
        arg_before_replace = workflow_def["flowdef"][1]["args"]
        print(workflow_def)
        self.assertEqual(arg_before_replace["source"], "webcam.pos")
        self.assertEqual(arg_before_replace["target"], "webcam.pos")
        with open("test.json", 'w') as f2:
            json.dump({}, f2)
        with open(workflow_config_path, 'rb') as f:
          with open("test.json", 'rb') as f2:
           file = UploadFile(f)
           file2 = UploadFile(f2)
           v = asyncio.run(start_run(experiment_id="test", workflow=file, payload=file2))
           
           response = json.loads(v.body)
           self.assertListEqual(response["wf"]["steps"][1]["args"]["source"], [0, 0, 0, 0, 0, 0])
           self.assertListEqual(response["wf"]["steps"][1]["args"]["target"], [0, 0, 0, 0, 0, 0])
        
