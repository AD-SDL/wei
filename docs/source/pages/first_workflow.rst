Quickstart Guide
=================

Setting Up
----------

#. To install the system and run the server, please follow the instructions `here <https://github.com/AD-SDL/rpl_wei#development-install>`_. 

Creating a Workflow
-------------------

Once you have the server up and running, it is time to define a Workflow! Workflows in ``rpl_wei`` are defined in YAML files. The structure of a workflow YAML file is as follows:

- ``metadata``: Information about the workflow such as its name, author, version, and general info.
- ``workcell``: The path to the workcell configuration file (another YAML file).
- ``modules``: A list of modules that will be used in the workflow.
- ``flowdef``: The actual sequence of commands that make up the workflow. Each command includes the module to be used, the command to execute, any arguments required by the command, checks (validations or conditions to meet), and a comment.

Here's a sample workflow YAML file:

.. code-block:: yaml

   metadata:
     name: Sample Workflow
     author: John Doe
     info: A basic workflow for demonstration
     version: 1.0

   workcell: /path/to/workcell.yaml

   modules:
     - name: module1
     - name: module2
     - name: module3

   flowdef:
     - name: Command 1
       module: module1
       command: start
       args: null
       checks: null
       comment: Run a command on module1

Running a Workflow
------------------

To execute a workflow, you need to use the ``Experiment`` class from ``rpl_wei`` and provide the path to your 
workflow file. Here's a basic script to run a workflow:

.. code-block:: python

   #!/usr/bin/env python3

   import logging
   from pathlib import Path
   from rpl_wei.exp_app import Experiment

   def main():
      exp = Experiment('127.0.0.1', '8000', 'Test_Experiment')
      exp.register_exp() #parser
      payload={}
      test = experiment.run_job(Path('path_to_workflow.yaml'),
      payload=payload, simulate=True)

   if __name__ == "__main__":
       main()

The above script will run the workflow defined in ``path_to_workflow.yaml``. The simulate param

Workcell Configuration
----------------------

The workcell file in ``rpl_wei`` describes the robotic system in the real world. It is referenced in the workflow file and provides configuration details about each module involved in a workflow. 

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

For more details on how to define a module and its positions, refer to the detailed ``rpl_wei`` documentation.


Next Steps
----------

Congratulations, you've taken your first steps with ``rpl_wei``! More information to come soon!
