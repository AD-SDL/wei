=========
Workflows
=========

WEI Workflows define a sequence of steps that can be executed in a :doc:`./workcell`, typically as part of a larger experiment. Each step in a Workflow specifies an action to be performed on a given :doc:`./module`, with a given set of arguments. When the Workflow is submitted to WEI to be run on a Workcell, the Scheduler executes each step in sequence as the corresponding Module is available.

The Workflow File
==================

Workflows can be defined declaratively using a YAML file, which should conform with the :class:`wei.types.workflow_types.Workflow`.

In general, a workflow file consists of the following parts:

- Name: the name of the workflow
- Metadata: defines information about the workflow as a whole
- Modules (Optional): lists the modules used in the workflow
- Parameters: defines the parameters that can be used in the workflow (and optionally their default values)
- Flowdef: a sequence of Steps to execute

As an example, consider the following Workflow file:

.. code-block:: yaml

    name: Example_Workflow
    metadata:
        author: Tobias Ginsburg, Kyle Hippe, Ryan D. Lewis
        info: Example workflow for WEI
        version: 0.2

    parameters:
        - name: wait_time
          default: 5

    flowdef:
        - name: Delay
            module: utilities
            action: delay
            args:
                seconds: $wait_time
            comment: Delay for $wait_time seconds before we take a picture

        - name: Take Picture
            module: camera
            action: take_picture
            comment: Takes a picture with the camera

Steps
=====

Each step in a Workflow is a dictionary that specifies, at the very least, the name of the step, the action to be performed, and the module on which the action should be performed. The step may also include a comment, which is a human-readable description of the step.

Each module supports a specific set of actions. You can find the list of supported actions for each module in the module's ``/about`` interface, on the Dashboard, or in the documentation/source code.

Many actions have arguments (``args``) that must be provided in order to execute the action. These arguments are specified as key-value pairs in the step dictionary. The value of each argument can be a string, a number, or any other JSON serializable value.

In addition, some actions may accept files as arguments. These arguments are specified as filepaths in a separate ``files`` dictionary within the step, and are automatically uploaded to the WEI server when the workflow is submitted. The filepaths in the dictionary must either be absolute paths, or relative paths to the ``working_dir`` of your ExperimentClient.

Parameters
==========

Parameters are values that can be set when a job is submitted, allowing for more flexible and reusable Workflows.

Parameters are specified in the ``parameters`` section of the workflow file, and can optionally include a ``default`` value. They can be referenced anywhere in the flowdef using the ``$parameter_name`` or ``${parameter_name}`` syntax.

For example, if the workflow file contains the following step:

.. code-block:: yaml

    - name: Delay Workflow
        module: utilities
        action: delay
        args:
            seconds: $wait_time
        comment: Delay for $wait_time seconds

And you pass in the parameters as ``{"wait_time": 10}``, then the step will be executed as if it were

.. code-block:: yaml

    - name: Delay Workflow
        module: utilities
        action: delay
        args:
            seconds: 10
        comment: Delay for 10 seconds

Next Steps
==========

To learn how to write your own workflow file, see :doc:`/pages/how-to/workflow`.
