=================
The WEI Dashboard
=================

The WEI Dashboard is a web-based interface for monitoring and controlling WEI workcells. It provides a visual representation of the workcell; information about the Modules, Locations, Workflows, and Experiments related to that workcell; and administrative controls.

.. figure:: /assets/dashboard.png

   The WEI Dashboard, showing a visual representation of a workcell.

Accessing the WEI Dashboard
=======================

The Dashboard can be accessed by navigating to the URL of the WEI server (the same hostname and port used in the ExperimentClient for submitting workflows) in a web browser.

Dashboard Tabs
==============

The Workcells Tab
-----------------

The Workcell Tab allows the user to get a quick view of the state of the workcell, including the status of each Module, Location, and recent Workflows.

These elements can be clicked on to get more detailed information about them.

At the top of each Workcell there are administrative controls, allowing you to:

- Pause and Resume the entire workcell
- Cancel all running workflows on the workcell
- Reset the workcell, which will reset all modules and locations to their initial state
- Lock and Unlock the workcell, which will prevent any new actions from being started
- Shutdown the Workcell, stopping the server
- Safety Stop the Workcell, which will stop all running actions immediately.

The Workflows Tab
-----------------

This tab provides a table of all Workflows that have been run on the workcell, with detailed information about each Workflow available by clicking on the corresponding row. The table can be sorted by any of the columns to make finding workflows as easy as possible.

The Experiments Tab
-------------------

The Experiments Tab provides a table of all Experiments that have been run on the workcell, with detailed information about each Experiment available by clicking on the corresponding row.

Dashboard Modals
================

The dashboard includes a number of modals that provide additional information.

The Module Modal
----------------

The Module Modal provides detailed information about a specific Module, including its current state, the actions it can perform, and the resources it controls.

Expanding an available action will show information about supported arguments and files. Actions can be run directly from this view with "Send Action". In addition, YAML-formatted workflow steps can be copied directly from the modal with "Show Copyable Workflow Step -> Copy YAML Step to Clipboard".

At the top of the module modal, you can find administrative controls, allowing you to:

- Pause and Resume the current action on the module
- Cancel the current action on the module
- Reset the module
- Lock and Unlock the module, which will prevent any new actions from being started
- Shutdown the module
- Safety Stop the module, which will stop all running actions immediately.
