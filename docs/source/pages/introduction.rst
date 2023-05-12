=======================
Introduction to RPL WEI
=======================

WEI is a Python-based tool designed to automate and manage workflows in a modular workcell environment.
This tool leverages ROS (Robot Operating System) for inter-module communication and FuncX, a 
function-as-a-service platform, for distributed computation. It is particularly geared towards managing 
complex workflows in scientific research and laboratory environments.

WEI allows you to define workflows in YAML format. Each workflow comprises a sequence of actions 
(commands), each performed by a specific module. A module represents an individual hardware or 
software component in the workcell. This modular approach provides the flexibility to design and 
implement diverse workflows across a variety of domains. 

Quickstart Guide
=================

Setting Up
----------

#. Make sure you have Python 3 installed on your system. You can download it from `Python's official website <https://www.python.org/downloads/>`_.

#. WEI is still in development, for installation instructions, please visit the `Github repository <https://github.com/AD-SDL/rpl_wei#development-install>`_. 

Creating a Workflow
-------------------

Workflows in rpl_wei are defined in YAML files. The structure of a workflow YAML file is as follows:

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
       comment: Start the module1

Running a Workflow
------------------

To execute a workflow, you need to use the ``WEI`` class from rpl_wei and provide the path to your 
workflow file. Here's a basic script to run a workflow:

.. code-block:: python

   #!/usr/bin/env python3

   import logging
   from pathlib import Path
   from rpl_wei.wei_workcell_base import WEI

   def main():
       wf_path = Path('./path_to_workflow.yaml')

       wei_client = WEI(
           wf_config=wf_path.resolve(), 
           workcell_log_level=logging.ERROR, 
           workflow_log_level=logging.ERROR,
       )

       payload={}
       run_info = wei_client.run_workflow(payload=payload)

   if __name__ == "__main__":
       main()

The above script will run the workflow defined in ``path_to_workflow.yaml``.

Next Steps
----------

Congratulations, you've taken your first steps with rpl_wei! More information to come soon!
