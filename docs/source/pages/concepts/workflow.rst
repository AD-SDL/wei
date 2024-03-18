=========
Workflows
=========

TODO: Update

Workflows define a sequence of steps that can be executed in a Workcell to perform a specific task or set of tasks, typically as part of a larger experiment.

Workflows consist of a list of Steps, each of which define a specific action to be performed, on a given Module, with a given set of arguments. When the workflow is submitted to WEI to be run on a specific Workcell, the steps are executed in sequence as determined by the Scheduler.

The Workflow File
==================

Workflows can be defined declaratively using a YAML file, which should conform with the Workflow schema as defined in the `wei` package.


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

    flowdef:
    #This defines a step in the workflow. Each step represents an action on a single module
    #This is a human legible name for the step
    - name: Sleep workcell for t seconds
    #This defines which module the action will run on, in this case, a test node that simply sleeps for t seconds
        module: sleeper
    #This tells the module which action in its library to run, in this case grabbing a wellplate from one of the storage tower
        action: sleep
    #These arguments specify the parameters for the action above, in this case, which tower the arm will pull a plate from.
        args:
            t: "payload.wait_time"
    #This represents checks that will take place before the system runs, in this case, there are none specified
        checks: null
    #This is a place for additional notes
        comment: Sleep for 5 seconds before we take a picture

    - name: Take Picture
        module: webcam
        action: take_picture
        args:
            file_name: "payload.file_name"


Payloads
========

A payload is a dictionary of values, supplied alongside a Workflow when it is submitted to WEI to be run. These values are used to parameterize the Workflow, allowing for more flexible and reusable Workflows.

When a payload is provided as part of starting a Workflow run, WEI will find each instance of the `payload.<key>` pattern in the Workflow and replace it with the corresponding value from the payload.
