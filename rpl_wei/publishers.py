from rpl_wei.wei_workflow_base import WF_Client


class PilotPublisher:
    def __init__():
        pass

    @staticmethod
    def publish(run: WF_Client) -> bool:
        globus_data = {
            "run_id": run.run_id,
            "workcell": run.wc_file,
            "workflow": run.wf_file,
            "run_folder": run.run_log_dir,
            "search_index": run.workcell.search_index,
        }

        print(globus_data)

        return True
