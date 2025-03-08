#!/usr/bin/env python3
"""test experiment/workflow for workflow admin commands"""

from pathlib import Path

from wei import ExperimentClient
from wei.types.experiment_types import ExperimentDesign



def main() -> None:
    """
    Run test workflow for workflow Admin Actions. Multi-step workflow involving all modules.
    """
    experiment = ExperimentDesign(
        experiment_name="Test_Experiment",
        experiment_description="An experiment for automated testing",
        email_addresses=[],
    )
    exp = ExperimentClient(
        server_host="localhost",
        server_port="8000",
        experiment="01JJ2SZNDS15FYYCZ7J1RHJ09P",
        campaign="01JJ2SZNDAATJZSBJDMD8TMHYV",
        working_dir=Path(__file__).resolve().parent,
    )
<<<<<<< HEAD
=======
    exp = ExperimentClient(
        server_host="localhost",
        server_port="8000",
        experiment="01JJ2SZNDS15FYYCZ7J1RHJ09P",
        campaign="01JJ2SZNDAATJZSBJDMD8TMHYV",
        working_dir=Path(__file__).resolve().parent,
    )
>>>>>>> 43187f45132f15e130ab4858d7a01dfef4d895f4
    exp._register_experiment(experiment_design=experiment)
    wf_path = Path(__file__).parent / "workflows" / "test_workflow.yaml"
    payload = {
        "delay": 5,
    }

    for _ in range(1):
        exp.start_run(
            wf_path.resolve(), payload=payload, raise_on_cancelled=False, blocking=False
        )
<<<<<<< HEAD
=======

    # print("Base timeline for un-optimized camera communication: ", time_avg/10)
    # print(json.dumps(run_info, indent=2))
>>>>>>> 43187f45132f15e130ab4858d7a01dfef4d895f4


if __name__ == "__main__":
    main()
