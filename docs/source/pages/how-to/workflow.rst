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

The modules section is simply a list of the names of modules that will be used in the workflow. WEI will use this list to ensure that the modules are available in the workcell, and to ensure that the workflow is valid.

Example Module List
^^^^^^^^^^^^^^^^^^^

.. code-block:: yaml

    modules:
        - transfer
        - synthesis
        - measure

Flow Definition
---------------

The flow definition is the heart of the workflow. It is a list of dictionaries, each of which represents a single step in the workflow.

Each step includes:

- The human-readable name of the step
- The name of the module that will be used to execute the step
- The desired action to be taken by that module
- Any arguments the module will need to execute the action (optional, this can be left out if the module does not require any arguments)
- Any files that the module will need to execute the action (optional, this can be left out if the module does not require any files).

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
            foo: 2.0
            bar: 0.5
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
            foo: 2.0
            bar: 0.5
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
