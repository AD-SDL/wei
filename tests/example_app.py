#!/usr/bin/env python3

from pathlib import Path

from wei import ExperimentClient
from wei.types.experiment_types import CampaignDesign, ExperimentDesign

def main() -> None:
    experiment = ExperimentDesign(
        experiment_name="Test_Experiment",
        experiment_description="An experiment for automated testing",
        email_addresses=[],
    )
    campaign = CampaignDesign(
        campaign_name="Test_Campaign",
        campaign_description="A campaign for automated testing",
    )
    exp = ExperimentClient(server_host="localhost", server_port="8000", experiment="01JJ2SZNDS15FYYCZ7J1RHJ09P", campaign="01JJ2SZNDAATJZSBJDMD8TMHYV", working_dir=Path(__file__).resolve().parent)
    exp._register_experiment(experiment_design=experiment)
    wf_path = Path(__file__).parent / "workflows" / "test_workflow.yaml"
    payload = {
        "delay": 20,
    }

    for _ in range(1):
        exp.start_run(wf_path.resolve(), payload=payload)
        

    # print("Base timeline for un-optimized camera communication: ", time_avg/10)
    # print(json.dumps(run_info, indent=2))


if __name__ == "__main__":
    main()



