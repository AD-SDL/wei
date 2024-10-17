===================
How-To: Experiments
===================

In order to use your WEI-powered automated workcell to run experiments, you will need to write an **Experiment Application**. This application will be responsible for submitting Workflows to the WEI server to run, logging Events, and retrieving data and results from the system. This guide will walk you through the process of writing an Experiment Application, and show you how to interact with the WEI system to run your experiments.

The ExperimentClient Class
==========================

The core of a WEI Experiment Application is the :class:`wei.experiment_client.ExperimentClient` class. This class provides a convenient interface to the WEI server's REST API, allowing you to easily create and manage Experiments, submit Workflows, log Events, and retrieve data and results. The ExperimentClient is designed to be easy to use, and provides a number of helper methods to simplify common tasks.

You can either create the client as a normal object, or use it as a context manager.

.. code-block:: python

        from wei.experiment_client import ExperimentClient

        # Create the client as a normal object
        experiment_client = ExperimentClient(experiment_name="ExampleExperiment")

        # Use the client as a context manager
        with ExperimentClient(experiment_name="ExampleExperiment") as experiment_client:
            # Do something with the client
            pass

The ExperimentClient class takes a number of different arguments, which allow you to customize its behavior.

- ``server_host``, which is the hostname or IP address of the WEI server you want to connect to. (Default: "localhost")
- ``server_port``, which is the port number of the WEI server you want to connect to. (Default: 8000)
- ``experiment_name``, which is the name of the Experiment you want to create or attach to. (Default: None). Note: you must provide an experiment name if you want to create a new Experiment; if you want to attach to an existing Experiment, you can omit this argument and pass in the existing experiment's ID instead (see below).
- ``experiment_id``, which is the ID of an existing Experiment you want to attach to. (Default: None). If you provide an experiment ID, the client will attach to that Experiment instead of creating a new one.
- ``working_dir``, which is the directory the client will use for any relative paths to files defined in Workflow definitions (Default: None).
- ``email_addresses``, which is a list of email addresses to notify for events like step failures. (Default: []).
- ``log_experiment_end_on_exit``, which is a boolean flag indicating whether to log the end of the experiment when the client's deconstructor is called. (Default: True). Set to False if you want to manually log the end of the experiment, such as when you know you'll want to resume the same experiment later.

Using Workflows
===============

You can easily submit workflows with the ExperimentClient by calling the :func:`wei.experiment_client.ExperimentClient.start_run` method. This method takes a Workflow definition as a string, and returns a Workflow Run object, which you can use to monitor the progress of the Workflow run and retrieve data points and results.

.. code-block:: python

    from pathlib import Path

    # Define a simple Workflow
    with ExperimentClient(experiment_name="ExampleExperiment") as experiment_client:

        wf_path = Path("example_workflow.yaml")

        # Submit the Workflow to the Experiment
        wf_run = experiment_client.start_run(
            workflow=wf_path,
            payload={"param1": 42, "param2": "hello"},
            simulate=False,
            blocking=True,
            raise_on_failed=True,
            raise_on_cancelled=True,
        )

        # Wait for the Workflow to finish
        wf_run.wait()

        # Get the results of the Workflow
        results = wf_run.get_results()

        print(results)
