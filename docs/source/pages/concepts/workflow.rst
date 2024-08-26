=========
Workflows
=========

WEI Workflows define a sequence of steps that can be executed in a :doc:`./workcell`, typically as part of a larger experiment. Each step in a Workflow specifies an action to be performed on a given :doc:`./module`, with a given set of arguments. When the Workflow is submitted to WEI to be run on a Workcell, the Scheduler executes each step in sequence as the corresponding Module is available.

The Workflow File
==================

Workflows can be defined declaratively using a YAML file, which should conform with the :class:`wei.types.workflow_types.Workflow`.

In general, a workflow file consists of 3 parts:

- Metadata: defines information about the workflow as a whole
- Modules (Optional): lists the modules used in the workflow
- Flowdef: a sequence of steps to execute

As an example, consider the following Workflow file:

.. code-block:: yaml

    name: Example_Workflow
    metadata:
        author: Tobias Ginsburg, Kyle Hippe, Ryan D. Lewis
        info: Example workflow for WEI
        version: 0.2

    modules:
    - name: sleeper
    - name: webcam

    - name: Sleep workcell for t seconds
        module: sleeper
        action: sleep
        args:
            t: "payload.wait_time"
        comment: Sleep for payload.wait_time seconds before we take a picture

    - name: Take Picture
        module: webcam
        action: take_picture
        args:
            file_name: "experiment_result.jgp"


Payloads
========

A payload is a dictionary of values, supplied alongside a Workflow when it is submitted to WEI to be run. These values are used to parameterize the Workflow, allowing for more flexible and reusable Workflows.

When a payload is provided while starting a Workflow run, WEI will find each instance of the `payload.<key>` pattern in the Workflow and replace it with the corresponding value from the payload.

For example, if the workflow file contains the following step:

.. code-block:: yaml

    - name: Wait for t seconds
        module: sleeper
        action: sleep
        args:
            t: "payload.wait_time"

And the payload is ``{"wait_time": 5}``, then the step will be executed as if it were

.. code-block:: yaml

    - name: Wait for t seconds
        module: sleeper
        action: sleep
        args:
            t: "5"

Next Steps
==========

To learn how to write your own workflow file, see :doc:`/pages/how-to/workflow`.
