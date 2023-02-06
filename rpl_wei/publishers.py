from typing import Dict, Any
from rpl_wei.wei_workflow_base import WF_Client


class PilotPublisher:
    def __init__():
        pass

    @staticmethod
    def publish(run_info: Dict[str, Any]) -> bool:
        globus_data = {
            "run_id": run_info.get("run_id", None),
            "workcell": run_info.get("workcell", None),
            "workflow": run_info.get("workflow", None),
            "run_folder": run_info.get("run_folder", None),
            "search_index": run_info.get("search_index", None),
        }

        assert globus_data
        # print(globus_data)

        return True
