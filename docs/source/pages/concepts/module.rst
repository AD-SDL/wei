========
Modules
========

A WEI Module is a combination of software and (typically) a physical hardware device, which is capable of performing actions as part of a Workflow.

Modules are designed to be independent and composable, such that they can be combined to create Workcells. Modules are also designed to be reusable, such that they can be used in multiple different Workcells, and to control different instances of the same device in a single Workcell.


The WEI Module Interface
========================

All Modules must implement the WEI Module Interface, which is a set of methods that allow the Module to be communicated with and controlled by WEI. The interface is protocol agnostic, with current support for implementations in REST, ROS 2, TCP, and ZeroMQ.

A Module must implement the following methods:

Action
------

The Action method is called by WEI to trigger a specified Action on the device or instrument controlled by the Module.

The Action argument should accept the following parameters:

- `action_handle`: The name of the action to be performed.
- `action_vars`: A dictionary of variables specific to the action in question. The keys of the dictionary are the names of the variables, and the values are the values of the variables.

State
-----

The State method is called by WEI to query the current state of the device or instrument controlled by the Module. It should return a dictionary of the current state of the device or instrument.

The status returned by this endpoint should conform to the to the ModuleStatus enum, which is defined in the `wei` package.

About
-----

The About method is called by WEI to query the Module for information about itself. It should return a dictionary of information about the Module, which should comply with the ModuleAbout specification defined in the `wei` package.

Resources
---------

The Resources method is called by WEI to query the Module for information about the resources it controls. This method is not yet standardized, and is currently under development.
