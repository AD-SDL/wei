======================================================
Introduction to the Workflow Execution Interface (WEI)
======================================================

The Workflow Execution Interface (WEI) is a set of tools and software intended to enable Self Directed Laboratories and Autonomous Scientific Discovery. In order to do this WEI provides:

- A common interface for controlling and communicating with scientific instruments, robots, devices, and software
- A workflow scheduler and executor that can run scientific workflows using these interfaces to automate laboratory processes
- A python library to help implement these interfaces for new devices
- A python client for integrating these workflows into python-based experiment applications

The system is designed to be modular and extensible, so that it can be used with a wide variety of scientific instruments and devices. It is also designed to be distributed, so that it can be used in a variety of laboratory environments, from small academic labs to large research facilities.

Core Concepts
=============

- :doc:`/pages/concepts/workcell`: A collection of scientific instruments, robots, devices, and software that are used together to perform scientific workflows. A WEI workcell is defined using a YAML file that includes all the information necessary to complete tasks on the workcell, including a list of the modules that are compose the workcell.
- :doc:`/pages/concepts/workflow`: A workflow is a sequence of steps to be performed on a workcell. A WEI workflow is defined using a YAML file that includes a list of steps, each of which specifies an action to perform on a module in the workcell.
- :doc:`/pages/concepts/module`: A module is a software package that controls a scientific instrument, robot, or device, and implements WEI's Module Interface. A WEI module consists of the software implementing the interface, the physical hardware being controlled, and any drivers or integrations used to control that hardware.
- :doc:`/pages/concepts/experiment`: An experiment is a collection of workflow runs and related logic that utilizes WEI to control a workcell. Experiment applications are able to run workflows on the workcell, analyze the results, and iterate to pursue closed-loop autonomous discovery.
- :doc:`/pages/concepts/datapoints`: A datapoint is any piece of data collected by the system during an experiment. These datapoints primarily come from instrument measurements, but can also include metadata, logs, and other information collected during the experiment.

.. graphviz:: /graphs/sdl_architecture_example.dot


Next Steps
==========

- To learn how to install and use WEI, consult the :doc:`/pages/quickstart`.
- To delve deeper into the Core Concepts underlying WEI, consult the :doc:`/pages/concepts/index`.
