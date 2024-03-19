===========
Experiments
===========

TODO: Update

An Experiment, in the context of WEI, is a set of related Workflow runs. Every time a Workflow is run, it is associated with an Experiment, and any data, files, or results that are generated are associated with that Experiment. This allows you to easily track and manage the results of your Workflow runs.

The `wei` python package provides an ExperimentClient class to easily manage Experiments, submit Workflows to be run as part of an experiment, and get results from that experiment. While all this can be done using the `wei_server`'s REST API, the ExperimentClient provides a convenient wrapper.

We refer to any program or application using the ExperimentClient or the REST API as an "experiment application". These experiment applications are the primary way to interact with the WEI system, and allow WEI user's to leverage the capabilities of a WEI Workcell to run their Workflows, while giving them the flexibility to integrate their own custom code, and logic. This is especially useful for dynamic or closed-loop AI experiments, where the same Workflow may be run multiple times with different parameters, or where the results of one Workflow run may be used to inform the parameters of the next run.
