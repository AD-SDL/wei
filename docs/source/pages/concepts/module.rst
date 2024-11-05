========
Modules
========

A WEI Module is a combination of software and a (typically) physical device (e.g. an instrument, robot, etc.), which is capable of performing actions as part of :doc:`/pages/concepts/workflow`.

Modules are designed to be:

- *Independent*: each module can act without relying on any other module.
- *Self-contained*: everything needed to integrate a single device is contained within that module
- *Composable*: multiple modules can be easily combined to create Workcells.
- *Portable and Reusable*: so they can be used in different workcells, or repeatedly in the same workcell to control multiple instances of a device.

.. figure:: /assets/module_logic.png

    An illustration of the hierarchical structure of a WEI Module. The standard Methods, depicted at the top, provide a standardized way to interact with the Device controlled by the Module.

The WEI Module Interface
========================

All Modules must implement the WEI Module Interface, which is a set of methods that allow the Module to be communicated with and controlled by WEI. The interface is protocol agnostic, with current support for implementations in REST, and legacy implementations in ROS 2, TCP, and ZeroMQ.

A Module must implement the following methods:

Action
------

The Action method is called by WEI to trigger a specified Action on the device or instrument controlled by the Module.

The Action method should accept the following parameters:

- ``name``: The name of the specific action to be performed.
- ``args``: A JSON-serializable dictionary of variables specific to the action in question. The keys and values of the dictionary correspond to the names and values of the variables, respectively.
- ``files`` (Optional): Some modules require one or more files as inputs, typically instruments that support their own protocols/workflows. These files are uploaded as Form data.

State
-----

The State method is called by WEI to query the current state of the device or instrument controlled by the Module. It should return a dictionary of the current state of the module that conforms to :class:`wei.types.module_types.ModuleState`.

It should, at the very least, return the following keys:

- ``status``: the status of the module, a dictionary of the form ``Dict[``:class:`wei.types.ModuleStatus` ``: bool]``, for example: ``{"READY": False, "ERROR": True, "BUSY": False}``. Flags that aren't set are assumed to be ``False``.
- ``error``: a string or list of strings describing any error that has occurred, or ``None`` if no error has occurred.

Additional keys may be provided on a per-module basis, allowing users and the system to monitor the state of the module and the device it controls in detail.

About
-----

The About method is called by WEI to query the Module for information about itself. It should return a dictionary of information about the Module, which should conform to the :class:`wei.types.ModuleAbout` specification.

This ``about`` method is both a very useful affordance for WEI users, allowing them to more easily parse how to use a particular module, and a valuable piece of functionality for the WEI Engine. Among other benefits, it allows the WEI Engine to pre-validate workflows, reducing runtime errors and failed workflow runs.

Resources
---------

.. admonition:: Coming Soon!

    This method is not yet standardized, and is currently under active development.

The Resources method is called by the WEI server to query the Module for information about the resources it controls.

Next Steps
==========

To learn how to develop your own Modules, consult the :doc:`/pages/how-to/module` guide.
