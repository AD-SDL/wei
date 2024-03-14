=================
Quickstart Guide
=================

TODO: Fold into Quickstart Guide/how-to's

Setting Up
----------

#. To install the system and run the server, please follow the instructions `here <https://github.com/AD-SDL/wei#development-install>`_.

Creating a Workflow
-------------------

Once you have the server up and running, it is time to define a Workflow! Workflows in ``wei`` are defined in YAML files. The structure of a workflow YAML file is as follows:

- ``metadata``: Information about the workflow such as its name, author, version, and general info.
- ``workcell``: The path to the workcell configuration file (another YAML file).
- ``modules``: A list of modules that will be used in the workflow.
- ``flowdef``: The actual sequence of commands that make up the workflow. Each command includes the module to be used, the command to execute, any arguments required by the command, checks (validations or conditions to meet), and a comment.

Here's a sample workflow YAML file:

.. code-block:: yaml

  metadata:
  name: PCR - Workflow
  author: Casey Stone, Rafael Vescovi
  info: Initial PCR workflow for RPL workcell
  version: 0.1

  workcell: test_workcell.yaml

  modules:
    - name: ot2_pcr_alpha
    - name: pf400
    - name: peeler
    - name: sealer
    - name: biometra
    - name: sciclops

  flowdef:
    #This defines a step in the workflow. Each step represents an action on a single module
    #This is a human legible name for the step
    - name: Sciclops gets plate from stacks
    #This defines which module the action will run on, in this case, a Huson Sciclops PlateCrane robot that has stacks to store wellplates
      module: sciclops
    #This tells the module which action in its library to run, in this case grabbing a wellplate from one of the storage tower
      command: get_plate
    #These arguments specify the parameters for the action above, in this case, which tower the arm will pull a plate from.
      args:
        loc: "tower1"
    #This represents checks that will take place before the system runs, in this case, there are none specified
      checks: null
    #This is a place for additional notes
      comment: Stage pcr plates

    - name: PF400 Moves plate from Sciclops to OT2
      module: pf400
      command: transfer
      args:
        source: sciclops.positions.exchange
        target: ot2_pcr_alpha.positions.deck2
        source_plate_rotation: narrow
        target_plate_rotation: wide
      checks: null
      comment: Place plate in ot2

    - name: The OT2 runs its protocol
      module: ot2_pcr_alpha
      command: run_protocol
      args:
        config_path: tests/test_ot2_protocol.yaml
      checks: RESOURCE_CHECK
      comment: Run a protocol on the OT2

    - name: Move the plate from OT2 to Sciclops
      module: pf400
      command: transfer
      args:
        source: ot2_pcr_alpha.positions.deck2
        target: sciclops.positions.exchange
        source_plate_rotation: wide
        target_plate_rotation: narrow
      checks: null
      comment: Move from the OT2 back to the Sciclops


Running a Workflow
------------------

To execute a workflow, you need to use the ``Experiment`` class from ``wei`` and provide the path to your
workflow file. This script is defined in wei/examples/run_example.py, and runs the workflow above while simulating communication with the real robots.

.. code-block:: python

  #!/usr/bin/env python3

  from pathlib import Path
  from wei import Experiment
  from wei.core.data_classes import WorkflowStatus

  def main():
      #The path to the Workflow definition yaml file
      wf_path = Path('../tests/test_workflow.yaml')
      #This defines the Experiment object that will communicate with the server for workflows
      exp = Experiment('127.0.0.1', '8000', 'Example Program')
      #This initilizes the connection to the server and the logs for this run of the program.
      exp.register_exp()
      #This runs the simulated_workflow a simulated workflow
      flow_info = exp.run_job(wf_path.resolve(), simulate=True)
      print(flow_info)
      #This checks the state of the experiment in the queue
      flow_status = exp.query_job(flow_info['job_id'])
      #This will print out the queued job
      print(flow_status)
      #This will wait until the flow has run and then print out the final result of the flow
      while flow_status["status"] != WorkflowStatus.COMPLETED:
      flow_status = exp.query_job(flow_info['job_id'])
      print(flow_status)

  if __name__ == "__main__":
      main()




Workcell Configuration
----------------------

The workcell file in ``wei`` describes the robotic system in the real world. It is referenced in the workflow file and provides configuration details about each module involved in a workflow.

The workcell file is organized into two main sections:

1. ``config``: Contains configuration settings for the workcell.
2. ``modules``: Describes the list of modules available in the workcell, including their names, types, configurations, and positions.

Workcell Configuration (`config`)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The `config` section contains the following fields:

- ``ros_namespace``: The namespace for ROS.
- ``funcx_local_ep``: The FuncX local endpoint ID.
- ``globus_local_ep``: The Globus local endpoint ID.
- ``globus_search_index``: The Globus Search index ID.
- ``globus_portal_ep``: The Globus Portal endpoint ID.
- ``globus_group``: The Globus group ID.

Module Configuration (`modules`)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Each module in the `modules` section is described by the following fields:

- ``name``: The unique name of the module.
- ``type``: The type of the module. Types include `wei_ros_node`, `wei_ros_camera`, and others.
- ``model``: The model of the module (optional).
- ``config``: Additional configuration details for the module, such as the associated ROS node.
- ``positions``: Predefined positions that the module can move to (if applicable). Positions are listed as arrays of numeric values.

Here's a sample excerpt from a workcell configuration file:

.. code-block:: yaml

   config:
     ros_namespace: rpl_workcell
     funcx_local_ep: "<compute-endpoint-id>"
     globus_local_ep: "<globus-endpoint-id>"
     globus_search_index: "<search-index-id>"
     globus_portal_ep: "<portal-endpoint-id>"
     globus_group: "<group-id>"

   modules:
     - name: pf400
       type: wei_ros_node
       model: pf400
       config:
         ros_node: "/std_ns/pf400Node"
       positions:
         trash: [218.457, -2.408, 38.829, 683.518, 89.109, 995.074]

     - name: pf400_camera_right
       type: wei_ros_camera
       config:
         ros_node: "/std_ns/pf400_camera_right"

For more details on how to define a module and its positions, refer to the detailed ``wei`` documentation.


Next Steps
----------

Congratulations, you've taken your first steps with ``wei``! More information to come soon!
