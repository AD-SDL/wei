=================
How-To: Workflows
=================

Workflows are defined entirely within a single YAML file, with three main sections: ``metadata``, ``modules``, and ``flowdef``. Creating a new workflow is as simple as creating a new yaml file, typically in the ``workflows`` directory of your workcell, and filling out each of these sections.

Currently, a workflow is dependent on the specific workcell it will be run on: module names must correspond to the modules of that workcell, location aliases are replaced using the values specified in the workcell configuration file, and so forth.

Creating the Workflow File
===========================

A workflow file should conform to the :class:`wei.types.Workflow` specification.

Name
----

The name of the workflow is specified with a top-level ``name`` key. This is a human-readable string that will be used to identify the workflow in the system.


Example Name
^^^^^^^^^^^^

.. code-block:: yaml

    name: My_Workflow

Metadata
--------

The metadata section is a dictionary of key-value pairs that provide additional information about the workflow. This section is optional, and can be used to store any additional information about the workflow that you would like to keep track of.

For a complete breakdown of the metadata schema, see :class:`wei.types.Metadata`.


Example Workflow Metadata
^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: yaml

    metadata:
        author: Tobias Ginsburg, Kyle Hippe, Ryan D. Lewis
        info: Example workflow for WEI
        version: 0.2

Modules
-------

The modules section is simply a list of the names of modules that will be used in the workflow. This section is optional.

Example Module List
^^^^^^^^^^^^^^^^^^^

.. code-block:: yaml

    modules:
        - transfer
        - synthesis
        - measure

Parameters
----------

Parameters are values that can be set when a job is submitted, allowing for more flexible and reusable Workflows.

They support a ``default`` value, which will be used if the parameter is not provided when the workflow is run. If no default is provided, the parameter is required to be provided at runtime.

For a complete breakdown of the parameters schema, see :class:`wei.types.workflow_types.WorkflowParameters`.

Example Workflow Parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: yaml

    parameters:
      - name: foo
        default: 10
      - name: bar

Flow Definition
---------------

The flow definition is the heart of the workflow. It is a list of dictionaries, each of which represents a single step in the workflow.

Each step includes:

- The human-readable name of the step
- The name of the module that will be used to execute the step
- The desired action to be taken by that module
- Any arguments the module will need to execute the action (optional, this can be left out if the module does not require any arguments)
- Any files that the module will need to execute the action (optional, this can be left out if the module does not require any files).
- A comment that can thoroughly describe the step for readers of the workflow file.

For a complete breakdown of the step schema, see :class:`wei.types.Step`.

Example Flowdef
^^^^^^^^^^^^^^^

.. code-block:: yaml

    flowdef:
      - name: Get plate
        module: transfer
        action: transfer
        args:
            target: "transfer.pos"
        comment: Get a new plate

      - name: Transfer plate to synthesis
        module: transfer
        action: transfer
        args:
            source: transfer.pos
            target: synthesis.pos
        comment: put a plate in first position

      - name: Synthesize foobar
        module: synthesis
        action: synthesize
        args:
            foo: $foo
            bar: $bar
        files:
            protocol: ./protocols/foobar_protocol.py
        comment: Combines foo and bar to produce foobar, using foobar_protocol.yaml

      - name: Transfer sample to measure
        module: transfer
        action: transfer
        args:
            source: synthesis.pos
            target: measure.pos

      - name: Measure foobar
        module: measure
        action: measure
        comment: Measure the amount of foobar in the sample

      - name: Discard sample
        module: transfer
        action: transfer
        args:
            source: measure.pos
            target: wc.trash

Full Example
------------

.. code-block:: yaml

    name: My_Workflow
    metadata:
        author: Tobias Ginsburg, Kyle Hippe, Ryan D. Lewis
        info: Example workflow for WEI
        version: 0.2
    modules:
        - transfer
        - synthesis
        - measure
    parameters:
      - name: foo
        default: 10
      - name: bar
    flowdef:
      - name: Get plate
        module: transfer
        action: transfer
        args:
            target: "transfer.pos"
        comment: Get a new plate

      - name: Transfer plate to synthesis
        module: transfer
        action: transfer
        args:
            source: transfer.pos
            target: synthesis.pos
        comment: put a plate in first position

      - name: Synthesize foobar
        module: synthesis
        action: synthesize
        args:
            foo: $foo
            bar: $bar
        files:
            protocol: ./protocols/foobar_protocol.py
        comment: Combines foo and bar to produce foobar, using foobar_protocol.yaml

      - name: Transfer sample to measure
        module: transfer
        action: transfer
        args:
            source: synthesis.pos
            target: measure.pos

      - name: Measure foobar
        module: measure
        action: measure
        comment: Measure the amount of foobar in the sample

      - name: Discard sample
        module: transfer
        action: transfer
        args:
            source: measure.pos
            target: wc.trash

Programmatically Creating Workflows
===================================

Workflows can be created programmatically using the :class:`wei.types.workflow_types.Workflow` class. This class allows you to define a workflow without having to write out the YAML file. This can be useful for creating workflows in a python script, or for dynamically creating workflows based on some external input.

Example
^^^^^^^

.. code-block:: python

    from wei.types.workflow_types import Workflow, WorkflowParameter
    from wei.types.base_types import Metadata
    from wei.types.step_types import Step

    workflow = Workflow(
        name="MyWorkflow",
        metadata=Metadata(
            author="Tobias Ginsburg, Kyle Hippe, Ryan D. Lewis",
            info="Example workflow for WEI",
            version="0.2",
        ),
        modules=["transfer", "synthesis", "measure"],
        parameters=[
            WorkflowParameter(name="foo", default=10),
            WorkflowParameter(name="bar"),
        ],
        steps=[
            Step(name="Get plate", module="transfer", action="transfer", args={"target": "transfer.pos"}),
            Step(name="Transfer plate to synthesis", module="transfer", action="transfer", args={"source": "transfer.pos", "target": "synthesis.pos"}),
            Step(name="Synthesize foobar", module="synthesis", action="synthesize", args={"foo": "$foo", "bar": "$bar"}, files={"protocol": "./protocols/foobar_protocol.py"}),
            Step(name="Transfer sample to measure", module="transfer", action="transfer", args={"source": "synthesis.pos", "target": "measure.pos"}),
            Step(name="Measure foobar", module="measure", action="measure"),
            Step(name="Discard sample", module="transfer", action="transfer", args={"source": "measure.pos", "target": "wc.trash"}),
        ],
    )
